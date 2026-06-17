#!/usr/bin/env python3
"""결과 JSONL → 진단 리포트(markdown) + 리더보드 JSON(--json).

용법:
    python scripts/make_report.py outputs/results/*.jsonl --out outputs/report.md
    python scripts/make_report.py outputs/results/*.jsonl --json outputs/leaderboard.json
"""
import glob
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ktaxbench.runlog import load_results  # noqa: E402
from ktaxbench.report import (  # noqa: E402
    aggregate_results, discrimination, error_cases, to_json, to_markdown,
)


def main() -> int:
    args = sys.argv[1:]
    out = "outputs/report.md"
    if "--out" in args:
        i = args.index("--out")
        out = args[i + 1]
        args = args[:i] + args[i + 2:]
    json_out = None
    if "--json" in args:
        i = args.index("--json")
        json_out = args[i + 1]
        args = args[:i] + args[i + 2:]
    inputs = [a for a in args if not a.startswith("--")]

    files: list[str] = []
    for p in inputs:
        files += glob.glob(p)
    if not files:
        print("입력 결과 파일 없음")
        return 1

    records: list[dict] = []
    for f in files:
        records += load_results(f)

    rep = aggregate_results(records)
    disc = discrimination(rep)
    errs = error_cases(records)

    if json_out:
        meta = {
            "n_records": rep["n_records"],
            "n_errors": rep["n_errors"],
            "models": rep["models"],
        }
        payload = to_json(rep, disc, errs, meta)
        Path(json_out).parent.mkdir(parents=True, exist_ok=True)
        Path(json_out).write_text(
            json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2),
            encoding="utf-8")
        print(f"leaderboard json -> {json_out} ({len(records)} records, "
              f"{len(rep['models'])} models, flag={disc['flag']})")
        return 0

    md = to_markdown(rep, disc, errs)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(md, encoding="utf-8")
    print(f"report -> {out} ({len(records)} records, {len(rep['models'])} models, "
          f"flag={disc['flag']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
