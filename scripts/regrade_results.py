#!/usr/bin/env python3
"""결과 JSONL 파일 재채점 (수동 재채점).

용법:
    python scripts/regrade_results.py --in-file outputs/results/gpt-5.5_*.jsonl \
        --out-file outputs/results/gpt-5.5_regraded.jsonl \
        --judge gpt-5.5 --data data/sample-questions-v0.1.jsonl --workers 4
"""
import sys
import json
import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ktaxbench.loader import load_questions
from ktaxbench.grading.judge import judge_answer, JudgeResult
from ktaxbench.grading.aggregate import combine
from ktaxbench.report import judge_failed

def regrade_record(r, questions_by_id, judge_model_name):
    qid = r.get("question_id")
    q = questions_by_id.get(qid)
    if not q:
        # Try finding by hash
        qhash = r.get("question_hash")
        for q_candidate in questions_by_id.values():
            if q_candidate.get("hash") == qhash:
                q = q_candidate
                break
    
    if not q:
        print(f"Warning: Question {qid} not found in database. Skipping regrading.")
        return r

    answer_text = r.get("answer_text", "")
    if not answer_text or r.get("error"):
        return r

    from ktaxbench.grading import code_grader
    model_name = r.get("model")
    cg = code_grader.grade(q, answer_text)
    code_scores = cg["scores"]
    grader_flags = list(cg.get("flags", []))
    old_flags = r.get("final", {}).get("flags", [])
    # Merge old flags with new grader flags (avoiding duplicates)
    flags = list(set(grader_flags + old_flags))

    try:
        jr = judge_answer(q, answer_text,
                          judge_model_name=judge_model_name,
                          candidate_model_name=model_name)
        from dataclasses import asdict
        r["code_scores"] = [asdict(cs) for cs in code_scores]
        if jr.error:  # 파싱 실패(미채점) — 빈 scores 를 0점으로 쓰지 않는다
            r["judge"] = {"error": f"judge: {jr.error}", "scores": {},
                          "fatal_flags": [], "raw_response": jr.raw_response}
            final = combine(code_scores, None, q.get("task_type", ""), extra_flags=flags)
            final["judge_error"] = True  # 집계 제외 마커(report.judge_failed)
            r["final"] = final
            r["scaffold"]["judge_model"] = judge_model_name
            return r
        judge = {"scores": jr.scores, "memo": jr.memo,
                 "fatal_flags": jr.fatal_flags, "judge_model": jr.judge_model}
        judge_obj = JudgeResult(scores=jr.scores, memo=jr.memo,
                                fatal_flags=jr.fatal_flags, judge_model=jr.judge_model)
        final = combine(code_scores, judge_obj, q.get("task_type", ""), extra_flags=flags)
        r["judge"] = judge
        r["final"] = final
        r["scaffold"]["judge_model"] = judge_model_name
    except Exception as e:
        print(f"Error grading {qid} with {judge_model_name}: {e}")
        r["judge"] = {"error": f"judge: {e}", "scores": {}, "fatal_flags": []}
        final = combine(code_scores, None, q.get("task_type", ""), extra_flags=flags)
        final["judge_error"] = True  # 미채점 마커 — 집계 제외(report.judge_failed)
        r["final"] = final
        from dataclasses import asdict
        r["code_scores"] = [asdict(cs) for cs in code_scores]
    
    return r

def main():
    parser = argparse.ArgumentParser(description="Regrade existing JSONL results with a new judge model.")
    parser.add_argument("--in-file", required=True, help="Input JSONL path")
    parser.add_argument("--out-file", required=True, help="Output JSONL path")
    parser.add_argument("--judge", required=True, help="Judge model name (e.g. gpt-5.5)")
    parser.add_argument("--data", default="data/sample-questions-v0.1.jsonl", help="Questions database path")
    parser.add_argument("--workers", type=int, default=4, help="Number of concurrent workers")
    parser.add_argument("--only-failed", action="store_true",
                        help="judge_failed(미채점)·run_error 레코드만 재채점, 나머지는 원본 보존 "
                             "(judge 호출실패 surgical heal — 멀쩡한 레코드 judge drift 방지)")
    args = parser.parse_args()

    questions = load_questions(args.data)
    questions_by_id = {q["id"]: q for q in questions}

    in_path = Path(args.in_file)
    out_path = Path(args.out_file)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if not in_path.exists():
        print(f"Error: Input file {in_path} does not exist.")
        sys.exit(1)

    records = []
    with open(in_path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    # 재채점 대상 인덱스 — --only-failed 면 미채점/실패만, 아니면 전체
    if args.only_failed:
        target_idx = [i for i, r in enumerate(records)
                      if judge_failed(r) or r.get("error")]
        print(f"Loaded {len(records)} records. --only-failed: {len(target_idx)} 대상 "
              f"(나머지 {len(records) - len(target_idx)} 보존).")
    else:
        target_idx = list(range(len(records)))
        print(f"Loaded {len(records)} records from {in_path}.")
    print(f"Regrading using judge model: {args.judge} with {args.workers} workers...")

    regraded_records = list(records)  # 원본 복사(보존 대상은 그대로 둠)
    if args.workers <= 1:
        for n, i in enumerate(target_idx):
            regraded_records[i] = regrade_record(records[i], questions_by_id, args.judge)
            if (n + 1) % 10 == 0:
                print(f"Progress: {n + 1}/{len(target_idx)} done.")
    else:
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            done = list(executor.map(
                lambda i: regrade_record(records[i], questions_by_id, args.judge),
                target_idx
            ))
        for i, r in zip(target_idx, done):
            regraded_records[i] = r

    with open(out_path, "w", encoding="utf-8") as f:
        for r in regraded_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    ok = [r for r in regraded_records if not r.get("error")]
    avg = (sum(r.get("final", {}).get("total", 0) for r in ok) / len(ok)) if ok else 0
    print(f"Successfully wrote {len(regraded_records)} records to {out_path}.")
    print(f"Average total score: {avg:.1f}")

if __name__ == "__main__":
    main()
