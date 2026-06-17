"""채점 집계 — code(객관) + judge(주관) 결합, statement-level 부분점, pass^k."""
from __future__ import annotations

from math import comb

from .rubric import DEDUCTIONS, grade_letter, weights_for


def combine(code_scores, judge, task_type: str, *, extra_flags=None) -> dict:
    """code-grader(차원 우선) + judge(나머지 차원)를 유형별 가중치로 합산.

    겹치는 차원은 code 우선(결정론). 감점은 fatal_flags(code+judge+extra) 합산 후 적용.
    """
    weights = weights_for(task_type)
    code_by_dim = {s.dimension: s for s in (code_scores or [])}
    judge_scores = dict(judge.scores) if judge else {}

    per_dim: dict[str, float] = {}
    for dim, maxp in weights.items():
        if dim in code_by_dim:
            per_dim[dim] = max(0.0, min(float(code_by_dim[dim].points), float(maxp)))
        elif dim in judge_scores:
            per_dim[dim] = max(0.0, min(float(judge_scores[dim]), float(maxp)))
        else:
            per_dim[dim] = 0.0

    subtotal = round(sum(per_dim.values()), 2)

    flags = list(extra_flags or [])
    if judge:
        flags += list(judge.fatal_flags)
    deduction = sum(DEDUCTIONS.get(f, 0) for f in flags)

    total = max(0.0, round(subtotal + deduction, 2))
    return {
        "per_dimension": per_dim,
        "subtotal": subtotal,
        "deduction": deduction,
        "flags": flags,
        "total": total,
        "grade": grade_letter(total),
    }


def statement_level_score(facts_covered: list[bool]) -> float:
    """사례형 부분점(SteuerEx 차용) — 반영한 사실관계 비율 0~1."""
    if not facts_covered:
        return 0.0
    return round(sum(1 for c in facts_covered if c) / len(facts_covered), 4)


def pass_caret_k(successes: int, k: int, n: int) -> float:
    """pass^k (τ-bench) — n회 중 무작위 k회를 뽑았을 때 모두 성공할 확률.

    = C(successes, k) / C(n, k). k>n 또는 분모 0 이면 0.
    """
    if k <= 0 or k > n or n <= 0:
        return 0.0
    denom = comb(n, k)
    if denom == 0:
        return 0.0
    return round(comb(successes, k) / denom, 4)
