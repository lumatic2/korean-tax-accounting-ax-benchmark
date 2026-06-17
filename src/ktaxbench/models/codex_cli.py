"""Codex CLI subprocess 어댑터 (M4+ R1 — ADR 0010).

OPENAI_API_KEY/SDK 미사용 — `codex exec` CLI subprocess만. 키 불필요(구독).
격리(ADR 0008/0010): 레포 밖 sandbox cwd + --ignore-user-config/rules + skip-git-repo-check.
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


class CodexCLIClient:
    """`codex exec --model <id>` 를 ModelClient 로 감싼 어댑터.

    isolated=True(기본): 레포 밖 sandbox cwd + 격리 플래그로 CLAUDE.md·MCP 오염 차단.
    """

    def __init__(self, name: str, model_id: str, timeout: int = 300,
                 isolated: bool = True):
        self.name = name
        self.model_id = model_id
        self.timeout = timeout
        self.isolated = isolated

    def complete(self, system: str, prompt: str) -> Response:
        _ensure_sandbox()
        tmp_name = f"codex_out_{uuid.uuid4().hex}.txt"
        tmp_path = _SANDBOX / tmp_name

        executable = "codex.cmd" if os.name == "nt" else "codex"
        cmd = [executable, "exec", "-m", self.model_id, "--ephemeral", "-o", str(tmp_path)]
        if self.isolated:
            cmd += [
                "-s", "read-only",
                "--ignore-user-config",
                "--ignore-rules",
                "--skip-git-repo-check",
                "-C", str(_SANDBOX),
            ]

        full_prompt = prompt
        if system:
            full_prompt = f"{system}\n\n{prompt}"

        cwd = str(_SANDBOX) if self.isolated else None
        retries = int(os.environ.get("KTAXBENCH_RL_RETRIES", "4"))
        base = float(os.environ.get("KTAXBENCH_RL_BACKOFF", "8"))
        t0 = time.perf_counter()

        for attempt in range(retries + 1):
            try:
                result = subprocess.run(
                    cmd,
                    input=full_prompt.encode("utf-8"),
                    capture_output=True,
                    timeout=self.timeout,
                    cwd=cwd,
                )
            except subprocess.TimeoutExpired:
                if tmp_path.exists():
                    try:
                        tmp_path.unlink()
                    except Exception:
                        pass
                return Response(text="", model=self.name,
                                latency_s=time.perf_counter() - t0,
                                raw_meta={"error": "timeout"})
            except FileNotFoundError:
                return Response(text="", model=self.name,
                                latency_s=time.perf_counter() - t0,
                                raw_meta={"error": "codex CLI not found"})

            dt = time.perf_counter() - t0
            out = result.stdout.decode("utf-8", errors="replace").strip()
            err = result.stderr.decode("utf-8", errors="replace").strip()

            if result.returncode != 0:
                if tmp_path.exists():
                    try:
                        tmp_path.unlink()
                    except Exception:
                        pass
                if _is_rate_limited(out + " " + err) and attempt < retries:
                    time.sleep(base * (2 ** attempt) + random.uniform(0, base))
                    continue
                return Response(text="", model=self.name, latency_s=dt,
                                raw_meta={"error": f"rc={result.returncode}: {(err or out)[:500]}"})

            # 성공 시 파일에서 최종 답변 읽기
            text = ""
            if tmp_path.exists():
                try:
                    text = tmp_path.read_text(encoding="utf-8").strip()
                    tmp_path.unlink()
                except Exception as e:
                    return Response(text="", model=self.name, latency_s=dt,
                                    raw_meta={"error": f"failed to read output file: {e}"})
            else:
                # 파일이 없을 경우 stdout 백업 시도
                text = out

            return Response(
                text=text,
                model=self.name,
                latency_s=dt,
                raw_meta={"returncode": 0, "attempts": attempt + 1},
            )
