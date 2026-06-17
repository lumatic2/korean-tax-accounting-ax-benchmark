# Step 7: question-expansion-and-review

> ⚠ 이 step은 **인간(본인) 검수가 필수 게이트**다. headless 세션은 *초안 작성·법령 선검증·validator 통과*까지만 하고, **status 승격은 하지 말고 blocked로 보고**하라. 이유: Judge 규약 — 문항 정답·근거는 모델 self-judgment 금지, 본인(세무·회계 자격) 검수만이 `internal_reviewed`로 승격 가능.

## 읽어야 할 파일
- `playbooks/question-authoring.md` — 제작 9단계 절차(시드→근거검증→재작성→정답·루브릭→검수→도장→라우팅·해시). **이 절차를 그대로 따른다.**
- `docs/DOMAIN.md` — 법인세 표(제55·13·15·19·60·25조). 재사용 검증분.
- `data/sample-questions-v0.1.jsonl` — 기존 19문항(특히 corp-tax-0003 = 모범 계산형, vat-0003/0005 = 모범).
- `scripts/validate_questions.py`·`scripts/hash_question.py` (step1 이후).
- `CLAUDE.local.md`(있으면) "이어서 할 일" — 잔여 검수 항목(부가세 호 단위·전자세금계산서 특례).

## 작업
문항을 19→~30으로 확충하고 검수 라운드를 연다.

### 1) 법인세 신규 문항 `ktb-corp-tax-0004~` (목표 +5~7)
- 후보 쟁점: 업무용승용차 손금(법§27의2), 감가상각 시부인(법§23), 부당행위계산부인(법§52), 대손금(법§19의2), 접대비 특수관계인 변형(§25④2호 — corp-tax-0003 후속).
- **새 조문은 law.go.kr 선검증 필수**(playbook 절차 2): 법제처 DRF(`law_client` 또는 `WebFetch`)로 조문 원문 확인 → DOMAIN.md 표 보강(+개정이력·기준일). 2026 기준(법률 제21218호), 2025 세율(9/19/21/24%) 혼동 금지.
- 유형 다양화: 계산형뿐 아니라 사례형·리스크형·객관식 포함(현 법인세는 계산·사례만).

### 2) 부가세/유형 보강(목표 +몇 개) — 객관식·agent형 비율 점검.

### 3) 검수 라운드
- 신규·기존 draft 문항을 playbook 체크리스트로 자가공격(가짜 조문·임계값 혼동·기준일 누락).
- **여기까지가 headless 한계.** 모든 신규 문항은 `status: draft`로 두고, `scripts/hash_question.py`로 hash 등록, `validate_questions.py` 통과 확인.

## Acceptance Criteria
```bash
uv run python scripts/validate_questions.py data/sample-questions-v0.1.jsonl   # 0 violations
uv run python scripts/hash_question.py data/sample-questions-v0.1.jsonl --check # 0 stale
uv run python -c "import json; n=sum(1 for l in open('data/sample-questions-v0.1.jsonl',encoding='utf-8') if l.strip()); print('count',n)"  # >= 25
```
> **AC를 다 통과해도 step은 completed가 아니다.** `internal_reviewed` 승격은 본인 검수 후에만 → 아래 참조.

## 검증 절차
1. AC 실행(validator·hash·count).
2. **반드시 `phases/mvp-eval-harness/index.json` step 7을 `"status": "blocked"`, `"blocked_reason": "신규 문항 초안·법령 선검증·validator 통과 완료. 본인(전문가) 검수 후 status를 internal_reviewed로 승격해야 M1 클로즈. Judge 규약상 self-judgment 승격 금지."` 로 기록하고 즉시 중단**한다.
3. (본인 후속, 수동) 검수 통과 문항을 `status: internal_reviewed`, `review.expert_reviewed_at` 기록 → 재해시 → validator 재확인. 그 후 step을 completed로.

## 금지사항
- **신규/기존 문항을 `internal_reviewed`/`expert_reviewed`로 승격하지 마라(headless).** 이유: Judge 규약 — 본인 검수만이 정답·근거를 확정. 모델 self-judgment 금지.
- **기존 19문항의 정답·근거를 수정하지 마라.** 이유: 검수된 자산. 확충만.
- **law.go.kr 미검증 조문·수치를 문항에 넣지 마라.** 이유: 가짜 조문은 fatal. 선검증 후 DOMAIN.md 보강분만 사용.
- 시드 기출 원문 표현을 복제하지 마라(저작권 — data-strategy §2.2).
