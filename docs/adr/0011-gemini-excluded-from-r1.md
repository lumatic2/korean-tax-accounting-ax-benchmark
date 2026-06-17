# 0011 — Gemini 를 M4+ R1 평가셋에서 제외 (Claude × GPT 2-벤더로 확정)

## Status
Accepted (2026-06-14). **ADR 0010 의 "Claude·GPT·Gemini 3-프로바이더" 의도를 2-벤더로 축소**한다. R1 은 Claude-Sonnet-4.6 × GPT-5.5(Codex) 로 출하한다. ADR 0010 의 CLI-subprocess 경계·격리 원칙은 유지.

## Context
ADR 0010 이 채택한 구독-CLI 경로에서 **GPT(Codex CLI `codex exec`)는 깨끗이 동작**(headless·stdout·즉시종료, smoke·101문항 풀런 완주 202/202). 그러나 **Gemini 는 가용한 두 경로가 모두 배치 평가에 부적합**하다(2026-06-13~14 검증):

- **(a) Antigravity CLI (`agy`)** — Gemini 3.x(3.5 Flash·3.1 Pro) 를 가졌으나 **에이전트형 구조**(tool-permission·conversation·`--add-dir`, TTY/GUI 세션 의존)다. non-TTY subprocess(배치 러너가 쓰는 방식)에서 `agy --print` 가 **응답 없이 행(hang)** 하거나 stdin 리다이렉트 시 무출력 종료. claude-cli/codex 같은 "단발 completer + 깨끗한 stdout" 모델이 아니라 스크립트 어댑터로 못 씀. 사용자 인증 TTY 점검에서도 동일했다.
- **(b) Gemini CLI (`gemini -p`)** — headless 는 되나 **gemini-2.5 계열만**(gemini-3-pro 는 `ModelNotFoundError` — 구독 미존재), **쿼터 락**(2.5-pro run 202중 111 에러=55%), **격리 P0 미해결**(`--approval-mode plan` 이 내장 `google_web_search` 를 못 막아 closed_book 에서 웹오염 가능, ADR 0008 격리 위반 risk). 비용 대비 신뢰도 낮음.

핵심 finding(same-family judge bias)은 Claude↔GPT 비교라 Gemini 가 없어도 성립하고, "단일 Claude 패밀리" reviewer 공격은 독립 벤더 GPT(OpenAI) 하나로 해소된다.

## Decision
**Gemini 를 R1 평가셋에서 제외.** R1 = **Claude-Sonnet-4.6 × GPT-5.5(Codex) 2-벤더** 교차변별 + Claude↔GPT judge-swap robustness.

`models/gemini_cli.py` 와 `config/models.yaml` 의 gemini 엔트리는 **삭제하지 않고 잔존**(ADR 0010 의 SDK 어댑터와 동일 — 코드·registry 테스트 유지, 평가 기본 경로에서만 제외). 재편입 경로 2개: ① Gemini API 키 + SDK 어댑터(`google_client.py`), ② Antigravity headless 개선 시.

수집된 Gemini 데이터(2.5-flash 182/202)는 격리 미검증·구버전이라 finding 에서 **provisional/제외**로 표기하고 정식 점수로 쓰지 않는다.

## Consequences
- ✅ R1 즉시 종료 — 독립 2 벤더(Anthropic·OpenAI)로 "단일 패밀리" 공격 해소. judge-bias finding 무손상.
- ⚠ ADR 0010의 "≥3 프로바이더" 목표 → 2-벤더로 축소. 3번째 벤더는 reviewer 강력 요구 시 Gemini **API 키 경로**(SDK 어댑터 잔존)로 후속.
- ⚠ Antigravity 의 Gemini 3.x 를 못 쓴 채 닫음 — 최신 Gemini 변별은 미측정. CLI 가 headless 를 지원하게 되면 재검토.
- gemini_cli.py 유지비 ≈ 0(미사용 어댑터, 테스트만 통과).
