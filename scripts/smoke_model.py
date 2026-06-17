#!/usr/bin/env python3
"""모델 호출 smoke (수동 — 구독 소모, CI 아님).

용법: python scripts/smoke_model.py [--model claude-haiku-4-5]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ktaxbench.models.registry import get_model  # noqa: E402


def main() -> int:
    args = sys.argv[1:]
    model = "claude-haiku-4-5"
    if "--model" in args:
        model = args[args.index("--model") + 1]
    client = get_model(model)
    resp = client.complete("You are concise.", "2+2=? 숫자만 답하라.")
    print(f"model={resp.model} latency={resp.latency_s:.2f}s")
    print("text:", resp.text[:200])
    print("meta:", resp.raw_meta)
    return 0 if resp.text else 1


if __name__ == "__main__":
    raise SystemExit(main())
