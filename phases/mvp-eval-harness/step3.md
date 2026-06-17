# Step 3: prompts-and-rag

## 읽어야 할 파일

- `docs/ARCHITECTURE.md` — 데이터 흐름(mode별 프롬프트 + RAG 근거 → 모델).
- `docs/benchmark-schema.md` — `benchmark_mode` enum(closed_book/rag/agent), `question` 객체(title·prompt·facts·choices·required_output).
- `src/ktaxbench/loader.py`, `src/ktaxbench/models/base.py` (step2 산출물).
- `docs/rubric-v0.1.md` — required_output을 프롬프트가 어떻게 유도해야 채점 가능한지(결론→근거→계산→주의 구조).
- **vendor 원본**(RAG):
  - `C:\Users\yusun\projects\tax-agent\src\tax_agent\agent\law_client.py` — `search_law`/`get_law_article`/`search_tax_articles`/`load_tax_corpus`, DRF `lawService.do`/`lawSearch.do` 호출, `LAW_API_OC` 환경변수(기본 '8307').
  - `C:\Users\yusun\projects\tax-agent\.env` 의 `LAW_API_OC` 값(있으면 참고. 이 레포 `.env`로 복사 가능하나 키 출력 금지).

## 작업

### 1) `src/ktaxbench/prompts.py`
```python
def build_prompt(question: dict, mode: str, *, context: str | None = None) -> tuple[str, str]:
    """(system, user) 반환. mode in {closed_book, rag, agent}."""
```
- 공통: 한국 회계·세무 전문가 system. `question.facts`·`required_output`을 명시적 섹션으로. **기준일(`time_basis`) 반드시 프롬프트에 포함**(적시성 — 모델이 시점 인지하도록).
- `closed_book`: 외부 자료 없이 답하라. 근거 조문은 기억 기반(환각 위험을 측정하는 모드).
- `rag`: `context`(아래 retriever 산출 근거 블록)를 프롬프트에 주입하고 "제공된 근거 내에서 인용하라".
- `agent`: 도구 사용 전제(이 단계는 **골격만** — system에 "단계적으로 도구를 사용해 근거를 찾고 계산하라" 지시 + required_output. 실제 trajectory 채점은 step5~6/M3에서). 과설계 금지.
- multiple_choice면 choices를 번호와 함께 제시하고 "정답 번호"를 요구.

### 2) `src/ktaxbench/rag/retriever.py` (vendor)
```python
def retrieve_context(question: dict, *, limit: int = 5) -> dict:
    """question.sources의 locator/키워드로 법제처 DRF 조회 → 근거 컨텍스트.
    반환: {"context_text": str, "retrieved": [{law, article, excerpt, url}], "accessed_at": "YYYY-MM-DD"}"""
```
- vendor: `law_client.py`의 DRF 호출·코퍼스 캐시 패턴을 가져온다(httpx, OC 키). 출처 주석 필수.
- 질의 구성: `question.sources[].locator`(예 "제25조")와 `question.tags`/title 키워드. `search_tax_articles` 류로 조문 본문 excerpt를 모은다.
- **재현성 핀**: `accessed_at`(오늘 날짜는 인자로 주입받거나 환경에서 — 단 `Date.now()` 류로 코드에 박지 말고, 호출자가 넘기게). 코퍼스 캐시 파일은 `outputs/`(gitignored) 또는 `data/private/`에.
- 키 없거나 네트워크 실패 시: 빈 context + `retrieved=[]` + 경고(예외로 죽지 말 것).

### 3) `tests/test_prompts.py` (결정론, 네트워크 없음)
- 각 mode에 대해 `build_prompt`가 (system, user) 튜플을 만들고 user에 facts·required_output·time_basis가 포함되는지.
- rag 모드에 context를 주면 user에 그 텍스트가 들어가는지.
- multiple_choice 문항이면 choices가 프롬프트에 번호로 들어가는지.
- retriever는 네트워크 의존이라 **단위테스트에서 호출 금지** — 대신 `scripts/smoke_rag.py`(수동)로 vat 문항 1개 조회.

## Acceptance Criteria
```bash
uv run pytest tests/test_prompts.py -q
uv run python -c "from ktaxbench.loader import load_questions; from ktaxbench.prompts import build_prompt; q=load_questions('data/sample-questions-v0.1.jsonl',domain='vat')[0]; s,u=build_prompt(q,'closed_book'); print('OK' if q['time_basis'] in u else 'MISSING time_basis')"
# (수동 smoke, 네트워크) uv run python scripts/smoke_rag.py   # vat 문항 → 조문 excerpt 출력
```

## 검증 절차
1. AC 실행(retriever smoke는 수동 1회 — 법제처 DRF 라이브).
2. 체크리스트: vendor 출처 주석 / 기준일이 모든 모드 프롬프트에 포함 / agent 모드 과설계 안 함 / 네트워크 실패 graceful.
3. `phases/mvp-eval-harness/index.json` step 3 업데이트.

## 금지사항
- **retriever를 결정론 pytest에 넣지 마라.** 이유: 라이브 DRF 의존 → 비결정·느림·네트워크 깨짐. smoke로 분리.
- **`Date.now()`/`datetime.now()`로 accessed_at을 코드 내부에 박지 마라.** 이유: 재현성 — 호출자가 기준일을 주입해야 같은 입력→같은 결과.
- 법제처 API 키를 로그·커밋에 노출하지 마라.
- agent 모드를 여기서 완성하려 하지 마라(골격만). 이유: trajectory 채점은 후속 step.
