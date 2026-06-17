"""ClaudeCLIClient 격리 재현 테스트 (ADR 0008).

후보·judge subprocess 가 레포 밖 sandbox cwd + --strict-mcp-config 로 실행되는지 검증.
subprocess.run 을 가로채 실제 claude CLI 호출 없이 cmd·cwd 만 단언한다.
"""
from __future__ import annotations

from pathlib import Path

from ktaxbench.models import claude_cli
from ktaxbench.models.claude_cli import ClaudeCLIClient, _ensure_sandbox


class _FakeCompleted:
    def __init__(self):
        self.returncode = 0
        self.stdout = b"OK"
        self.stderr = b""


def _capture(monkeypatch):
    """subprocess.run 을 가로채 (cmd, kwargs) 를 기록하고 가짜 결과 반환."""
    seen = {}

    def fake_run(cmd, **kwargs):
        seen["cmd"] = cmd
        seen["kwargs"] = kwargs
        return _FakeCompleted()

    monkeypatch.setattr(claude_cli.subprocess, "run", fake_run)
    return seen


def test_isolated_default_adds_strict_mcp_and_sandbox_cwd(monkeypatch):
    seen = _capture(monkeypatch)
    cl = ClaudeCLIClient("haiku", "claude-haiku-4-5")
    assert cl.isolated is True
    cl.complete("sys", "prompt")
    assert "--strict-mcp-config" in seen["cmd"]
    cwd = seen["kwargs"]["cwd"]
    assert cwd == _ensure_sandbox()
    # sandbox 는 레포 밖이어야 한다(레포 CLAUDE.md 미발견의 핵심).
    repo = Path(__file__).resolve().parents[1]
    assert repo not in Path(cwd).resolve().parents and Path(cwd).resolve() != repo


def test_isolated_false_keeps_legacy_behavior(monkeypatch):
    seen = _capture(monkeypatch)
    cl = ClaudeCLIClient("haiku", "claude-haiku-4-5", isolated=False)
    cl.complete("sys", "prompt")
    assert "--strict-mcp-config" not in seen["cmd"]
    assert seen["kwargs"]["cwd"] is None


def test_system_prompt_still_appended_under_isolation(monkeypatch):
    seen = _capture(monkeypatch)
    ClaudeCLIClient("haiku", "claude-haiku-4-5").complete("SYSTEM_X", "prompt")
    cmd = seen["cmd"]
    assert "--append-system-prompt" in cmd
    assert cmd[cmd.index("--append-system-prompt") + 1] == "SYSTEM_X"


# ── rate-limit 재시도 (transient 서버 제한이 eval 을 오염시키지 않게) ──

class _FakeResult:
    def __init__(self, returncode, stdout=b"", stderr=b""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _no_sleep(monkeypatch):
    monkeypatch.setattr(claude_cli.time, "sleep", lambda *_: None)


def test_rate_limit_retries_then_succeeds(monkeypatch):
    # rate-limit 메시지가 stdout 으로 나오는 실제 동작 재현. 2번 제한 후 성공.
    _no_sleep(monkeypatch)
    calls = {"n": 0}

    def fake_run(cmd, **kwargs):
        calls["n"] += 1
        if calls["n"] <= 2:
            return _FakeResult(1, stdout=b"API Error: Server is temporarily limiting requests \xc2\xb7 Rate limited")
        return _FakeResult(0, stdout=b"ANSWER")

    monkeypatch.setattr(claude_cli.subprocess, "run", fake_run)
    monkeypatch.setenv("KTAXBENCH_RL_RETRIES", "4")
    r = ClaudeCLIClient("haiku", "claude-haiku-4-5").complete("sys", "p")
    assert r.text == "ANSWER"
    assert r.raw_meta.get("error") is None
    assert calls["n"] == 3  # 2 retries + 1 success
    assert r.raw_meta["attempts"] == 3


def test_rate_limit_exhausts_returns_error(monkeypatch):
    # 계속 제한되면 retries 소진 후 error Response (예외 아님).
    _no_sleep(monkeypatch)
    calls = {"n": 0}

    def fake_run(cmd, **kwargs):
        calls["n"] += 1
        return _FakeResult(1, stdout=b"Rate limited")

    monkeypatch.setattr(claude_cli.subprocess, "run", fake_run)
    monkeypatch.setenv("KTAXBENCH_RL_RETRIES", "3")
    r = ClaudeCLIClient("haiku", "claude-haiku-4-5").complete("sys", "p")
    assert r.text == ""
    assert "rc=1" in r.raw_meta["error"]
    assert calls["n"] == 4  # 1 + 3 retries


def test_non_ratelimit_error_no_retry(monkeypatch):
    # rate-limit 이 아닌 진짜 에러는 즉시 반환(재시도 안 함).
    _no_sleep(monkeypatch)
    calls = {"n": 0}

    def fake_run(cmd, **kwargs):
        calls["n"] += 1
        return _FakeResult(2, stderr=b"some other failure")

    monkeypatch.setattr(claude_cli.subprocess, "run", fake_run)
    r = ClaudeCLIClient("haiku", "claude-haiku-4-5").complete("sys", "p")
    assert "rc=2" in r.raw_meta["error"]
    assert calls["n"] == 1  # 재시도 없음
