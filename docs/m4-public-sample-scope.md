# M4 공개 샘플셋 범위 · canary 전략

> M4 공개 트랙 step0 산출물. 공개 릴리스에 **무엇을** 내보내고 canary를 **언제·어떻게** 삽입할지의 결정론적 규칙. 실제 canary 값 삽입·공개 푸시는 이 문서 시점에 **하지 않는다**(공개 릴리스 시점 작업). 근거 스키마: [benchmark-schema.md](benchmark-schema.md) §visibility·§canary·§hash, 정책: [data-strategy.md](data-strategy.md).

## 1. 공개 릴리스 집합 — 선택 규칙 (화이트리스트)

공개 적격 문항 = 아래 **세 조건을 모두** 만족하는 것만:

```
visibility            == "public_sample"
license.public_release_allowed == true
status                in {"internal_reviewed", "expert_reviewed"}   # draft 제외
```

- **화이트리스트 원칙**: 공개 적격만 포함. "이건 빼자"식 블랙리스트 금지 — 누락 1건이 holdout 누수가 되면 채점셋 해자가 무너진다(Leaderboard Illusion 1차 실패모드 = 공개셋 과적합).
- holdout(58) · draft(9) · private 는 **절대 공개 금지**. 리더보드 순위는 holdout으로 매긴다([ADR 0009](adr/0009-leaderboard-submission-policy.md)).
- 카운트·ID 목록은 **수기 상수로 박지 않는다** — 아래 규칙으로 매번 재산출(`scripts/export_public_set.py --dry-run`). 데이터가 늘면 집합도 자동 확장.

## 2. 현재 스냅샷 (2026-06-12 기준, 스크립트 재산출값)

**공개 적격 = 34문항** (전체 101 중).

| 분포축 | 내역 |
|---|---|
| domain | income 8 · accounting 7 · corp 6 · vat 5 · basic 5 · mixed 3 |
| task_type | citation 13 · calc 7 · case 6 · risk 6 · MC 1 · short 1 |
| difficulty | **medium 31 · hard 1 · easy 2** |

> **관측**: 공개셋은 거의 medium. hard/expert 문항은 holdout에 집중 → 공개셋 과적합으로도 상위 난이도 변별은 못 가져가는 구조(해자 강화). 공개셋은 "연습·디버그·재현 데모"용, 순위 산정은 holdout.

ID 목록(34): accounting-0002·0003·0006·0008·0009·0011·0015 / basic-tax-law-0001·0002·0006·0010·0012 / corp-tax-0003·0006·0008·0010·0017·0022 / income-tax-0003·0006·0007·0009·0013·0016·0017·0018 / mixed-0006·0008·0010 / vat-0005·0008·0011·0013·0021.
(이 목록은 스냅샷 — 정본은 스크립트 재산출. 데이터 변경 시 이 표만 갱신.)

## 3. canary 삽입 전략 (삽입은 공개 릴리스 시점 — 지금 미실행)

- **삽입 시점**: 공개 릴리스 직전. 그 전에는 `canary` 필드를 데이터에 넣지 않는다(스키마 §canary "값 삽입은 공개 릴리스 시점").
- **삽입 형태**:
  - 문항별: 공개 각 문항에 `"canary": "KTAXBENCH-CANARY-<uuid4>"` 1개.
  - 데이터셋 전역: 릴리스 아카이브에 sentinel 1줄(`KTAXBENCH-CANARY-GLOBAL-<uuid4>`) — README/매니페스트에 박제.
- **hash 불변성**: canary는 hash 산출 기준(`{question, final_answer}`)에서 **제외**된다(스키마 §hash). 따라서 canary 삽입 후에도 기존 `hash` 값은 변하지 않음 → 공개↔비공개 누수 대조가 canary와 무관하게 유지된다. (릴리스 PR에서 hash diff 0건을 게이트로 확인.)
- **오염 모니터링**: 향후 공개 LLM이 sentinel 문자열을 복창하면 학습데이터 오염 신호. 점검은 공개 모델 probe(분기 1회 권장)로 수동 — 자동화는 범위 밖.

## 4. 릴리스 전 체크 (공개 시점 게이트)

1. `export_public_set.py --dry-run` 카운트 = 의도한 N과 일치.
2. 공개 대상에 holdout/draft/private id가 **0건** 섞였는지 교차확인.
3. 각 공개 문항 `license.public_release_allowed == true` 재확인.
4. canary 삽입 후 기존 `hash` diff 0건(canary가 hash에 안 들어감 확인).
5. holdout 문항 본문·정답이 공개 아카이브에 **미포함**(웹은 holdout 집계값만 노출 — [ADR 0009](adr/0009-leaderboard-submission-policy.md)).
