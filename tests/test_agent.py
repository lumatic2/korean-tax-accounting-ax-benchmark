"""agent 모드 ReAct 루프 재현 테스트 (ADR 0005) — stub 모델·stub 도구(네트워크 없음)."""
from __future__ import annotations

from pathlib import Path

from ktaxbench.loader import load_questions
from ktaxbench.models.base import Response
from ktaxbench.runner import run_one
from ktaxbench.agent.tools import (
    parse_tool_call, ToolCall, make_executor, _extract_article_branch,
)
from ktaxbench.grading.grounding import grounding_report

_DATA = str(Path(__file__).resolve().parents[1] / "data" / "sample-questions-v0.1.jsonl")
_BY_ID = {q["id"]: q for q in load_questions(_DATA)}
_Q = _BY_ID["ktb-mixed-0001"]

_JUDGE = ('{"scores": {"conclusion_accuracy": 15, "tool_process": 15, '
          '"legal_basis": 15, "deliverable_quality": 10}, "memo": {}, "fatal_flags": []}')


class _SeqStub:
    """호출마다 미리 정한 텍스트를 순서대로 반환(마지막은 반복)."""
    def __init__(self, name: str, texts: list[str]):
        self.name = name
        self._texts = list(texts)
        self.calls = 0

    def complete(self, system: str, prompt: str) -> Response:
        t = self._texts[min(self.calls, len(self._texts) - 1)]
        self.calls += 1
        return Response(t, self.name, 0.0, {"returncode": 0})


def _stub_te(call: ToolCall) -> str:
    return f"OBS({call.name}:{call.arg})"


def _judge():
    return _SeqStub("judge", [_JUDGE])


# ── 파서 단위 ────────────────────────────────────────────────────────

def test_parse_tool_call():
    assert parse_tool_call("[도구] 법령조문: 법인세법 제34조") == ToolCall("법령조문", "법인세법 제34조")
    assert parse_tool_call("앞말\n[도구] 계산: 900 * 0.1\n뒷말") == ToolCall("계산", "900 * 0.1")
    assert parse_tool_call("[최종] 결론입니다") is None
    assert parse_tool_call("도구 없이 그냥 답") is None


def test_parse_tool_call_markdown_decorated():
    """실전 모델이 마커를 마크다운으로 감싸도 파싱 — 누락 방지(실전 run 발견)."""
    assert parse_tool_call("**[도구]** 법령조문: 법인세법 제34조") == ToolCall("법령조문", "법인세법 제34조")
    assert parse_tool_call("## [도구] 기준서문단: 1115 문단 74") == ToolCall("기준서문단", "1115 문단 74")
    assert parse_tool_call("- [도구] 계산: 9000-8200") == ToolCall("계산", "9000-8200")


# ── 루프 동작 ────────────────────────────────────────────────────────

def test_agent_tool_then_final():
    cand = _SeqStub("cand", [
        "[도구] 법령조문: 법인세법 제34조",
        "[최종] 결론: 대손충당금은 손금산입 (법인세법 제34조). 누락자료: 채권명세.",
    ])
    rec = run_one(_Q, "agent", "claude-haiku-4-5",
                  client=cand, judge_client=_judge(), judge_model_name="claude-sonnet-4-6",
                  tool_executor=_stub_te)
    assert rec.error is None
    assert len(rec.agent_steps) == 1
    assert rec.agent_steps[0]["tool"] == "법령조문"
    assert rec.agent_steps[0]["observation"] == "OBS(법령조문:법인세법 제34조)"
    assert "[도구 사용 기록]" in rec.answer_text       # 채점 대상에 도구기록 노출
    assert "결론" in rec.answer_text
    assert isinstance(rec.final, dict)                  # 채점이 예외 없이 수행
    assert cand.calls == 2


def test_agent_no_tool_immediate_final():
    cand = _SeqStub("cand", ["[최종] 도구 없이 바로 답한다."])
    rec = run_one(_Q, "agent", "claude-haiku-4-5",
                  client=cand, judge_client=_judge(), judge_model_name="claude-sonnet-4-6",
                  tool_executor=_stub_te)
    assert rec.error is None
    assert rec.agent_steps == []
    assert "[도구 사용 기록]" not in rec.answer_text
    assert "바로 답" in rec.answer_text
    assert cand.calls == 1


