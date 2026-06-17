# Step 5: llm-judge-and-aggregate

## 읽어야 할 파일
- `docs/rubric-v0.1.md` — 7차원 만점/부분점 기준, 채점자 메모 형식(점수/주요오류/치명오류/실무위험/개선포인트), 감점·실격.
- `docs/benchmark-design-principles.md` — **self-eval 천장**(모델이 자기 답을 채점하면 안 됨), statement-level 부분점(SteuerEx), pass^k(τ-bench) 차용 근거. 해당 섹션을 읽어라.
- `CLAUDE.md`·`docs/DOMAIN.md` — Judge 규약(self-judgment 금지).
- `src/ktaxbench/grading/rubric.py`·`code_grader.py` (step4), `src/ktaxbench/models/base.py`·`registry.py` (step2).

## 작업
주관 차원(근거 적절성·사실반영·실무·리스크·설명)을 LLM-judge로 채점하고, code-grader와 합쳐 최종 점수를 낸다.

### 1) `src/ktaxbench/grading/judge.py`
```python
@dataclass
class JudgeResult:
    scores: dict[str, float]      # dimension -> points
    memo: dict                    # 주요오류/치명오류/실무위험/개선포인트
    fatal_flags: list[str]
    judge_model: str

def judge_answer(question: dict, answer_text: str, *, judge_model_name: str,
                 candidate_model_name: str) -> JudgeResult: ...
```
규칙:
- judge 프롬프트는 `question`(정답·key_points·common_wrong_answers·rubric.criteria·fatal_errors)을 **기준 정답으로** 제공하고, 후보 응답을 차원별 배점에 맞춰 채점하게 한다. 출력은 **구조화 JSON**(dimension→점수 + memo)로 강제(파싱 실패 시 1회 재시도).
- **self-eval 가드(필수)**: `judge_model_name == candidate_model_name`이면 경고를 `memo`에 남기고 `JudgeResult`에 플래그. 가능하면 호출자가 다른 모델을 쓰도록 — 기본 judge는 후보와 다른 모델(레지스트리에서 선택). 이 가드를 우회하지 마라.
- judge는 `ModelClient`로 호출(step2 어댑터 재사용).

### 2) `src/ktaxbench/grading/aggregate.py`
```python
def combine(code_scores: list, judge: JudgeResult, task_type: str) -> dict:
    """code-grader(객관 차원) + judge(주관 차원)를 유형별 가중치로 합산 → 최종 점수·등급·감점 적용."""

def statement_level_score(facts_covered: list[bool]) -> float: ...   # 사례형 부분점(SteuerEx 차용)

def pass_caret_k(successes: int, k: int, n: int) -> float: ...        # agent 신뢰도(τ-bench): n회 중 k회 성공 확률 추정
```
- code 차원과 judge 차원이 겹치면(예 conclusion) **code 우선**(결정론). judge는 code가 못 매기는 차원만.
- 감점(DEDUCTIONS)·fatal 실격은 합산 후 적용. 등급(A/B/C/D)은 rubric-v0.1.md 컷.

### 3) 테스트
- `tests/test_aggregate.py`(결정론, LLM 없음): `combine`이 유형별 가중치로 올바르게 합산, 감점 적용, 등급 매핑. `statement_level_score`·`pass_caret_k` 수식 단위테스트.
- judge 자체는 LLM 의존 → `scripts/smoke_judge.py`(수동): case_reasoning 1문항을 judge_model로 2회 채점해 **분산(재현성)** 출력.

## Acceptance Criteria
```bash
uv run pytest tests/test_aggregate.py -q
uv run pytest -q                                  # 전체 그린
# (수동, 구독 소모) uv run python scripts/smoke_judge.py --question ktb-vat-0001 --judge claude-sonnet-4-6 --candidate claude-haiku-4-5
```

## 검증 절차
1. AC 실행. aggregate는 결정론 테스트로, judge는 smoke로 재현성 분산을 1회 확인.
2. 체크리스트: self-eval 가드 동작(judge==candidate 경고) / code 차원이 judge 차원보다 우선 / pass^k·statement-level 수식이 설계 문서와 일치.
3. `phases/mvp-eval-harness/index.json` step 5 업데이트.

## 금지사항
- **judge_model == candidate_model 을 조용히 허용하지 마라.** 이유: self-eval 천장(design-principles). 반드시 경고·플래그.
- **judge를 결정론 pytest에 넣지 마라.** 이유: 비결정·구독 소모. aggregate만 단위테스트.
- code-grader가 이미 매긴 객관 차원을 judge 점수로 덮어쓰지 마라. 이유: 결정론 우선.
- 기존 테스트를 깨뜨리지 마라.
