# Step 1: cli-subprocess-adapters  (run — billing 0, 단위테스트만)

> `codex exec`·`gemini -p` 를 `ModelClient` 로 감싼 어댑터 2개 + registry 분기 + config 핀. step0 HANDOFF 답(병렬 안전성·실모델 ID)을 반영해 `max_workers` 기본·격리 플래그를 확정한 뒤 착수.

## 읽어야 할 파일
- `phases/m4r1-multi-provider/HANDOFF.md` 답 메모(step0 summary) — 왜: 동시성 한도 → 어댑터 동시성 가드·`config` `max_workers`, 실제 `-m` 모델 ID, 출력 억제 플래그. **이 값들 없이 착수 금지.**
- `src/ktaxbench/models/claude_cli.py` — 왜: 본뜰 원형. `Response` 계약, rate-limit 마커·지수backoff, `_ensure_sandbox`, `isolated` 기본 True, timeout·FileNotFound 처리 그대로 차용.
- `src/ktaxbench/models/registry.py` — 왜: `get_model` 의 provider 분기에 `codex_cli`·`gemini_cli` 추가 지점.
- `src/ktaxbench/models/base.py` — 왜: `ModelClient` 프로토콜·`Response(text, model, latency_s, raw_meta)` 시그니처.
- `config/models.yaml` — 왜: 신규 provider 엔트리 핀(placeholder 모델 ID → HANDOFF 실값으로 교체).
- `tests/test_claude_cli.py` — 왜: 어댑터 단위테스트 패턴(subprocess mock). 신규 2개도 동형 테스트.
- `docs/adr/0010-multi-vendor-cli-subprocess.md` / `0008-...md` — 왜: 격리 플래그 패리티 요구사항.

## 작업
- `src/ktaxbench/models/codex_cli.py` — `CodexCLIClient(name, model_id, timeout, isolated=True)`. `complete(system, prompt)`:
  - cmd: `codex exec -m <model_id> -o <tmpfile>`; isolated 시 `-s read-only --ignore-user-config --ignore-rules --skip-git-repo-check -C <sandbox>`. system 은 prompt 앞에 합쳐 stdin/PROMPT 로(코덱스엔 append-system 없음 — system+"\n\n"+prompt). 최종답은 `-o` 파일에서 읽음.
- `src/ktaxbench/models/gemini_cli.py` — `GeminiCLIClient(...)`. cmd: `gemini -p <prompt> -m <model_id> -o text`; isolated 시 cwd=sandbox + `--approval-mode plan`. system 은 prompt 앞 합치기.
- 둘 다 claude_cli 의 rate-limit backoff·timeout·FileNotFound→`Response(text="", raw_meta={"error":...})` 계약 준수. 동시성 한도 가드(HANDOFF 답 반영).
- `registry.py`: provider `codex_cli`→CodexCLIClient, `gemini_cli`→GeminiCLIClient 분기.
- `config/models.yaml`: 기존 `gpt-5.4`(provider openai)·`gemini-3-pro`(provider google) 엔트리를 **CLI 경로로 교체 또는 신규 키 추가** — `provider: codex_cli`/`gemini_cli` + HANDOFF 실 모델 ID.
- `tests/test_codex_cli.py`·`tests/test_gemini_cli.py`: subprocess mock 으로 정상/타임아웃/비정상rc/빈출력 계약 테스트.

## Acceptance Criteria
```bash
uv run ruff check src/ tests/
uv run pytest tests/test_codex_cli.py tests/test_gemini_cli.py tests/test_registry.py
uv run pytest   # 전체 green (회귀 0)
```

## 검증 절차
1. AC 실행(lint·신규 테스트·전체 green).
2. registry 가 4개 provider(claude_cli·codex_cli·gemini_cli + 잔존 openai/google) 분기 무에러.
3. `index.json` step1 → `completed` + summary(파일·테스트수·확정 max_workers·실모델 ID).

## 금지사항
- HANDOFF 병렬 답 없이 `max_workers>1` 기본값 박기 금지. 이유: 세션파일 충돌로 답안 오염 위험(claude_cli 18-concurrency rate-limit 오염 전례).
- 라이브 CLI 호출로 "테스트" 금지(여기선 mock 만). 이유: billing·smoke 는 step2.
- 기존 claude_cli/openai/google 어댑터·테스트 변경 금지(surgical). 이유: 회귀.
