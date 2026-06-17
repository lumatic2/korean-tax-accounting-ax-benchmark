"""Google Gemini 어댑터 (M3 — step8). SDK·키는 lazy.

`uv sync --extra providers` 후 GEMINI_API_KEY/GOOGLE_API_KEY(.env)로 동작.
"""
from __future__ import annotations

import time

from .base import Response


class GoogleClient:
    def __init__(self, name: str, model_id: str, temperature: float = 0.0):
        self.name = name
        self.model_id = model_id
        self.temperature = temperature

    def complete(self, system: str, prompt: str) -> Response:
        t0 = time.perf_counter()
        try:
            from google import genai  # lazy
            from google.genai import types
            client = genai.Client()  # GEMINI_API_KEY / GOOGLE_API_KEY
            r = client.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system,
                    temperature=self.temperature,
                ),
            )
            return Response((r.text or "").strip(), self.name,
                            time.perf_counter() - t0, {"provider": "google"})
        except Exception as e:
            return Response("", self.name, time.perf_counter() - t0,
                            {"error": f"google: {e}"})
