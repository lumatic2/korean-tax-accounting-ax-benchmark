"""레지스트리 provider 분기 — 클래스 매핑(키·SDK 불필요, lazy)."""
from __future__ import annotations

from ktaxbench.models.registry import get_model, list_models
from ktaxbench.models.claude_cli import ClaudeCLIClient
from ktaxbench.models.codex_cli import CodexCLIClient
from ktaxbench.models.gemini_cli import GeminiCLIClient
from ktaxbench.models.openai_client import OpenAIClient
from ktaxbench.models.google_client import GoogleClient


def test_provider_class_mapping():
    assert isinstance(get_model("claude-haiku-4-5"), ClaudeCLIClient)
    assert isinstance(get_model("gpt-5.4"), OpenAIClient)
    assert isinstance(get_model("gemini-3-pro"), GoogleClient)
    assert isinstance(get_model("gpt-5.5"), CodexCLIClient)
    assert isinstance(get_model("gemini-2.5-pro"), GeminiCLIClient)


def test_model_ids_set():
    assert get_model("gpt-5.4").model_id == "gpt-5.4"
    assert get_model("gemini-3-pro").model_id == "gemini-3-pro"
    assert get_model("gpt-5.5").model_id == "gpt-5.5"
    assert get_model("gemini-2.5-pro").model_id == "gemini-2.5-pro"


def test_list_includes_all_providers():
    names = set(list_models())
    assert {"gpt-5.4", "gemini-3-pro", "claude-opus-4-8", "gpt-5.5", "gemini-2.5-pro"} <= names


def test_unknown_model_raises():
    import pytest
    with pytest.raises(KeyError):
        get_model("nonexistent-model")
