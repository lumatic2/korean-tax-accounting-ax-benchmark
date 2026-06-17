"""부트스트랩 신뢰구간·페어 유의성 — 핵심 수치(spread·RAG차·judge-swap)에 불확실성 동반(M6).

scipy/numpy 의존 없음(경량·재현). random.Random(seed) 로 결정론 → 시드 고정 테스트.
순수 함수 — 레코드 파싱은 호출자(report.ci_summary)가 담당.
"""
from __future__ import annotations

import random
from statistics import mean


def _percentile(sorted_xs: list[float], q: float) -> float:
    """정렬된 표본의 선형보간 percentile (q ∈ [0,1])."""
    if not sorted_xs:
        return 0.0
    if len(sorted_xs) == 1:
        return float(sorted_xs[0])
    idx = q * (len(sorted_xs) - 1)
    lo = int(idx)
    frac = idx - lo
    if lo + 1 < len(sorted_xs):
        return sorted_xs[lo] * (1 - frac) + sorted_xs[lo + 1] * frac
    return float(sorted_xs[lo])


def bootstrap_ci(values, statistic=mean, n: int = 2000, seed: int = 0,
                 alpha: float = 0.05) -> tuple[float, float]:
    """표본 통계량(기본 평균)의 percentile 부트스트랩 CI. 시드 고정 → 결정론."""
    vals = [float(v) for v in values]
    if not vals:
        return (0.0, 0.0)
    if len(vals) == 1:
        v = round(float(statistic(vals)), 2)
        return (v, v)
    rng = random.Random(seed)
    k = len(vals)
    stats = [statistic([vals[rng.randrange(k)] for _ in range(k)]) for _ in range(n)]
    stats.sort()
    return (round(_percentile(stats, alpha / 2), 2),
            round(_percentile(stats, 1 - alpha / 2), 2))


def paired_bootstrap_diff(a, b, n: int = 2000, seed: int = 0,
                          alpha: float = 0.05) -> dict:
    """동일 항목으로 매칭된 두 점수열의 평균차 CI + 양측 p.

    a, b 는 같은 순서로 페어링된 동일 길이 리스트(호출자가 question_id 로 교집합·정렬).
    d = a-b 의 평균을 부트스트랩. p 는 부트스트랩 평균차 분포가 0 을 넘는 비율의 양측값.
    """
    diffs = [float(x) - float(y) for x, y in zip(a, b)]
    if not diffs:
        return {"diff": 0.0, "ci": (0.0, 0.0), "p": 1.0, "n": 0}
    point = mean(diffs)
    rng = random.Random(seed)
    k = len(diffs)
    boot = sorted(mean([diffs[rng.randrange(k)] for _ in range(k)]) for _ in range(n))
    n_le = sum(1 for d in boot if d <= 0)
    n_ge = sum(1 for d in boot if d >= 0)
    p = min(1.0, 2 * min(n_le, n_ge) / len(boot))
    return {"diff": round(point, 2),
            "ci": (round(_percentile(boot, alpha / 2), 2),
                   round(_percentile(boot, 1 - alpha / 2), 2)),
            "p": round(p, 4), "n": k}


def spread_ci(groups: dict, n: int = 2000, seed: int = 0,
              alpha: float = 0.05) -> dict:
    """모델별 점수 리스트 dict → spread(최고평균-최저평균) 부트스트랩 CI."""
    items = [(m, [float(x) for x in v]) for m, v in groups.items() if v]
    if len(items) < 2:
        return {"spread": 0.0, "ci": (0.0, 0.0)}
    rng = random.Random(seed)
    point_means = [mean(v) for _, v in items]
    point_spread = max(point_means) - min(point_means)
    boot = []
    for _ in range(n):
        ms = [mean([v[rng.randrange(len(v))] for _ in range(len(v))]) for _, v in items]
        boot.append(max(ms) - min(ms))
    boot.sort()
    return {"spread": round(point_spread, 2),
            "ci": (round(_percentile(boot, alpha / 2), 2),
                   round(_percentile(boot, 1 - alpha / 2), 2))}
