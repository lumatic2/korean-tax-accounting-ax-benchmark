"""GeminiCLIClient 격리 재현 테스트 (ADR 0010).

후보·judge subprocess가 레포 밖 sandbox cwd + 격리 플래그로 실행되는지 검증.
"""
from __future__ import annotations

from pathlib import Path

from ktaxbench.models import gemini_cli
from ktaxbench.models.gemini_cli import GeminiCLIClient, _ensure_sandbox


class _FakeCompleted:
    def __init__(self, returncode=0, stdout=b"OK", stderr=b""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _capture(monkeypatch, stdout_text=b"OK"):
    seen = {}

    def fake_run(cmd, **kwargs):
        seen["cmd"] = cmd
        seen["kwargs"] = kwargs
        return _FakeCompleted(stdout=stdout_text)

    monkeypatch.setattr(gemini_cli.subprocess, "run", fake_run)
    return seen


def test_isolated_default_adds_flags_and_sandbox_cwd(monkeypatch):
    seen = _capture(monkeypatch)
    cl = GeminiCLIClient("gemini-2.5-pro-cli", "gemini-2.5-pro")
    assert cl.isolated is True
    cl.complete("sys", "prompt")
    
    assert "--approval-mode" in seen["cmd"]
    assert "plan" in seen["cmd"]
    assert "--skip-trust" in seen["cmd"]
    assert "--session-id" in seen["cmd"]
    
    cwd = seen["kwargs"]["cwd"]
    assert cwd == _ensure_sandbox()
    
    repo = Path(__file__).resolve().parents[1]
    assert repo not in Path(cwd).resolve().parents and Path(cwd).resolve() != repo


def test_isolated_false_keeps_legacy_behavior(monkeypatch):
    seen = _capture(monkeypatch)
    cl = GeminiCLIClient("gemini-2.5-pro-cli", "gemini-2.5-pro", isolated=False)
    cl.complete("sys", "prompt")
    assert "--approval-mode" not in seen["cmd"]
    assert seen["kwargs"]["cwd"] is None


def test_system_prompt_merged(monkeypatch):
    seen = _capture(monkeypatch)
    GeminiCLIClient("gemini-2.5-pro-cli", "gemini-2.5-pro").complete("SYSTEM_X", "prompt")
    assert seen["kwargs"]["input"] == b"SYSTEM_X\n\nprompt"


def test_model_id_from_config_by_default(monkeypatch):
    seen = _capture(monkeypatch)
    monkeypatch.delenv("KTAXBENCH_GEMINI_MODEL", raising=False)
    GeminiCLIClient("gemini-2.5-pro-cli", "gemini-2.5-pro").complete("sys", "p")
    i = seen["cmd"].index("-m")
    assert seen["cmd"][i + 1] == "gemini-2.5-pro"


def test_env_overrides_model_id(monkeypatch):
    seen = _capture(monkeypatch)
    monkeypatch.setenv("KTAXBENCH_GEMINI_MODEL", "gemini-2.5-flash")
    GeminiCLIClient("gemini-2.5-pro-cli", "gemini-2.5-pro").complete("sys", "p")
    i = seen["cmd"].index("-m")
    assert seen["cmd"][i + 1] == "gemini-2.5-flash"  # config 무시하고 env 우선


# ── rate-limit 재시도 ──

def _no_sleep(monkeypatch):
    monkeypatch.setattr(gemini_cli.time, "sleep", lambda *_: None)


def test_rate_limit_retries_then_succeeds(monkeypatch):
    _no_sleep(monkeypatch)
    calls = {"n": 0}

    def fake_run(cmd, **kwargs):
        calls["n"] += 1
        if calls["n"] <= 2:
            return _FakeCompleted(1, stdout=b"Rate limited error")
        return _FakeCompleted(0, stdout=b"ANSWER")

    monkeypatch.setattr(gemini_cli.subprocess, "run", fake_run)
    monkeypatch.setenv("KTAXBENCH_RL_RETRIES", "4")
    r = GeminiCLIClient("gemini-2.5-pro-cli", "gemini-2.5-pro").complete("sys", "p")
    assert r.text == "ANSWER"
    assert r.raw_meta.get("error") is None
    assert calls["n"] == 3
    assert r.raw_meta["attempts"] == 3


def test_rate_limit_exhausts_returns_error(monkeypatch):
    _no_sleep(monkeypatch)
    calls = {"n": 0}

    def fake_run(cmd, **kwargs):
        calls["n"] += 1
        return _FakeCompleted(1, stdout=b"Rate limited")

    monkeypatch.setattr(gemini_cli.subprocess, "run", fake_run)
    monkeypatch.setenv("KTAXBENCH_RL_RETRIES", "3")
    r = GeminiCLIClient("gemini-2.5-pro-cli", "gemini-2.5-pro").complete("sys", "p")
    assert r.text == ""
    assert "rc=1" in r.raw_meta["error"]
    assert calls["n"] == 4


def test_non_ratelimit_error_no_retry(monkeypatch):
    _no_sleep(monkeypatch)
    calls = {"n": 0}

    def fake_run(cmd, **kwargs):
        calls["n"] += 1
        return _FakeCompleted(2, stderr=b"some other failure")

    monkeypatch.setattr(gemini_cli.subprocess, "run", fake_run)
    r = GeminiCLIClient("gemini-2.5-pro-cli", "gemini-2.5-pro").complete("sys", "p")
    assert "rc=2" in r.raw_meta["error"]
    assert calls["n"] == 1
