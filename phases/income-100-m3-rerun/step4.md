# Step 4: report-and-docs

> 로컬·무billing. M3 재평가 결과를 문서화하고 M1을 100 돌파로 클로즈. job-watcher 재가동 + 핸드오프.

## 읽어야 할 파일
- `phases/income-100-m3-rerun/step3.md` 의 결과(index.json step3 summary) — 왜: spread·모델점수·RAG 효과·신규 문항 스팟체크 결과. 리포트·ROADMAP에 박을 수치.
- `ROADMAP.md` — 왜: M1 🔄→상태 갱신·M3 변경이력 append(150줄 cap). 마일스톤 기록 위치.
- `README.md` — 왜: 현재 상태(94문항→101·도메인 분포) 최신화 위치.
- `docs/findings/` — 왜: M3 재평가 신규 finding(101문항 spread·RAG 재확인) 추가 위치.
- `CLAUDE.local.md` — 왜: 다음 세션 핸드오프 덮어쓰기(M1 100 달성·M4 착수 검토로 갱신).

## 작업
### 1) 진단 리포트 문서화
- `outputs/m3-rerun-101-<date>/report.md`(gitignored)의 핵심 수치를 `docs/findings/m3-rerun-101.md`로 추출·박제(spread·모델순위·RAG 환각감소·신규 income 문항 거동).

### 2) 마일스톤 갱신
- `ROADMAP.md`: M1 성공기준 충족분 갱신(101문항·6→7도메인 셀 충족·소득세 calc 0→4) + 변경이력에 본 세션 1줄(150줄 cap 유지). M1 100 돌파 명시.
- `README.md`: 문항수·도메인 분포·모드 현황 최신화.

### 3) 마감
- job-watcher 재가동(step0에서 정지한 것).
- `CLAUDE.local.md` 핸드오프 갱신: M1 100 달성·M3 재평가 완료·다음=M4 공개 트랙 착수 검토.
- (선택) `/session-end`로 ROADMAP·핸드오프·vault 로그 일괄.

## Acceptance Criteria
```bash
uv run python scripts/validate_questions.py data/sample-questions-v0.1.jsonl   # 0 violations (최종 확인)
uv run pytest                                                                   # all green
git status --short                                                             # 의도한 문서 변경만 staged
test -f docs/findings/m3-rerun-101.md && echo "finding doc OK"
```

## 검증 절차
1. AC 실행(validator 0 · pytest green · finding 문서 존재).
2. ROADMAP·README·CLAUDE.local.md 갱신 내용이 step3 실측 수치와 일치(추정 0).
3. 커밋: `docs(ROADMAP): M1 100 돌파 — 소득세 +7·M3 101문항 재평가` 등 문서 커밋.
4. `phases/income-100-m3-rerun/index.json` step 4 → `completed` + `summary`. phases/index.json의 `income-100-m3-rerun` → `completed`.

## 금지사항
- **outputs/ 원본을 커밋하지 마라.** 이유: gitignored 대용량. 추출한 finding 요약만 추적.
- **step3에서 안 나온 수치를 리포트에 쓰지 마라.** 이유: Judge 규약 — 실측만. self-judgment 금지.
- job-watcher 재가동을 빠뜨리지 마라. 이유: step0에서 정지시킨 자율 도메인 작업 — 복구 안 하면 income 자율채움이 멈춘 채 방치.
