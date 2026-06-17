"""진단 리포트 — 결과 JSONL → 모델×분야×차원 분해 + 변별 지표 + 오류 사례.

리포트 로직은 결정론(fixture 로 테스트). 실제 풀런(M3 성공기준)은 데이터 공급원일 뿐.
"""
from __future__ import annotations

from statistics import mean


def _avg(xs: list[float]) -> float:
    return round(mean(xs), 2) if xs else 0.0


def judge_failed(r: dict) -> bool:
    """judge 호출/파싱 실패 레코드 — final.total=0.0 은 '정당한 0점'이 아니라 미채점이다.

    구·신 데이터 공통: judge dict 에 'error' 키가 있으면 실패(runner/regrade 가 박는다).
    신 데이터는 final.judge_error 마커도 가진다(자기기술). 집계에서 제외해야 평균·변별이
    오염되지 않는다(R4 선행 디버그: Claude judge 58/202 JSON 실패가 +24.8 아티팩트를 만듦).
    """
    j = r.get("judge")
    if j and j.get("error"):
        return True
    return bool((r.get("final") or {}).get("judge_error"))


def aggregate_results(records: list[dict]) -> dict:
    ok = [r for r in records if not r.get("error") and not judge_failed(r)]
    models = sorted({r["model"] for r in records})
    by_model: dict[str, dict] = {}
    for m in models:
        rs = [r for r in ok if r["model"] == m]
        totals = [r["final"]["total"] for r in rs if r.get("final")]
        doms = sorted({r.get("domain", "") for r in rs})
        by_domain = {d: _avg([r["final"]["total"] for r in rs if r.get("domain") == d])
                     for d in doms}
        modes = sorted({r.get("mode", "") for r in rs})
        by_mode = {md: _avg([r["final"]["total"] for r in rs if r.get("mode") == md])
                   for md in modes}
        dim_acc: dict[str, list[float]] = {}
        for r in rs:
            for dim, pts in (r["final"].get("per_dimension") or {}).items():
                dim_acc.setdefault(dim, []).append(pts)
        by_dim = {d: _avg(v) for d, v in sorted(dim_acc.items())}
        grades: dict[str, int] = {}
        for r in rs:
            g = r["final"].get("grade", "-")
            grades[g] = grades.get(g, 0) + 1
        by_model[m] = {
            "n": len(rs), "avg_total": _avg(totals), "by_domain": by_domain,
            "by_mode": by_mode, "by_dimension": by_dim, "grades": grades,
        }
    return {"models": models, "by_model": by_model,
            "n_records": len(records), "n_errors": len(records) - len(ok)}


def discrimination(report: dict) -> dict:
    """모델 간 변별. saturation(다 높음)/floor(다 낮음)/low_discrimination 플래그."""
    avgs = [report["by_model"][m]["avg_total"] for m in report["models"]
            if report["by_model"][m]["n"] > 0]
    if not avgs:
        return {"spread": 0.0, "range": (0.0, 0.0), "flag": "empty"}
    lo, hi = min(avgs), max(avgs)
    spread = round(hi - lo, 2)
    if lo >= 85:
        flag = "saturation"
    elif hi <= 40:
        flag = "floor"
    elif spread < 10:
        flag = "low_discrimination"
    else:
        flag = "ok"
    return {"spread": spread, "range": (lo, hi), "flag": flag}


def ci_summary(records: list[dict], *, seed: int = 0, n: int = 2000) -> dict:
    """핵심 수치 + 부트스트랩 CI(M6). aggregate 와 별개 경로 — 웹 payload 불간섭(추가 전용).

    judge_failed·run_error 제외한 깨끗한 레코드에서 모델별 total 분포 → 평균 CI + spread CI.
    paired diff(RAG vs closed, judge-swap)는 호출자가 stats.paired_bootstrap_diff 로 페어링.
    """
    from .stats import bootstrap_ci, spread_ci
    ok = [r for r in records if not r.get("error") and not judge_failed(r) and r.get("final")]
    groups: dict[str, list[float]] = {}
    for r in ok:
        groups.setdefault(r["model"], []).append(r["final"]["total"])
    per_model = {m: {"avg": _avg(v), "n": len(v), "ci": bootstrap_ci(v, seed=seed, n=n)}
                 for m, v in sorted(groups.items())}
    return {"by_model": per_model, "spread": spread_ci(groups, seed=seed, n=n),
            "n_records": len(records), "n_scored": len(ok)}


def error_cases(records: list[dict]) -> list[dict]:
    """환각(가짜·미검증 인용)·계산오류·근거오류·실행오류 사례 추출."""
    out: list[dict] = []
    for r in records:
        base = {"id": r.get("question_id"), "model": r.get("model"), "mode": r.get("mode")}
        if r.get("error"):
            out.append({**base, "type": "run_error", "detail": r["error"]})
            continue
        final = r.get("final") or {}
        flags = final.get("flags") or []
        if any("fake_source" in f or "unverified_citation" in f for f in flags):
            out.append({**base, "type": "hallucination", "detail": ", ".join(flags)})
        per = final.get("per_dimension") or {}
        if r.get("task_type") == "calculation" and per.get("conclusion_accuracy", 1) == 0:
            out.append({**base, "type": "calc_error", "detail": "결론 수치 불일치(0점)"})
        if r.get("task_type") == "citation" and per.get("legal_basis", 1) == 0:
            out.append({**base, "type": "citation_error", "detail": "근거 조문 불일치(0점)"})
    return out


def to_json(report: dict, disc: dict, errors: list[dict],
            meta: dict | None = None) -> dict:
    """리더보드 웹의 빌드타임 입력 — report+변별+오류를 직렬화 가능한 dict로.

    결정론: 같은 입력 → 같은 dict (정렬·파생값만). 웹은 이 구조만 소비하고
    raw 답변·채점을 재계산하지 않는다(단일 진실원 src/ktaxbench).
    """
    return {
        "schema_version": "leaderboard-v0.1",
        "meta": meta or {},
        "discrimination": {
            "spread": disc["spread"],
            "range": list(disc["range"]),
            "flag": disc["flag"],
        },
        "report": report,
        "errors": errors,
    }


_QUALITY_ERROR_TYPES = ("hallucination", "calc_error", "citation_error")


def build_public_payload(records: list[dict], visibility_map: dict[str, str],
                         meta: dict | None = None) -> dict:
    """공개 리더보드용 누수-안전 payload (ADR 0009 + m4-public-sample-scope).

    - **순위(ranking)는 holdout 집계** — ADR 0009 "순위는 holdout으로만".
    - **공개셋(public_sample)은 별도 집계** — 과적합 가시화용 별도 표기.
    - holdout 문항은 **집계값만** 노출: 문항 id·본문·답변 비노출. holdout 오류는
      type별 카운트만(어떤 holdout 문항이 틀렸는지 비공개). 공개셋 오류는 id 포함 가능.
    - run_error(인프라 timeout 등)는 모델 품질 신호가 아니므로 오류 표시에서 제외.
    """
    def vis(r: dict) -> str:
        return visibility_map.get(r.get("question_id", ""), "unknown")

    holdout = [r for r in records if vis(r) == "holdout"]
    public = [r for r in records if vis(r) == "public_sample"]
    rank_rep = aggregate_results(holdout)
    pub_rep = aggregate_results(public)

    errs_public = [e for e in error_cases(public)
                   if e["type"] in _QUALITY_ERROR_TYPES]
    hold_by_type: dict[str, int] = {}
    for e in error_cases(holdout):
        if e["type"] in _QUALITY_ERROR_TYPES:
            hold_by_type[e["type"]] = hold_by_type.get(e["type"], 0) + 1

    # 버전핀(ADR 0009 배지) — model별 prompt_version·judge·mode·accessed_at
    pins: dict[str, dict] = {}
    for r in holdout + public:
        m = r.get("model", "")
        p = pins.setdefault(m, {"prompt_version": set(), "judge_model": set(),
                                "modes": set(), "accessed_at": set()})
        sc = r.get("scaffold") or {}
        if sc.get("prompt_version"):
            p["prompt_version"].add(sc["prompt_version"])
        if sc.get("judge_model"):
            p["judge_model"].add(sc["judge_model"])
        if r.get("mode"):
            p["modes"].add(r["mode"])
        if r.get("accessed_at"):
            p["accessed_at"].add(r["accessed_at"])
    version_pins = {m: {k: sorted(v) for k, v in d.items()}
                    for m, d in sorted(pins.items())}

    return {
        "schema_version": "leaderboard-public-v0.1",
        "meta": {**(meta or {}),
                 "n_holdout_records": rank_rep["n_records"],
                 "n_public_records": pub_rep["n_records"],
                 "models": sorted(set(rank_rep["models"]) | set(pub_rep["models"]))},
        "ranking": {"basis": "holdout", "report": rank_rep,
                    "discrimination": discrimination(rank_rep)},
        "public_sample": {"report": pub_rep,
                          "discrimination": discrimination(pub_rep)},
        "version_pins": version_pins,
        "errors_public": errs_public,
        "errors_holdout_agg": {"by_type": dict(sorted(hold_by_type.items()))},
    }


