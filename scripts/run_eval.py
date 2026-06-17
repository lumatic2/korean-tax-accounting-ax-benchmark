#!/usr/bin/env python3
"""평가 실행 CLI (수동 풀런 — 구독 소모).

용법:
    python scripts/run_eval.py --models claude-haiku-4-5 --modes closed_book,rag \\
        --domains corp_tax,vat --data data/sample-questions-v0.1.jsonl --out outputs/results \\
        --judge claude-sonnet-4-6 --limit 5
"""
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ktaxbench.loader import load_questions  # noqa: E402
from ktaxbench.runner import run_batch  # noqa: E402
from ktaxbench.runlog import write_results  # noqa: E402


def _arg(args, name, default=None):
    return args[args.index(name) + 1] if name in args else default


def main() -> int:
    args = sys.argv[1:]
    models = (_arg(args, "--models", "claude-haiku-4-5")).split(",")
    modes = (_arg(args, "--modes", "closed_book")).split(",")
    data = _arg(args, "--data", "data/sample-questions-v0.1.jsonl")
    out = _arg(args, "--out", "outputs/results")
    judge = _arg(args, "--judge")
    domains = _arg(args, "--domains")
    task_types = _arg(args, "--task-types")
    ids = _arg(args, "--id")
    limit = _arg(args, "--limit")
    workers = int(_arg(args, "--workers", "8"))
    acc = _arg(args, "--accessed-at", datetime.now(timezone.utc).strftime("%Y-%m-%d"))

    questions = load_questions(data)
    if domains:
        ds = set(domains.split(","))
        questions = [q for q in questions if q.get("domain") in ds]
    if task_types:
        ts = set(task_types.split(","))
        questions = [q for q in questions if q.get("task_type") in ts]
    if ids:
        idset = set(ids.split(","))
        questions = [q for q in questions if q.get("id") in idset]
    if limit:
        questions = questions[: int(limit)]

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    for model in models:
        recs = run_batch(questions, modes, model,
                         judge_model_name=judge, accessed_at=acc, max_workers=workers)
        path = write_results(recs, out, model=model, timestamp=ts)
        ok = [r for r in recs if not r.error]
        avg = (sum(r.final.get("total", 0) for r in ok) / len(ok)) if ok else 0
        print(f"[{model}] {len(recs)} runs, {len(ok)} ok, avg total={avg:.1f} -> {path}")
        for r in recs:
            tag = r.error or f"{r.final.get('total', 0):.0f}/{r.final.get('grade', '-')}"
            print(f"  {r.question_id} [{r.mode}] {tag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
