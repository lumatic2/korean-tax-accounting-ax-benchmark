# Step 8: multi-provider

> ⚠ 어댑터 코드 작성은 키 없이 가능하나, **검증(각 프로바이더 1회 호출)은 API 키가 필요**하다. 키가 없으면 코드만 작성하고 **blocked로 보고**하라.

## 읽어야 할 파일
- `docs/adr/0002-claude-cli-first.md` — `ModelClient` 프로토콜 경계. M3에서 어댑터 추가로 확장.
- `src/ktaxbench/models/base.py`(프로토콜)·`claude_cli.py`(참조 구현)·`registry.py` (step2).
- `config/models.yaml` — 모델 핀.

## 작업
M3 멀티프로바이더 비교를 위해 OpenAI·Google 어댑터를 **같은 `ModelClient` 프로토콜**로 추가한다.

### 1) 의존성
`pyproject.toml`의 `[project.optional-dependencies] providers`(이미 선언됨: anthropic·openai·google-genai) → `uv sync --extra providers`.

### 2) `src/ktaxbench/models/openai.py`, `src/ktaxbench/models/google.py`
```python
class OpenAIClient:   # implements ModelClient — OPENAI_API_KEY 사용
    def __init__(self, name: str, model_id: str, temperature: float = 0.0): ...
    def complete(self, system: str, prompt: str) -> Response: ...

class GoogleClient:   # implements ModelClient — GEMINI_API_KEY/GOOGLE_API_KEY 사용
    ...
```
- SDK 사용(openai, google-genai). `.env`에서 키 로드(python-dotenv). 키 없으면 생성 시 명확한 예외 또는 `available()=False`.
- `base.Response`로 정규화(text·model·latency·raw_meta).

### 3) `config/models.yaml` 확장 + `registry.py` 분기
```yaml
  gpt-5.4:       { provider: openai, model_id: gpt-5.4,            temperature: 0.0, prompt_version: v1 }
  gemini-3-pro:  { provider: google, model_id: gemini-3-pro,      temperature: 0.0, prompt_version: v1 }
```
- `registry.get_model`이 provider별로 ClaudeCLIClient/OpenAIClient/GoogleClient 분기.

### 4) 테스트
- `tests/test_registry.py`(결정론, 호출 없음): models.yaml의 각 모델이 올바른 클라이언트 클래스로 매핑되는지(키 없이 클래스 타입만 확인 — lazy init).

## Acceptance Criteria
```bash
uv sync --extra providers
uv run pytest tests/test_registry.py -q
# (키 있을 때만) uv run python scripts/smoke_model.py --model gpt-5.4
# (키 있을 때만) uv run python scripts/smoke_model.py --model gemini-3-pro
```

## 검증 절차
1. `uv sync --extra providers` + `test_registry.py` 통과(여기까진 키 불필요).
2. 환경에 `OPENAI_API_KEY`·`GEMINI_API_KEY`가 있으면 smoke 1회씩 → completed.
3. 키가 **없으면** `phases/mvp-eval-harness/index.json` step 8을 `"status": "blocked"`, `"blocked_reason": "OpenAI·Gemini 어댑터 코드·registry 분기·test_registry 통과 완료. 실호출 검증은 OPENAI_API_KEY/GEMINI_API_KEY 필요 — 사용자 키 설정 후 재개."` 로 기록하고 중단.

## 금지사항
- **키를 코드·로그·커밋에 하드코딩/노출하지 마라.** 이유: 보안. `.env`(gitignored)에서만 로드.
- **claude_cli 어댑터(step2)를 변경하지 마라.** 이유: 회귀 위험. 새 파일로만 추가.
- 키 없는 환경에서 실호출 테스트를 CI/pytest 필수 경로에 넣지 마라. 이유: 키 의존·비결정.
