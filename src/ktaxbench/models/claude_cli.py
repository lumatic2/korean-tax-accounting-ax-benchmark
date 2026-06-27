"""Claude CLI subprocess 어댑터 (M2 단독 — ADR 0002).

vendored from tax-agent/src/tax_agent/agent/llm/adapter.py (2026-06-02), trimmed (ADR 0001).
ANTHROPIC_API_KEY/SDK 미사용 — `claude -p` CLI subprocess만. 키 불필요(구독).

격리(ADR 0008): 후보·judge 를 환경에서 분리한다. 레포 cwd 에서 그냥 `claude -p` 를 돌리면
후보가 ① 레포 CLAUDE.md(judge 규약·루브릭)를 읽고 자신을 *문항 검증자*로 프레이밍, ② 전역
law-mcp 로 우회 조회해 eval ReAct `[도구]` 를 안 써서 forced_tool_unmet 오탐을 낸다. 막는 법:
레포·home 밖 빈 sandbox cwd(→ CLAUDE.md 미발견) + --strict-mcp-config(→ 모든 MCP 차단).
"""
from __future__ import annotations

import os
import random
import subprocess
import time
from pathlib import Path

from .base import Response

# home 트리 밖(전역/레포 지시 파일 발견까지 차단). env 로 override 가능.
_SANDBOX = Path(os.environ.get("KTAXBENCH_SANDBOX", "C:/ktaxbench-sandbox"))

# 서버측 일시적 동시성 제한(구독 쿼터 아님) — claude CLI 가 rc!=0 + 이 마커를 stdout/stderr 로 낸다.
_RATE_LIMIT_MARKERS = (
    "rate limit", "temporarily limiting", "limiting requests", "overloaded", "529",
)


def _is_rate_limited(text: str) -> bool:
    t = text.lower()
    return any(m in t for m in _RATE_LIMIT_MARKERS)


def _ensure_sandbox() -> str:
    """격리 cwd 보장(멱등). 레포·home 밖의 빈 디렉토리 — CLAUDE.md 자동탐색이 닿지 않는다."""
    _SANDBOX.mkdir(parents=True, exist_ok=True)
    return str(_SANDBOX)


class ClaudeCLIClient:
    """`claude -p --model <id>` 를 ModelClient 로 감싼 어댑터.

    isolated=True(기본): 레포 밖 sandbox cwd + --strict-mcp-config 로 CLAUDE.md·MCP 오염 차단.
    """

    def __init__(self, name: str, model_id: str, timeout: int = 300,
                 isolated: bool = True):
        self.name = name
        self.model_id = model_id
        self.timeout = timeout
        self.isolated = isolated

    def complete(self, system: str, prompt: str) -> Response:
        cmd = ["claude", "-p", "--model", self.model_id]
        if self.isolated:
            cmd.append("--strict-mcp-config")  # law-mcp 등 모든 MCP 차단
        if system:
            cmd += ["--append-system-prompt", system]
        cwd = _ensure_sandbox() if self.isolated else None
        # 서버 일시 제한(rc!=0 + rate-limit 마커)은 지수 backoff 로 재시도 — transient 가 eval 을 오염시키지 않게.
        retries = int(os.environ.get("KTAXBENCH_RL_RETRIES", "4"))
        base = float(os.environ.get("KTAXBENCH_RL_BACKOFF", "8"))
        t0 = time.perf_counter()
        for attempt in range(retries + 1):
            try:
                result = subprocess.run(
                    cmd,
                    input=prompt.encode("utf-8"),
                    capture_output=True,
                    timeout=self.timeout,
                    cwd=cwd,
                )
            except subprocess.TimeoutExpired:
                return Response(text="", model=self.name,
                                latency_s=time.perf_counter() - t0,
                                raw_meta={"error": "timeout"})
            except FileNotFoundError:
                return Response(text="", model=self.name,
                                latency_s=time.perf_counter() - t0,
                                raw_meta={"error": "claude CLI not found"})
            dt = time.perf_counter() - t0
            if result.returncode != 0:
                out = result.stdout.decode("utf-8", errors="replace").strip()
                err = result.stderr.decode("utf-8", errors="replace").strip()
                # 메시지는 stdout 으로 나오기도 함 → 둘 다 검사
                if _is_rate_limited(out + " " + err) and attempt < retries:
                    time.sleep(base * (2 ** attempt) + random.uniform(0, base))  # jitter 로 thundering herd 완화
                    continue
                return Response(text="", model=self.name, latency_s=dt,
                                raw_meta={"error": f"rc={result.returncode}: {(err or out)[:500]}"})
            return Response(
                text=result.stdout.decode("utf-8", errors="replace").strip(),
                model=self.name,
                latency_s=dt,
                raw_meta={"returncode": 0, "attempts": attempt + 1},
            )
