# Step 2: loader-and-models

## 읽어야 할 파일

- `docs/ARCHITECTURE.md` — 디렉토리 구조·단방향 파이프라인·vendor 원칙.
- `docs/adr/0002-claude-cli-first.md` — M2는 Claude CLI 단독, `ModelClient` 프로토콜 경계.
- `src/ktaxbench/schema.py` (step1 산출물) — `validate_question`/`is_valid` 재사용.
- `docs/benchmark-schema.md` — 문항 dict 구조.
- **vendor 원본**(읽고 trimmed copy — ADR 0001):
  - `C:\Users\yusun\projects\tax-agent\src\tax_agent\agent\llm\adapter.py` — `ClaudeCLIChat`(subprocess로 `claude` CLI 호출). 이 클래스의 호출 패턴(인자 구성·timeout·출력 파싱)을 가져온다.
  - `C:\Users\yusun\projects\tax-agent\src\tax_agent\agent\llm\registry.py`·`registry.yaml` — `ModelSpec`·YAML 로더 패턴.
  - `C:\Users\yusun\projects\tax-agent\exam\mcq_eval.py` — `ask_claude_cli`의 CLI 인자·응답 텍스트 추출 참고.

## 작업

문항 로더와 모델 호출 어댑터(Claude CLI)를 만든다.

### 1) `src/ktaxbench/loader.py`
```python
def load_questions(path: str, *, domain: str | None = None, task_type: str | None = None,
                   visibility: str | None = None, status: str | None = None,
                   validate: bool = False) -> list[dict]:
    """JSONL(한 줄 1문항) 로드 후 필터. validate=True면 schema.is_valid 통과분만."""
```
- UTF-8, 빈 줄 무시. 필터는 AND. 원본 dict 그대로 반환(가공 금지 — 불변 입력 원칙).

### 2) `src/ktaxbench/models/base.py`
```python
@dataclass(frozen=True)
class Response:
    text: str
    model: str
    latency_s: float
    raw_meta: dict   # 토큰·종료사유 등(있으면)

class ModelClient(Protocol):
    name: str
    def complete(self, system: str, prompt: str) -> Response: ...
```

### 3) `src/ktaxbench/models/claude_cli.py` (vendor)
`ClaudeCLIChat`를 참고해 `ClaudeCLIClient`를 만든다:
```python
class ClaudeCLIClient:  # implements ModelClient
    def __init__(self, name: str, model_id: str, timeout: int = 300): ...
    def complete(self, system: str, prompt: str) -> Response: ...
```
- `subprocess.run(["claude", "-p", "--model", model_id, ...], ...)`로 호출. system은 `--append-system-prompt` 또는 프롬프트 앞에 붙이는 방식(원본 패턴 따름). stdin/인자로 prompt 전달.
- **출처 주석 필수**: 파일 상단에 `# vendored from tax-agent/src/tax_agent/agent/llm/adapter.py (2026-06-02)`.
- 타임아웃·CalledProcessError를 잡아 `raw_meta`에 에러 기록(예외로 죽지 말 것 — 한 문항 실패가 전체 런을 죽이면 안 됨).

### 4) `src/ktaxbench/models/registry.py`
```python
def get_model(name: str) -> ModelClient: ...   # config/models.yaml 조회 → ClaudeCLIClient 인스턴스
def list_models() -> list[str]: ...
```

### 5) `config/models.yaml`
```yaml
models:
  claude-opus-4-8:   { provider: claude_cli, model_id: claude-opus-4-8,   temperature: 0.0, prompt_version: v1 }
  claude-sonnet-4-6: { provider: claude_cli, model_id: claude-sonnet-4-6, temperature: 0.0, prompt_version: v1 }
  claude-haiku-4-5:  { provider: claude_cli, model_id: claude-haiku-4-5,  temperature: 0.0, prompt_version: v1 }
```
(model_id는 실제 `claude --model` 이 받는 값. 확실치 않으면 `claude --help`로 확인하되, 위 3개를 기본 핀으로 둔다.)

### 6) `src/ktaxbench/models/__init__.py`, `tests/test_loader.py`
- `test_loader.py`(결정론, 모델 호출 없음): 19문항 로드 / `domain="corp_tax"` → 3 / `task_type="calculation"` 필터 / 없는 값 → 0.
- 모델 호출 smoke는 `scripts/smoke_model.py`(별도, CI 아님): `get_model("claude-haiku-4-5").complete("","2+2=?")` → 텍스트 출력.

## Acceptance Criteria

```bash
uv run pytest tests/test_loader.py -q          # 통과
uv run python -c "from ktaxbench.loader import load_questions; print(len(load_questions('data/sample-questions-v0.1.jsonl')))"   # 19
uv run python -c "from ktaxbench.models.registry import list_models; print(list_models())"   # 3개 모델
# (선택, 수동 smoke — 구독 소모) uv run python scripts/smoke_model.py
```

## 검증 절차
1. AC 커맨드 실행. 모델 호출 smoke는 1회만 수동 확인(필수 아님 — 느리고 비결정).
2. 체크리스트: vendor 출처 주석 있는가 / ADR 0001(신규 무거운 의존성 금지) 지켰는가 / `ModelClient` 프로토콜을 claude_cli가 만족하는가.
3. `phases/mvp-eval-harness/index.json` step 2 업데이트(completed+summary / error / blocked).

## 금지사항
- **Anthropic SDK·API 키 사용 금지.** 이유: M2는 CLI 단독(ADR 0002). SDK는 step8(M3).
- **모델 호출을 pytest 필수 경로에 넣지 마라.** 이유: 느리고 비결정·구독 소모 → CI/결정론 테스트를 오염시킴. smoke는 분리.
- 한 문항 모델 호출 실패가 예외로 전파돼 전체 런을 죽이게 하지 마라. 이유: 배치 평가 견고성.
- 기존 테스트(test_schema.py)를 깨뜨리지 마라.