def to_markdown(report: dict, disc: dict, errors: list[dict]) -> str:
    lines: list[str] = []
    lines.append("# K-TaxBench 진단 리포트\n")
    lines.append(f"- 결과 레코드: {report['n_records']} (오류 {report['n_errors']})")
    lines.append(f"- 변별: spread={disc['spread']} range={disc['range']} "
                 f"**flag={disc['flag']}**\n")
    if disc["flag"] in ("saturation", "floor", "low_discrimination"):
        lines.append("> ⚠ 모델 변별이 약하다 — 문항 난이도·문항 수 재설계 필요(M3 리스크).\n")

    lines.append("## 모델 랭킹\n")
    lines.append("| 모델 | n | 평균 | 등급분포 |")
    lines.append("|---|---|---|---|")
    ranked = sorted(report["models"],
                    key=lambda m: report["by_model"][m]["avg_total"], reverse=True)
    for m in ranked:
        bm = report["by_model"][m]
        gr = " ".join(f"{k}:{v}" for k, v in sorted(bm["grades"].items()))
        lines.append(f"| {m} | {bm['n']} | {bm['avg_total']} | {gr} |")

    lines.append("\n## 분야별 평균\n")
    all_domains = sorted({d for m in report["models"]
                          for d in report["by_model"][m]["by_domain"]})
    lines.append("| 모델 | " + " | ".join(all_domains) + " |")
    lines.append("|---|" + "---|" * len(all_domains))
    for m in ranked:
        bd = report["by_model"][m]["by_domain"]
        lines.append(f"| {m} | " + " | ".join(str(bd.get(d, "-")) for d in all_domains) + " |")

    lines.append("\n## 차원별 평균\n")
    all_dims = sorted({d for m in report["models"]
                       for d in report["by_model"][m]["by_dimension"]})
    lines.append("| 모델 | " + " | ".join(all_dims) + " |")
    lines.append("|---|" + "---|" * len(all_dims))
    for m in ranked:
        bdm = report["by_model"][m]["by_dimension"]
        lines.append(f"| {m} | " + " | ".join(str(bdm.get(d, "-")) for d in all_dims) + " |")

    if errors:
        lines.append("\n## 대표 오류 사례\n")
        for e in errors[:20]:
            lines.append(f"- [{e['type']}] {e['id']} ({e['model']}/{e['mode']}): {e['detail']}")

    return "\n".join(lines) + "\n"
