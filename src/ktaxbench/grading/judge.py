"""LLM-judge — 주관 차원 채점. self-eval 가드 필수(judge≠candidate).

순수 헬퍼(build_judge_prompt·parse_judge_json·self_eval_warning)는 테스트 가능.
judge_answer 만 실제 모델을 호출(비결정 → smoke 로 검증).
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass

from .rubric import weights_for
from ..models.registry import get_model


_RAW_CLIP = 2000  # 진단용 원문 보존 상한(레코드 비대화 방지)


@dataclass
class JudgeResult:
    scores: dict       # dimension -> points
    memo: dict         # 주요오류/치명오류/실무위험/개선포인트 (+self_eval_warning)
    fatal_flags: list  # 예: ["fake_source", "ignore_time_basis"]
    judge_model: str
    error: str | None = None         # JSON 파싱/호출 실패 사유 (성공 시 None)
    raw_response: str | None = None  # 실패 시 judge 원문(절단) — 왜 실패했나 사후 진단용


def self_eval_warning(judge_model_name: str, candidate_model_name: str) -> str | None:
    """judge == candidate 면 self-eval 천장 경고 문자열. 아니면 None."""
    if judge_model_name == candidate_model_name:
        return f"self-eval: judge({judge_model_name}) == candidate({candidate_model_name})"
    return None


def build_judge_prompt(question: dict, answer_text: str) -> tuple[str, str]:
    a = question.get("answer", {})
    rubric = question.get("rubric", {})
    dims = weights_for(question.get("task_type", ""))
    crit = "\n".join(f"- {d}: 최대 {p}점" for d, p in dims.items())
    fatal = "\n".join(f"- {e}" for e in rubric.get("fatal_errors", []))
    kp = "\n".join(f"- {k}" for k in a.get("key_points", []))
    cw = "\n".join(f"- {k}" for k in a.get("common_wrong_answers", []))
    system = (
        "당신은 엄정한 한국 세무·회계 채점관이다. 아래 기준 정답과 루브릭에 따라 "
        "후보 답안을 차원별로 채점하라. 반드시 JSON만 출력한다. "
        "출력은 '{' 로 시작해 '}' 로 끝나야 하며, 코드펜스(```)·머리말·설명 문장을 "
        "절대 덧붙이지 마라. JSON 객체 하나만 출력한다."
    )
    user = f"""[기준 정답]
{a.get('final_answer', '')}

[핵심 채점 포인트]
{kp}

[흔한 오답]
{cw}

[루브릭 차원·배점]
{crit}

[치명 오류 — 해당 시 fatal_flags 에 'fake_source'/'ignore_time_basis'/'assert_without_source' 등]
{fatal}

[후보 답안]
{answer_text}

다음 JSON 스키마로만 답하라:
{{"scores": {{"차원명": 점수}}, "memo": {{"주요오류": "", "치명오류": "", "실무위험": "", "개선포인트": ""}}, "fatal_flags": []}}"""
    return system, user


def _extract_json_object(text: str) -> str | None:
    """첫 '{' 부터 균형 맞는 '}' 까지 추출. 문자열 내부 중괄호·이스케이프는 무시.

    greedy 정규식 `\\{.*\\}` 은 trailing prose 의 '}' 까지 물어 json.loads 를 깨뜨린다
    (예: '{...} 이상입니다. {참고}'). 깊이 카운팅으로 첫 객체만 정확히 잘라낸다.
    """
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(text)):
        c = text[i]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
            continue
        if c == '"':
            in_str = True
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    return None


def parse_judge_json(text: str) -> dict:
    # 코드펜스(```json … ``` / ``` … ```) 제거 후 첫 균형 JSON 객체만 추출.
    cleaned = re.sub(r"```(?:json)?", "", text)
    obj = _extract_json_object(cleaned)
    if obj is None:
        raise ValueError("judge 응답에 JSON 없음")
    return json.loads(obj)


def judge_answer(question: dict, answer_text: str, *,
                 judge_model_name: str, candidate_model_name: str,
                 client=None) -> JudgeResult:
    """judge 채점. 파싱 실패 시 예외를 던지지 않고 error·raw_response 가 채워진
    JudgeResult 를 반환한다(미채점). 호출자는 jr.error 로 실패를 가린다 — 빈 scores 를
    정당한 0점으로 둔갑시키지 않기 위함(R4 선행 디버그, [[judge-failure-silent-zero]]).
    원문(raw_response)을 보존해 *왜* 비-JSON 이었는지(세션 cap·절단·prose) 사후 진단.
    """
    system, user = build_judge_prompt(question, answer_text)
    client = client or get_model(judge_model_name)
    warn = self_eval_warning(judge_model_name, candidate_model_name)

    data = None
    last_raw = ""
    # 1회 재촉 재시도(총 2회). 모두 비-JSON 이면 미채점으로 flag.
    for extra in ("", "\n\n주의: 직전 응답이 JSON 형식이 아니었다. 코드펜스·설명 없이 "
                  "'{' 로 시작하는 순수 JSON 객체 하나만 다시 출력하라."):
        resp = client.complete(system, user + extra)
        last_raw = resp.text or ""
        try:
            data = parse_judge_json(last_raw)
            break
        except Exception:
            continue

    memo = dict(data.get("memo", {})) if data else {}
    if warn:
        memo["self_eval_warning"] = warn
    if data is None:
        return JudgeResult(
            scores={}, memo=memo, fatal_flags=[], judge_model=judge_model_name,
            error="judge 응답에 JSON 없음(재시도 후)",
            raw_response=last_raw[:_RAW_CLIP],
        )
    return JudgeResult(
        scores=dict(data.get("scores", {})),
        memo=memo,
        fatal_flags=list(data.get("fatal_flags", [])),
        judge_model=judge_model_name,
    )
