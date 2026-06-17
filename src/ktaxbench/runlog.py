"""결과 영속화 — RunRecord → JSONL (버전핀 포함). timestamp는 호출자 주입."""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path


def _record_to_dict(rec) -> dict:
    return asdict(rec) if hasattr(rec, "__dataclass_fields__") else dict(rec)


def write_results(records: list, out_dir: str = "outputs/results", *,
                  model: str = "model", timestamp: str = "run") -> str:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{model}_{timestamp}.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(_record_to_dict(rec), ensure_ascii=False) + "\n")
    return str(path)


def load_results(path: str) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows
