# 0005 — agent 모드는 러너가 제어하는 ReAct 텍스트 루프로 구현한다

## Status
Accepted (2026-06-09)

## Context
positioning.md 5대 역량 중 **⑤도구 사용성**(AX 실무 수행: 도구 오케스트레이션·누락자료 요청·다단계 grounding)은 이 벤치마크의 이름값인데, 실행 경로가 없었다. `runner.py`는 `closed_book`/`rag`만 분기했고, `mode=="agent"`는 분기가 없어 단발 `complete()`로 떨어졌다 — 즉 "agent 모드 = 시스템 프롬프트만 다른 closed_book". `rubric.py`의 `agent_workflow.tool_process`(20점)는 실행되는 도구가 없어 **구조적으로 획득 불가**였다. mixed-0001(`benchmark_mode:["agent"]`)이 막혀 있었다.

모델 클라이언트는 `claude -p` subprocess(`claude_cli.py`)이고 `complete()`는 텍스트 in→out 단발이다. agent 루프를 어디에 둘지가 갈림길:

- **(A) 러너가 제어하는 ReAct 텍스트 루프** — 러너가 도구 메뉴를 프롬프트에 주고, 모델이 `[도구] 이름: 인자` 텍스트로 호출 → 러너가 파싱·실행(`retriever.py` DRF·kifrs DB 재사용)·관측 주입 → `[최종]` 또는 스텝 상한까지 반복.
- **(B) `claude -p` 네이티브 도구** — `--allowedTools`로 CLI 자체 도구 루프를 돌리고 transcript 캡처.

## Decision
**(A) 러너 제어 ReAct 텍스트 루프.** 핵심 근거는 **재현성**이다 — 이 레포는 모든 RunRecord에 버전핀(model·question_hash·prompt_version·scaffold)을 박아 재현·비교가능성을 명시 가치로 둔다(`runner.py` 도입부). (B)는 그 핵심을 깬다:
- CLI·도구·MCP 버전이 버전핀 밖 → 같은 기준일 재실행이 동일을 보장 못 함.
- headless에서 MCP 부재 가능, stub 주입 불가 → **재현 테스트 작성 불가**(Judge 규약 product 갈래 위반).
- 후보 모델에게 Bash 부여 = 보안 냄새 + 하네스-Claude와 후보 혼동.

(A)는 도구 실행기를 주입형으로 두어 테스트는 stub(네트워크 0)으로, 실전은 DRF/kifrs로 돈다. 도구 호출을 `agent_steps`로 객관 기록 → 오케스트레이션을 명시 측정. 텍스트 프로토콜이 실제 tool-use API가 아니라 인위적이라는 단점은 감수한다(재현성·테스트성 우선).

도구 3종(MVP): `법령조문(법령, 조문)`(DRF), `기준서문단(기준서, 문단)`(kifrs DB), `계산(식)`. 스텝 상한으로 비용 경계. 타 벤더 제외(Claude 모델군 한정, [0002] 부분 supersede 맥락)로 provider 무관성은 필수 아니나, 텍스트 프로토콜은 부수적으로 그것도 만족한다.

## Consequences
- ✅ ⑤도구 셀(+11) 실행 가능 — mixed-0001 및 agent형 문항 배치 해제.
- ✅ `tool_process` 획득 가능 — 실제 도구 실행 + `agent_steps` 기록.
- ✅ 결정론·버전핀·stub 재현 테스트 유지(핵심 평가경로 변경의 검증 가능).
- ✅ DRF/kifrs 경로 재사용(중복 없음).
- ⚠ 텍스트 프로토콜 준수를 모델에 의존 — 미준수 시 도구 0회(그 자체가 ⑤ 낮음 신호로 기록). 향후 네이티브 tool-use API 어댑터로 교체 가능(루프 추상은 유지).
- ⚠ MVP는 턴당 도구 1회·스텝 상한. 멀티툴 병렬·동적 상한은 후속.
