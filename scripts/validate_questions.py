#!/usr/bin/env python3
"""문항 JSONL 전체를 스키마 검증한다.

용법:
    python scripts/validate_questions.py data/sample-questions-v0.1.jsonl
    python scripts/validate_questions.py data/sample-questions-v0.1.jsonl --json
    python scripts/validate_questions.py data/sample-questions-v0.1.jsonl --warnings  # 경고도 출력

에러(violations)가 1건이라도 있으면 exit 1, 없으면 exit 0.
경고(draft 완성도 미달 등)는 exit code에 영향을 주지 않는다.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "src"))

from ktaxbench.schema import lint_question  # noqa: E402


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 2
    path = args[0]
    as_json = "--json" in args
    show_warn = "--warnings" in args

    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))

    all_errors: list[dict] = []
    all_warnings: list[dict] = []
    for obj in rows:
        errs, warns = lint_question(obj)
        qid = obj.get("id", "<no-id>")
        for e in errs:
            all_errors.append({"id": qid, "violation": e})
        for w in warns:
            all_warnings.append({"id": qid, "warning": w})

    if as_json:
        print(json.dumps({"errors": all_errors, "warnings": all_warnings},
                         ensure_ascii=False, indent=2))
    else:
        for e in all_errors:
            print(f"  [ERROR] {e['id']}: {e['violation']}")
        if show_warn:
            for w in all_warnings:
                print(f"  [warn]  {w['id']}: {w['warning']}")
        n = len(rows)
        nv = len(all_errors)
        nw = len(all_warnings)
        print(f"{n} questions, {nv} violations, {nw} warnings"
              f"{'' if show_warn else ' (--warnings 로 경고 표시)'}")

    return 1 if all_errors else 0


if __name__ == "__main__":
    sys.exit(main())
