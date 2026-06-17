"""canary 삽입 회귀(M5 step0) — 멱등·hash 불변·전역 sentinel·전 문항 canary."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from insert_canary import insert_canary, _PREFIX, _GLOBAL_PREFIX  # noqa: E402
from hash_question import content_hash  # noqa: E402


def _rows():
    return [
        {"id": "q1", "question": "부가가치세 세율은?",
         "answer": {"final_answer": "100분의 10"}, "hash": "sha256:x"},
        {"id": "q2", "question": "법인세 신고기한은?",
         "answer": {"final_answer": "사업연도 종료일이 속하는 달의 말일부터 3개월"},
         "hash": "sha256:y"},
    ]


def test_all_questions_get_canary():
    out, _ = insert_canary(_rows(), seed=1)
    assert all(q["canary"].startswith(_PREFIX) for q in out)
    assert len(out) == 2


def test_hash_invariant_after_canary():
    rows = _rows()
    before = [content_hash(q) for q in rows]
    out, _ = insert_canary(rows, seed=1)
    after = [content_hash(q) for q in out]
    assert before == after            # canary 가 hash 산출에 안 들어감


def test_idempotent_per_question_canary():
    out1, _ = insert_canary(_rows(), seed=1)
    out2, _ = insert_canary(out1, seed=1)   # 이미 canary 있는 입력 재실행
    assert [q["canary"] for q in out1] == [q["canary"] for q in out2]  # 보존(멱등)


def test_global_sentinel_format():
    _, sentinel = insert_canary(_rows(), seed=1)
    assert sentinel.startswith(_GLOBAL_PREFIX)
    assert len(sentinel) > len(_GLOBAL_PREFIX)


def test_seed_deterministic():
    a, sa = insert_canary(_rows(), seed=7)
    b, sb = insert_canary(_rows(), seed=7)
    assert [q["canary"] for q in a] == [q["canary"] for q in b]  # 같은 시드 → 같은 canary
    assert sa == sb


def test_does_not_mutate_input():
    rows = _rows()
    insert_canary(rows, seed=1)
    assert "canary" not in rows[0]    # 입력 dict 불변(복사본에만 삽입)
