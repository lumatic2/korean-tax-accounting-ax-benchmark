"""모드별 프롬프트 빌더. closed_book / rag / agent.

설계: 답변이 루브릭 차원(결론·근거·계산·실무·리스크)으로 채점 가능하도록 구조를 유도.
기준일(time_basis)은 모든 모드에서 프롬프트에 포함한다(적시성 — 모델이 시점을 인지).
"""
from __future__ import annotations

_BASE_SYSTEM = (
    "당신은 한국 회계·세무 실무 전문가다. 한국 세법·회계기준에 근거해 정확히 답한다. "
    "결론 → 근거(법령 조문/기준서) → 계산/판단 과정 → 실무상 주의점 순서로 구조화해 답하라. "
    "근거가 불확실하면 단정하지 말고 추가 확인이 필요함을 밝혀라. "
    "존재하지 않는 조문·판례를 지어내지 마라."
)

_MODE_SYSTEM = {
    "closed_book": " 외부 자료 없이 당신의 지식만으로 답하라.",
    "rag": " 아래 [제공 근거] 안의 조문을 우선 인용하라. 제공 근거에 없으면 그 사실을 밝혀라.",
    "agent": " 단계적으로 필요한 근거를 도구로 찾고 계산한 뒤 최종 답을 제시하라. 각 단계의 근거를 남겨라.",
    "agent_forced": " 최종 답을 내기 전에 반드시 법령조문/기준서문단 도구로 근거를 직접 확인하라. 기억에 의존하거나 추측하지 말고, 인용하는 모든 조문·문단은 도구로 조회한 것이어야 한다.",
}

_VALID_MODES = set(_MODE_SYSTEM)


def build_prompt(question: dict, mode: str, *, context: str | None = None) -> tuple[str, str]:
    """(system, user) 반환. mode in {closed_book, rag, agent}."""
    if mode not in _VALID_MODES:
        raise ValueError(f"unknown mode: {mode} (valid: {sorted(_VALID_MODES)})")

    system = _BASE_SYSTEM + _MODE_SYSTEM[mode]

    q = question.get("question", {})
    parts: list[str] = []
    parts.append(f"[기준일] {question.get('time_basis', '미상')}")
    if q.get("title"):
        parts.append(f"[제목] {q['title']}")
    parts.append(f"[문제] {q.get('prompt', '')}")

    facts = q.get("facts") or []
    if facts:
        parts.append("[사실관계]\n" + "\n".join(f"- {f}" for f in facts))

    choices = q.get("choices") or []
    if choices:
        lines = []
        for i, c in enumerate(choices, 1):
            if isinstance(c, dict):
                lines.append(f"{c.get('label', i)}. {c.get('text', '')}")
            else:
                lines.append(f"{i}. {c}")
        parts.append("[선택지]\n" + "\n".join(lines))
        parts.append("정답 번호(또는 라벨)를 명시하라.")

    req = q.get("required_output") or []
    if req:
        parts.append("[답변에 반드시 포함]\n" + "\n".join(f"- {r}" for r in req))

    if mode == "rag" and context:
        parts.insert(0, "[제공 근거]\n" + context + "\n")

    if mode in ("agent", "agent_forced"):
        from .agent.tools import TOOL_MENU
        parts.append(
            "[사용 가능한 도구]\n" + TOOL_MENU + "\n\n"
            "[작업 방식] 근거가 필요하면 한 줄로 `[도구] 이름: 인자` 형식으로 호출하라(한 번에 하나). "
            "도구 결과는 [관측]으로 주어진다. 필요한 만큼 반복한 뒤, 더 이상 도구가 필요 없으면 "
            "`[최종]`으로 시작하는 최종 답(누락자료 요청·리스크 분류 포함)을 작성하라. "
            "추측 대신 도구로 확인하고, 자료가 부족하면 어떤 자료가 더 필요한지 명시하라."
        )

    return system, "\n\n".join(parts)
