# Step 1: schema-validator

## 읽어야 할 파일

먼저 아래를 읽고 문항 스키마·검증 규약·기존 자산을 파악하라:

- `docs/benchmark-schema.md` — 문항 스키마 v0.1 전체(최상위 필드·enum·question/answer/rubric/sources/review/license 객체). **이 문서가 단일 진실 원천(SSOT)이다.**
- `docs/ARCHITECTURE.md` — 디렉토리 구조·패턴(결정론 분리, 단방향 파이프라인).
- `docs/adr/0001-vendor-not-import-taxagent.md`, `docs/adr/0002-claude-cli-first.md`.
- `CLAUDE.md` — ⚠ Judge 규약(product/backend: lint·테스트 통과 전 완료 선언 금지, 새 기능은 재현 테스트로 검증).
- `scripts/hash_question.py` — 기존 해시 산출 도구(`content_hash(obj)`). 검증기는 이 해시 기준을 **재구현하지 말고 import해서 재사용**하라.
- `data/sample-questions-v0.1.jsonl` — 검증 대상 19문항(한 줄 1문항). UTF-8.
- `src/ktaxbench/__init__.py` — 패키지 진입점(이미 존재).

## 작업

문항 스키마를 코드로 박고, 데이터셋 전체를 검증하는 CLI와 pytest를 만든다.

### 1) `src/ktaxbench/schema.py`

`docs/benchmark-schema.md`의 enum과 객체 구조를 dataclass + 검증 함수로 옮긴다. 표준 라이브러리만 사용(pydantic 금지 — 의존성 최소, ADR 0001 정신).

핵심 enum 상수(문자열 집합)를 모듈 상수로 정의:
- `DOMAINS` = {vat, corp_tax, income_tax, basic_tax_law, local_tax, accounting, audit, commercial_law, mixed}
- `TASK_TYPES` = {multiple_choice, short_answer, calculation, case_reasoning, citation, risk_analysis, agent_workflow}
- `VISIBILITIES` = {public_sample, private, holdout}
- `STATUSES` = {draft, internal_reviewed, expert_reviewed, retired}
- `BENCHMARK_MODES` = {closed_book, rag, agent}
- `DIFFICULTIES` = {easy, medium, hard, expert}
- `SOURCE_TYPES` = {statute, regulation, ruling, case_law, tax_tribunal, exam, standard, practice_case, secondary}

시그니처(구현은 재량, 단 규칙은 준수):

```python
def validate_question(obj: dict) -> list[str]:
    """문항 1개를 검증. 위반 메시지 리스트 반환(빈 리스트=통과). 예외 던지지 말 것."""

def is_valid(obj: dict) -> bool: ...
```

`validate_question`이 **반드시 잡아야 하는** 규칙(M1 성공기준·Judge 규약에서 도출):
1. 필수 최상위 필드 존재: id, version, status, visibility, language, jurisdiction, benchmark_mode, domain, task_type, difficulty, time_basis, question, answer, rubric, sources, tags, review, license, hash.
2. enum 위반: domain/task_type/visibility/status/difficulty/benchmark_mode[]/sources[].type 값이 위 집합에 속하는가.
3. `id` 형식: `ktb-{domain}-{NNNN}` 정규식, 그리고 id의 domain 부분이 `domain` 필드와 일치.
4. `time_basis` 형식: `YYYY-MM-DD`.
5. **rubric 합계 == total_points**: `sum(criteria[].points) == rubric.total_points` (보통 100). 불일치는 위반.
6. **sources locator 존재**: 각 `sources[]`에 비어있지 않은 `locator`가 있어야 한다(근거 추적성). `url`은 권장(없으면 경고가 아니라 통과시키되, statute/regulation 타입은 url 권장 메시지). statute/case_law 등 권위 출처가 sources에 **최소 1개** 있어야 한다(근거 없는 문항 금지 — Judge 규약).
7. **hash 일치**: `scripts/hash_question.py`의 `content_hash(obj)` 결과가 `obj['hash']`와 같아야 한다(오염 추적 무결성).
8. multiple_choice면 `question.choices`가 비어있지 않아야 하고, calculation이면 `answer.calculation_steps`가 비어있지 않아야 한다(유형-필드 정합).

