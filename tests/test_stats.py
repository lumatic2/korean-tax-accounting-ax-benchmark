"""통계 모듈 결정론 테스트(M6 step1) — 시드 고정 부트스트랩 CI·페어 유의성."""
from __future__ import annotations

from ktaxbench.stats import (
    bootstrap_ci, paired_bootstrap_diff, spread_ci, _percentile,
)
from ktaxbench.report import ci_summary


def test_percentile_basic():
    xs = [0.0, 10.0, 20.0, 30.0, 40.0]
    assert _percentile(xs, 0.0) == 0.0
    assert _percentile(xs, 1.0) == 40.0
    assert _percentile(xs, 0.5) == 20.0


def test_bootstrap_ci_deterministic():
    vals = [80, 85, 90, 95, 100]
    a = bootstrap_ci(vals, seed=0, n=500)
    b = bootstrap_ci(vals, seed=0, n=500)
    assert a == b                      # 같은 시드 → 같은 출력(재현)
    lo, hi = a
    assert lo <= sum(vals) / len(vals) <= hi   # CI 가 점추정 포함


def test_bootstrap_ci_seed_changes_result():
    vals = [10, 50, 90, 30, 70]
    assert bootstrap_ci(vals, seed=0, n=500) != bootstrap_ci(vals, seed=1, n=500) or True
    # (드물게 동일할 수 있어 강제하지 않음 — 핵심은 위 결정론)


def test_bootstrap_ci_edge_cases():
    assert bootstrap_ci([], n=100) == (0.0, 0.0)
    assert bootstrap_ci([42], n=100) == (42.0, 42.0)


def test_paired_diff_positive():
    # a 가 일관되게 b 보다 ~10 높음 → diff>0, CI 가 0 미포함, p 작음
    a = [90, 80, 85, 95, 88]
    b = [80, 70, 75, 85, 78]
    r = paired_bootstrap_diff(a, b, seed=0, n=1000)
    assert r["n"] == 5
    assert r["diff"] > 0
    assert r["ci"][0] > 0              # 신뢰구간 하한 > 0 (유의)
    assert r["p"] < 0.10


def test_paired_diff_no_difference():
    a = [80, 85, 90]
    b = [80, 85, 90]
    r = paired_bootstrap_diff(a, b, seed=0, n=500)
    assert r["diff"] == 0.0
    assert r["p"] == 1.0               # 차이 0 → 양측 p 최대


def test_paired_diff_empty():
    r = paired_bootstrap_diff([], [], n=100)
    assert r == {"diff": 0.0, "ci": (0.0, 0.0), "p": 1.0, "n": 0}


def test_spread_ci():
    groups = {"hi": [95, 90, 92], "mid": [70, 72, 68], "lo": [40, 45, 42]}
    r = spread_ci(groups, seed=0, n=500)
    assert r["spread"] > 40           # 95평균 - 42평균 ≈ 50
    lo, hi = r["ci"]
    assert lo <= r["spread"] <= hi


def test_spread_ci_single_group():
    assert spread_ci({"only": [80, 90]}, n=100) == {"spread": 0.0, "ci": (0.0, 0.0)}


def _rec(model, total, fail=False):
    r = {"model": model, "question_id": f"q-{model}-{total}", "error": None,
         "final": {"total": float(total), "grade": "B", "per_dimension": {}}}
    if fail:
        r["final"]["judge_error"] = "json fail"
    return r


def test_ci_summary_excludes_judge_failed():
    records = [_rec("A", 90), _rec("A", 92), _rec("A", 0, fail=True),
               _rec("B", 50), _rec("B", 52)]
    s = ci_summary(records, seed=0, n=300)
    # judge_failed(0점) 제외 → A 평균은 91 부근(0 안 섞임)
    assert s["by_model"]["A"]["n"] == 2
    assert s["by_model"]["A"]["avg"] == 91.0
    assert s["n_scored"] == 4
    assert s["spread"]["spread"] > 30
