"""루브릭 가중치·감점 — docs/rubric-v0.1.md 의 코드판(숫자 일치)."""
from __future__ import annotations

# 유형별 가중치(합=100). docs/rubric-v0.1.md '문항 유형별 가중치 조정'.
_WEIGHTS = {
    "multiple_choice": {
        "conclusion_accuracy": 50, "legal_basis": 20, "fact_handling": 10,
        "risk_handling": 10, "clarity": 10,
    },
    "calculation": {
        "conclusion_accuracy": 20, "calculation_or_process": 40, "legal_basis": 15,
        "fact_handling": 10, "practicality": 10, "clarity": 5,
    },
    "case_reasoning": {
        "conclusion_accuracy": 25, "legal_basis": 20, "fact_handling": 15,
        "practicality": 20, "risk_handling": 15, "clarity": 5,
    },
    # 근거 제시형 / RAG형
    "citation": {
        "conclusion_accuracy": 20, "legal_basis": 35, "fact_handling": 10,
        "practicality": 15, "risk_handling": 15, "clarity": 5,
    },
    "agent_workflow": {
        "conclusion_accuracy": 20, "tool_process": 20, "legal_basis": 20,
        "calculation_or_process": 15, "deliverable_quality": 15, "risk_handling": 10,
    },
}

# short_answer·risk_analysis 등 미지정 유형은 기본 7차원.
_BASE = {
    "conclusion_accuracy": 25, "legal_basis": 20, "calculation_or_process": 15,
    "fact_handling": 10, "practicality": 15, "risk_handling": 10, "clarity": 5,
}

# 감점(총점에서 추가 차감). docs/rubric-v0.1.md '감점/실격 규칙'.
DEDUCTIONS = {
    "fake_source": -20,          # 존재하지 않는 근거 생성
    "ignore_time_basis": -10,    # 기준시점 무시
    "format_violation": -5,      # 요청 형식 미준수
    "disclaimer_evasion": -5,    # 과도한 면책으로 실질 회피
    "assert_without_source": -10,  # 출처 없이 단정
    "forced_tool_unmet": -15,    # agent_forced 인데 권위 도구를 끝까지 안 씀(ADR 0006)
    "ungrounded_citation": -10,  # 인용 조문이 실제 조회된 것과 불일치(기억 인용, ADR 0006)
}

# 등급 컷
GRADE_CUTS = [(90, "A"), (75, "B"), (60, "C"), (0, "D")]


def weights_for(task_type: str) -> dict[str, int]:
    """task_type 의 차원별 배점(합=100)."""
    return dict(_WEIGHTS.get(task_type, _BASE))


def grade_letter(score: float) -> str:
    for cut, letter in GRADE_CUTS:
        if score >= cut:
            return letter
    return "D"
