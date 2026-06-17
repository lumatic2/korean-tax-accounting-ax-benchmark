#!/usr/bin/env python3
"""공개 릴리스 집합 추출 (M4 공개 트랙).

선택 규칙(화이트리스트, docs/m4-public-sample-scope.md §1):
    visibility == public_sample ∧ license.public_release_allowed ∧ status ∈ {internal_reviewed, expert_reviewed}

용법:
    python scripts/export_public_set.py --dry-run                  # 카운트·분포만
    python scripts/export_public_set.py --out data/public/release.jsonl
"""
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


def _arg(args, name, default=None):
    return args[args.index(name) + 1] if name in args else default


_PUBLISHABLE_STATUS = {"internal_reviewed", "expert_reviewed"}


def is_publishable(q: dict) -> bool:
    return (
        q.get("visibility") == "public_sample"
        and bool(q.get("license", {}).get("public_release_allowed"))
        and q.get("status") in _PUBLISHABLE_STATUS
    )


def main() -> int:
    args = sys.argv[1:]
    data = _arg(args, "--data", "data/sample-questions-v0.1.jsonl")
    out = _arg(args, "--out")
    dry = "--dry-run" in args

    rows = [json.loads(l) for l in open(data, encoding="utf-8") if l.strip()]
    pub = [q for q in rows if is_publishable(q)]

    print(f"publishable: {len(pub)} / {len(rows)}")
    print("  domain:   ", dict(Counter(q["domain"] for q in pub)))
    print("  task_type:", dict(Counter(q["task_type"] for q in pub)))
    print("  difficulty:", dict(Counter(q["difficulty"] for q in pub)))

    # 누수 가드: 공개 대상에 holdout/draft/private 가 섞이면 즉시 실패
    leak = [q["id"] for q in pub if q.get("visibility") != "public_sample"]
    assert not leak, f"LEAK: non-public_sample in export set: {leak}"

    if dry or not out:
        if not out and not dry:
            print("(no --out given; nothing written. use --dry-run or --out)")
        return 0

    Path(out).parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        for q in sorted(pub, key=lambda q: q["id"]):
            f.write(json.dumps(q, ensure_ascii=False) + "\n")
    print(f"wrote {len(pub)} -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
