#!/usr/bin/env python3
"""RAG retriever smoke (네트워크 — 법제처 DRF, LLM 비용 아님).

용법: python scripts/smoke_rag.py [--id ktb-vat-0003] [--date 2026-06-02]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ktaxbench.loader import load_questions  # noqa: E402
from ktaxbench.rag.retriever import retrieve_context  # noqa: E402


def main() -> int:
    args = sys.argv[1:]
    qid = args[args.index("--id") + 1] if "--id" in args else "ktb-vat-0003"
    date = args[args.index("--date") + 1] if "--date" in args else "2026-06-02"
    data = str(Path(__file__).resolve().parents[1] / "data" / "sample-questions-v0.1.jsonl")
    rows = [q for q in load_questions(data) if q["id"] == qid]
    if not rows:
        print(f"문항 없음: {qid}")
        return 1
    res = retrieve_context(rows[0], accessed_at=date)
    print(f"retrieved={len(res['retrieved'])} warnings={res['warnings']}")
    print("---")
    print(res["context_text"][:800])
    return 0 if res["retrieved"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
