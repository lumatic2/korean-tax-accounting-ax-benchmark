#!/usr/bin/env python3
"""variance 반복런 — 같은 입력을 N회 실행해 점수 비결정성(run-to-run variance)을 정량한다 (M6 옵션).

모든 모델이 temperature=0 이지만 CLI subprocess/인프라 샘플링으로 잔여 비결정성이 남는다.
이 스크립트는 그 잔여 노이즈를 측정한다 — 같은 (문항, mode)를 N회 채점해 점수 분산을 본다.

⚠ 라이브 run (구독/billing 소모). judge_failed·run_error 레코드는 제외하고 집계한다
   (미채점은 품질신호가 아님 — [[judge-failure-silent-zero]]).

용법:
    PYTHONPATH=src python scripts/variance_run.py \\
        --model claude-haiku-4-5 --modes closed_book --n 5 \\
        --data data/sample-questions-v0.1.jsonl --judge claude-sonnet-4-6 \\
        --one-per-domain --out outputs/m6-variance

    --n N             반복 횟수 (기본 5)
    --one-per-domain  도메인별 첫 문항 1개씩만 (대표 subset, billing 절약)
    --domains/--id/--limit  run_eval.py 와 동일한 subset 필터
"""
import json
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ktaxbench.loader import load_questions  # noqa: E402
from ktaxbench.runner import run_batch  # noqa: E402
from ktaxbench.runlog import write_results  # noqa: E402
from ktaxbench.report import judge_failed  # noqa: E402
from ktaxbench.stats import bootstrap_ci  # noqa: E402


def _arg(args, name, default=None):
    return args[args.index(name) + 1] if name in args else default


def _select(questions, *, domains, ids, limit, one_per_domain):
    if domains:
        ds = set(domains.split(","))
        questions = [q for q in questions if q.get("domain") in ds]
    if ids:
        idset = set(ids.split(","))
        questions = [q for q in questions if q.get("id") in idset]
    if one_per_domain:
        seen, picked = set(), []
        for q in questions:
            d = q.get("domain")
            if d not in seen:
                seen.add(d)
                picked.append(q)
        questions = picked
    if limit:
        questions = questions[: int(limit)]
    return questions


def main() -> int:
    args = sys.argv[1:]
    model = _arg(args, "--model", "claude-haiku-4-5")
    modes = (_arg(args, "--modes", "closed_book")).split(",")
    data = _arg(args, "--data", "data/sample-questions-v0.1.jsonl")
    judge = _arg(args, "--judge", "claude-sonnet-4-6")
    out = _arg(args, "--out", "outputs/m6-variance")
    n = int(_arg(args, "--n", "5"))
    workers = int(_arg(args, "--workers", "8"))
    domains = _arg(args, "--domains")
    ids = _arg(args, "--id")
    limit = _arg(args, "--limit")
    one_per_domain = "--one-per-domain" in args
    acc = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    questions = _select(load_questions(data), domains=domains, ids=ids,
                        limit=limit, one_per_domain=one_per_domain)
    if not questions:
        print("선택된 문항 없음 — subset 필터 확인", file=sys.stderr)
        return 2

    run_ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = Path(out) / f"{model}_{run_ts}"
    out_dir.mkdir(parents=True, exist_ok=True)
    n_calls = len(questions) * len(modes) * n
    print(f"variance run: model={model} judge={judge} modes={modes} "
          f"문항={len(questions)} × N={n} = {n_calls} candidate run (+judge)")

    # ── N회 반복 실행 ────────────────────────────────────────────────
    # by_key[(qid, mode)] = [run0_total, run1_total, ...]  (제외 run 은 None)
    by_key: dict[tuple, list] = {}
    run_means: list[float] = []
    for i in range(n):
        recs = run_batch(questions, modes, model,
                         judge_model_name=judge, accessed_at=acc, max_workers=workers)
        path = write_results(recs, str(out_dir), model=model, timestamp=f"{run_ts}-r{i}")
        rows = [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines()]
        valid_totals = []
        for r in rows:
            key = (r["question_id"], r.get("mode"))
            excluded = bool(r.get("error")) or judge_failed(r)
            total = None if excluded else (r.get("final") or {}).get("total")
            by_key.setdefault(key, []).append(total)
            if total is not None:
                valid_totals.append(total)
        rm = statistics.mean(valid_totals) if valid_totals else float("nan")
        run_means.append(rm)
        print(f"  run {i}: {len(valid_totals)}/{len(rows)} valid, run-mean={rm:.2f}")

    # ── 문항별 variance 집계 ─────────────────────────────────────────
    per_q = []
    for (qid, mode), totals in sorted(by_key.items()):
        vals = [t for t in totals if t is not None]
        excl = len(totals) - len(vals)
        if len(vals) >= 1:
            mean = round(statistics.mean(vals), 2)
            std = round(statistics.pstdev(vals), 2) if len(vals) >= 2 else 0.0
            lo, hi = min(vals), max(vals)
        else:
            mean = std = lo = hi = None
        per_q.append({"question_id": qid, "mode": mode, "n_valid": len(vals),
                      "n_excluded": excl, "mean": mean, "std": std,
                      "min": lo, "max": hi,
                      "range": (round(hi - lo, 2) if vals else None),
                      "totals": totals})

    scored = [q for q in per_q if q["std"] is not None]
    stable = [q for q in scored if q["std"] == 0.0]
    pooled = [t for q in per_q for t in q["totals"] if t is not None]

    valid_run_means = [m for m in run_means if m == m]  # drop nan
    agg = {
        "run_means": [round(m, 2) for m in valid_run_means],
        "mean_of_run_means": round(statistics.mean(valid_run_means), 2) if valid_run_means else None,
        "std_of_run_means": round(statistics.pstdev(valid_run_means), 2) if len(valid_run_means) >= 2 else 0.0,
        "pooled_total_ci95": bootstrap_ci(pooled) if pooled else None,
    }
    summary = {
        "model": model, "judge": judge, "modes": modes, "n_repeats": n,
        "n_questions": len(questions), "generated_at": run_ts,
        "n_scored_keys": len(scored),
        "n_perfectly_stable": len(stable),
        "pct_stable": round(100 * len(stable) / len(scored), 1) if scored else None,
        "max_per_question_std": max((q["std"] for q in scored), default=0.0),
        "max_per_question_range": max((q["range"] for q in scored), default=0.0),
        "mean_per_question_std": round(statistics.mean([q["std"] for q in scored]), 2) if scored else 0.0,
        "aggregate": agg,
    }

    report = {"summary": summary, "per_question": per_q}
    rp = out_dir / "variance_report.json"
    rp.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    # ── 콘솔 출력 ────────────────────────────────────────────────────
    print(f"\n=== variance summary ({model}, N={n}) ===")
    print(f"문항(scored): {len(scored)}  | 완전안정(std=0): {len(stable)} "
          f"({summary['pct_stable']}%)")
    print(f"문항별 std: mean={summary['mean_per_question_std']} "
          f"max={summary['max_per_question_std']}  | max range={summary['max_per_question_range']}")
    print(f"run-mean: {agg['run_means']}  std={agg['std_of_run_means']}")
    print(f"pooled total CI95: {agg['pooled_total_ci95']}")
    print("\nper-question (std>0 만):")
    for q in sorted(scored, key=lambda x: -(x["std"] or 0)):
        if q["std"] and q["std"] > 0:
            print(f"  {q['question_id']:<22} [{q['mode']}] std={q['std']:<5} "
                  f"range={q['range']:<5} totals={q['totals']}")
    print(f"\n리포트: {rp}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
