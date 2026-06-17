# Step 0: public-sample-scope-and-canary

> 로컬·무billing. M4 공개 릴리스에 **어떤 문항을** 내보내고, canary 오염추적 문자열을 **언제·어떻게** 삽입할지의 규칙을 확정한다. 실제 canary 값 삽입·공개 푸시는 **하지 않는다**(공개 릴리스 시점 작업). 이 step의 산출물은 결정론적 선택 규칙 + 전략 문서다.

## 읽어야 할 파일
- `docs/benchmark-schema.md` (§visibility, §canary, §hash) — 왜: 공개 집합을 가르는 필드(`visibility`/`license.public_release_allowed`/`status`)의 enum 정의와 canary 예약 규약("필드 예약만, 값 삽입은 공개 릴리스 시점")이 이 step의 직접 전제.
- `docs/data-strategy.md` (§4 오염·§5 공개시점) — 왜: hash 대조·공개시점 기록의 기존 정책. canary 전략이 이와 모순되면 안 됨.
- `ROADMAP.md` (M4 + 가로지르는 원칙 "적시성·저작권") — 왜: 공개셋이 해자(오염저항)와 저작권 안전선을 동시에 만족해야 함을 명시.
- `data/sample-questions-v0.1.jsonl` — 왜: 실제 분포로 공개 가능 집합을 산출(이미 확인: public_sample 43 중 internal_reviewed 34만 공개 적격, draft 9 제외).

## 작업
### 1) 공개 릴리스 집합 규칙 확정 (결정론)
- 공개 적격 = `visibility == "public_sample"` ∧ `license.public_release_allowed == true` ∧ `status == "internal_reviewed"`(또는 이후 `expert_reviewed`). **draft 제외**.
- 2026-06-12 기준 = **34문항**(income8·accounting7·corp6·vat5·basic5·mixed3 / citation13·calc7·case6·risk6·MC1·short1).
- holdout 58 + draft 9 + private는 **절대 공개 금지**(리더보드 채점셋의 해자).

### 2) canary 삽입 전략 문서화 (삽입은 미실행)
- 공개 시점에 각 공개 문항에 `"canary": "KTAXBENCH-CANARY-<uuid>"` 1개 + 데이터셋 전역 sentinel 1줄 삽입.
- canary는 hash 산출 기준(`question`+`final_answer`)에서 **제외**되어야 함(스키마 §hash 재확인) → 삽입해도 기존 hash 불변임을 명시.
- 오염 모니터링: 향후 모델이 sentinel을 복창하면 학습오염 신호. 점검 주기·방법(공개 모델 probe)을 문서에 적되 자동화는 범위 밖.

### 3) 산출물
- `docs/m4-public-sample-scope.md` — (a) 선택 규칙 SQL식 정의 (b) 현재 34문항 ID 목록·분포표 (c) canary 전략·삽입 시점·hash 불변성 (d) holdout 누수 방지 체크.
- (선택) `scripts/export_public_set.py` — 위 규칙으로 공개 집합을 추출하는 결정론 헬퍼(실제 export 파일은 안 만들고 `--dry-run` 카운트만). 단순 유지 — argparse 없이 기존 `run_eval.py` `_arg` 스타일 따름.

## Acceptance Criteria
```bash
# 문서 생성됨
test -f docs/m4-public-sample-scope.md && echo "doc OK"
# 공개 집합 카운트가 문서 주장과 일치(결정론 재현)
uv run python -X utf8 -c "import json; rows=[json.loads(l) for l in open('data/sample-questions-v0.1.jsonl',encoding='utf-8') if l.strip()]; n=sum(1 for r in rows if r['visibility']=='public_sample' and r.get('license',{}).get('public_release_allowed') and r['status']=='internal_reviewed'); print('publishable',n); assert n==34, n"
# canary 미삽입 확인(이 step에서 데이터 불변)
grep -c '"canary"' data/sample-questions-v0.1.jsonl  # 0 이어야
# 기존 테스트 무회귀
uv run pytest -q
```

## 검증 절차
1. AC 실행(문서 존재·publishable=34·canary 0·테스트 green).
2. 문서의 34문항 ID가 실제 데이터 필터 결과와 1:1 일치하는지 스크립트로 교차확인(수기 나열 금지 — 결정론 산출).
3. `phases/m4-public-track/index.json` step 0 → `completed` + `summary`(확정 규칙·34 분포·canary 시점). 다음 step preamble로 전달.

## 금지사항
- **canary 실제 값을 지금 삽입하지 마라.** 이유: 스키마 §canary가 "값 삽입은 공개 릴리스 시점"으로 명시. 공개 전 삽입은 hash·재현성 혼선 + 미공개 상태 오염추적 무의미.
- **holdout/draft/private 문항을 공개 목록에 넣지 마라.** 이유: 채점셋 해자 붕괴 = Leaderboard Illusion의 1차 원인(공개셋으로 과적합). 규칙은 화이트리스트(공개 적격만)로, 블랙리스트 금지.
- **데이터 파일(jsonl)을 수정하지 마라.** 이유: 검수된 자산. 이 step은 규칙·문서·추출 헬퍼만.
- 34라는 수치를 수기 상수로 박지 마라(데이터 변하면 stale). 문서엔 규칙을, 카운트는 스크립트 재산출.
