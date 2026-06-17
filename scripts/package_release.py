#!/usr/bin/env python3
"""공개 릴리스 번들 패키징 (M5 공개 트랙).

파이프라인: export_public_set(공개 적격) → insert_canary(canary+sentinel) → 번들 4파일.
출력(dist/, gitignored): release.jsonl · README.md · MANIFEST.json · LICENSE.

용법:
    python scripts/package_release.py --data data/sample-questions-v0.1.jsonl \\
        --out dist/public-release-v1.0 --version 1.0 --accessed-at 2026-06-14 --seed 42
"""
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # 형제 스크립트 재사용
from export_public_set import is_publishable  # noqa: E402
from insert_canary import insert_canary  # noqa: E402
from hash_question import content_hash  # noqa: E402

_LICENSE = """K-TaxBench Public Sample — CC BY-NC 4.0 (Attribution-NonCommercial)

이 공개 샘플셋은 연구·재현·디버그 용도로 제공된다. 기출문제를 시드로 표현을 전면
재작성했으며(data-strategy §2.4), 상업적 재배포는 별도 협의가 필요하다.
순위 산정은 비공개 holdout 으로 매긴다(공개셋은 연습·재현 데모용).
"""


def _arg(args, name, default=None):
    return args[args.index(name) + 1] if name in args else default


def build_manifest(rows: list[dict], sentinel: str, generated_at: str,
                   version: str) -> dict:
    return {
        "name": "k-taxbench-public-sample",
        "version": version,
        "generated_at": generated_at,
        "n_questions": len(rows),
        "distribution": {
            "domain": dict(sorted(Counter(q["domain"] for q in rows).items())),
            "task_type": dict(sorted(Counter(q["task_type"] for q in rows).items())),
            "difficulty": dict(sorted(Counter(q["difficulty"] for q in rows).items())),
        },
        "global_canary_sentinel": sentinel,
        "hashes": {q["id"]: content_hash(q) for q in sorted(rows, key=lambda q: q["id"])},
        "gate": _gate(rows),
    }


def _gate(rows: list[dict]) -> dict:
    """릴리스 전 결정론 게이트(m4-public-sample-scope §4)."""
    non_public = [q["id"] for q in rows if q.get("visibility") != "public_sample"]
    not_allowed = [q["id"] for q in rows
                   if not q.get("license", {}).get("public_release_allowed")]
    not_publishable = [q["id"] for q in rows if not is_publishable(q)]
    return {
        "leak_non_public_sample": non_public,    # 비어야 PASS
        "license_not_allowed": not_allowed,      # 비어야 PASS
        "not_publishable": not_publishable,      # 비어야 PASS
        "passed": not (non_public or not_allowed or not_publishable),
    }


def build_readme(sentinel: str, version: str, manifest: dict) -> str:
    d = manifest["distribution"]
    return f"""# K-TaxBench — 공개 샘플셋 v{version}

한국 회계·세무 AI의 **실무 검증 통과 여부**를 재는 표준 평가 인프라(K-TaxBench)의
공개 샘플셋이다. 이 셋은 **연습·재현·디버그용**이며, 리더보드 순위는 비공개 holdout 으로
매긴다([제출/철회 정책 ADR 0009](https://github.com/lumatic2/ktaxbench-leaderboard)).

- 문항 수: **{manifest['n_questions']}**
- domain: {d['domain']}
- task_type: {d['task_type']}
- difficulty: {d['difficulty']}
- 생성일: {manifest['generated_at']} · 버전: {version}

## 재현 방법
```bash
# 1) 로드
python -c "import json; rows=[json.loads(l) for l in open('release.jsonl',encoding='utf-8') if l.strip()]; print(len(rows))"
# 2) 채점기·러너는 본 벤치마크 코드(closed_book/rag/agent 3모드) 사용. 동일 공개셋·실행기로 재현.
```

## 학습오염 탐지 (canary)
이 릴리스 아카이브에는 sentinel 문자열이 박혀 있다:

    {sentinel}

공개 LLM 이 이 문자열을 복창하면 학습데이터 오염 신호다. 각 문항에도 개별 `canary` 필드가
있으며, canary 는 문항 hash 산출 기준에서 제외돼 공개↔비공개 누수 대조 불변성을 해치지 않는다.

## 라이선스
CC BY-NC 4.0 — `LICENSE` 참조.
"""


def write_bundle(rows: list[dict], sentinel: str, out_dir: str,
                 generated_at: str, version: str) -> dict:
    manifest = build_manifest(rows, sentinel, generated_at, version)
    assert manifest["gate"]["passed"], f"릴리스 게이트 FAIL: {manifest['gate']}"

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "release.jsonl", "w", encoding="utf-8") as f:
        for q in sorted(rows, key=lambda q: q["id"]):
            f.write(json.dumps(q, ensure_ascii=False) + "\n")
    (out / "MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2), encoding="utf-8")
    (out / "README.md").write_text(build_readme(sentinel, version, manifest), encoding="utf-8")
    (out / "LICENSE").write_text(_LICENSE, encoding="utf-8")
    return manifest


def main() -> int:
    args = sys.argv[1:]
    data = _arg(args, "--data", "data/sample-questions-v0.1.jsonl")
    out_dir = _arg(args, "--out", "dist/public-release-v1.0")
    version = _arg(args, "--version", "1.0")
    accessed_at = _arg(args, "--accessed-at", "2026-06-14")
    seed_s = _arg(args, "--seed")
    seed = int(seed_s) if seed_s is not None else None

    allrows = [json.loads(l) for l in open(data, encoding="utf-8") if l.strip()]
    pub = [q for q in allrows if is_publishable(q)]
    canaried, sentinel = insert_canary(pub, seed=seed)
    manifest = write_bundle(canaried, sentinel, out_dir, accessed_at, version)

    print(f"bundle -> {out_dir}/ ({manifest['n_questions']} questions)")
    print(f"  gate passed: {manifest['gate']['passed']}")
    print(f"  GLOBAL_SENTINEL={sentinel}")
    return 0 if manifest["gate"]["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
