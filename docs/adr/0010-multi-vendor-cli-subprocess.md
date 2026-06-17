# 0010 — 멀티벤더 교차변별은 CLI subprocess(구독 인증)로 재활성한다

## Status
Accepted (2026-06-13). **ADR 0002 의 범위축소(2026-06-02 부분 supersede)를 재개방한다** — M4+ R1 에서 GPT·Gemini 교차변별을 다시 계획에 넣되, *어댑터 구현 방식*은 SDK/API 키가 아니라 **CLI subprocess + 구독 인증**으로 정한다. `ModelClient` 프로토콜 경계(ADR 0002) 및 격리 원칙(ADR 0008)은 그대로 상속.

## Context
M4+ R1 성공기준은 "≥3 프로바이더(Claude·GPT·Gemini) 교차 변별 + judge-swap robustness 1건"이다 — reviewer 의 "단일 Claude 패밀리" 공격(#2)을 해소하려면 타 벤더 점수가 필요하다. 어댑터 경로는 두 가지:

- **(A) SDK + API 키** — 기존 `models/openai_client.py`·`models/google_client.py`(M3 step8 작성, 미사용). metered billing + 키 관리.
- **(B) CLI subprocess + 구독 인증** — `models/claude_cli.py`(`claude -p`)와 동형. 구독 로그인으로 동작, 키 불필요·정액.

키 현황(2026-06-13 확인): `OPENAI_API_KEY` 는 401(만료/오류), `GEMINI_API_KEY`/`GOOGLE_API_KEY` 는 미설정. 그리고 ADR 0002 가 애초에 CLI-first 를 택한 이유 자체가 "키·비용 0으로 파이프라인 검증"이었다 — (A)는 그 결정을 되돌려 키 발급·종량 과금을 재도입한다. 로컬에 `codex exec`(codex-cli 0.139.0)·`gemini -p`(gemini 0.42.0) 가 이미 구독 인증된 채로 설치돼 있어 (B)가 즉시 가능하다.

## Decision
**(B) CLI subprocess.** GPT → **Codex CLI**(`codex exec -m <model> -o <file>`), Gemini → **Gemini CLI**(`gemini -p -m <model> -o text`). 각각 `claude_cli.py` 를 본뜬 `ModelClient` 어댑터(`models/codex_cli.py`·`models/gemini_cli.py`)로 감싸고, `config/models.yaml` 에 `provider: codex_cli`·`provider: gemini_cli` 로 핀한다. registry 분기 추가.

격리는 ADR 0008 패리티: 레포 밖 sandbox cwd(후보가 레포 CLAUDE.md·루브릭을 읽지 못하게) + 도구/MCP 차단 — Codex `-s read-only --ignore-user-config --ignore-rules -C <sandbox>`, Gemini `--approval-mode plan`(read-only) + cwd 밖 + MCP 미허용. eval 후보는 law-mcp 등 외부 권위를 우회 조회하면 안 된다(격리 eval 의도).

기존 SDK 어댑터(`openai_client.py`·`google_client.py`)는 **삭제하지 않고 잔존**(키 보유 시 선택 경로) — eval 기본 경로에서만 빠진다.

**미해결(→ step0 handoff 로 검증 후 확정)**: 두 CLI 가 `ThreadPoolExecutor(max_workers>1)` 하의 동시 headless 호출을 안전하게 견디는지(세션파일 충돌·구독 동시성 한도). 검증 전엔 `--workers 1` 순차로 가정.

## Consequences
- ✅ API 키 0·종량과금 0(구독 정액)으로 3-프로바이더 교차변별 — R1 의 "노력비 대비 신뢰도 최고" 취지에 부합.
- ✅ `ModelClient` 경계 덕에 확장이 국소적(어댑터 2 파일 + registry 분기 + config).
- ⚠ subprocess 는 SDK 보다 느리고 동시성 특성 불명 — 병렬 안전성은 step0 handoff 로 CLI 에 직접 확인 후 `max_workers` 확정(미확인 시 순차).
- ⚠ 사용자가 지목한 **Antigravity CLI 는 PATH 에 없음** → 동일 구독 계열의 **Gemini CLI** 로 대체. Antigravity CLI 가 별도로 필요하면 재검토.
- ⚠ SDK 어댑터 2개가 미사용으로 잔존(orphan) — 키 기반 API 경로가 필요해질 때를 위한 보존.
- ⚠ CLI 별 출력에 사고로그·배너가 섞일 수 있어 `-o`(Codex last-message)·`-o text`(Gemini)로 최종답만 추출 — 어댑터에서 파싱 견고성 필요.
