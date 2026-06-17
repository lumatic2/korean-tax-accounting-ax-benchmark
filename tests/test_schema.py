"""schema 검증 회귀 테스트 — 기존 데이터셋은 통과, 결함은 검출."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from ktaxbench.schema import lint_question, validate_question, is_valid

_REPO = Path(__file__).resolve().parents[1]
_DATA = _REPO / "data" / "sample-questions-v0.1.jsonl"


def _load() -> list[dict]:
    return [json.loads(l) for l in _DATA.read_text(encoding="utf-8").splitlines() if l.strip()]


def test_existing_dataset_valid():
    """19문항 전부 하드 위반 0 (회귀 가드)."""
    rows = _load()
    assert len(rows) >= 19
    for obj in rows:
        errs = validate_question(obj)
        assert errs == [], f"{obj.get('id')}: {errs}"


def _a_valid_question() -> dict:
    for obj in _load():
        if obj["id"] == "ktb-vat-0003":
            return copy.deepcopy(obj)
    raise AssertionError("fixture 문항 없음")


def test_enum_violation_detected():
    obj = _a_valid_question()
    obj["domain"] = "bogus"
    assert any("domain" in e for e in validate_question(obj))
    assert not is_valid(obj)


def test_rubric_sum_mismatch_detected():
    obj = _a_valid_question()
    obj["rubric"]["criteria"][0]["points"] += 7
    assert any("rubric 배점 합" in e for e in validate_question(obj))


def test_missing_source_locator_detected():
    obj = _a_valid_question()
    obj["sources"][0]["locator"] = ""
    assert any("locator" in e for e in validate_question(obj))


def test_hash_mismatch_detected():
    obj = _a_valid_question()
    obj["question"]["title"] = obj["question"]["title"] + " (변경)"
    # hash 필드는 그대로 → 내용 불일치 검출
    assert any("hash 내용 불일치" in e for e in validate_question(obj))


def test_id_domain_mismatch_detected():
    obj = _a_valid_question()
    obj["domain"] = "corp_tax"  # id는 ktb-vat-0003 인데 domain만 변경
    assert any("불일치" in e for e in validate_question(obj))


def test_calc_steps_warning_for_draft_error_for_reviewed():
    obj = _a_valid_question()
    obj["answer"]["calculation_steps"] = []
    # draft: 경고
    obj["status"] = "draft"
    errs, warns = lint_question(obj)
    assert any("calculation_steps" in w for w in warns)
    assert not any("calculation_steps" in e for e in errs)
    # internal_reviewed: 에러로 승격
    obj["status"] = "internal_reviewed"
    errs2, _ = lint_question(obj)
    assert any("calculation_steps" in e for e in errs2)
