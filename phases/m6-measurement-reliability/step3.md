# Step 3: reaggregate-with-ci-report  (step2 게이트)

heal 후 깨끗한 레코드로 재집계 + step1 CI 동반 핵심수치 리포트. step2(heal) 완료가 전제 — step2 blocked 동안 대기.

## 읽어야 할 파일
- 생성된 step1 `src/ktaxbench/stats.py` — 왜: 재집계 수치에 bootstrap CI·paired test 적용.
- `src/ktaxbench/report.py` (`aggregate_results`·`build_public_payload`) — 왜: heal 된 레코드로 재집계. judge_failed 제외가 이제 거의 0(heal 효과).
- `docs/findings/m4r1-multi-provider.md` (§3-1 clean-116 재집계) — 왜: heal 후 수치를 기존 clean-116 과 대조. 정정 헤드라인 업데이트 지점.
- step2 index.json summary — 왜: heal 전후 카운트가 재집계 입력.

## 작업 (step2 완료 후)
1. heal 된 outputs 로 리포트 재산출(`make_report.py --json`) — judge_failed 거의 0 확인.
2. 핵심 수치에 CI 동반: spread CI / RAG vs closed paired diff CI / judge-swap(GPT vs Claude judge) paired CI. step1 stats 사용.
3. finding 문서 갱신: clean-116 → heal 후 full-N 재집계 수치 + CI. 정정 이력 보존(폐기 수치 명시).
4. (선택) 리더보드 payload 에 CI 노출 — build_public_payload 가 step1 CI 필드 포함 시.

## Acceptance Criteria
```bash
PYTHONPATH=src python scripts/make_report.py --json outputs/m4r1/*.jsonl --data data/sample-questions-v0.1.jsonl
PYTHONPATH=src python -m pytest -q
```

## 검증 절차
1. 재집계에서 judge_failed 거의 0(heal 효과 반영).
2. 핵심 수치 3종에 CI 동반 표기.
3. finding 정정(heal 후 수치 + CI, 폐기 수치 이력).
4. index.json step3 → completed + summary.

## 금지사항
- step2(heal) 미완 상태로 재집계 결론 박제 금지. 이유: judge_failed 오염분이 남아 평균 왜곡.
- CI 없이 "유의미 차이" 단정 금지. 이유: M6 verify = 핵심수치에 CI 동반. 근거 없는 단정은 judge 규약 위반.
