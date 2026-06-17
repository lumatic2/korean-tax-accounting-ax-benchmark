# 0002 — M2 모델 호출은 Claude CLI 단독으로 시작한다

## Status
Accepted (2026-06-02). **부분 supersede (2026-06-02 범위 결정)**: 타 벤더(GPT·Gemini) 교차변별을 계획에서 제외하고 Claude 모델군 내부 변별로 1차 목표를 한정함에 따라, 아래 "멀티프로바이더는 M3 step8에서 추가" 전제는 더 이상 유효하지 않다(ROADMAP M3 참조). `models/openai.py`·`models/google.py` 등 멀티프로바이더 코드는 미사용으로 잔존. `ModelClient` 프로토콜 경계 결정 자체는 유지.

## Context
실행기는 후보 모델을 호출해야 한다. 선택지:
- **(A) 멀티프로바이더 SDK**: Anthropic+OpenAI+Google SDK를 처음부터. API 키 필요.
- **(B) Claude CLI subprocess**: `tax-agent`의 `ClaudeCLIChat` 방식. 구독으로 동작, 키 불필요. Claude 계열만.
- **(C) 하이브리드**: Claude=CLI, 타사=SDK.

M2의 성공기준은 *한 모델*을 3모드로 돌려 채점 파이프라인이 재현 가능하게 도는 것이다.
모델 다양성(GPT/Gemini 비교)은 M3의 성공기준이다. M2 단계에서 멀티프로바이더를 깔면
키 발급·비용·어댑터 추상화를 조기에 떠안아 파이프라인 검증이 느려진다.

## Decision
**M2 = (B) Claude CLI 단독.** `models/claude_cli.py`가 `ModelClient` 프로토콜을 구현하고,
`config/models.yaml`에 claude-opus/sonnet/haiku를 핀한다. 멀티프로바이더(GPT·Gemini)는
**M3(Step 8)에서 `models/openai.py`·`models/google.py`를 같은 프로토콜로 추가**한다.

`ModelClient` 프로토콜(`complete(system, prompt) -> Response`)을 처음부터 두어,
M3 확장이 어댑터 추가만으로 끝나게 한다.

## Consequences
- ✅ 키·비용 0으로 M2 파이프라인 즉시 검증. claude-opus/sonnet/haiku로 초기 변별도 일부 확인 가능.
- ✅ 프로토콜 경계가 있어 M3 확장이 국소적(어댑터 파일 추가).
- ⚠ M2 점수는 Claude 계열 내부 비교라 진짜 변별(타사 대비)은 M3까지 미확정.
- ⚠ CLI subprocess는 SDK보다 느리고 토큰 사용량·로그 제어가 거침 — 대량 실행 시 M3에서 SDK 경로 우선 고려.
