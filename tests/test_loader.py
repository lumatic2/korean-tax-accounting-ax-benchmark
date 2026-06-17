"""loader + registry 결정론 테스트(모델 호출 없음)."""
from __future__ import annotations

from pathlib import Path

from ktaxbench.loader import load_questions
from ktaxbench.models.registry import list_models, get_model
from ktaxbench.models.claude_cli import ClaudeCLIClient

_DATA = str(Path(__file__).resolve().parents[1] / "data" / "sample-questions-v0.1.jsonl")


def test_load_all():
    # 데이터가 늘어나도 깨지지 않게 파일의 비어있지 않은 줄 수와 대조(loader 가 행을 누락하지 않는지)
    n_lines = sum(1 for line in open(_DATA, encoding="utf-8") if line.strip())
    assert len(load_questions(_DATA)) == n_lines


def test_filter_domain_corp_tax():
    rows = load_questions(_DATA, domain="corp_tax")
    expected = [r for r in load_questions(_DATA) if r["domain"] == "corp_tax"]
    assert rows == expected
    assert len(rows) >= 1
    assert all(r["domain"] == "corp_tax" for r in rows)


def test_filter_task_type_calculation():
    rows = load_questions(_DATA, task_type="calculation")
    assert len(rows) >= 1
    assert all(r["task_type"] == "calculation" for r in rows)


def test_filter_unknown_returns_empty():
    assert load_questions(_DATA, domain="bogus") == []


def test_registry_lists_claude_models():
    names = list_models()
    assert {"claude-opus-4-8", "claude-sonnet-4-6", "claude-haiku-4-5"} <= set(names)


def test_get_model_returns_claude_client():
    m = get_model("claude-haiku-4-5")
    assert isinstance(m, ClaudeCLIClient)
    assert m.model_id == "claude-haiku-4-5"
