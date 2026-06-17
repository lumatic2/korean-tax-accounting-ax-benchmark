"""agent 모드 도구 — 파서 + 주입형 실행기 (ADR 0005).

프로토콜(텍스트): 모델은 한 줄로 도구를 호출한다.
    [도구] 법령조문: 법인세법 제34조
    [도구] 기준서문단: 1115 문단74
    [도구] 계산: 900 * 0.1
도구를 더 안 쓰면 [최종]으로 시작하는 최종 답을 낸다. `[도구]` 줄이 없으면 최종으로 간주.

실행기는 주입형(`make_executor`/stub). 실전은 DRF(`retriever.py` 헬퍼)·kifrs DB 재사용,
테스트는 stub 으로 네트워크 없이 재현. import 시 httpx/sqlite 를 끌어오지 않도록 지연 import.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass

# kifrs DB 경로 — env override 가능(타 머신·CI). 기본값은 로컬 경로.
_KIFRS_DB_DEFAULT = r"C:\Users\yusun\projects\kifrs-rag\data\kifrs.db"

# 도구 메뉴 — prompts.py 가 import (단일 출처)
TOOL_MENU = (
    "[법령조문] 법령명과 조문으로 원문 조회. 예: [도구] 법령조문: 법인세법 제34조\n"
    "[기준서문단] K-IFRS 기준서·문단 원문 조회. 예: [도구] 기준서문단: 1115 문단74\n"
    "[계산] 산술식 계산. 예: [도구] 계산: 900 * 0.1"
)

# [도구] 앞뒤 마크다운 장식(**, ##, -, > 등)에 견고하게 — 실전 모델은 마커를 감싸는 일이 잦다.
_TOOL_RE = re.compile(r"\[도구\]\s*\**\s*([^:：\n*]+?)\s*\**\s*[:：]\s*([^\n]+)")
# 조문 + 가지번호(제27조의2) 파싱 — 세법은 가지번호 조문이 흔하다.
_ARTICLE_RE = re.compile(r"제\s*(\d+)\s*조(?:\s*의\s*(\d+))?")
_PARA_RE = re.compile(r"(\d{3,4})\D+([\dA-Za-z.]+)")


def _flat(x) -> str:
    """DRF 항내용이 str·list·dict 어느 것이든 평탄화."""
    if x is None:
        return ""
    if isinstance(x, str):
        return x
    if isinstance(x, list):
        return " ".join(_flat(i) for i in x)
    if isinstance(x, dict):
        return " ".join(_flat(v) for v in x.values())
    return str(x)


def _extract_article_branch(law_json: dict, jo: str, ui: str | None) -> str | None:
    """(조문번호 jo, 가지번호 ui)에 정확히 일치하는 조문단위 본문 추출. 순수함수(테스트 가능)."""
    from ..rag.retriever import _clean
    law = law_json.get("법령", law_json)
    arts = (law.get("조문", {}) or {}).get("조문단위", [])
    if isinstance(arts, dict):
        arts = [arts]
    for a in arts:
        # DRF는 편/장/절/관 제목을 같은 조문번호의 pseudo-조문단위(조문여부="전문")로 인코딩한다.
        # 章 시작 조문(예: 법인세법 제13조)은 제목 전문이 먼저 매치되므로 전문은 건너뛴다.
        if str(a.get("조문여부", "조문")).strip() == "전문":
            continue
        if str(a.get("조문번호", "")).strip() == str(jo) and \
           str(a.get("조문가지번호", "") or "").strip() == (ui or ""):
            chunks = []
            if a.get("조문내용"):
                chunks.append(_clean(_flat(a["조문내용"])))
            hangs = a.get("항")
            if hangs:
                hangs = hangs if isinstance(hangs, list) else [hangs]
                for h in hangs:
                    if not isinstance(h, dict):
                        continue
                    if h.get("항내용"):
                        chunks.append(_clean(_flat(h["항내용"])))
                    hos = h.get("호")  # 수치·요건이 호 단위에 있는 조문(세율·필요경비율 등) 포함
                    if hos:
                        hos = hos if isinstance(hos, list) else [hos]
                        for ho in hos:
                            if isinstance(ho, dict) and ho.get("호내용"):
                                chunks.append(_clean(_flat(ho["호내용"])))
            return "\n".join(c for c in chunks if c.strip())
    return None
_SAFE_CALC = re.compile(r"^[\d\s.+\-*/()]+$")


@dataclass(frozen=True)
class ToolCall:
    name: str
    arg: str


def parse_tool_call(text: str) -> ToolCall | None:
    """모델 응답에서 첫 `[도구]` 호출을 추출. 없으면 None(=최종 답)."""
    m = _TOOL_RE.search(text or "")
    if not m:
        return None
    name = m.group(1).strip().strip("*#> ").strip()
    arg = m.group(2).strip().strip("*").strip()
    return ToolCall(name=name, arg=arg)


# ── 실전 실행기 (지연 import) ─────────────────────────────────────────

def _exec_법령조문(arg: str, *, accessed_at: str) -> str:
    from ..rag.retriever import _search_law_mst, _fetch_law
    m = _ARTICLE_RE.search(arg)
    if not m:
        return f"인자 형식 오류(법령명 제N조 필요): {arg!r}"
    jo, ui = m.group(1), m.group(2)  # ui=가지번호(없으면 None)
    law_name = arg[: m.start()].strip()
    label = f"제{jo}조" + (f"의{ui}" if ui else "")
    if not law_name:
        return f"법령명 누락: {arg!r}"
    try:
        mst = _search_law_mst(law_name)
        if not mst:
            return f"법령 미발견: {law_name}"
        excerpt = _extract_article_branch(_fetch_law(mst, accessed_at), jo, ui)
        return excerpt or f"조문 미추출: {law_name} {label}"
    except Exception as e:  # 네트워크·키 실패 — graceful
        return f"조회 실패({law_name} {label}): {e}"


def _exec_기준서문단(arg: str, *, accessed_at: str) -> str:
    import sqlite3
    from pathlib import Path
    m = _PARA_RE.search(arg)
    if not m:
        return f"인자 형식 오류(기준서 문단 필요): {arg!r}"
    standard, no = m.group(1), m.group(2)
    db = Path(os.getenv("KIFRS_DB_PATH", _KIFRS_DB_DEFAULT))
    if not db.exists():
        return f"kifrs DB 없음: {db} (KIFRS_DB_PATH 로 지정 가능)"
    try:
        con = sqlite3.connect(str(db))
        row = con.execute(
            "SELECT body FROM paragraph WHERE standard=? AND no=?", (standard, no)
        ).fetchone()
        con.close()
        return row[0] if row else f"문단 미발견: {standard}-{no}"
    except Exception as e:
        return f"조회 실패({standard}-{no}): {e}"


def _exec_계산(arg: str, *, accessed_at: str) -> str:
    expr = arg.strip()
    if not _SAFE_CALC.match(expr):
        return f"허용되지 않는 식(숫자·연산자만): {arg!r}"
    try:
        return str(eval(expr, {"__builtins__": {}}, {}))  # noqa: S307 — _SAFE_CALC 로 제한
    except Exception as e:
        return f"계산 오류: {e}"


_REAL = {"법령조문": _exec_법령조문, "기준서문단": _exec_기준서문단, "계산": _exec_계산}


def make_executor(accessed_at: str | None = None):
    """실전 도구 실행기 반환. (call: ToolCall) -> 관측 문자열."""
    acc = accessed_at or "unknown"

    def _run(call: ToolCall) -> str:
        fn = _REAL.get(call.name.strip())
        if fn is None:
            return f"알 수 없는 도구: {call.name!r} (사용 가능: {', '.join(_REAL)})"
        return fn(call.arg, accessed_at=acc)

    return _run
