"""Gemini CLI subprocess 어댑터 (M4+ R1 — ADR 0010).

GOOGLE_API_KEY/SDK 미사용 — `gemini -p` CLI subprocess만. 키 불필요(구독).
격리(ADR 0008/0010): 레포 밖 sandbox cwd + --approval-mode plan + --skip-trust.
"""
from __future__ import annotations

import os
import random
import subprocess
import time
import uuid
from pathlib import Path

from .base import Response

# home 트리 밖. env 로 override 가능.
_SANDBOX = Path(os.environ.get("KTAXBENCH_SANDBOX", "C:/ktaxbench-sandbox"))

# 서버측 일시적 동시성 제한
_RATE_LIMIT_MARKERS = (
    "rate limit", "temporarily limiting", "limiting requests", "overloaded", "529", "429", "quota",
)


def _is_rate_limited(text: str) -> bool:
    t = text.lower()
    return any(m in t for m in _RATE_LIMIT_MARKERS)


def _ensure_sandbox() -> str:
    """격리 cwd 보장(멱등)."""
    _SANDBOX.mkdir(parents=True, exist_ok=True)
    return str(_SANDBOX)


class GeminiCLIClient:
    """`gemini -p <prompt> --model <id>` 를 ModelClient 로 감싼 어댑터.

    isolated=True(기본): 레포 밖 sandbox cwd + 격리 플래그로 CLAUDE.md·MCP 오염 차단.
    """

    def __init__(self, name: str, model_id: str, timeout: int = 300,
                 isolated: bool = True):
        self.name = name
        self.model_id = model_id
        self.timeout = timeout
        self.isolated = isolated

    def complete(self, system: str, prompt: str) -> Response:
        model_id = os.environ.get("KTAXBENCH_GEMINI_MODEL", self.model_id)
        full_prompt = prompt
        if system:
            full_prompt = f"{system}\n\n{prompt}"

        cwd = _ensure_sandbox() if self.isolated else None
        retries = int(os.environ.get("KTAXBENCH_RL_RETRIES", "4"))
        base = float(os.environ.get("KTAXBENCH_RL_BACKOFF", "8"))
        t0 = time.perf_counter()

        for attempt in range(retries + 1):
            session_id = str(uuid.uuid4())
            executable = "gemini.cmd" if os.name == "nt" else "gemini"
            cmd = [executable, "-p", "", "-m", model_id, "-o", "text"]
            if self.isolated:
                cmd += [
                    "--approval-mode", "plan",
                    "--skip-trust",
                    "--session-id", session_id,
                ]
            # Strip IDE integration env vars to prevent directory mismatch / companion connection errors in sandbox
            env = os.environ.copy()
            for k in list(env.keys()):
                if k.startswith("GEMINI_CLI_IDE_") or k.startswith("VSCODE_"):
                    env.pop(k)
            env.pop("TERM_PROGRAM", None)
            env.pop("TERM_PROGRAM_VERSION", None)

            try:
                result = subprocess.run(
                    cmd,
                    input=full_prompt.encode("utf-8"),
                    capture_output=True,
                    timeout=self.timeout,
                    cwd=cwd,
                    env=env,
                )
            except subprocess.TimeoutExpired:
                return Response(text="", model=self.name,
                                latency_s=time.perf_counter() - t0,
                                raw_meta={"error": "timeout"})
            except FileNotFoundError:
                return Response(text="", model=self.name,
                                latency_s=time.perf_counter() - t0,
                                raw_meta={"error": "gemini CLI not found"})

            dt = time.perf_counter() - t0
            out = result.stdout.decode("utf-8", errors="replace").strip()
            err = result.stderr.decode("utf-8", errors="replace").strip()

            if result.returncode != 0:
                if _is_rate_limited(out + " " + err) and attempt < retries:
                    time.sleep(base * (2 ** attempt) + random.uniform(0, base))
                    continue
                return Response(text="", model=self.name, latency_s=dt,
                                raw_meta={"error": f"rc={result.returncode}: {(err or out)[:500]}"})

            return Response(
                text=out,
                model=self.name,
                latency_s=dt,
                raw_meta={"returncode": 0, "attempts": attempt + 1},
            )
