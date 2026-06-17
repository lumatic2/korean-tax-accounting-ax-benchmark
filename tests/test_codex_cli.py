"""CodexCLIClient 격리 재현 테스트 (ADR 0010).

후보·judge subprocess가 레포 밖 sandbox cwd + 격리 플래그로 실행되는지 검증.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from ktaxbench.models import codex_cli
from ktaxbench.models.codex_cli import CodexCLIClient, _ensure_sandbox


class _FakeCompleted:
    def __init__(self, returncode=0, stdout=b"OK", stderr=b""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _capture(monkeypatch, fake_out_text="OK"):
    seen = {}

    def fake_run(cmd, **kwargs):
        seen["cmd"] = cmd
        seen["kwargs"] = kwargs
        # find the -o filepath if present and write fake output there
        if "-o" in cmd:
            idx = cmd.index("-o")
            out_file = cmd[idx + 1]
            Path(out_file).write_text(fake_out_text, encoding="utf-8")
        return _FakeCompleted()

    monkeypatch.setattr(codex_cli.subprocess, "run", fake_run)
    return seen


def test_isolated_default_adds_flags_and_sandbox_cwd(monkeypatch):
    seen = _capture(monkeypatch)
    cl = CodexCLIClient("gpt-5.5-cli", "gpt-5.5")
    assert cl.isolated is True
    cl.complete("sys", "prompt")
    
    assert "-s" in seen["cmd"]
    assert "read-only" in seen["cmd"]
    assert "--ignore-user-config" in seen["cmd"]
    assert "--ignore-rules" in seen["cmd"]
    assert "--skip-git-repo-check" in seen["cmd"]
    assert "--ephemeral" in seen["cmd"]
    
    cwd = seen["kwargs"]["cwd"]
    assert cwd == _ensure_sandbox()
    
    repo = Path(__file__).resolve().parents[1]
    assert repo not in Path(cwd).resolve().parents and Path(cwd).resolve() != repo


def test_isolated_false_keeps_legacy_behavior(monkeypatch):
    seen = _capture(monkeypatch)
    cl = CodexCLIClient("gpt-5.5-cli", "gpt-5.5", isolated=False)
    cl.complete("sys", "prompt")
    assert "-s" not in seen["cmd"]
    assert seen["kwargs"]["cwd"] is None


def test_system_prompt_merged(monkeypatch):
    seen = _capture(monkeypatch)
    CodexCLIClient("gpt-5.5-cli", "gpt-5.5").complete("SYSTEM_X", "prompt")
    assert seen["kwargs"]["input"] == b"SYSTEM_X\n\nprompt"


# ── rate-limit 재시도 ──

def _no_sleep(monkeypatch):
    monkeypatch.setattr(codex_cli.time, "sleep", lambda *_: None)


def test_rate_limit_retries_then_succeeds(monkeypatch):
    _no_sleep(monkeypatch)
    calls = {"n": 0}

    def fake_run(cmd, **kwargs):
        calls["n"] += 1
        if calls["n"] <= 2:
            return _FakeCompleted(1, stdout=b"Rate limited error")
        # write fake file on success
        if "-o" in cmd:
            idx = cmd.index("-o")
            out_file = cmd[idx + 1]
            Path(out_file).write_text("ANSWER", encoding="utf-8")
        return _FakeCompleted(0)

    monkeypatch.setattr(codex_cli.subprocess, "run", fake_run)
    monkeypatch.setenv("KTAXBENCH_RL_RETRIES", "4")
    r = CodexCLIClient("gpt-5.5-cli", "gpt-5.5").complete("sys", "p")
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

    monkeypatch.setattr(codex_cli.subprocess, "run", fake_run)
    monkeypatch.setenv("KTAXBENCH_RL_RETRIES", "3")
    r = CodexCLIClient("gpt-5.5-cli", "gpt-5.5").complete("sys", "p")
    assert r.text == ""
    assert "rc=1" in r.raw_meta["error"]
    assert calls["n"] == 4


def test_non_ratelimit_error_no_retry(monkeypatch):
    _no_sleep(monkeypatch)
    calls = {"n": 0}

    def fake_run(cmd, **kwargs):
        calls["n"] += 1
        return _FakeCompleted(2, stderr=b"some other failure")

    monkeypatch.setattr(codex_cli.subprocess, "run", fake_run)
    r = CodexCLIClient("gpt-5.5-cli", "gpt-5.5").complete("sys", "p")
    assert "rc=2" in r.raw_meta["error"]
    assert calls["n"] == 1
