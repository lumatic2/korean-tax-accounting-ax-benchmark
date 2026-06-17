#!/usr/bin/env python3
"""결과 파일 내 실패(error) 행만 골라 재실행하여 치유하는 스크립트.

용법:
    python scripts/heal_results.py --file outputs/m4r1/gemini-2.5-flash_*.jsonl \
        --judge gpt-5.5 --data data/sample-questions-v0.1.jsonl
"""
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ktaxbench.loader import load_questions
from ktaxbench.runner import run_one
from ktaxbench.report import judge_failed

def main():
    parser = argparse.ArgumentParser(description="Heal failed runs in a results JSONL file.")
    parser.add_argument("--file", required=True, help="Path to the results JSONL file to heal")
    parser.add_argument("--data", default="data/sample-questions-v0.1.jsonl", help="Questions database path")
    parser.add_argument("--judge", default="gpt-5.5", help="Judge model name")
    args = parser.parse_args()

    questions = load_questions(args.data)
    questions_by_id = {q["id"]: q for q in questions}

    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Error: file {file_path} not found.")
        sys.exit(1)

    records = []
    with open(file_path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    # Identify failed records — top-level run error OR judge 미채점(silent 0.0)
    failed_indices = [i for i, r in enumerate(records) if r.get("error") or judge_failed(r)]
    n_judge = sum(1 for r in records if not r.get("error") and judge_failed(r))
    print(f"Loaded {len(records)} records. Found {len(failed_indices)} failed runs "
          f"(run_error {len(failed_indices) - n_judge} + judge_fail {n_judge}).")

    if not failed_indices:
        print("No failed runs to heal!")
        return

    acc = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    healed_count = 0
    for idx in failed_indices:
        r = records[idx]
        qid = r["question_id"]
        mode = r["mode"]
        model = r["model"]
        print(f"Healing {qid} [{mode}]...")
        
        q = questions_by_id.get(qid)
        if not q:
            print(f"  Warning: Question {qid} not found in database. Skipping.")
            continue

        try:
            # Run the single evaluation sequentially
            new_r = run_one(q, mode, model, judge_model_name=args.judge, accessed_at=acc)
            from dataclasses import asdict
            new_dict = asdict(new_r)
            if not new_r.error and not (new_dict.get("final") or {}).get("judge_error"):
                records[idx] = new_dict
                healed_count += 1
                print(f"  Success! Score: {new_dict.get('final', {}).get('total', 0)}")
            elif new_r.error:
                print(f"  Failed again: {new_r.error}")
            else:
                print(f"  Judge failed again: {(new_dict.get('judge') or {}).get('error')}")
        except Exception as e:
            print(f"  Error: {e}")

    # Write healed records back to the file
    with open(file_path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"Healed {healed_count}/{len(failed_indices)} failures. Saved back to {file_path}.")

if __name__ == "__main__":
    main()