def test_agent_step_cap_never_final_is_error():
    """모델이 끝까지 도구만 호출하면 강제-최종도 도구호출 → 성공으로 채점하지 않고 에러(ADR 0005 캡 목적)."""
    cand = _SeqStub("cand", ["[도구] 계산: 1+1"])  # 항상 도구 호출(강제 최종까지)
    rec = run_one(_Q, "agent", "claude-haiku-4-5",
                  client=cand, judge_client=_judge(), judge_model_name="claude-sonnet-4-6",
                  tool_executor=_stub_te)
    assert rec.error is not None
    assert "상한" in rec.error                 # 스텝 상한 초과로 명시
    assert len(rec.agent_steps) == 4          # max_steps 도구 라운드
    assert cand.calls == 5                    # 4 라운드 + 1 강제 최종
    assert rec.answer_text == ""              # 도구호출 텍스트를 답으로 채점하지 않음


def test_agent_step_cap_then_final():
    """스텝 상한에 닿아도 강제-최종에서 [최종]을 내면 정상 채점된다."""
    cand = _SeqStub("cand", ["[도구] 계산: 1+1", "[도구] 계산: 1+1", "[도구] 계산: 1+1",
                             "[도구] 계산: 1+1", "[최종] 상한 후 최종 답."])
    rec = run_one(_Q, "agent", "claude-haiku-4-5",
                  client=cand, judge_client=_judge(), judge_model_name="claude-sonnet-4-6",
                  tool_executor=_stub_te)
    assert rec.error is None
    assert len(rec.agent_steps) == 4
    assert cand.calls == 5
    assert "상한 후 최종" in rec.answer_text


def test_agent_empty_response_is_error():
    cand = _SeqStub("cand", [""])             # 첫 응답이 비면 에러 기록(예외 아님)
    rec = run_one(_Q, "agent", "claude-haiku-4-5", client=cand, tool_executor=_stub_te)
    assert rec.error is not None
    assert rec.answer_text == ""


# ── 실전 실행기 (네트워크 없는 부분만) ────────────────────────────────

def test_extract_article_branch_disambiguates_가지번호():
    """제27조 vs 제27조의2를 가지번호로 정확히 구분(실전 발견: 가지번호 미구분 시 엉뚱한 조문 반환)."""
    law = {"법령": {"조문": {"조문단위": [
        {"조문번호": "27", "조문가지번호": "", "조문내용": "제27조(업무와 관련 없는 비용의 손금불산입) 본문"},
        {"조문번호": "27", "조문가지번호": "2", "조문내용": "제27조의2(업무용승용차 관련비용의 손금불산입 등 특례)",
         "항": [{"항내용": "③ ... 각각 800만원 ..."}]},
    ]}}}
    assert "업무용승용차" in _extract_article_branch(law, "27", "2")
    assert "800만원" in _extract_article_branch(law, "27", "2")
    assert "업무와 관련 없는" in _extract_article_branch(law, "27", None)
    assert _extract_article_branch(law, "99", None) is None


def test_extract_article_branch_skips_장절_제목_전문():
    """章 시작 조문(법인세법 제13조)은 같은 조문번호의 편/장/절 제목 전문이 먼저 와도
    실제 조문(조문여부='조문')을 반환해야 한다(라이브 발견: 제13조→제2장 제목 반환 버그)."""
    law = {"법령": {"조문": {"조문단위": [
        {"조문번호": "13", "조문여부": "전문", "조문내용": "제2장 내국법인의 ... 법인세"},
        {"조문번호": "13", "조문여부": "전문", "조문내용": "제1절 과세표준과 그 계산"},
        {"조문번호": "13", "조문여부": "조문", "조문제목": "과세표준",
         "조문내용": "제13조(과세표준)", "항": [{"항내용": "① ... 100분의 80 ..."}]},
    ]}}}
    out = _extract_article_branch(law, "13", None)
    assert "과세표준" in out
    assert "100분의 80" in out
    assert "제2장" not in out


def test_extract_article_branch_includes_호내용():
    """수치·요건이 항이 아니라 각 호에 있는 조문(필요경비율·세율 등)은 호내용까지 추출해야
    grounding 가능(라이브 발견: 소득세법 시행령 §87 필요경비율 60%가 호에만 있어 누락됨)."""
    law = {"법령": {"조문": {"조문단위": [
        {"조문번호": "87", "조문여부": "조문", "조문제목": "기타소득의 필요경비계산",
         "조문내용": "제87조(기타소득의 필요경비계산)",
         "항": [{"항내용": "① 기타소득의 필요경비는 다음 각 호에 따른다.", "호": [
             {"호번호": "1", "호내용": "1. ... 100분의 80에 상당하는 금액을 필요경비로 한다."},
             {"호번호": "1의2", "호내용": "1의2. 법 제21조제1항제19호 ... 100분의 60에 상당하는 금액을 필요경비로 한다."},
         ]}]},
    ]}}}
    out = _extract_article_branch(law, "87", None)
    assert "100분의 60" in out
    assert "100분의 80" in out


