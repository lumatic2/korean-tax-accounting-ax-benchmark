#!/usr/bin/env python3
"""LLM-judge smoke (수동 — 구독 소모). judge 2회 실행 분산(재현성) 출력.

용법: python scripts/smoke_judge.py --question ktb-vat-0001 --judge claude-sonnet-4-6 --candidate claude-haiku-4-5
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ktaxbench.loader import load_questions  # noqa: E402
from ktaxbench.grading.judge import judge_answer  # noqa: E402


def _arg(args, name, default):
    return args[args.index(name) + 1] if name in args else default


def main() -> int:
    args = sys.argv[1:]
    qid = _arg(args, "--question", "ktb-vat-0001")
    judge = _arg(args, "--judge", "claude-sonnet-4-6")
    cand = _arg(args, "--candidate", "claude-haiku-4-5")
    data = str(Path(__file__).resolve().parents[1] / "data" / "sample-questions-v0.1.jsonl")
    q = next(x for x in load_questions(data) if x["id"] == qid)
    answer = q["answer"]["final_answer"]  # 정답을 후보로 넣어 만점 근처 기대
    for i in (1, 2):
        r = judge_answer(q, answer, judge_model_name=judge, candidate_model_name=cand)
        print(f"run{i} scores={r.scores} flags={r.fatal_flags}")
        if r.memo.get("self_eval_warning"):
            print("  WARN:", r.memo["self_eval_warning"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
