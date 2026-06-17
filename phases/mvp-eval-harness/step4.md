# Step 4: code-grader

## 읽어야 할 파일
- `docs/rubric-v0.1.md` — **채점 SSOT**. 7차원(결론25·근거20·계산15·사실10·실무15·리스크10·설명5) + **유형별 가중치 조정**(객관식/계산형/사례형/근거형/에이전트형) + 감점/실격 규칙 + 등급.
- `docs/benchmark-schema.md` — `rubric` 객체(total_points·criteria[].name/points·fatal_errors), `answer` 객체(final_answer·acceptable_answers·calculation_steps).
- `src/ktaxbench/schema.py`, `loader.py` (이전 step).
- `CLAUDE.md` — Judge 규약(결정론 테스트로 검증).
- **vendor 참고**: `C:\Users\yusun\projects\tax-agent\exam\mcq_eval.py`(digit 추출), `C:\Users\yusun\projects\tax-agent\scripts\eval_composite.py`(`_ruling_match` 정규화·동의어), `C:\Users\yusun\projects\tax-agent\evals\eval_goldset.py`(set 기반 채점).

## 작업
**코드로 결정론 채점 가능한 부분만** 담당한다(MC·계산·근거 locator). 주관 차원(실무·리스크·설명)은 step5 LLM-judge 몫.

### 1) `src/ktaxbench/grading/rubric.py`
```python
def weights_for(task_type: str) -> dict[str, int]:
    """rubric-v0.1.md '유형별 가중치 조정' 표를 그대로 반환. 합 == 100."""
DEDUCTIONS = {...}  # 존재하지않는근거 -20, 기준시점무시 -10, 형식미준수 -5, 면책회피 -5, 출처없이단정 -10
```
- 유형별 가중치는 rubric-v0.1.md의 숫자를 **정확히** 옮긴다(객관식 결론50/근거20/사실10/리스크10/설명10 등).

### 2) `src/ktaxbench/grading/code_grader.py`
```python
@dataclass
class CodeScore:
    dimension: str        # conclusion_accuracy 등
    points: float
    max_points: float
    detail: str

def grade_multiple_choice(question: dict, answer_text: str) -> list[CodeScore]: ...
def grade_calculation(question: dict, answer_text: str) -> list[CodeScore]: ...
def grade_citation(question: dict, answer_text: str) -> list[CodeScore]: ...
def can_code_grade(task_type: str) -> bool:   # mc/calculation/citation = True
```
규칙(결정론):
- **MC**: 응답에서 정답 번호 추출(mcq_eval digit 패턴 재사용) → `final_answer`와 비교. 일치=conclusion 만점, 불일치=0. acceptable_answers도 허용.
- **계산**: 응답에서 최종 수치 추출(정규식; 콤마·"원"·억/만원 단위 정규화) → `final_answer`의 정답 수치와 비교. 정확 일치=계산차원 만점. fatal: 정답과 현저히 다른데 확신표현(감지 시 플래그). 부분점은 step5(과정)와 결합.
- **근거(citation)**: 응답에서 조문 locator(예 "제25조", "제61조") 추출 → `sources[].locator` 집합과 비교. 맞는 locator 매칭률로 근거차원 점수. **존재하지 않는 조문 패턴 생성** 감지 시 fatal(-20) 플래그.
- 수치·locator 추출은 순수 함수(같은 입력→같은 출력). 외부 호출 금지.

### 3) `tests/test_code_grader.py` (★ M2 핵심 — 결정론 강제)
- `test_mc_exact`: choices 있는 가상 문항, 정답 번호 응답 → 만점 / 오답 → 0.
- `test_calculation_match`: corp-tax-0003(정답 "손금불산입 800만원") 류 응답에서 800만/8,200만 추출·비교.
- `test_citation_locator`: "제25조" 포함 응답 → sources locator 매칭.
- `test_determinism`: **같은 (question, answer_text)를 2회 채점하면 점수가 정확히 같다**(핵심 회귀).
- `test_fake_article_flagged`: "제999조의5" 류 미존재 조문 생성 시 fatal 플래그.

## Acceptance Criteria
```bash
uv run pytest tests/test_code_grader.py -q     # 전부 통과(특히 test_determinism)
uv run pytest -q                                # 전체 그린(schema·loader·prompts 포함)
```

## 검증 절차
1. AC 실행. `test_determinism` 통과가 M2 성공기준의 핵심.
2. 체크리스트: 유형별 가중치 숫자가 rubric-v0.1.md와 정확히 일치 / 추출 함수가 순수(네트워크·시간·랜덤 없음) / fatal 규칙 반영.
3. `phases/mvp-eval-harness/index.json` step 4 업데이트.

## 금지사항
- **LLM 호출로 채점하지 마라(이 step).** 이유: 여기는 결정론 코드 채점. LLM-judge는 step5.
- **수치/locator 추출에 시간·랜덤·네트워크를 쓰지 마라.** 이유: 결정론(같은 입력→같은 점수)이 M2 성공기준. test_determinism이 이를 강제.
- 정답 수치 비교에서 단위 혼동(만원/억원) 정규화를 빠뜨리지 마라. 이유: 한국어 금액 표기 다양.
- 기존 테스트를 깨뜨리지 마라.
