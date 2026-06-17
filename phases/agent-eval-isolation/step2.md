# Step 2: isolate-claude-cli

## 읽어야 할 파일
- src/ktaxbench/models/claude_cli.py (수정 대상)
- src/ktaxbench/models/base.py (Response)
- step1 결론: sandbox `C:/ktaxbench-sandbox`(home 밖) + `--strict-mcp-config` 가 MCP·CLAUDE.md 둘 다 제거(구독 인증 유지)

## 작업
`ClaudeCLIClient` 에 격리 추가(ADR 0008):
- 생성자 `isolated: bool = True` (기본 ON — 전 모드+judge).
- 모듈 상수 sandbox 경로 = env `KTAXBENCH_SANDBOX` 우선, 기본 `C:/ktaxbench-sandbox`. `_ensure_sandbox()` 가 mkdir(exist_ok=True) 후 경로 반환(멱등).
- `complete()`: isolated 면 cmd 에 `--strict-mcp-config` 추가 + `subprocess.run(..., cwd=<sandbox>)`. isolated=False 면 종전(cwd=None, 플래그 없음).
- `--append-system-prompt` 는 유지(eval 시스템 프롬프트 그대로). full-replace 안 함.

## Acceptance Criteria
```bash
PYTHONPATH=src python -X utf8 -c "from ktaxbench.models.claude_cli import ClaudeCLIClient, _ensure_sandbox; import os; print(_ensure_sandbox()); print('strict-mcp build ok')"
```

## 금지사항
- registry/config 에 격리 노브 추가 금지(YAGNI — 생성자 기본값으로 충분). 이유: 전 모드 일괄 ON 결정.
- 기존 closed_book/rag 동작 시그니처(complete(system, prompt)) 변경 금지.
