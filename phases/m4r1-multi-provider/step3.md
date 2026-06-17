# Step 3: live-eval-101-and-judge-swap  ★ billing 게이트② (구독 소모, 대규모)

> **101문항 × closed/rag × 신규 provider = 대규모 라이브 run.** 진입 전 사용자 opt-in 필수. claude_cli 풀런 전례(세션 usage 한도·rate-limit 오염)를 반영해 동시성 보수적·슬라이스 실행.

## 읽어야 할 파일
- `scripts/run_eval.py` — 왜: 풀런 CLI(`--models --modes closed_book,rag --data ... --judge ... --workers ... --out`). 신규 provider 이름으로 호출. 인자 파싱 그대로.
- `phases/income-100-m3-rerun/index.json` step3 summary — 왜: claude_cli 풀런 교훈(18-concurrency rate-limit 606중435 오염→backoff, 세션 usage 한도로 슬라이스 필요). 동시성·슬라이스 전략의 직접 선례.
- `phases/m4r1-multi-provider/step2.md` 결과 — 왜: 확정 모델 ID·동시성·latency. 풀런 규모 산정.
- `data/sample-questions-v0.1.jsonl` — 왜: 평가 대상 101문항(closed/rag 전부 적용).
- `docs/findings/m3-rerun-101.md` (있으면) — 왜: Claude 3모델 기준선 점수. 교차변별 비교 baseline.
- `src/ktaxbench/runlog.py` (`write_results`) — 왜: 출력 jsonl 형식·경로 규약.

## 작업
1. **교차변별 풀런**: 각 신규 provider 를 101 × {closed_book, rag} 로 평가. judge=claude-sonnet-4-6(M3 기준 동일). 동시성은 step2 근거치(미확인 시 `--workers 1`). 슬라이스로 세션 한도 회피.
   - `uv run python scripts/run_eval.py --models <gpt> --modes closed_book,rag --data data/sample-questions-v0.1.jsonl --judge claude-sonnet-4-6 --out outputs/m4r1 --workers <n>`
   - gemini 동일.
2. **judge-swap robustness 1건**: 동일 답안 셋(또는 핵심 부분집합)을 **비-Claude judge**(gpt 또는 gemini)로 재채점 → Claude-judge 순위와 비교. judge 가 자기 패밀리를 편애하는지(self-preference) 점검.
3. raw 결과 `outputs/m4r1/` 에 박제. 오염(rate-limit·빈답) run 은 표시·제외.

## Acceptance Criteria
```bash
ls outputs/m4r1/*.jsonl    # 신규 provider별 결과 존재
uv run python -c "import json,glob; [print(f, sum(1 for _ in open(f,encoding='utf-8'))) for f in glob.glob('outputs/m4r1/*.jsonl')]"  # run 수 확인
```

## 검증 절차
1. provider별 closed/rag 결과 jsonl 존재 + 완주율(오염 제외) 기록.
2. judge-swap 결과(Claude-judge vs 비-Claude judge 순위) 1건 산출.
3. `index.json` step3 → `completed` + summary(provider별 평균·완주율·judge-swap 일치도). 세션 한도/rate-limit 으로 중단 시 `blocked` + 사유(어디까지 됐는지).

## 금지사항
- 사용자 opt-in 없이 풀런 금지. 이유: billing·대규모.
- 오염(rate-limit·빈답) run 을 정상 점수로 리포트 금지. 이유: M3 전례 — 오염이 변별을 왜곡.
- judge self-judgment 으로 정답 판정 금지(Judge 규약). judge-swap 은 robustness 측정이지 정답 재정의가 아님.
