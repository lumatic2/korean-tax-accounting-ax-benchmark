#!/usr/bin/env python3
"""결과 JSONL → 공개 리더보드용 누수-안전 JSON (M4 step3.1).

holdout 순위 + 공개셋 별도 + holdout 문항 비노출(집계만). ADR 0009 / m4-public-sample-scope.

용법:
    python scripts/build_leaderboard_data.py "outputs/m3-rerun-101-20260611/*.jsonl" \\
        --data data/sample-questions-v0.1.jsonl --out outputs/leaderboard-public.json
"""
import glob
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ktaxbench.runlog import load_results  # noqa: E402
from ktaxbench.report import build_public_payload  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]


def _arg(args, name, default=None):
    return args[args.index(name) + 1] if name in args else default


def main() -> int:
    args = sys.argv[1:]
    data = _arg(args, "--data", "data/sample-questions-v0.1.jsonl")
    out = _arg(args, "--out", "outputs/leaderboard-public.json")
    pins_path = _arg(args, "--pins", str(REPO_ROOT / "config" / "leaderboard-pins.json"))
    inputs = [a for a in args if not a.startswith("--")
              and args[args.index(a) - 1] not in ("--data", "--out", "--pins")]

    files: list[str] = []
    for p in inputs:
        files += glob.glob(p)
    if not files:
        print("입력 결과 파일 없음")
        return 1

    records: list[dict] = []
    for f in files:
        records += load_results(f)

    # 문항 id → visibility 맵
    vis_map: dict[str, str] = {}
    for line in open(data, encoding="utf-8"):
        if line.strip():
            q = json.loads(line)
            vis_map[q["id"]] = q.get("visibility", "unknown")

    pin_overrides = {}
    if pins_path and Path(pins_path).exists():
        pin_overrides = json.loads(Path(pins_path).read_text(encoding="utf-8"))

    payload = build_public_payload(
        records,
        vis_map,
        meta={"source_files": sorted(Path(f).name for f in files)},
        pin_overrides=pin_overrides,
    )

    # ── 누수 가드 (커밋·배포 전 필수) ──
    blob = json.dumps(payload, ensure_ascii=False)
    holdout_ids = [qid for qid, v in vis_map.items() if v == "holdout"]
    leaked = [qid for qid in holdout_ids if qid in blob]
    assert not leaked, f"LEAK: holdout 문항 id가 공개 payload에 노출: {leaked[:5]}"
    assert "answer_text" not in blob, "LEAK: answer_text 노출"
    private_ids = [qid for qid, v in vis_map.items() if v == "private"]
    leaked_priv = [qid for qid in private_ids if qid in blob]
    assert not leaked_priv, f"LEAK: private 문항 id 노출: {leaked_priv[:5]}"

    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2),
                         encoding="utf-8")
    r = payload["ranking"]["report"]
    print(f"public leaderboard -> {out}")
    print(f"  ranking(holdout): {r['n_records']} records, {len(r['models'])} models, "
          f"spread={payload['ranking']['discrimination']['spread']}")
    print(f"  public_sample: {payload['public_sample']['report']['n_records']} records")
    print(f"  errors_public: {len(payload['errors_public'])}, "
          f"errors_holdout_agg: {payload['errors_holdout_agg']['by_type']}")
    print("  누수 가드 PASS (holdout/private id·answer_text 0)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
