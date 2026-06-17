# Step 0: canary-insert-script

공개 릴리스 학습오염 탐지를 위한 canary 삽입 스크립트. **이 step 은 스크립트만 만든다 — 실제 데이터/릴리스에 canary 를 넣지 않는다**(삽입은 step3 릴리스 시점).

## 읽어야 할 파일
- `docs/m4-public-sample-scope.md` (§3 canary 삽입 전략, §4 릴리스 게이트) — 왜: 삽입 형태(문항별 `KTAXBENCH-CANARY-<uuid4>` + 전역 sentinel)·hash 불변 규칙이 여기 결정론으로 박혀있음. 스크립트는 이 규칙의 코드화.
- `docs/benchmark-schema.md` (§canary, §hash) — 왜: canary 는 hash 산출 기준(`{question, final_answer}`)에서 제외. 삽입 후 기존 hash 가 변하면 안 됨(누수 대조 불변).
- `scripts/export_public_set.py` — 왜: 공개 적격 release.jsonl 추출 경로. canary 삽입은 이 출력에 적용됨. 같은 입출력 컨벤션(`--data`/`--out`/`--dry-run`) 따를 것.
- `scripts/hash_question.py` — 왜: hash 산출 함수 재사용. 삽입 전후 hash diff 0 을 스크립트 내부에서 assert.

## 작업
`scripts/insert_canary.py` 신규:
- 입력: release.jsonl(공개 적격 문항) + 선택 `--seed`(재현용). 출력: canary 삽입된 jsonl + 전역 sentinel.
- 시그니처(인라인 CLI, argparse 없이 기존 스크립트 컨벤션 따라도 됨):
  - 각 문항에 `q["canary"] = f"KTAXBENCH-CANARY-{uuid4}"` (문항당 1개, 이미 있으면 덮어쓰지 않음 — **멱등**).
  - 전역 sentinel `KTAXBENCH-CANARY-GLOBAL-<uuid4>` 1줄을 별도 반환/출력(매니페스트가 박제 — step1).
  - **hash 불변 강제**: 삽입 전 각 문항 hash 계산 → canary 삽입 → 재계산 → `assert before == after` (canary 가 hash 입력에 새면 즉시 실패). 이게 핵심 안전장치.
  - `--seed` 주면 uuid 결정론(`uuid.UUID(int=...)` 또는 seeded rng)으로 재현 가능 테스트.
- 재현테스트 `tests/test_insert_canary.py`: ① 멱등(2회 실행 시 canary 불변) ② hash 불변 ③ 모든 공개 문항에 canary 존재 ④ 전역 sentinel 형식.

## Acceptance Criteria
```bash
PYTHONPATH=src python -m pytest tests/test_insert_canary.py -q && PYTHONPATH=src python -m pytest -q
```

## 검증 절차
1. AC 커맨드 — 신규 테스트 + 전체 그린(현 98 → 신규분 추가).
2. canary 가 hash 산출에 안 들어가는지 스크립트 내부 assert 로 강제됨을 테스트가 확인.
3. index.json step0 → completed + summary(생성 파일·테스트 수).

## 금지사항
- **실제 data/sample-questions-v0.1.jsonl 에 canary 삽입 금지.** 이유: 삽입은 릴리스 시점(step3)에만. 본 데이터 오염 시 hash 누수 대조 깨짐.
- canary 를 hash 입력(`{question, final_answer}`)에 포함 금지. 이유: 공개↔비공개 hash 대조 불변성 파괴(schema §hash).
- 기존 테스트 깨지 마라.