def test_real_executor_calc_and_unknown():
    run = make_executor()
    assert run(ToolCall("계산", "900 * 0.1")) == "90.0"
    assert run(ToolCall("계산", "(1000-200)*3/4")) == "600.0"
    assert "허용되지 않는" in run(ToolCall("계산", "__import__('os')"))   # 안전 가드
    assert "알 수 없는 도구" in run(ToolCall("없는도구", "x"))


# ── 근거매칭 (ADR 0006) ──────────────────────────────────────────────

def test_grounding_report():
    steps = [
        {"tool": "법령조문", "arg": "법인세법 제13조", "observation": "제13조(과세표준) ..."},
        {"tool": "계산", "arg": "1+1", "observation": "2"},
    ]
    g = grounding_report("결론은 제13조 및 제99조에 따라 ...", steps)
    assert g["authority_used"] is True
    assert "제13조" in g["fetched"] and "제99조" not in g["fetched"]
    assert "제13조" in g["grounded"]
    assert "제99조" in g["ungrounded"]
    assert g["grounded_ratio"] == 0.5
    # 실패한 조회는 근거로 치지 않음
    g2 = grounding_report("제5조 참조", [{"tool": "법령조문", "arg": "없는법 제5조",
                                       "observation": "법령 미발견: 없는법"}])
    assert "제5조" not in g2["fetched"]
    assert g2["authority_used"] is True


# ── agent_forced 게이트 (ADR 0006) ──────────────────────────────────

def test_agent_forced_nudge_then_tool():
    """권위 도구 없이 [최종]을 내면 재촉하고, 도구를 쓰면 통과(flag 없음)."""
    cand = _SeqStub("cand", [
        "[최종] 기억으로 바로 답 (제13조)",        # 권위 도구 없음 → nudge
        "[도구] 법령조문: 법인세법 제13조",          # 재촉 후 도구 사용
        "[최종] 결론: 제13조에 따라 ...",            # 근거 일치 최종
    ])
    rec = run_one(_Q, "agent_forced", "claude-haiku-4-5",
                  client=cand, judge_client=_judge(), judge_model_name="claude-sonnet-4-6",
                  tool_executor=_stub_te)
    assert rec.error is None
    assert len(rec.agent_steps) == 1 and rec.agent_steps[0]["tool"] == "법령조문"
    assert "forced_tool_unmet" not in rec.final["flags"]
    assert "ungrounded_citation" not in rec.final["flags"]   # 제13조 인용=조회와 일치
    assert cand.calls == 3


def test_agent_forced_unmet_flagged():
    """끝까지 권위 도구를 안 쓰면 nudge 소진 후 forced_tool_unmet 감점."""
    cand = _SeqStub("cand", ["[최종] 기억으로 답 (제13조)"])   # 항상 최종, 도구 0
    rec = run_one(_Q, "agent_forced", "claude-haiku-4-5",
                  client=cand, judge_client=_judge(), judge_model_name="claude-sonnet-4-6",
                  tool_executor=_stub_te)
    assert rec.error is None
    assert rec.agent_steps == []
    assert cand.calls == 3                                  # 최초 + nudge 2
    assert "forced_tool_unmet" in rec.final["flags"]
    assert rec.final["deduction"] <= -15


def test_agent_forced_ungrounded_citation_flagged():
    """권위 도구는 썼지만 최종이 조회 안 한 조문을 인용하면 ungrounded_citation 감점."""
    cand = _SeqStub("cand", [
        "[도구] 법령조문: 법인세법 제13조",
        "[최종] 결론: 제99조에 따라 ...",                     # 제99조는 조회 안 함
    ])
    rec = run_one(_Q, "agent_forced", "claude-haiku-4-5",
                  client=cand, judge_client=_judge(), judge_model_name="claude-sonnet-4-6",
                  tool_executor=_stub_te)
    assert rec.error is None
    assert "ungrounded_citation" in rec.final["flags"]
    assert "forced_tool_unmet" not in rec.final["flags"]


def test_agent_forced_prompt_has_tools():
    from ktaxbench.prompts import build_prompt
    _, user = build_prompt(_Q, "agent_forced")
    assert "법령조문" in user and "[도구]" in user
