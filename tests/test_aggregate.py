"""aggregate + judge 순수 헬퍼 결정론 테스트(LLM 호출 없음)."""
from __future__ import annotations

from pathlib import Path

from ktaxbench.loader import load_questions
from ktaxbench.grading.code_grader import CodeScore
from ktaxbench.grading.aggregate import combine, statement_level_score, pass_caret_k
from ktaxbench.grading.judge import (
    JudgeResult, self_eval_warning, build_judge_prompt, parse_judge_json,
)

_DATA = str(Path(__file__).resolve().parents[1] / "data" / "sample-questions-v0.1.jsonl")
_BY_ID = {q["id"]: q for q in load_questions(_DATA)}


def test_combine_calculation_full():
    code = [CodeScore("conclusion_accuracy", 20, 20, ""),
            CodeScore("calculation_or_process", 40, 40, "")]
    judge = JudgeResult(scores={"legal_basis": 15, "fact_handling": 10,
                                "practicality": 10, "clarity": 5},
                        memo={}, fatal_flags=[], judge_model="j")
    out = combine(code, judge, "calculation")
    assert out["total"] == 100.0
    assert out["grade"] == "A"


def test_combine_code_priority():
    code = [CodeScore("conclusion_accuracy", 10, 20, "")]
    judge = JudgeResult(scores={"conclusion_accuracy": 20}, memo={},
                        fatal_flags=[], judge_model="j")
    out = combine(code, judge, "calculation")
    assert out["per_dimension"]["conclusion_accuracy"] == 10.0  # code 우선


def test_combine_deduction_applied():
    judge = JudgeResult(scores={}, memo={}, fatal_flags=["fake_source"], judge_model="j")
    out = combine([], judge, "citation")
    assert out["deduction"] == -20


def test_statement_level():
    assert statement_level_score([True, True, False, True]) == 0.75
    assert statement_level_score([]) == 0.0


def test_pass_caret_k():
    assert pass_caret_k(2, 1, 2) == 1.0
    assert pass_caret_k(1, 1, 2) == 0.5
    assert pass_caret_k(1, 2, 2) == 0.0
    assert pass_caret_k(3, 2, 3) == 1.0


def test_self_eval_warning():
    assert self_eval_warning("m", "m") is not None
    assert self_eval_warning("a", "b") is None


def test_build_judge_prompt_includes_reference():
    q = _BY_ID["ktb-corp-tax-0003"]
    system, user = build_judge_prompt(q, "후보 답안 텍스트")
    assert q["answer"]["final_answer"][:10] in user      # 기준 정답 포함
    assert "calculation_or_process" in user              # 루브릭 차원 포함
    assert "후보 답안 텍스트" in user


def test_parse_judge_json():
    txt = '설명...\n{"scores": {"legal_basis": 30}, "memo": {}, "fatal_flags": []}\n끝'
    data = parse_judge_json(txt)
    assert data["scores"]["legal_basis"] == 30
