# Step 2: leaderboard-two-column-verify

리더보드가 **holdout 순위 + 공개셋 별도 컬럼**을 둘 다 라이브로 보여주는지 확인. M4 step3.3 summary 에 "holdout vs 공개셋 분리 컬럼"이 이미 있다 → 우선 **검증**, 누락 시에만 보강.

## 읽어야 할 파일
- `phases/m4-public-track/index.json` (step3 summary) — 왜: 웹이 이미 ranking(holdout)+public_sample+정책배지를 렌더한다고 기록됨. 실제 라이브와 대조.
- `src/ktaxbench/report.py` (`build_public_payload`) — 왜: payload 는 `ranking`(holdout)+`public_sample`+`version_pins`를 이미 분리 산출. 웹이 public_sample 블록을 실제로 그리는지가 관건.
- `leaderboard/` (Next.js 앱 소스) — 왜: 공개셋 컬럼 렌더 컴포넌트 위치. 누락이면 여기 보강.
- `docs/adr/0009-leaderboard-submission-policy.md` (규칙 2: holdout 순위·공개셋 별도표기) — 왜: 두 컬럼 분리가 정책 요구사항.

## 작업
1. 라이브 사이트(https://lumatic2.github.io/ktaxbench-leaderboard/) 또는 로컬 `leaderboard/` 빌드 산출을 확인 — holdout 순위 표 + 공개셋(public_sample) 집계가 **둘 다 가시적**인지.
2. payload 에 public_sample 데이터가 들어있는데 UI 가 안 그리면 → 공개셋 컬럼/섹션 추가(최소 변경).
3. 둘 다 라이브면 → 검증 통과로 기록(코드 변경 없음). 스크린샷/HTML grep 으로 근거 남길 것.

## Acceptance Criteria
```bash
# 웹 데이터 계약 회귀(payload 두 블록 존재) — 코드 변경 시
PYTHONPATH=src python -m pytest tests/test_report.py -q
# + 라이브/빌드에서 'public_sample' 또는 '공개셋' 컬럼 렌더 확인(육안/grep)
```

## 검증 절차
1. payload 에 ranking·public_sample 두 블록 존재(test_report 회귀).
2. 웹 렌더에 두 컬럼 가시(라이브 fetch 또는 `leaderboard/` 빌드 out grep).
3. index.json step2 → completed + summary(라이브 확인 결과 / 코드 변경 여부).

## 금지사항
- 멀쩡한 웹을 리팩터 금지. 이유: 검증이 목적. 두 컬럼 이미 라이브면 코드 변경 없이 통과 기록.
- holdout 문항 본문·id 를 공개셋 컬럼에 노출 금지. 이유: ADR 0009 — holdout 은 집계값만.
