# Step 3: m3-rerun-eval  ★ billing 게이트② (가장 비용 큼)

> **이 step은 101문항 라이브 평가 = billing 최대.** 진입 전 사용자 opt-in 필수. closed_book + rag × opus/sonnet/haiku, judge=sonnet(self-eval 제거)로 M3 진단을 갱신한다.

## 읽어야 할 파일
- `phases/income-100-m3-rerun/step2.md` 의 결과(index.json step2 summary) — 왜: 신규 income 문항 분포·로드 확인 완료. 평가 대상이 깨끗함을 보장.
- `scripts/run_eval.py` — 왜: 실행 CLI(`--models --modes closed_book,rag --judge --domains --id --accessed-at --workers --out`). 호출 시그니처.
- `src/ktaxbench/runner.py` — 왜: run_batch ThreadPoolExecutor 병렬(`--workers`, 출력순서 보존)·RunRecord 버전핀(model·question_hash·prompt_version·scaffold).
- `docs/findings/m3-rag-vs-closed-book.md` — 왜: 직전 RAG vs closed_book 결과(fake_source 14→4, 평균 24.9→60.25). 이번 재실행이 그 가설을 101문항에서 재확인하는지 비교 기준.
- `ROADMAP.md` (변경 이력 2026-06-09) — 왜: 직전 전체 리포트 spread(30.1, sonnet 93.6·opus 92.8·haiku 63.4). 신규 7문항 추가 후 spread가 유지/개선되는지(saturation/floor 아님) 판단 기준.
- `CLAUDE.local.md` — 왜: 라이브 run 명령 패턴(`set -a && . ~/projects/tax-agent/.env; set +a` 후 PYTHONPATH=src ... --accessed-at 2026-06-11 --workers).

## 작업
### 1) 라이브 평가 실행 (Workflow 병렬 슬라이스 또는 run_eval --workers)
- 모델: claude-opus-4-8 · claude-sonnet-4-6 · claude-haiku-4-5
- 모드: closed_book, rag
- judge: claude-sonnet-4-6 (opus self-eval 오염 제거)
- 데이터: 101문항 전체(`data/sample-questions-v0.1.jsonl`), `--accessed-at 2026-06-11`
- 출력: `outputs/m3-rerun-101-<date>/` (gitignored)
- 병렬: Workflow로 모델×모드 6슬라이스(또는 +도메인 분할) 동시 — 직전 세션 60분→~11분 전례.

### 2) 신규 income 7문항 노이즈 점검
- 신규 문항에서 전 모델 0점/일괄붕괴가 나오면 = 데이터 결함 신호(gold 누락·locator 결함 — basic-tax-law-0001 전례). 해당 문항을 격리·수정 후 재실행.

## Acceptance Criteria
```bash
# 결과 레코드가 생성되고 모델×모드 슬라이스가 다 찼는지(6 슬라이스 × 101 = 606 기대, 실패 레코드 0 지향)
uv run python -c "import json,glob; recs=[json.loads(l) for f in glob.glob('outputs/m3-rerun-101-*/**/*.jsonl',recursive=True) for l in open(f,encoding='utf-8') if l.strip()]; errs=[r for r in recs if r.get('error')]; print('records',len(recs),'errors',len(errs))"
# 변별 성립(리포트 생성 후 spread flag=ok)
uv run python scripts/make_report.py outputs/m3-rerun-101-<date> --out outputs/m3-rerun-101-<date>/report.md && echo "report OK"
```
> spread가 직전 30.1 대비 **유지/개선**이고 flag=ok(saturation/floor 아님)면 PASS. 신규 income 문항이 강모델을 끌어내리면(노이즈) 문항 수정 후 재실행.

## 검증 절차
1. 라이브 실행 완료 → 결과 레코드 무결성(슬라이스 풀충전·error 0 지향).
2. 리포트 생성 → spread·모델순위·RAG 환각감소(fake_source) 직전 대비 비교.
3. 신규 income 7문항 점수 스팟체크(0점 일괄붕괴 = 데이터 결함 → 수정·재실행).
4. `phases/income-100-m3-rerun/index.json` step 3 → `completed` + `summary`(spread·모델점수·RAG 효과 요약). 결과물은 outputs/(gitignored)이므로 리포트 요약을 summary에 박제.

## 금지사항
- **사용자 opt-in 없이 라이브 평가 실행 금지.** 이유: billing 최대·롤백불가.
- **judge=opus 금지.** 이유: opus 후보 self-eval 오염(M3 결정). judge=sonnet 고정.
- **신규 문항 0점을 "모델 약점"으로 단정 금지.** 이유: gold 결함일 수 있음(basic-tax-law-0001 전례 — locator에 조문번호 누락으로 구조적 0점이었음). 먼저 데이터 결함 배제.
- 결과 outputs/를 git에 커밋하지 마라. 이유: gitignored 대용량. 리포트 요약만 docs/문서에(step4).
