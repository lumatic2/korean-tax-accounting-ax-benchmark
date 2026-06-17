"""결정론 코드 채점 — MC/계산/근거(citation). 같은 입력 → 같은 점수.

순수 함수만(네트워크·시간·랜덤 금지). 주관 차원(실무·리스크·설명)은 LLM-judge(step5) 몫.
계산 점수는 gold 금액 집합에 대한 recall 프록시(거친 점수) — 세밀한 과정 채점은 judge가 보완.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .rubric import weights_for

# ── 추출 유틸(전부 순수 함수) ──────────────────────────────────────────────
_LOC_RE = re.compile(r"제\s*\d+\s*조(?:\s*의\s*\d+)?")
_FAKE_HINT = re.compile(r"제\s*\d+\s*조")

# K-IFRS 기준서-문단 (회계 근거채점, ADR 0007). 기준서는 4자리(1001+)라 세무 '제N호'와 안 겹친다.
_KIFRS_STD_RE = re.compile(r"제\s*(\d{4})\s*호")                         # 기준서 번호
_KIFRS_PARA_RE = re.compile(r"문단\s*([0-9A-Za-z][0-9A-Za-z.]*)")        # 문단 토큰(57·4.1.2A·B35)
_KIFRS_BRACKET_RE = re.compile(                                          # [1038-57] 표준 인용
    r"\[\s*(\d{4})\s*[-–]\s*([0-9A-Za-z][0-9A-Za-z.]*?)\s*\]")


@dataclass(frozen=True)
class CodeScore:
    dimension: str
    points: float
    max_points: float
    detail: str


def can_code_grade(task_type: str) -> bool:
    return task_type in {"multiple_choice", "calculation", "citation"}


def _mc_label(text: str) -> str | None:
    """응답/정답에서 선택지 라벨(A-E) 추출. 숫자(1-5)는 라벨로 환산."""
    m = re.search(r"정답[은는이]?\s*[:\-]?\s*([A-Ea-e1-5])", text)
    tok = m.group(1) if m else None
    if tok is None:
        labels = re.findall(r"(?<![A-Za-z])([A-E])(?![A-Za-z])", text)
        digits = re.findall(r"(?<!\d)([1-5])(?!\d)", text)
        tok = labels[-1] if labels else (digits[-1] if digits else None)
    if tok is None:
        return None
    tok = tok.upper()
    if tok.isdigit():
        return chr(ord("A") + int(tok) - 1)
    return tok


def parse_korean_amounts(text: str) -> set[int]:
    """한국어 금액 표기 → 원 단위 정수 집합. '8,200만원'→82000000, '1억600만'→106000000."""
    res: set[int] = set()
    for m in re.finditer(r"(\d[\d,]*)\s*억(?:\s*(\d[\d,]*)\s*만)?", text):
        eok = int(m.group(1).replace(",", ""))
        man = int(m.group(2).replace(",", "")) if m.group(2) else 0
        res.add(eok * 100_000_000 + man * 10_000)
    for m in re.finditer(r"(\d[\d,]*)\s*만\s*원?", text):
        res.add(int(m.group(1).replace(",", "")) * 10_000)
    for m in re.finditer(r"(\d[\d,]{3,})\s*원", text):
        res.add(int(m.group(1).replace(",", "")))
    return res


def _norm_loc(s: str) -> str:
    return re.sub(r"\s+", "", s)


def _base_article(s: str) -> str:
    """'제25조 제4항' / '제25조의2 제1항' → '제25조' / '제25조의2'."""
    m = re.match(r"제\d+조(?:의\d+)?", _norm_loc(s))
    return m.group(0) if m else _norm_loc(s)


def _kifrs_key(std: str, para: str) -> str:
    """기준서 번호 + 문단 → 정규 매치키 '1038-57'. 문단은 대문자 정규화·후행점 제거."""
    return f"{std}-{para.upper().rstrip('.')}"


def _kifrs_source_key(source: dict) -> str | None:
    """회계 source(title='K-IFRS 제1038호 …', locator='문단 57') → '1038-57'. 아니면 None."""
    std = _KIFRS_STD_RE.search(source.get("title", "") or "")
    para = _KIFRS_PARA_RE.search(source.get("locator", "") or "")
    return _kifrs_key(std.group(1), para.group(1)) if std and para else None


def _kifrs_cited(text: str) -> set[str]:
    """답변에서 기준서-문단 인용 추출. 1순위 '[1038-57]', 2순위 '제1038호 … 문단 57'(근접 윈도우)."""
    keys: set[str] = set()
    for m in _KIFRS_BRACKET_RE.finditer(text):
        keys.add(_kifrs_key(m.group(1), m.group(2)))
    for m in _KIFRS_STD_RE.finditer(text):                 # 자연어: 기준서 뒤 40자 내 문단
        pm = _KIFRS_PARA_RE.search(text[m.end(): m.end() + 40])
        if pm:
            keys.add(_kifrs_key(m.group(1), pm.group(1)))
    return keys


# ── 채점기 ────────────────────────────────────────────────────────────────
def grade_multiple_choice(question: dict, answer_text: str) -> list[CodeScore]:
    w = weights_for("multiple_choice")["conclusion_accuracy"]
    gold = _mc_label(question.get("answer", {}).get("final_answer", ""))
    pred = _mc_label(answer_text)
    hit = gold is not None and pred == gold
    return [CodeScore("conclusion_accuracy", float(w) if hit else 0.0, float(w),
                      f"gold={gold} pred={pred}")]


def grade_calculation(question: dict, answer_text: str) -> list[CodeScore]:
    wc = weights_for("calculation")
    gold = parse_korean_amounts(question.get("answer", {}).get("final_answer", ""))
    pred = parse_korean_amounts(answer_text)
    ratio = (len(gold & pred) / len(gold)) if gold else 0.0
    detail = f"gold={sorted(gold)} matched={sorted(gold & pred)}"
    return [
        CodeScore("conclusion_accuracy", round(ratio * wc["conclusion_accuracy"], 2),
                  float(wc["conclusion_accuracy"]), detail),
        CodeScore("calculation_or_process", round(ratio * wc["calculation_or_process"], 2),
                  float(wc["calculation_or_process"]), "recall 프록시(과정 세부는 judge)"),
    ]


def grade_citation(question: dict, answer_text: str) -> tuple[list[CodeScore], list[str]]:
    w = weights_for("citation")["legal_basis"]
    sources = question.get("sources", [])
    # gold: 세무 조문(제N조) ∪ 회계 기준서-문단(1038-57). 문항은 둘 중 하나라 교차오염 없음(ADR 0007).
    gold = {_base_article(s.get("locator", "")) for s in sources
            if _FAKE_HINT.search(s.get("locator", ""))}
    gold |= {k for s in sources if (k := _kifrs_source_key(s))}
    cited = {_base_article(x) for x in _LOC_RE.findall(answer_text)} | _kifrs_cited(answer_text)
    matched = gold & cited
    ratio = (len(matched) / len(gold)) if gold else 0.0
    unverified = sorted(cited - gold)  # 인용했으나 gold sources 에 없음 → judge/사람 확인 필요
    flags = [f"unverified_citation:{u}" for u in unverified]
    score = CodeScore("legal_basis", round(ratio * w, 2), float(w),
                      f"gold={sorted(gold)} cited={sorted(cited)}")
    return [score], flags


def grade(question: dict, answer_text: str) -> dict:
    """task_type 에 맞는 결정론 채점. {scores: [CodeScore], flags: [str]}."""
    tt = question.get("task_type")
    flags: list[str] = []
    scores: list[CodeScore] = []
    if tt == "multiple_choice":
        scores = grade_multiple_choice(question, answer_text)
    elif tt == "calculation":
        scores = grade_calculation(question, answer_text)
    elif tt == "citation":
        scores, flags = grade_citation(question, answer_text)
    return {"scores": scores, "flags": flags}
