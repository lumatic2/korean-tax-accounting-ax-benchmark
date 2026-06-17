"""OpenAI 어댑터 (M3 — step8). SDK·키는 lazy(호출 시점) — 미설치/미키여도 import·생성 가능.

`uv sync --extra providers` 후 OPENAI_API_KEY(.env)로 동작.
"""
from __future__ import annotations

import time

from .base import Response


class OpenAIClient:
    def __init__(self, name: str, model_id: str, temperature: float = 0.0):
        self.name = name
        self.model_id = model_id
        self.temperature = temperature

    def complete(self, system: str, prompt: str) -> Response:
        t0 = time.perf_counter()
        try:
            from openai import OpenAI  # lazy — 패키지 없으면 여기서만 실패
            client = OpenAI()  # OPENAI_API_KEY 환경변수
            r = client.chat.completions.create(
                model=self.model_id,
                temperature=self.temperature,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
            )
            text = (r.choices[0].message.content or "").strip()
            return Response(text, self.name, time.perf_counter() - t0,
                            {"provider": "openai"})
        except Exception as e:
            return Response("", self.name, time.perf_counter() - t0,
                            {"error": f"openai: {e}"})
