#!/usr/bin/env python3
"""문항 content hash 등록/backfill.

각 JSONL 문항에 `hash` 필드(sha256)를 부여한다. 산출 기준은
{"question": <question 객체>, "final_answer": <answer.final_answer>} 의
canonical JSON(키 정렬·공백 제거). hash 자체는 기준에서 제외되므로 재실행해도 안정적.

용법:
    python scripts/hash_question.py data/sample-questions-v0.1.jsonl          # in-place backfill
    python scripts/hash_question.py data/sample-questions-v0.1.jsonl --check  # 변경 없이 검증만
"""
import hashlib
import json
import sys


def content_hash(obj: dict) -> str:
    basis = {"question": obj["question"], "final_answer": obj["answer"]["final_answer"]}
    canonical = json.dumps(basis, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    path = sys.argv[1]
    check = "--check" in sys.argv[2:]

    with open(path, encoding="utf-8") as f:
        objs = [json.loads(line) for line in f if line.strip()]

    changed = 0
    for obj in objs:
        h = content_hash(obj)
        if obj.get("hash") != h:
            changed += 1
            if not check:
                obj["hash"] = h

    if check:
        print(f"{len(objs)} questions, {changed} stale/missing hash")
        return 1 if changed else 0

    with open(path, "w", encoding="utf-8") as f:
        for obj in objs:
            f.write(json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n")
    print(f"{len(objs)} questions hashed ({changed} updated) -> {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
