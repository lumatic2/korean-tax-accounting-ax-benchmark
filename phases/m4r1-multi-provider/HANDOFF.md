# HANDOFF — Codex CLI / Gemini CLI 병렬·헤드리스 능력 검증

> **목적**: K-TaxBench M4+ R1 은 GPT·Gemini 를 평가 후보로 추가한다(ADR 0010). 어댑터는 API 키가 아니라 **CLI subprocess + 구독 인증**(`claude -p` 와 동형)으로 간다. 평가 러너는 `ThreadPoolExecutor(max_workers=8)` 로 한 문항=한 subprocess 를 동시 호출한다. **착수 전 확정해야 할 것: 두 CLI 가 동시 headless 호출을 안전히 견디는가, 실제 모델 ID, 격리(도구·MCP 차단) 가능 여부.**
>
> **사용법**: 아래 두 블록을 각각 해당 CLI 에 그대로 붙여넣어 답을 받는다. 답은 이 파일 하단 "수집된 답" 에 적고, step0 summary 로 올려 step1 어댑터 설계(`max_workers` 기본·격리 플래그·모델 ID)에 반영한다.

---

## 확인된 사실 (로컬, 2026-06-13)
- Codex CLI `codex-cli 0.139.0` — `codex exec [PROMPT]`(비대화형), `-m <model>`, `-o <file>`(최종답만 파일로), `-s read-only|workspace-write|danger-full-access`, `-C <dir>`(작업루트), `--ignore-user-config`, `--ignore-rules`, `--skip-git-repo-check`, `--ephemeral`(세션파일 미저장), `--json`(JSONL 이벤트).
- Gemini CLI `gemini 0.42.0` — `gemini -p "<prompt>"`(헤드리스), `-m <model>`, `-o text|json|stream-json`, `--approval-mode plan`(read-only), `-s`(sandbox), `-y/--yolo`, `--allowed-mcp-server-names`, `-w/--worktree`(새 worktree), `--session-id`.
- Antigravity CLI 는 PATH 에 없음 → Gemini CLI 로 대체.

---

## 블록 A — Codex CLI 에 물을 것 (이 CLI 안에서 답)

당신은 codex-cli 0.139.0 입니다. 한 자동화 파이프라인이 당신을 `codex exec` 로 **101개 평가 프롬프트를 동시에 최대 8개 프로세스**로 헤드리스 호출하려 합니다. 각 호출은 독립적이고 read-only 여야 합니다. 다음을 사실에 근거해 답해 주세요 (모르면 "불명"):

1. **병렬 안전성**: 같은 머신·같은 계정에서 `codex exec` 프로세스 8개를 동시에 띄우면 — 세션파일/락 충돌, `$CODEX_HOME` 경합, 또는 토큰 갱신 레이스가 발생합니까? `--ephemeral` 이 이를 없앱니까? 권장 동시 실행 수는?
2. **구독 동시성 한도**: 구독(Plus/Pro 등) 인증 시 동시 요청/분당 요청에 서버측 한도가 있습니까? 한도 초과 시 어떤 신호(종료코드·stderr 문구)로 나타나며, 재시도로 회복 가능한 transient 입니까?
3. **격리**: `codex exec -s read-only -C <레포밖_빈디렉토리> --ignore-user-config --ignore-rules --skip-git-repo-check` 로 호출하면, 모델이 **웹·파일쓰기·MCP·쉘**을 일절 못 쓰고 순수 텍스트 답만 내도록 강제됩니까? read-only 에서도 실행되는 도구가 있습니까?
4. **출력**: `-o out.txt` 가 사고로그/배너 없이 **최종 답 텍스트만** 줍니까? `--json` 과 어느 쪽이 파싱에 안전합니까?
5. **모델 ID**: 구독에서 `-m` 에 넣을 수 있는 실제 모델 ID 목록은? (placeholder `gpt-5.4` 가 유효한가, 아니면 정확한 식별자는?)
6. **system 프롬프트**: `claude -p --append-system-prompt` 같은 별도 system 주입 플래그가 있습니까, 아니면 system 을 프롬프트 본문에 합쳐야 합니까?

---

## 블록 B — Gemini CLI 에 물을 것 (이 CLI 안에서 답)

당신은 gemini-cli 0.42.0 입니다. 한 자동화 파이프라인이 당신을 `gemini -p` 로 **101개 평가 프롬프트를 동시에 최대 8개 프로세스**로 헤드리스 호출하려 합니다. 각 호출은 독립·read-only 여야 합니다. 사실에 근거해 답해 주세요 (모르면 "불명"):

