"""평가 파이프라인 — 한 문항을 (mode, model)로 평가하고 버전핀과 함께 RunRecord 생성.

버전핀(model·question_hash·prompt_version·scaffold)은 모든 RunRecord에 박는다(재현성·비교가능성).
모델/judge 클라이언트는 주입 가능(테스트 stub) — 미주입 시 registry에서 생성.
한 문항 실패는 RunRecord.error에 기록하고 계속(배치 견고성).
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

from .prompts import build_prompt
from .models.registry import get_model, get_spec
from .grading import code_grader
from .grading.judge import judge_answer
from .grading.aggregate import combine


@dataclass
class RunRecord:
    question_id: str
    question_hash: str
    model: str
    mode: str
    prompt_version: str
    answer_text: str
    code_scores: list
    judge: dict | None
    final: dict
    scaffold: dict
    accessed_at: str | None = None
    error: str | None = None
    latency_s: float = 0.0
    domain: str = ""
    task_type: str = ""
    agent_steps: list = field(default_factory=list)
    grounding: dict = field(default_factory=dict)


def _run_agent(cl, system: str, user: str, tool_executor, *,
               max_steps: int = 4, require_authority: bool = False):
    """ReAct 텍스트 루프 (ADR 0005, 강제 게이트 ADR 0006). 모델이 [도구] 호출 →
    실행기로 실행 → [관측] 주입 반복. [도구]가 없으면 최종 답. require_authority면
    권위 도구(법령조문/기준서문단) 1회도 없이 [최종]을 내면 거부·재촉(nudge ≤2).
    max_steps 도구 라운드 후엔 도구 없이 최종을 강제한다.
    반환: (final_text, total_latency, agent_steps, error|None)."""
    from .agent.tools import parse_tool_call
    from .grading.grounding import AUTHORITY_TOOLS
    convo = user
    steps: list = []
    latency = 0.0
    nudges = 0
    while len(steps) < max_steps:
        resp = cl.complete(system, convo)
        latency += getattr(resp, "latency_s", 0.0)
        text = resp.text or ""
        if not text:
            err = resp.raw_meta.get("error") if hasattr(resp, "raw_meta") else "empty response"
            return "", latency, steps, str(err)
        call = parse_tool_call(text)
        if call is None:
            authority_used = any(s["tool"] in AUTHORITY_TOOLS for s in steps)
            if require_authority and not authority_used and nudges < 2:
                nudges += 1
                convo += (f"\n\n[모델]\n{text}\n\n[지시] 최종 답 전에 반드시 법령조문 또는 "
                          "기준서문단 도구로 근거를 1회 이상 확인해야 한다. 추측 금지. 지금 [도구]로 조회하라.")
                continue
            return text, latency, steps, None  # 최종(권위 충족 또는 nudge 소진)
        obs = tool_executor(call)
        steps.append({"step": len(steps) + 1, "tool": call.name, "arg": call.arg, "observation": obs})
        convo += f"\n\n[모델]\n{text}\n\n[관측]\n{obs}"
    # 스텝 상한 도달 — 도구 없이 최종 강제(추가 도구 호출은 무시됨을 명시)
    resp = cl.complete(system, convo + "\n\n스텝 상한에 도달했다. 도구를 더 쓸 수 없으니, 지금까지의 "
                       "[관측]만으로 [최종] 답을 작성하라. 추가 [도구] 호출은 무시된다.")
    latency += getattr(resp, "latency_s", 0.0)
    final = resp.text or ""
    if not final:
        return "", latency, steps, "empty final"
    if parse_tool_call(final) is not None:
        # 상한 후에도 도구만 호출 = 최종 답 미생성 → 성공으로 채점하지 않는다(캡의 목적).
        return final, latency, steps, "스텝 상한 초과: 최종 답 미생성"
    return final, latency, steps, None


def run_one(question: dict, mode: str, model_name: str, *,
            client=None, judge_model_name: str | None = None, judge_client=None,
            accessed_at: str | None = None, tool_executor=None) -> RunRecord:
    spec = {}
    try:
        spec = get_spec(model_name)
    except Exception:
        pass
    prompt_version = str(spec.get("prompt_version", "v1"))
    qid = question.get("id", "<no-id>")
    qhash = question.get("hash", "")
    dom = question.get("domain", "")
    tt = question.get("task_type", "")

    context = None
    used_acc = None
    if mode == "rag":
        # 지연 import — closed_book/agent 경로는 네트워크 의존 없음
        from .rag.retriever import retrieve_context
        rc = retrieve_context(question, accessed_at=accessed_at or "unknown")
        context = rc["context_text"]
        used_acc = rc["accessed_at"]

    scaffold = {
        "prompt_version": prompt_version,
        "judge_model": judge_model_name,
        "retriever_used": mode == "rag",
    }

    agent_steps: list = []
    agent_flags: list = []
    grounding: dict = {}
    try:
        cl = client or get_model(model_name)
        system, user = build_prompt(question, mode, context=context)
        if mode in ("agent", "agent_forced"):
            from .agent.tools import make_executor
            from .grading.grounding import grounding_report
            te = tool_executor or make_executor(used_acc or accessed_at)
            answer_text, latency, agent_steps, aerr = _run_agent(
                cl, system, user, te, require_authority=(mode == "agent_forced"))
            if aerr:  # 빈 응답/스텝상한 초과 등 — 도구호출을 최종답으로 오채점하지 않는다
                return RunRecord(qid, qhash, model_name, mode, prompt_version, "",
                                 [], None, {}, scaffold, used_acc, error=str(aerr),
                                 latency_s=latency, domain=dom, task_type=tt,
                                 agent_steps=agent_steps)
            grounding = grounding_report(answer_text, agent_steps)
            if mode == "agent_forced":  # ADR 0006 근거매칭 감점
                if not grounding["authority_used"]:
                    agent_flags.append("forced_tool_unmet")
                elif grounding["cited"] and (grounding["grounded_ratio"] or 0) < 0.5:
                    agent_flags.append("ungrounded_citation")
            if agent_steps:  # 도구 사용 기록을 채점 대상에 명시(판정자가 tool_process 평가)
                rec = "\n".join(f"- {s['tool']}: {s['arg']}" for s in agent_steps)
                answer_text = f"{answer_text}\n\n---\n[도구 사용 기록]\n{rec}"
        else:
            resp = cl.complete(system, user)
            answer_text = resp.text
            latency = getattr(resp, "latency_s", 0.0)
            if not answer_text:
                err = resp.raw_meta.get("error") if hasattr(resp, "raw_meta") else "empty response"
                return RunRecord(qid, qhash, model_name, mode, prompt_version, "",
                                 [], None, {}, scaffold, used_acc, error=str(err),
                                 latency_s=latency, domain=dom, task_type=tt)
    except Exception as e:
        return RunRecord(qid, qhash, model_name, mode, prompt_version, "",
                         [], None, {}, scaffold, used_acc, error=f"model call: {e}",
                         domain=dom, task_type=tt)

    cg = code_grader.grade(question, answer_text)
    code_scores = cg["scores"]
    flags = list(cg["flags"]) + agent_flags

    judge = None
    if judge_model_name or judge_client:
        try:
            jr = judge_answer(question, answer_text,
                              judge_model_name=judge_model_name or "judge",
                              candidate_model_name=model_name, client=judge_client)
            judge = {"scores": jr.scores, "memo": jr.memo,
                     "fatal_flags": jr.fatal_flags, "judge_model": jr.judge_model}
            if jr.error:  # 파싱 실패(미채점) — 사유·원문 보존, 집계 제외 신호
                judge["error"] = f"judge: {jr.error}"
                judge["raw_response"] = jr.raw_response
        except Exception as e:  # judge 호출(API) 실패 — 원문 없음
            judge = {"error": f"judge: {e}", "scores": {}, "fatal_flags": []}

    judge_obj = None
    if judge and "scores" in judge and not judge.get("error"):
        from .grading.judge import JudgeResult
        judge_obj = JudgeResult(scores=judge.get("scores", {}), memo=judge.get("memo", {}),
                                fatal_flags=judge.get("fatal_flags", []),
                                judge_model=judge.get("judge_model", judge_model_name or ""))
    final = combine(code_scores, judge_obj, question.get("task_type", ""), extra_flags=flags)
    if judge and judge.get("error"):
        # judge 실패 → final.total 0.0 은 미채점이지 정당한 0점이 아니다. 집계 제외 마커.
        final["judge_error"] = True

    return RunRecord(qid, qhash, model_name, mode, prompt_version, answer_text,
                     code_scores, judge, final, scaffold, used_acc, latency_s=latency,
                     domain=dom, task_type=tt, agent_steps=agent_steps, grounding=grounding)


def _safe_run_one(question: dict, mode: str, model_name: str, **kw) -> RunRecord:
    """run_one 래퍼 — 예기치 못한 예외가 배치 전체를 죽이지 않게 RunRecord.error 로 흡수."""
    try:
        return run_one(question, mode, model_name, **kw)
    except Exception as e:  # pragma: no cover - 방어적
        return RunRecord(question.get("id", "<no-id>"), question.get("hash", ""),
                         model_name, mode, "v1", "", [], None, {}, {}, None,
                         error=f"run_one: {e}", domain=question.get("domain", ""),
                         task_type=question.get("task_type", ""))


def run_batch(questions: list[dict], modes: list[str], model_name: str, *,
              max_workers: int = 8, **kw) -> list[RunRecord]:
    """문항×모드를 평가. 각 run_one 은 blocking subprocess(모델·judge) = I/O bound →
    ThreadPoolExecutor 로 병렬화. 출력 순서는 입력 순서와 동일(ex.map). max_workers<=1 이면 순차."""
    tasks = [(q, mode) for q in questions for mode in modes]
    if max_workers <= 1 or len(tasks) <= 1:
        return [_safe_run_one(q, mode, model_name, **kw) for q, mode in tasks]
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        return list(ex.map(lambda t: _safe_run_one(t[0], t[1], model_name, **kw), tasks))
