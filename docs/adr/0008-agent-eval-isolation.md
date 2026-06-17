# 0008 — 후보·judge `claude -p` 를 레포 밖 sandbox cwd + `--strict-mcp-config` 로 환경 격리한다

## Status
Accepted (2026-06-10)

## Context
[ADR 0006] agent_forced 라이브 후속 스모크([findings/agent-tool-forcing.md](../findings/agent-tool-forcing.md) "후속 스모크")에서 **하네스 오염**이 드러났다. 후보 모델을 벤치마크 레포 cwd 에서 `claude -p` 로 돌리면 후보가 환경을 상속한다:

1. **CLAUDE.md 누설** — 레포 `CLAUDE.md`(judge 규약·게이트·환각·루브릭 어휘)를 읽고 자신을 *문항 검증자*로 프레이밍("검증 결과: 모델 답안 정확 … agent_forced 게이트 통과"). 블라인드 에이전트가 아니다.
2. **MCP 우회** — 전역 `law-mcp`(`~/.claude.json`)로 조회 → eval 의 ReAct `[도구]` 프로토콜을 안 써서 `agent_steps` 미포착 → `forced_tool_unmet` **오탐**(실제론 MCP 로 조회·검증함).

진단(2026-06-10): `prompts.py` 의 agent 시스템 프롬프트는 깨끗하다(순수 세무 전문가 + `[도구]` 지시) — 오염은 100% 환경발. 행동 probe 로 확인: 레포 cwd 무격리는 `law-mcp(6)`+`CLAUDE로드`, sandbox+격리는 `도구없음`+`CLAUDE없음`.

선택지:
- (A) `--bare` — CLAUDE.md 자동탐색·hooks·MCP 전부 끔. 단 Anthropic 인증을 ANTHROPIC_API_KEY/apiKeyHelper 로 한정(OAuth·keychain 무시) → **구독 인증이 깨짐**(ADR 0002 전제 위배).
- (B) `--system-prompt` 전체교체 — Claude Code 프레이밍 제거. 단 전 모드(closed_book/rag) 동작·도구사용 포맷까지 바꾸는 큰 변경.
- (C) **cwd 격리 + `--strict-mcp-config`** — subprocess cwd 를 레포·home 밖 빈 디렉토리로(→ CLAUDE.md 자동탐색 미발견) + `--strict-mcp-config`(→ 모든 MCP 차단). 최소 변경·구독 인증 유지.

## Decision
**(C).** `ClaudeCLIClient(isolated=True)` 기본 격리:
- **cwd** = 레포·home 트리 밖 빈 sandbox(`C:/ktaxbench-sandbox`, env `KTAXBENCH_SANDBOX` override). home 밖이라 전역 `C:\Users\yusun\CLAUDE.md` 발견까지 차단.
- **`--strict-mcp-config`** (no `--mcp-config`) → law-mcp 등 0개. 구독 인증(OAuth) 유지.
- **`--append-system-prompt` 유지** — eval 시스템 프롬프트는 그대로 주입(full-replace 안 함, surgical).
- **전 모드 + judge 일괄** — closed_book 후보가 레포 CLAUDE.md 를 읽는 것도 오염. registry 가 `ClaudeCLIClient` 를 기본 생성하므로 별도 배선 없이 후보·judge 전부 적용.

## Consequences
- ✅ 후보가 자기 벤치마크의 judge 규약·루브릭을 누설받지 않는다(블라인드 에이전트 회복).
- ✅ 경쟁 MCP(law-mcp)가 사라져 후보는 eval ReAct `[도구]` 로만 조회 → `agent_steps` 포착, `forced_tool_unmet` 오탐 해소.
- ✅ 구독 인증 유지(`--bare` 회피). 전 모드 hermetic = 벤치마크 비교가능성↑.
- ⚠ **Claude Code 내장도구(Read/Bash 등) 잔존** — sandbox 가 비어 세무 답에 무용하므로 ReAct 로 폴백하지만, 완전 차단은 아님. A4 라이브 스모크로 폴백 확인. 누설 관측 시 `--disallowedTools` 추가(후속).
- ⚠ sandbox 경로가 Windows 고정 기본값(`C:/ktaxbench-sandbox`). 타 OS 는 env override 필요.
- ⚠ 격리 전 산출된 라이브 run(gitignored outputs)은 비교 기준이 달라짐 — 격리 후 재실행본으로 대체.
