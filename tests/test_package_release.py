"""릴리스 번들 패키징 회귀(M5 step1) — 4파일·카운트·누수가드·sentinel 박제."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from package_release import write_bundle, build_manifest, _gate  # noqa: E402
from insert_canary import insert_canary  # noqa: E402


def _pub_row(qid, domain="vat", tt="citation", diff="medium"):
    return {"id": qid, "domain": domain, "task_type": tt, "difficulty": diff,
            "visibility": "public_sample", "status": "internal_reviewed",
            "license": {"public_release_allowed": True},
            "question": f"q-{qid}", "answer": {"final_answer": f"a-{qid}"}}


def test_bundle_writes_four_files(tmp_path):
    rows, sentinel = insert_canary([_pub_row("vat-1"), _pub_row("corp-1", "corp")], seed=1)
    write_bundle(rows, sentinel, str(tmp_path), "2026-06-14", "1.0")
    for name in ("release.jsonl", "MANIFEST.json", "README.md", "LICENSE"):
        assert (tmp_path / name).exists(), name


def test_manifest_count_matches_jsonl(tmp_path):
    rows, sentinel = insert_canary([_pub_row(f"q-{i}") for i in range(5)], seed=2)
    m = write_bundle(rows, sentinel, str(tmp_path), "2026-06-14", "1.0")
    n_lines = sum(1 for l in open(tmp_path / "release.jsonl", encoding="utf-8") if l.strip())
    assert m["n_questions"] == 5 == n_lines


def test_readme_embeds_sentinel(tmp_path):
    rows, sentinel = insert_canary([_pub_row("vat-1")], seed=1)
    write_bundle(rows, sentinel, str(tmp_path), "2026-06-14", "1.0")
    readme = (tmp_path / "README.md").read_text(encoding="utf-8")
    assert sentinel in readme


def test_gate_blocks_holdout_leak():
    leaked = _pub_row("hold-1")
    leaked["visibility"] = "holdout"        # 누수 시도
    g = _gate([_pub_row("vat-1"), leaked])
    assert not g["passed"]
    assert "hold-1" in g["leak_non_public_sample"]


def test_gate_blocks_license_not_allowed():
    bad = _pub_row("vat-2")
    bad["license"]["public_release_allowed"] = False
    g = _gate([bad])
    assert not g["passed"]
    assert "vat-2" in g["license_not_allowed"]


def test_write_bundle_raises_on_gate_fail(tmp_path):
    leaked = _pub_row("hold-1")
    leaked["visibility"] = "holdout"
    try:
        write_bundle([leaked], "S", str(tmp_path), "2026-06-14", "1.0")
        assert False, "게이트 FAIL 인데 번들이 써짐"
    except AssertionError as e:
        assert "게이트" in str(e) or "gate" in str(e).lower()


def test_manifest_hashes_present(tmp_path):
    rows, sentinel = insert_canary([_pub_row("vat-1"), _pub_row("corp-1", "corp")], seed=1)
    m = build_manifest(rows, sentinel, "2026-06-14", "1.0")
    assert set(m["hashes"].keys()) == {"vat-1", "corp-1"}
    assert all(h.startswith("sha256:") for h in m["hashes"].values())
