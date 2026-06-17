"""문항 JSONL 로더. 원본 dict 그대로 반환(불변 입력 원칙)."""
from __future__ import annotations

import json

from .schema import is_valid


def load_questions(
    path: str,
    *,
    domain: str | None = None,
    task_type: str | None = None,
    visibility: str | None = None,
    status: str | None = None,
    validate: bool = False,
) -> list[dict]:
    """JSONL(한 줄 1문항)을 로드해 필터(AND) 적용. validate=True면 하드위반 없는 문항만."""
    out: list[dict] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            obj = json.loads(line)
            if domain is not None and obj.get("domain") != domain:
                continue
            if task_type is not None and obj.get("task_type") != task_type:
                continue
            if visibility is not None and obj.get("visibility") != visibility:
                continue
            if status is not None and obj.get("status") != status:
                continue
            if validate and not is_valid(obj):
                continue
            out.append(obj)
    return out
