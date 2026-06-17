# Step 2: m2-load-and-validate

> 로컬·무billing. M1 산출물(신규 income 7문항)을 M2 실행기가 정상 로드·채점경로에 태우는지 확인하는 **다리**. 이번 +7은 calc/case/risk만(agent형 없음) → **격리 스모크 불필요**(세션4·5 동일 판단). 로드·grade 경로 sanity만.

## 읽어야 할 파일
- `phases/income-100-m3-rerun/step1.md` 의 결과(index.json step1 summary) — 왜: 신규 7문항 id·task_type·visibility. 이 step이 검증할 대상.
- `src/ktaxbench/loader.py` — 왜: 필터 로드(domain·task_type·visibility·id). 신규 문항이 로더 필터에 정상 잡히는지.
- `src/ktaxbench/schema.py` — 왜: lint_question enum·status 연동. validator의 단일 진실원천.
- `tests/test_loader.py` — 왜: 로더 카운트 동적화 테스트. 101문항·income 19로 카운트가 맞는지.
- `scripts/run_eval.py` — 왜: `--id` 필터로 신규 문항만 골라 dry 로드·프롬프트 빌드 경로 확인(라이브 호출 없이).

## 작업
### 1) 신규 문항 로드·필터 sanity
- 신규 7 id가 `--domains income_tax` / `--task-types calculation,case_reasoning,risk` / `--id <신규ids>` 필터에 정확히 잡히는지.
- visibility 라우팅(public_sample/holdout)이 의도대로 분포하는지.

### 2) 프롬프트 빌드 경로(라이브 호출 없이)
- closed_book·rag 두 모드로 신규 문항의 `build_prompt`가 에러 없이 빌드되는지(기준일·required_output·choices 주입). **모델 호출은 안 한다** — 이 step은 무billing.

### 3) 코드 채점 경로 sanity
- calc 문항: `parse_korean_amounts`가 final_answer 금액을 파싱하는지. citation/case: locator 매칭 키 존재 확인. (실채점은 step3 라이브에서.)

## Acceptance Criteria
```bash
uv run pytest                                                                   # all green (loader 카운트 101 반영)
uv run python scripts/validate_questions.py data/sample-questions-v0.1.jsonl    # 0 violations
# 신규 income 로드·프롬프트 빌드 sanity (라이브 호출 없음)
uv run python -c "import sys; sys.path.insert(0,'src'); from ktaxbench.loader import load_questions; from ktaxbench.prompts import build_prompt; qs=[q for q in load_questions('data/sample-questions-v0.1.jsonl') if q.domain=='income_tax']; [build_prompt(q,'closed_book') for q in qs]; [build_prompt(q,'rag') for q in qs]; print('income loaded+built', len(qs))"  # 19, no error
```

## 검증 절차
1. AC 실행(pytest green · validator 0 · income 19 로드·빌드 무에러).
2. visibility 분포·task_type 분포를 step summary에 기록(step3 슬라이스 설계 입력).
3. `phases/income-100-m3-rerun/index.json` step 2 → `completed` + `summary`.

## 금지사항
- **이 step에서 모델 라이브 호출 금지.** 이유: 무billing step. 라이브는 step3 게이트②에서만.
- 신규 agent형이 없으므로 격리 스모크를 돌리지 마라(불필요·시간낭비). 이유: calc/case/risk는 max_steps 도구루프 대상 아님(세션4·5 판단).
- 로더·스키마 코드를 신규 문항 통과시키려고 고치지 마라. 이유: 문항이 스키마를 따라야지 반대 아님. 실패 시 문항을 고친다.
