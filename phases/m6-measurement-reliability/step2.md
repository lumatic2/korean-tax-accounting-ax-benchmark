# Step 2: heal-judge-fail-records — regrade(judge-only) 재채점

58 judge-fail 레코드를 working judge 로 재채점. **라이브 judge 호출 = billing → 사용자 opt-in 필요.**
step0(judge 강건화) 머지 후 실행해야 재실패율↓.

## ⚠ 도구: heal 아닌 regrade --only-failed (세션12 정정)
- 대상 58건은 **candidate 답안은 멀쩡, judge(claude-sonnet-4-6)만 비-JSON 실패**한 경우다.
- `heal_results.py` 는 `run_one` 풀 재실행 → **candidate 답안 재생성**(GPT 답안 새로 굴림·2× billing·원본 손실). run_error 치유용.
- `regrade_results.py` 는 **저장된 answer_text 재사용 + judge 만 재호출**(1× billing·답안 보존·`--workers` 병렬 내장). judge-only 실패엔 이게 정확 — 변수를 judge 하나로 격리(M6 목적·M8 κ 전제 "같은 답안 채점"과 일치).
- 단 regrade 는 기본 전체 재채점 → 멱쩡한 144건도 judge drift 오염. **세션12에 `--only-failed` 추가**(judge_failed·error 만 재채점, 나머지 원본 보존).
- Workflow 불필요: `--workers` ThreadPoolExecutor 가 검증된 병렬 경로(CLAUDE.md — 기존 병렬경로 우선). 58건은 `--workers 8`로 금방.

## 읽어야 할 파일
- `scripts/regrade_results.py` — 왜: 재채점 실행기(`regrade_record` 가 answer_text 재사용 + 강화된 judge_answer 호출 + judge.error 시 미채점 마커, no silent-0). `--only-failed`·`--workers`.
- 생성된 step0 `src/ktaxbench/grading/judge.py`(강화본) — 왜: 강화된 파서로 재실패율↓. step0 완료가 전제.
- `src/ktaxbench/report.py` (`judge_failed`) — 왜: 대상 식별 + 전후 카운트 대조 기준.

## 작업 (opt-in 후)
1. 대상: `outputs/m4r1/gpt-5.5_20260613T092709Z.jsonl` — 58 judge_failed(candidate gpt-5.5 × judge claude-sonnet-4-6). 전후 judge_failed 카운트 기록.
2. judge 는 **claude-sonnet-4-6**(원본 judge 동일 → step0 강건화 효과 + judge-swap 분석 유효. self-eval 가드: judge≠candidate(gpt-5.5) OK).
3. 실행:
   ```bash
   PYTHONPATH=src python scripts/regrade_results.py \
     --in-file outputs/m4r1/gpt-5.5_20260613T092709Z.jsonl \
     --out-file outputs/m4r1/gpt-5.5_20260613T092709Z_regraded.jsonl \
     --judge claude-sonnet-4-6 --only-failed --data data/sample-questions-v0.1.jsonl --workers 8
   ```
4. 재집계 영향은 step3.

## Acceptance Criteria
```bash
PYTHONPATH=src python -c "import json,sys; sys.path.insert(0,'src'); from ktaxbench.report import judge_failed; \
rs=[json.loads(l) for l in open('outputs/m4r1/gpt-5.5_20260613T092709Z_regraded.jsonl',encoding='utf-8') if l.strip()]; \
print('judge_failed:', sum(judge_failed(r) for r in rs), '/ total', len(rs))"
```

## 검증 절차
1. 재채점 후 judge_failed 카운트 대폭 감소(잔존분은 raw_response 로 원인 진단).
2. 보존 144건 점수 불변(원본 그대로) + healed 58건 정당한 점수(0 아닌 실채점) 표본 육안.
3. index.json step2 blocked→completed + summary(전후 카운트·잔존 원인). **opt-in 전에는 blocked 유지.**

## 금지사항
- 사용자 opt-in 없이 라이브 judge 실행 금지. 이유: billing·CLAUDE.md 자동위임금지.
- `--only-failed` 없이 전체 재채점 금지. 이유: 멀쩡한 144건 judge drift 오염.
- judge == candidate 로 재채점 금지. 이유: self-eval 천장(judge 규약).
- 잔존 judge_failed 를 0점으로 둔갑 금지. 이유: silent-0 재발. 미채점은 집계 제외 유지.
