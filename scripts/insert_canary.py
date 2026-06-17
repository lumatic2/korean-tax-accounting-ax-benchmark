#!/usr/bin/env python3
"""공개 릴리스 문항에 canary 삽입 (M5 공개 트랙).

전략: docs/m4-public-sample-scope.md §3. 문항별 KTAXBENCH-CANARY-<uuid4> 1개 + 전역 sentinel.
canary 는 hash 산출 기준({question, final_answer})에서 제외 → 삽입 후 hash 불변(schema §hash).
이미 canary 가 있으면 보존(멱등) — 릴리스 버전 간 canary 안정.

용법:
    python scripts/insert_canary.py --in data/public/release.jsonl --out dist/release-canary.jsonl
    python scripts/insert_canary.py --in ... --out ... --seed 42   # 재현용 결정론 uuid
"""
import json
import random
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # hash_question 재사용
from hash_question import content_hash  # noqa: E402

_PREFIX = "KTAXBENCH-CANARY-"
_GLOBAL_PREFIX = "KTAXBENCH-CANARY-GLOBAL-"


def _arg(args, name, default=None):
    return args[args.index(name) + 1] if name in args else default


def _uuid(rng: random.Random | None) -> str:
    if rng is None:
        return str(uuid.uuid4())
    return str(uuid.UUID(int=rng.getrandbits(128), version=4))


def insert_canary(rows: list[dict], seed: int | None = None) -> tuple[list[dict], str]:
    """각 문항에 canary 삽입(멱등) + 전역 sentinel 반환. hash 불변 보장(assert).

    canary 가 content_hash 입력에 새면 즉시 AssertionError — 공개↔비공개 hash 대조 불변성
    파괴 방지(핵심 안전장치). 이미 canary 가 있는 문항은 덮어쓰지 않는다(멱등).
    """
    rng = random.Random(seed) if seed is not None else None
    out: list[dict] = []
    for q in rows:
        before = content_hash(q)
        nq = dict(q)
        if not nq.get("canary"):
            nq["canary"] = _PREFIX + _uuid(rng)
        after = content_hash(nq)
        assert before == after, f"canary 가 hash 를 바꿈(누수 위험): {nq.get('id')}"
        out.append(nq)
    sentinel = _GLOBAL_PREFIX + _uuid(rng)
    return out, sentinel


def main() -> int:
    args = sys.argv[1:]
    inp = _arg(args, "--in")
    out = _arg(args, "--out")
    seed_s = _arg(args, "--seed")
    seed = int(seed_s) if seed_s is not None else None
    if not inp or not out:
        print(__doc__)
        return 2

    rows = [json.loads(l) for l in open(inp, encoding="utf-8") if l.strip()]
    new_rows, sentinel = insert_canary(rows, seed=seed)

    Path(out).parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        for q in new_rows:
            f.write(json.dumps(q, ensure_ascii=False) + "\n")
    print(f"canary inserted: {len(new_rows)} questions -> {out}")
    print(f"GLOBAL_SENTINEL={sentinel}")  # 매니페스트가 박제(package_release)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
