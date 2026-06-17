"""code-grader 결정론 테스트 — M2 핵심(같은 입력→같은 점수)."""
from __future__ import annotations

from pathlib import Path

from ktaxbench.loader import load_questions
from ktaxbench.grading import code_grader as cg
from ktaxbench.grading.rubric import weights_for

_DATA = str(Path(__file__).resolve().parents[1] / "data" / "sample-questions-v0.1.jsonl")
_BY_ID = {q["id"]: q for q in load_questions(_DATA)}


def _score(scores, dim):
    return next(s.points for s in scores if s.dimension == dim)


def test_mc_exact():
    q = _BY_ID["ktb-vat-0005"]  # 정답 C
    full = weights_for("multiple_choice")["conclusion_accuracy"]
    right = cg.grade(q, "검토 결과 정답은 C입니다. 세율 10%.")
    assert _score(right["scores"], "conclusion_accuracy") == full
    wrong = cg.grade(q, "정답은 A 라고 본다.")
    assert _score(wrong["scores"], "conclusion_accuracy") == 0.0


def test_calculation_match():
    q = _BY_ID["ktb-corp-tax-0003"]
    ok = ("기본한도 1,200만원 + 수입금액별 7,000만원 = 한도 8,200만원, "
          "지출 9,000만원 중 800만원 손금불산입.")
    res = cg.grade(q, ok)
    # 모든 gold 금액 포함 → conclusion 만점
    assert _score(res["scores"], "conclusion_accuracy") == float(
        weights_for("calculation")["conclusion_accuracy"])
    bad = cg.grade(q, "손금불산입액은 5,000만원이다.")
    assert _score(bad["scores"], "conclusion_accuracy") < _score(res["scores"], "conclusion_accuracy")


def test_citation_locator():
    q = _BY_ID["ktb-corp-tax-0003"]  # sources locator '제25조 제4항'
    full = weights_for("citation")["legal_basis"]
    res = cg.grade_citation(q, "법인세법 제25조에 따라 한도를 계산한다.")
    assert _score(res[0], "legal_basis") == full
    none = cg.grade_citation(q, "관련 법령에 따른다.")
    assert _score(none[0], "legal_basis") == 0.0


def test_fake_article_flagged():
    q = _BY_ID["ktb-corp-tax-0003"]
    _, flags = cg.grade_citation(q, "법인세법 제999조의5 및 제25조에 근거한다.")
    assert any("제999조의5" in f for f in flags)


def test_citation_kifrs_match():
    # 회계 source: title='K-IFRS 제1038호 무형자산', locator='문단 57'/'문단 68' (ADR 0007)
    q = _BY_ID["ktb-accounting-0002"]
    full = weights_for("citation")["legal_basis"]
    res = cg.grade_citation(q, "무형자산 인식요건은 [1038-57] 및 [1038-68]에 따른다.")
    assert _score(res[0], "legal_basis") == full
    none = cg.grade_citation(q, "관련 기준서에 따른다.")
    assert _score(none[0], "legal_basis") == 0.0


def test_citation_kifrs_partial():
    q = _BY_ID["ktb-accounting-0002"]  # gold 2건(1038-57, 1038-68)
    full = weights_for("citation")["legal_basis"]
    res = cg.grade_citation(q, "[1038-57]만 인용한다.")  # 1/2 매칭
    assert 0.0 < _score(res[0], "legal_basis") < full


def test_citation_kifrs_natural_language():
    q = _BY_ID["ktb-accounting-0002"]
    res = cg.grade_citation(q, "K-IFRS 제1038호 무형자산 문단 57에 근거한다.")
    assert _score(res[0], "legal_basis") > 0.0


def test_citation_kifrs_alnum_paragraph():
    # 문단 토큰이 영숫자(B35/B37)인 경우 — title='제1115호', locator='문단 B35'/'문단 B37'
    q = {
        "task_type": "citation",
        "sources": [
            {"title": "K-IFRS 제1115호 고객과의 계약에서 생기는 수익", "locator": "문단 B35"},
            {"title": "K-IFRS 제1115호 고객과의 계약에서 생기는 수익", "locator": "문단 B37"},
        ],
    }
    full = weights_for("citation")["legal_basis"]
    res = cg.grade_citation(q, "수익인식 적용지침 [1115-B35], [1115-B37] 참조.")
    assert _score(res[0], "legal_basis") == full


def test_kifrs_fake_flagged():
    q = _BY_ID["ktb-accounting-0002"]
    _, flags = cg.grade_citation(q, "[9999-12] 및 [1038-57]에 근거한다.")
    assert any("9999-12" in f for f in flags)


def test_determinism():
    q = _BY_ID["ktb-corp-tax-0003"]
    ans = "한도 8,200만원, 손금불산입 800만원 (법인세법 제25조)."
    r1 = cg.grade(q, ans)
    r2 = cg.grade(q, ans)
    assert [(s.dimension, s.points) for s in r1["scores"]] == \
           [(s.dimension, s.points) for s in r2["scores"]]
    assert r1["flags"] == r2["flags"]


def test_amount_parser():
    amts = cg.parse_korean_amounts("8,200만원과 800만원, 1억600만원")
    assert 82_000_000 in amts
    assert 8_000_000 in amts
    assert 106_000_000 in amts