1. **병렬 안전성**: 같은 머신·같은 계정에서 `gemini -p` 8개를 동시 실행하면 세션/설정/캐시 충돌이 납니까? `--session-id` 를 매번 새로 주거나 `-w/--worktree` 로 분리해야 안전합니까? 권장 동시 실행 수는?
2. **구독 동시성 한도**: 구독 인증(Google AI 구독 등) 시 동시/분당 요청 한도가 있습니까? 초과 시 신호(종료코드·stderr)와 transient 여부는?
3. **격리**: `gemini -p "<prompt>" --approval-mode plan` + 레포 밖 cwd 로 호출하면 모델이 **도구·MCP·파일·웹**을 못 쓰고 순수 텍스트만 냅니까? plan 모드가 모든 도구 실행을 막습니까? MCP 를 확실히 끄려면 추가로 무엇이 필요합니까(`--allowed-mcp-server-names` 빈값 등)?
4. **출력**: `-o text` 가 최종 답만 깨끗이 줍니까? 배너/사고과정을 억제하는 플래그가 있습니까? `-o json` 의 어느 필드가 최종 답입니까?
5. **모델 ID**: 구독에서 `-m` 에 넣을 실제 모델 ID 는? (placeholder `gemini-3-pro` 가 유효한가, 정확한 식별자는?)
6. **system 프롬프트**: system instruction 을 별도로 주입하는 플래그가 있습니까, 아니면 프롬프트 본문에 합쳐야 합니까?

---

## 수집된 답 (여기에 기록 → step0 summary 로 승격)

### Codex
- 병렬 안전성 / 권장 동시성: `--ephemeral` 플래그를 사용하면 세션 파일을 디스크에 저장하지 않으므로 병렬 충돌을 완전히 방지할 수 있습니다. 권장 동시성은 8 프로세스 정도는 무난히 지원됩니다.
- 구독 동시성 한도·transient 신호: 분당 요청 한도(Rate limit) 초과 시 stdout/stderr에 `Rate limited`나 `temporarily limiting` 등의 메시지가 포함되며, 지수 백오프 재시도로 극복 가능합니다.
- 격리(도구·MCP 차단) 확인: `-s read-only --ignore-user-config --ignore-rules --skip-git-repo-check -C <sandbox>` 플래그 조합을 통해 샌드박스 폴더에서 실행하여 도구 실행 및 MCP 접근을 완전히 격리 차단합니다.
- 출력 플래그: `-o <file>` 옵션으로 사고 로그/배너가 배제된 최종 답변만 텍스트 파일로 출력할 수 있어 안전합니다.
- 실제 모델 ID: `gpt-5.5`가 유효하고 로컬 기본값으로 잡혀 있습니다.
- system 주입 방식: 별도 플래그가 없으므로 프롬프트 본문에 합쳐서 입력해야 합니다 (`{system}\n\n{prompt}`).

### Gemini
- 병렬 안전성 / 권장 동시성: 동일 머신/계정에서 `gemini -p` 8개를 동시 실행할 경우, 세션 파일(프로젝트별 `~/.gemini/tmp/<project_hash>/chats/` 저장) 업데이트 경합으로 충돌이 발생할 수 있습니다. `--worktree` 또는 `-w` 옵션으로 격리된 작업 디렉토리를 생성하여 실행하는 것이 안전합니다.
- 구독 동시성 한도·transient 신호: 구독 유형에 따라 일일/분당 제한이 엄격하며, 초과 시 보통 종료 코드 1(일반 실패/속도 제한) 또는 53(턴 한도 초과)을 반환하고 오류 메시지가 stderr에 출력됩니다. 속도 제한은 transient로 간주되어 백오프 재시도가 가능합니다.
- 격리(도구·MCP 차단) 확인: 레포지토리 외부 실행만으로는 도구가 차단되지 않습니다. `--approval-mode plan`을 설정하더라도 `read_file`, `google_web_search` 등 읽기 전용 도구는 차단되지 않으므로, 도구를 확실히 비활성화하기 위해 `--allowed-mcp-server-names ""` (빈 리스트) 설정 및 프롬프트 내 도구 미사용 지침 주입이 병행되어야 합니다.
- 출력 플래그: `-o text`는 최종 자연어 답변만 깨끗하게 출력하므로 텍스트 파싱에 적합합니다. (단, `--debug` 플래그는 해제해야 함). 구조화된 정보가 필요하다면 `-o json`을 사용하여 `response` 필드를 읽는 것이 안전합니다.
- 실제 모델 ID: `auto`, `pro`, `flash` 등의 단축 칭호 외에, 정확한 모델 ID 식별자로 `gemini-3-pro`, `gemini-2.5-pro` 등이 사용 가능하며, `gemini-3-pro`가 최신 모델 지정을 위한 유효한 식별자입니다.
- system 주입 방식: 별도의 시스템 instruction 주입용 단일 플래그(예: `-s` 등)는 없으며, 어댑터 수준에서 시스템 지침을 프롬프트 본문에 합쳐서 전달해야 합니다.

### 결론 → step1 반영값
- `max_workers` 기본 (미확인이면 1): 기본값은 1로 설정하여 안전하게 순차 실행하도록 하며, `--worktree`나 독립 세션 디렉토리 분리가 보장될 경우에 한해 최대 4~8개로 스케일업을 허용합니다.
- codex 격리 플래그 최종: `--ephemeral --skip-git-repo-check -s read-only --ignore-user-config --ignore-rules` (단, 텍스트 반환 강제를 위해 프롬프트 내 지침 합산 필수)
- gemini 격리 플래그 최종: `--approval-mode plan --allowed-mcp-server-names ""`
- config/models.yaml 모델 ID: Codex는 `gpt-5.4`(또는 mini/spark), Gemini는 `gemini-3-pro`를 기본 평가용 모델 ID로 매핑합니다.
