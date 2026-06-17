# Step 1: statistics-ci-paired-test

핵심 수치(spread·RAG +8.6·judge-swap ±2~4)에 신뢰구간을 동반시킨다. 구 R5. 결정론 모듈 — 무billing·테스트 가능(시드 고정 bootstrap).

## 읽어야 할 파일
- `src/ktaxbench/report.py` (`aggregate_results`·`discrimination`·`build_public_payload`) — 왜: 통계는 이 집계의 *불확실성 정량화*. 같은 records 입력 위에서 CI 산출. 통합 지점(리포트에 CI 필드 추가).
- `tests/test_report.py` — 왜: 리포트 결정론 fixture 위치. CI 도 시드 고정으로 결정론 테스트.
- `docs/findings/m4r1-multi-provider.md` — 왜: judge-swap ±2~4, clean-116 페어 수치. paired test 대상(같은 문항에 judge A vs B). 비교의 단위가 문항-페어임을 확인.
- `scripts/make_report.py` — 왜: 리포트 CLI. CI 출력 표면화 지점.

## 작업 (시그니처 수준)
`src/ktaxbench/stats.py` 신규(순수 함수):
- `bootstrap_ci(values, statistic=mean, n=2000, seed=0, alpha=0.05) -> (lo, hi)` — 재현용 seed 고정(numpy 없으면 random.Random(seed)). 표본 평균/spread 의 percentile CI.
- `paired_bootstrap_diff(a, b, n=2000, seed=0) -> {"diff": , "ci": (lo,hi), "p": }` — 같은 문항에 매칭된 두 점수열(judge A vs B, 또는 RAG vs closed)의 차이 CI + 양측 p(부호 비율). 길이 불일치/결측은 교집합 문항만(페어링 키 명시).
- `spread_ci(by_model_totals, ...)` — 모델 평균들의 spread(최고-최저) bootstrap CI.
- 통합: report 에 얇게 — `aggregate_results` 결과에 `avg_total_ci`(모델별), discrimination 에 `spread_ci` 추가(선택 필드, 기존 소비자 안 깨지게).
- 재현테스트 `tests/test_stats.py`: ① seed 고정 → CI 결정론(같은 입력 같은 출력) ② 알려진 분포 CI 포함관계 ③ paired diff 부호/p ④ 결측·길이불일치 교집합 처리 ⑤ 빈 입력 안전.

## Acceptance Criteria
```bash
PYTHONPATH=src python -m pytest tests/test_stats.py -q && PYTHONPATH=src python -m pytest -q
```

## 검증 절차
1. AC — 신규 + 전체 그린. CI 가 시드 고정으로 결정론(테스트 재현).
2. report 통합이 기존 소비자(웹 payload·markdown) 안 깨는지 test_report 회귀.
3. index.json step1 → completed + summary(stats 함수·통합 지점·테스트 수).

## 금지사항
- 외부 의존성(scipy 등) 새로 추가 금지(있으면 재사용). 이유: 경량 유지·재현성. random.Random 으로 충분.
- 기존 report 필드 시그니처 파괴 금지. 이유: 웹 payload·make_report 동시 의존. CI 는 *추가* 필드.
- self-judgment 으로 p값 해석 결론 박제 금지. 이유: judge 규약 — 수치는 산출만, 해석은 finding 에서 근거와.
