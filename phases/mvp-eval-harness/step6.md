# Step 6: runner-and-runlog

## 읽어야 할 파일
- `docs/ARCHITECTURE.md` — 데이터 흐름·버전핀·상태관리(불변 입력·결과 산출물 outputs/).
- `docs/PRD.md` — M2 성공기준(3모드, 같은 입력→같은 code-score, 버전핀 기록).
- 이전 step 산출물 전부: `loader.py`, `prompts.py`, `rag/retriever.py`, `models/`, `grading/`.
- `scripts/hash_question.py` — data hash(문항 무결성)·결과 핀에 재사용.

## 작업
파이프라인을 엮어 한 문항을 (mode, model)로 평가하고 버전핀과 함께 결과를 영속화한다.

### 1) `src/ktaxbench/runner.py`
```python
@dataclass
class RunRecord:
    question_id: str
    question_hash: str        # 문항 content hash(오염 추적)
    model: str
    mode: str                 # closed_book/rag/agent
    prompt_version: str
    answer_text: str
    code_scores: list
    judge: dict | None
    final: dict               # aggregate.combine 결과(점수·등급·감점)
    accessed_at: str | None   # rag면 retriever 핀
    scaffold: dict            # {prompt_version, retriever_limit, judge_model, ...} 재현 메타

def run_one(question: dict, mode: str, model_name: str, *,
            judge_model_name: str | None = None, accessed_at: str | None = None) -> RunRecord: ...

def run_batch(questions: list[dict], modes: list[str], model_name: str, **kw) -> list[RunRecord]: ...
```
규칙:
- rag 모드면 `retrieve_context` 호출해 context 주입, `accessed_at` 핀 기록.
- code-gradable 유형이면 code_grader, 아니면(또는 주관 차원) judge 호출 → aggregate.combine.
- **버전핀 필수**: model id, question_hash, prompt_version, scaffold를 모든 RunRecord에 박는다. 이게 비교가능성·재현성의 핵심(M2 성공기준).
- 한 문항 실패는 RunRecord에 error로 기록하고 계속(배치 견고성).

### 2) `src/ktaxbench/runlog.py`
```python
def write_results(records: list[RunRecord], out_dir: str = "outputs/results") -> str:
    """JSONL로 저장(파일명에 model·timestamp). timestamp는 인자/호출자 주입(코드에 now() 박지 말 것)."""
def load_results(path: str) -> list[dict]: ...
```

### 3) `scripts/run_eval.py` (CLI)
```
python scripts/run_eval.py --models claude-haiku-4-5 --modes closed_book,rag \
    --domains corp_tax,vat --data data/sample-questions-v0.1.jsonl --out outputs/results
```
- `--models`(쉼표), `--modes`, `--domains`/`--task-types` 필터, `--judge`(judge 모델), `--limit N`.
- 결과 요약(모델×모드 평균점수)을 stdout에 표로.

### 4) 테스트
- `tests/test_runner.py`: **모델 호출을 가짜(stub ModelClient)로 주입**해 결정론 검증 — 같은 stub 응답 → 같은 code-score·같은 RunRecord(핀 제외 필드). run_batch가 필터·모드를 올바르게 순회.
- 실제 풀런은 `scripts/run_eval.py`로 수동(구독 소모).

## Acceptance Criteria
```bash
uv run pytest tests/test_runner.py -q
uv run pytest -q                                # 전체 그린
# (수동 풀런, 구독 소모) uv run python scripts/run_eval.py --models claude-haiku-4-5 --modes closed_book --domains corp_tax --limit 3
#   → outputs/results/*.jsonl 생성, 재실행 시 code_scores 동일
```

## 검증 절차
1. AC 실행. stub 주입 결정론 테스트로 "같은 입력→같은 code-score" 보장. 수동 풀런 1회로 JSONL·핀 확인.
2. 체크리스트: 모든 RunRecord에 버전핀(model·hash·prompt_version·scaffold) 존재 / outputs/ 가 gitignored / now()를 코드에 안 박음(주입).
3. `phases/mvp-eval-harness/index.json` step 6 업데이트. **여기까지 통과면 M2(실행기 v1) 완료.**

## 금지사항
- **결정론 테스트에서 실제 모델을 호출하지 마라.** 이유: stub 주입으로 파이프라인 결정론만 검증. 실모델은 수동.
- **타임스탬프/accessed_at을 코드 내부 now()로 생성하지 마라.** 이유: 재현성·캐시 안정(execute.py resume·회귀).
- 버전핀 필드를 누락하지 마라. 이유: 비교가능성이 벤치마크의 존재 이유.
- outputs/를 git에 추적되게 하지 마라(.gitignore 확인).