`scripts/hash_question.py` import 방법: 그 파일은 `scripts/` 에 있고 패키지가 아니다. `schema.py`에서 직접 import가 어렵다면, 해시 검증 로직은 `validate_questions.py`(아래 CLI)에서 `scripts/hash_question.py`의 `content_hash`를 import해 수행하고, `schema.py`는 hash 필드 **존재·형식**(`sha256:` 접두)만 검사하도록 역할을 나눠도 된다. 단 어느 쪽이든 hash 불일치는 최종적으로 검출돼야 한다.

### 2) `scripts/validate_questions.py`

CLI. 용법:
```
python scripts/validate_questions.py data/sample-questions-v0.1.jsonl
python scripts/validate_questions.py data/sample-questions-v0.1.jsonl --json
```
- JSONL을 한 줄씩 로드, 각 문항에 `validate_question` 적용 + `content_hash` 대조.
- 위반이 있으면 `{id}: {메시지}` 를 stderr/stdout에 출력하고 **exit code 1**, 0건이면 `N questions, 0 violations` + exit 0.
- `--json`이면 위반을 JSON 배열로 출력.
- 출력은 한글 깨짐 방지(`encoding='utf-8'`, Windows에서 `python -X utf8` 가정).

### 3) `tests/test_schema.py`

pytest. 표준 라이브러리 + pytest만.
- `test_existing_dataset_valid`: `data/sample-questions-v0.1.jsonl`의 **19문항 전부** `validate_question` 통과(위반 0). 이게 회귀 가드.
- `test_enum_violation_detected`: 정상 문항을 복사해 `domain`을 `"bogus"`로 바꾸면 위반 메시지가 나온다.
- `test_rubric_sum_mismatch_detected`: criteria points 합을 틀리게 만들면 검출된다.
- `test_missing_source_locator_detected`: sources[0].locator를 지우면 검출된다.
- `test_hash_mismatch_detected`: question을 바꾸고 hash를 그대로 두면 검출된다.

`tests/__init__.py`는 비워서 생성. 데이터 경로는 레포 루트 기준으로 robust하게(`pathlib.Path(__file__).resolve().parents[1]`).

## Acceptance Criteria

```bash
uv run python scripts/validate_questions.py data/sample-questions-v0.1.jsonl   # exit 0, "19 questions, 0 violations"
uv run pytest tests/test_schema.py -q                                          # all pass
uv run python scripts/hash_question.py data/sample-questions-v0.1.jsonl --check # 0 stale/missing hash
```

## 검증 절차

1. 위 AC 3개 커맨드를 모두 실행해 통과를 확인한다.
2. 아키텍처 체크리스트:
   - `src/ktaxbench/schema.py` 가 `docs/ARCHITECTURE.md` 구조를 따르는가?
   - 표준 라이브러리만 썼는가(pydantic 등 신규 의존성 추가 금지 — ADR 0001)?
   - enum 값이 `docs/benchmark-schema.md`와 **정확히** 일치하는가(오타·누락 없이)?
3. `phases/mvp-eval-harness/index.json`의 step 1을 업데이트한다:
   - 성공 → `"status": "completed"`, `"summary"`: 생성 파일(schema.py·validate_questions.py·test_schema.py)과 검증 결과 한 줄.
   - 3회 수정 후에도 실패 → `"status": "error"`, `"error_message"`: 구체적 실패 내용.

## 금지사항

- **기존 19문항 데이터를 수정하지 마라.** 이유: 검증기가 데이터에 맞추는 게 아니라, 데이터가 스키마를 통과해야 한다. 만약 기존 문항이 위반을 내면 그것은 schema 규칙이 과도한 것이거나 진짜 데이터 결함이다 — 데이터를 고치지 말고 `error` 상태로 보고하라(문항 정답·근거 수정은 self-judgment 금지, Judge 규약).
- **pydantic·jsonschema 등 신규 런타임 의존성 추가 금지.** 이유: ADR 0001 의존성 최소화. 표준 라이브러리로 충분하다.
- **`scripts/hash_question.py`의 해시 산출 기준을 재구현하지 마라.** 이유: 두 곳의 해시 로직이 갈라지면 오염 추적이 깨진다. 반드시 그 파일의 함수를 재사용하라.
- 기존 테스트를 깨뜨리지 마라(아직 없으면 해당 없음).
