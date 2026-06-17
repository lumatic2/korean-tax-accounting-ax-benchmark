"""모델 레지스트리 — config/models.yaml → ModelClient 인스턴스 (provider 분기)."""
from __future__ import annotations

from pathlib import Path

import yaml

from .claude_cli import ClaudeCLIClient

_REPO = Path(__file__).resolve().parents[3]
_CFG = _REPO / "config" / "models.yaml"


def _load_cfg() -> dict:
    return yaml.safe_load(_CFG.read_text(encoding="utf-8"))["models"]


def list_models() -> list[str]:
    return list(_load_cfg().keys())


def get_spec(name: str) -> dict:
    cfg = _load_cfg()
    if name not in cfg:
        raise KeyError(f"unknown model: {name} (있는 모델: {list(cfg)})")
    return cfg[name]


def get_model(name: str):
    """name → ModelClient. provider 분기(claude_cli / codex_cli / gemini_cli / openai / google)."""
    spec = get_spec(name)
    provider = spec.get("provider")
    temp = float(spec.get("temperature", 0.0))
    if provider == "claude_cli":
        return ClaudeCLIClient(
            name=name,
            model_id=spec["model_id"],
            timeout=int(spec.get("timeout", 300)),
        )
    if provider == "codex_cli":
        from .codex_cli import CodexCLIClient
        return CodexCLIClient(
            name=name,
            model_id=spec["model_id"],
            timeout=int(spec.get("timeout", 300)),
        )
    if provider == "gemini_cli":
        from .gemini_cli import GeminiCLIClient
        return GeminiCLIClient(
            name=name,
            model_id=spec["model_id"],
            timeout=int(spec.get("timeout", 300)),
        )
    if provider == "openai":
        from .openai_client import OpenAIClient
        return OpenAIClient(name=name, model_id=spec["model_id"], temperature=temp)
    if provider == "google":
        from .google_client import GoogleClient
        return GoogleClient(name=name, model_id=spec["model_id"], temperature=temp)
    raise NotImplementedError(f"provider '{provider}' 미지원")
