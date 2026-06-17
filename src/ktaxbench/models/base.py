"""모델 클라이언트 프로토콜 — 모든 provider가 구현하는 공통 경계(ADR 0002)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class Response:
    text: str
    model: str
    latency_s: float
    raw_meta: dict = field(default_factory=dict)


@runtime_checkable
class ModelClient(Protocol):
    name: str

    def complete(self, system: str, prompt: str) -> Response:
        """system+prompt로 1회 완성. 실패해도 예외 대신 Response(text='', raw_meta={'error':...})."""
        ...
