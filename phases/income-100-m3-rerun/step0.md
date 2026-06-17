# Step 0: prep-and-calc-verify

> 로컬·무billing. job-watcher 충돌 차단 + 소득세 calc 4종 룰프록시의 현행 수치·산식을 law-mcp로 도장한다. **이 step이 끝나야 step1 Workflow가 검증된 수치 위에서 문항을 만든다.**

## 읽어야 할 파일
- `CLAUDE.local.md` — 왜: "이어서 할 일"의 소득세 목표 셀(calc·case·risk)·job-watcher 자율 도메인 경고·calc 3단 게이트 교훈(B1-Q1 기부금 final_answer↔explanation 모순)이 이 step의 전제.
- `docs/question-blueprint.md` (§6-2) — 왜: 소득세 토픽 커버리지(소득구분§4·거주자성·국외소득·필요경비·양도§89·금융소득종합과세) 중 calc 4종을 어디에 배치할지 근거.
- `docs/DOMAIN.md` — 왜: 소득세 조문 표 현황 확인. 없는 조문은 이 step에서 law-mcp 검증 후 보강(+기준일).
- `data/sample-questions-v0.1.jsonl` — 왜: 기존 income 12문항(calc 0개) 확인 + 모범 calc 문항(corp-tax-0003) 산식 서술 스타일 참조.

## 작업
### 1) job-watcher 일시정지
- 현재 income 작업이 세션5 이전부터 정체 상태지만 pid 살아있음(SessionStart 기준 43452). 충돌·중복 커밋 방지 위해 정지.
- 정지 후 `git log --oneline -5 | grep -i income` 로 정지 중 income 커밋이 안 들어옴을 확인.

### 2) 백업
- `cp data/sample-questions-v0.1.jsonl tmp/backup-before-income.jsonl`

### 3) calc 4종 룰프록시 현행 수치·산식 law-mcp 직접 도장 (소득세법 law_id 001565 / 시행령 003956)
각 토픽의 **계산에 직접 쓰는 수치·산식**을 `mcp__law-mcp__get_law_article`로 확인하고 메모(기준일 2026-06-11):
- **종합소득 산출세액(누진)**: §55 종합소득세율표(과표 구간·누진공제). 항의 각 호 테이블 절단 반환 주의 → 구조 확인 후 표준 현행 세율표로 보강.
- **금융소득 종합과세(그로스업)**: §17(배당소득·배당가산액) 그로스업율, §14 종합과세 기준금액(2천만원), §62 비교과세(원천징수세율 14%) 구조.
- **양도소득세(§89·세율)**: §89 비과세(1세대1주택 등 요건), §104 양도소득세율, §95 장기보유특별공제, §103 양도소득기본공제.
- **근로소득 연말정산**: §47 근로소득공제, §59 근로소득세액공제(산식·한도), §50~52 인적공제 구조.

> 호 단위 테이블이 절단 반환되면(§24·§25 전례) 구조만 확인되는 즉시 **표준 현행값으로 보강**하고 출처·기준일을 메모. 시점민감 수치(공제율·기준금액)는 반드시 직접 조회.

## Acceptance Criteria
```bash
# 백업 존재
test -f tmp/backup-before-income.jsonl && echo "backup OK"
# job-watcher 정지 확인(정지 중 income 커밋 없음)
git log --oneline -5 | grep -i income || echo "no income commit during pause — OK"
# 기준 카운트(이 step에선 문항 불변)
uv run python -c "import json; n=sum(1 for l in open('data/sample-questions-v0.1.jsonl',encoding='utf-8') if l.strip()); print('count',n)"  # 94
```

## 검증 절차
1. AC 실행(백업·정지·카운트=94).
2. calc 4종 수치·산식 메모가 전부 law-mcp 출처+기준일을 가졌는지 확인(추정 0건). DOMAIN.md 소득세 섹션에 신규 조문 보강이 필요하면 이 step에서 반영.
3. `phases/income-100-m3-rerun/index.json` step 0 → `completed` + `summary`(검증한 4종 수치·확인한 조문번호 요약). 다음 step preamble로 전달.

## 금지사항
- **law-mcp 미검증 수치를 step1로 넘기지 마라.** 이유: calc 문항의 정답이 곧 이 수치 — 가짜면 fatal. Judge 규약.
- **job-watcher 정지 안 하고 step1 진입 금지.** 이유: 같은 income 도메인 동시 편집 → 커밋 충돌·중복 문항.
- 기존 94문항을 수정하지 마라. 이유: 검수된 자산. 이 흐름은 확충·평가만.
