# 0001 — tax-agent 자산은 import가 아니라 vendor(복사)한다

## Status
Accepted (2026-06-02)

## Context
평가 실행기는 형제 레포 `~/projects/tax-agent`의 검증된 자산을 재사용한다:
LLM 어댑터(`agent/llm/adapter.py`의 `ClaudeCLIChat`), 법제처 DRF 클라이언트(`agent/law_client.py`),
채점 패턴(`evals/`, `exam/mcq_eval.py`).

재사용 방식은 두 갈래다.
- **(A) import**: `tax-agent`를 의존성으로 걸어 직접 호출.
- **(B) vendor**: 필요한 함수만 trimmed copy로 이 레포 안에 들여옴.

제약: K-TaxBench는 **M4에서 공개 레포로 릴리스**된다(포트폴리오 트랙). `tax-agent`는
비공개 개인 프로젝트이고 langgraph·streamlit·claude-agent-sdk 등 무거운 의존성을 끌고 온다.
공개 레포가 비공개 레포에 import 의존하면 릴리스가 불가능하고, 무거운 의존성은 실행기 설치를 무겁게 한다.

## Decision
**(B) vendor.** `tax-agent`에서 가져오는 코드는 `src/ktaxbench/` 안에 출처 주석과 함께 복사한다.
복사 대상은 최소 표면적만(ClaudeCLIChat, DRF 검색 함수, 채점 헬퍼). import 의존성으로 걸지 않는다.

## Consequences
- ✅ 공개 레포 독립성 확보(M4 릴리스 가능). 설치 의존성 최소(httpx·dotenv·pyyaml).
- ✅ K-TaxBench 도메인에 맞게 자유롭게 수정 가능(원본 결합도 0).
- ⚠ 원본 버그 수정이 자동 전파되지 않음 — 복사 시점·출처를 주석에 남겨 수동 동기화 추적.
- ⚠ 코드 중복 — 단, 표면적이 작고(수백 줄) 도메인이 갈라져 실질 부담 낮음.
