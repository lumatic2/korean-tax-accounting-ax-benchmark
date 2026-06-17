"""프롬프트 빌더 결정론 테스트(네트워크 없음)."""
from __future__ import annotations

from pathlib import Path

import pytest

from ktaxbench.loader import load_questions
from ktaxbench.prompts import build_prompt

_DATA = str(Path(__file__).resolve().parents[1] / "data" / "sample-questions-v0.1.jsonl")


def _vat_calc():
    return load_questions(_DATA, domain="vat", task_type="calculation")[0]


def _mc():
    return load_questions(_DATA, task_type="multiple_choice")[0]


@pytest.mark.parametrize("mode", ["closed_book", "rag", "agent"])
def test_modes_include_core_fields(mode):
    q = _vat_calc()
    system, user = build_prompt(q, mode)
    assert isinstance(system, str) and isinstance(user, str)
    assert q["time_basis"] in user                       # 기준일 포함
    assert q["question"]["facts"][0] in user             # 사실관계 포함
    assert q["question"]["required_output"][0] in user   # 요구 출력 포함


def test_rag_injects_context():
    q = _vat_calc()
    _, user = build_prompt(q, "rag", context="[부가가치세법 제61조] 간이과세...")
    assert "제공 근거" in user
    assert "제61조" in user


def test_multiple_choice_lists_choices():
    q = _mc()
    _, user = build_prompt(q, "closed_book")
    assert "선택지" in user
    assert "정답 번호" in user


def test_unknown_mode_raises():
    with pytest.raises(ValueError):
        build_prompt(_vat_calc(), "bogus")
