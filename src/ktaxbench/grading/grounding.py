"""근거매칭 (ADR 0006) — 최종 답이 인용한 근거(조문·문단)가 이번 run 에서 실제 도구로
조회된 것인지 대조한다. 기억-인용 vs 도구-근거를 결정론적으로 가른다.

토큰 정규식 휴리스틱: 법령(제N조·제N조의M), 기준서([1115-74]·"1115 문단74"). 인용 형식이
어긋나면 누락될 수 있어 forced 모드에서만 감점에 쓴다.
"""
from __future__ import annotations

import re

AUTHORITY_TOOLS = {"법령조문", "기준서문단"}

_LAW_TOK = re.compile(r"제\s*\d+\s*조(?:\s*의\s*\d+)?")
_STD_BRACKET = re.compile(r"\[(\d{3,4})-([\dA-Za-z.]+)\]")
_STD_PARA = re.compile(r"(\d{3,4})\s*문단\s*([\dA-Za-z.]+)")

# 조회 실패/오류 관측 prefix — 근거로 치지 않는다.
_FAIL_PREFIX = ("조회 실패", "법령 미발견", "조문 미추출", "문단 미발견",
                "kifrs DB 없음", "인자 형식", "알 수 없는 도구", "법령명 누락")


def _tokens(text: str) -> set[str]:
    text = text or ""
    out = {re.sub(r"\s+", "", m.group(0)) for m in _LAW_TOK.finditer(text)}
    out |= {f"{m.group(1)}-{m.group(2)}" for m in _STD_BRACKET.finditer(text)}
    out |= {f"{m.group(1)}-{m.group(2)}" for m in _STD_PARA.finditer(text)}
    return out


def grounding_report(answer_text: str, agent_steps: list | None) -> dict:
    """반환: {cited, fetched, grounded, ungrounded, grounded_ratio(0~1|None), authority_used(bool)}.

    fetched = 성공한 권위 도구 호출의 인자에서 뽑은 토큰. cited = 최종 답의 토큰.
    grounded = cited ∩ fetched. ratio = grounded/cited (cited 없으면 None).
    """
    fetched: set[str] = set()
    authority_used = False
    for s in (agent_steps or []):
        if s.get("tool") in AUTHORITY_TOOLS:
            authority_used = True
            obs = str(s.get("observation", ""))
            if obs.startswith(_FAIL_PREFIX):
                continue
            fetched |= _tokens(str(s.get("arg", "")))
    cited = _tokens(answer_text)
    grounded = cited & fetched
    ratio = (len(grounded) / len(cited)) if cited else None
    return {
        "cited": sorted(cited),
        "fetched": sorted(fetched),
        "grounded": sorted(grounded),
        "ungrounded": sorted(cited - fetched),
        "grounded_ratio": (round(ratio, 3) if ratio is not None else None),
        "authority_used": authority_used,
    }
