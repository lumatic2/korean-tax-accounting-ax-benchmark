# Step 9: pilot-and-report

> ⚠ 리포트 코드(`report.py`)는 결정론으로 fixture에서 테스트 가능. **실제 파일럿 풀런(3~5모델 × ~30문항)은 구독·키 소모**라 수동/사용자 트리거. 멀티프로바이더(step8) 미완 시 Claude 멀티버전(opus/sonnet/haiku)으로 우선 진행.

## 읽어야 할 파일
- `docs/PRD.md`·`ROADMAP.md`(M3) — 성공기준: 모델 점수가 **유의미하게 벌어짐**(saturation/floor 아님), 분야×차원 진단 리포트.
- `docs/rubric-v0.1.md` — 차원·등급(A/B/C/D), 채점자 메모 형식.
- `src/ktaxbench/runlog.py`(결과 JSONL 포맷)·`runner.py`·`grading/aggregate.py` (이전 step).

## 작업

### 1) `src/ktaxbench/report.py`
```python
def aggregate_results(records: list[dict]) -> dict:
    """결과 JSONL → 모델×분야×차원 점수 매트릭스 + 변별 지표."""
def discrimination(matrix: dict) -> dict:
    """모델 간 점수 분산·범위. saturation(다 높음)/floor(다 낮음) 플래그."""
def error_cases(records: list[dict]) -> dict:
    """환각(가짜 조문 fatal)·계산오류·근거오류 사례 추출(차원별 0점·fatal_flags 기준)."""
def to_markdown(report: dict) -> str:
    """분야×차원 표 + 모델 랭킹 + 변별 진단 + 대표 오류 사례. 한국어."""
```

### 2) `scripts/make_report.py` (CLI)
```
python scripts/make_report.py outputs/results/*.jsonl --out outputs/report.md
```

### 3) 테스트
- `tests/test_report.py`(결정론): `tests/fixtures/sample_results.jsonl`(소수 가짜 결과)로 `aggregate_results`·`discrimination`·`error_cases`가 올바른 매트릭스·플래그를 내는지. saturation/floor 경계 케이스.

### 4) 파일럿 풀런(수동/사용자 트리거)
- `scripts/run_eval.py`로 모델 3~5개 × 모드 × ~30문항 실행 → `outputs/results/`.
- `scripts/make_report.py`로 리포트 생성 → 모델 변별 확인.

## Acceptance Criteria
```bash
uv run pytest tests/test_report.py -q
uv run pytest -q                              # 전체 그린
uv run python scripts/make_report.py tests/fixtures/sample_results.jsonl --out outputs/report_fixture.md && echo "report OK"
# (수동 파일럿, 구독/키 소모)
# uv run python scripts/run_eval.py --models claude-opus-4-8,claude-sonnet-4-6,claude-haiku-4-5 --modes closed_book,rag --data data/sample-questions-v0.1.jsonl --out outputs/results
# uv run python scripts/make_report.py outputs/results/*.jsonl --out outputs/report.md
```

## 검증 절차
1. AC(결정론 부분) 실행 — fixture 리포트 생성·테스트 통과.
2. **파일럿 풀런은 수동**: 모델 3개 이상으로 실행 후 리포트가 모델 변별을 보이는지 확인.
   - 변별 안 됨(다 비슷) → `blocked`/메모로 "M1 문항 난이도·문항 수 재설계 필요(M3 리스크)" 기록 후 사용자 논의.
3. `phases/mvp-eval-harness/index.json` step 9 업데이트. 통과 시 **M3(파일럿+진단) 1차 완료** = phases/index.json의 mvp-eval-harness completed.

## 금지사항
- **리포트 로직을 라이브 풀런에 의존시키지 마라.** 이유: fixture로 결정론 테스트. 풀런은 데이터 공급원일 뿐.
- 변별이 안 나오는데 "성공"으로 보고하지 마라. 이유: M3의 목적은 변별 증명 — 안 되면 그게 발견(문항 재설계 신호)이다. 솔직히 플래그.
- outputs/ 산출물을 git에 커밋하지 마라(gitignored).
