# Step 1: m1-income-authoring  ★ billing 게이트① (Workflow)

> **이 step은 라이브 Workflow run = billing.** 진입 전 사용자 opt-in 필수(추정 실행 금지). 소득세 +7 문항(calc4·case1·risk2)을 제작해 income 12→19, 총 94→101로 M1을 100 돌파시킨다.

## 읽어야 할 파일
- `phases/income-100-m3-rerun/step0.md` 의 결과 메모(index.json step0 summary) — 왜: calc 4종의 law-mcp 검증 수치·산식. **이 수치 위에서만 calc 문항을 만든다.**
- `playbooks/question-authoring.md` — 왜: 제작 9단계 절차(시드→근거검증→재작성→정답·루브릭→검수→도장→라우팅·해시). 그대로 따른다.
- `tmp/fill_cases_calc_wf.js` — 왜: 범용 authoring Workflow 스크립트(task_type별 prompt·schema superset: calc=calculation_steps, risk=missing_data, case=IRAC, citation=근거정확). **args만 income으로 교체해 재사용**.
- `tmp/assemble_b2b3.py` — 왜: 범용 조립 스크립트(4 task_type 루브릭+FATAL+PATCHES 훅). PREFIX에 income_tax 추가, OUTFILES를 income .output 경로로. 호출: `python tmp/assemble_b2b3.py <batch>`.
- `docs/question-blueprint.md` (§6-1·§6-2) — 왜: 소득세 목표 셀(calc3·case1·risk2 → 본 흐름은 calc4로 초과) + 토픽 배치.
- `data/sample-questions-v0.1.jsonl` — 왜: id 충돌 방지(다음 income 번호 확인)·모범 문항 참조.
- `CLAUDE.local.md` — 왜: ★3단 게이트(draft+독립verify+오케스트레이터 결정적 재검증)·calc final_answer↔explanation 내부정합 직접 검산 교훈.

## 작업
### 1) Workflow 배치 제작 (specs → income)
- calc 4: 종합소득 산출세액(누진 §55)·금융소득 종합과세 그로스업(§17·§14·§62)·양도소득세(§89·§104·§95)·근로소득 연말정산(§59·§47).
- case 1: 소득구분/거주자성/필요경비 중 1개(IRAC).
- risk 2: 자료 누락·불확실성 정직성(missing_data) 2개.
- 파이프라인: **draft → 독립 verify 에이전트(조문 실재·현행) → 오케스트레이터(나) 결정적 재검증**.

### 2) ★ calc 4문항 final_answer ↔ explanation 내부정합 직접 역산 검산 (게이트 3단계)
- B1-Q1(기부금) 전례: draft가 final_answer에 오답·explanation에 정답을 적는 모순을 독립 verify가 역산으로 합리화하며 놓침 → 오케스트레이터가 law-mcp로 한도산식 직접조회해 수정.
- **calc 4문항 각각**: final_answer 숫자를 explanation의 단계식으로 독립 역산해 일치 확인. 불일치 시 law-mcp(§55/§17/§104/§59) 직접조회로 정정.

### 3) 조립·검증·해시
- `python tmp/assemble_b2b3.py income` → data 파일에 append.
- validator·hash 통과. 신규 문항 `expert_review_required: true`(본인 검수 전 단계), visibility 라우팅(hard→holdout / medium→public_sample).

## Acceptance Criteria
```bash
uv run python scripts/validate_questions.py data/sample-questions-v0.1.jsonl   # 0 violations, 0 warnings
uv run python scripts/hash_question.py data/sample-questions-v0.1.jsonl --check # 0 stale
uv run pytest                                                                   # all green (loader count 동적 갱신)
uv run python -c "import json; rows=[json.loads(l) for l in open('data/sample-questions-v0.1.jsonl',encoding='utf-8') if l.strip()]; inc=[r for r in rows if r['domain']=='income_tax']; calc=[r for r in inc if r['task_type'] in ('calculation','calculation_steps')]; print('total',len(rows),'income',len(inc),'income_calc',len(calc))"  # total 101, income 19, income_calc 4
```

## 검증 절차
1. AC 실행(validator 0/0 · hash 0 stale · pytest green · count total 101·income 19·income_calc 4).
2. calc 4문항 내부정합 직접 검산 로그를 step summary에 남긴다(어떤 조문으로 어떤 수치를 확정했는지).
3. 커밋: `run(question-authoring): 소득세 +7 — calc4(산출세액·그로스업·양도·연말정산)·case1·risk2 → 101`. (한 데이터파일 여러 배치 섞임 주의 — 이 흐름은 단일 income 배치라 단순 커밋.)
4. `phases/income-100-m3-rerun/index.json` step 1 → `completed` + `summary`.

## 금지사항
- **사용자 opt-in 없이 Workflow run 실행 금지.** 이유: billing·롤백불가 side-effect.
- **calc 문항을 내부정합 검산 없이 커밋 금지.** 이유: verify는 조문 실재만 보장, 수치 정합은 오케스트레이터 책임(B1-Q1 교훈).
- **law-mcp 미검증 조문·수치 문항 금지.** 이유: 가짜 조문 fatal.
- 신규 문항을 `internal_reviewed`/`expert_reviewed`로 승격 금지(headless). 이유: Judge 규약 — 본인 검수만 정답 확정. `expert_review_required: true`로 둔다.
- 시드 기출 원문 표현 복제 금지(저작권 — data-strategy §2.2).
