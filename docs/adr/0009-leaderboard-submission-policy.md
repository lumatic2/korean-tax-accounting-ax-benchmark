# 0009 — 공개 리더보드 제출·철회·재현 정책을 「Leaderboard Illusion」 4대 실패모드 차단으로 설계한다

## Status
Accepted (2026-06-12)

## Context
M4 공개 트랙은 모델을 줄 세우는 공개 리더보드를 연다([ROADMAP](../../ROADMAP.md) M4). 그러나 공개 리더보드는 운영 규칙이 없으면 신뢰자산이 아니라 조작 표면이 된다. 「The Leaderboard Illusion」(Chatbot Arena 분석)이 실증한 4대 실패모드:

1. **비공개 N회 재시도 후 best-pick** — 같은 모델을 여러 번 비공개로 돌려 가장 좋은 점수만 게시 → 운(variance)을 실력으로 오인.
2. **선택적 철회로 손실 표본 은폐** — 불리한 결과를 내려 표본을 편향시킴(생존자 편향).
3. **데이터 접근 비대칭** — 일부 제출자만 비공개 데이터·실행기에 접근 → 공정 비교 붕괴.
4. **공개 테스트셋 과적합** — 공개된 문항에 맞춰 튜닝 → 일반화 아닌 암기.

K-TaxBench는 이미 이를 막을 자산을 갖췄다: 버전핀(model id·data hash·scaffold·mode), visibility 분리(public_sample 34 vs holdout 58, [m4-public-sample-scope.md](../m4-public-sample-scope.md)), self-eval 제거(judge=비self 모델, [CLAUDE.md](../../CLAUDE.md) Judge 규약). 정책은 이 자산을 규칙으로 박는다. 이 ADR은 **정책 결정**이며 웹 구현(step3)이 아니다.

## Decision
다음 5개 규칙을 공개 리더보드 운영 정책으로 확정한다. 각 규칙은 실패모드와 1:1 대응한다.

| # | 규칙 | 차단 실패모드 |
|---|------|--------------|
| 1 | **제출 단위 = 버전핀 동결·append-only** | ① 재시도 best-pick |
| 2 | **순위는 holdout으로만, 공개셋 점수는 별도 표기** | ④ 공개셋 과적합 |
| 3 | **게시물 철회 불가(아카이브 회색표시만)** | ② 선택적 은폐 |
| 4 | **등재 = 버전핀 재현 검증 통과(self-report 금지)** | (Judge 규약 self-eval 천장) |
| 5 | **모든 제출자 동일 공개셋·동일 실행기** | ③ 접근 비대칭 |

세부:
1. **버전핀 동결·append-only** — 제출 시 model id·제출일·scaffold(prompt_version)·mode를 동결. 같은 모델 재제출은 **새 행**(덮어쓰기 금지). 여러 행이 보이면 variance가 가시화돼 best-pick이 무의미.
2. **holdout 순위** — 리더보드 순위는 비공개 holdout(58)+로테이션으로 산정. 공개셋(34)은 연습·디버그·재현 데모용이며 점수는 별도 컬럼으로만 표기(공개셋↔holdout 격차가 과적합 지표).
3. **철회 불가** — 한번 게시된 결과는 내릴 수 없다. 재현 오류·정정은 supersede 행 추가로(원행은 회색 아카이브로 잔존). 손실 표본 은폐 차단.
4. **재현 검증** — 제출 결과는 버전핀으로 운영자가 재실행해 재현돼야 등재. 제출자 self-report 점수는 등재 불가([CLAUDE.md](../../CLAUDE.md) Judge 규약 — self-eval 천장). judge는 비self 모델 고정([ADR 0002](0002-claude-cli-first.md) 후속, judge=sonnet 관행).
5. **접근 대칭** — 모든 제출은 동일 공개셋·동일 실행기(`scripts/run_eval.py` + 핀된 config)로 평가. 비공개 데이터·전용 실행기 우대 없음.

## Consequences
- ✅ 4대 실패모드를 운영 규칙으로 구조적으로 차단 — "리더보드 환상"이 아닌 재현 가능한 변별 자산.
- ✅ holdout 순위 + 공개셋 격차 표기로 과적합이 점수에 드러남(숨길 수 없음).
- ✅ append-only·철회불가로 표본 조작·운빨 best-pick 차단.
- ⚠ **운영 비용** — 매 제출을 운영자가 재현 검증(billing·usage). 초기엔 본인이 모든 제출을 대행(외부 셀프서비스 제출은 후속). 대규모 eval은 세션 usage창 슬라이스 필요([CLAUDE.local.md] 교훈).
- ⚠ **holdout 소진** — 순위셋이 공개·암기되면 무력화. 로테이션·신선문항 보충(적시성 원칙)으로 상쇄. canary는 공개셋 오염추적이지 holdout 보호가 아님.
- ⚠ 철회불가는 정정 마찰을 만든다 — 데이터 결함 발견 시 supersede 행 + finding 문서로 투명 정정(과거 basic-tax-law-0001 gold 결함 사례처럼).
