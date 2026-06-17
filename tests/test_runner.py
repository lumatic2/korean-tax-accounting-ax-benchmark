"""runner 결정론 테스트 — stub 모델 주입(네트워크·LLM 없음)."""
from __future__ import annotations

import json
from pathlib import Path

from ktaxbench.loader import load_questions
from ktaxbench.models.base import Response
from ktaxbench.runner import run_one, run_batch
from ktaxbench.runlog import write_results, load_results

_DATA = str(Path(__file__).resolve().parents[1] / "data" / "sample-questions-v0.1.jsonl")
_BY_ID = {q["id"]: q for q in load_questions(_DATA)}


class _Stub:
    def __init__(self, name: str, text: str):
        self.name = name
        self._t = text

    def complete(self, system: str, prompt: str) -> Response:
        return Response(self._t, self.name, 0.0, {"returncode": 0})


_CAND_ANSWER = ("기본한도 1,200만원 + 수입금액별 7,000만원 = 한도 8,200만원, "
                "지출 9,000만원 중 800만원 손금불산입 (법인세법 제25조).")
_JUDGE_JSON = ('{"scores": {"legal_basis": 15, "fact_handling": 10, '
               '"practicality": 10, "clarity": 5}, "memo": {}, "fatal_flags": []}')


def _run(q):
    return run_one(q, "closed_book", "claude-haiku-4-5",
                   client=_Stub("cand", _CAND_ANSWER),
                   judge_model_name="claude-sonnet-4-6",
                   judge_client=_Stub("judge", _JUDGE_JSON))


def test_run_one_calculation_full():
    rec = _run(_BY_ID["ktb-corp-tax-0003"])
    assert rec.error is None
    assert rec.scaffold["prompt_version"] == "v1"
    assert rec.question_hash.startswith("sha256:")
    assert rec.final["total"] == 100.0
    assert rec.final["grade"] == "A"


def test_runner_determinism():
    q = _BY_ID["ktb-corp-tax-0003"]
    r1, r2 = _run(q), _run(q)
    assert r1.final == r2.final
    assert [(s.dimension, s.points) for s in r1.code_scores] == \
           [(s.dimension, s.points) for s in r2.code_scores]


def test_run_batch_iterates_modes():
    qs = [_BY_ID["ktb-corp-tax-0003"], _BY_ID["ktb-vat-0003"]]
    recs = run_batch(qs, ["closed_book"], "claude-haiku-4-5",
                     client=_Stub("cand", _CAND_ANSWER),
                     judge_model_name="claude-sonnet-4-6",
                     judge_client=_Stub("judge", _JUDGE_JSON))
    assert len(recs) == 2
    assert all(r.mode == "closed_book" for r in recs)


def test_run_batch_parallel_matches_sequential():
    """병렬(max_workers>1)과 순차(=1) 결과가 순서·내용 모두 동일 — 재현성 보장."""
    qs = [_BY_ID["ktb-corp-tax-0003"], _BY_ID["ktb-vat-0003"], _BY_ID["ktb-corp-tax-0001"]]
    kw = dict(client=_Stub("cand", _CAND_ANSWER),
              judge_model_name="claude-sonnet-4-6",
              judge_client=_Stub("judge", _JUDGE_JSON))
    seq = run_batch(qs, ["closed_book"], "claude-haiku-4-5", max_workers=1, **kw)
    par = run_batch(qs, ["closed_book"], "claude-haiku-4-5", max_workers=4, **kw)
    assert [r.question_id for r in seq] == [r.question_id for r in par]
    assert [r.final for r in seq] == [r.final for r in par]


def test_judge_non_json_flagged_not_silent_zero():
    """judge 가 비-JSON 응답 → 미채점으로 flag(원문 보존·집계제외 마커), 예외 미발생.

    회귀: 과거엔 빈 scores 가 total=0.0/D 로 둔갑해 정당한 0점과 구별 불가했다
    ([[judge-failure-silent-zero]], R4 선행 디버그).
    """
    bad_judge = _Stub("judge", "죄송합니다. 채점을 진행할 수 없습니다. (세션 한도)")
    rec = run_one(_BY_ID["ktb-corp-tax-0003"], "closed_book", "claude-haiku-4-5",
                  client=_Stub("cand", _CAND_ANSWER),
                  judge_model_name="claude-sonnet-4-6", judge_client=bad_judge)
    assert rec.error is None                      # 후보 답안은 정상 — 런 에러 아님
    assert rec.judge.get("error")                 # judge 실패 사유 기록
    assert "세션 한도" in (rec.judge.get("raw_response") or "")  # 원문 보존(왜 실패했나)
    assert rec.final.get("judge_error") is True   # 집계 제외 마커
    from ktaxbench.report import judge_failed, aggregate_results
    assert judge_failed(rec.__dict__) is True
    # 집계에서 제외 → 평균 오염 없음
    good = run_one(_BY_ID["ktb-corp-tax-0003"], "closed_book", "claude-haiku-4-5",
                   client=_Stub("cand", _CAND_ANSWER),
                   judge_model_name="claude-sonnet-4-6", judge_client=_Stub("judge", _JUDGE_JSON))
    rep = aggregate_results([good.__dict__, rec.__dict__])
    assert rep["by_model"]["claude-haiku-4-5"]["n"] == 1  # 실패 제외


def test_model_error_recorded_not_raised():
    class _Boom:
        name = "boom"
        def complete(self, system, prompt):
            return Response("", "boom", 0.0, {"error": "rc=1: boom"})

    rec = run_one(_BY_ID["ktb-corp-tax-0003"], "closed_book", "claude-haiku-4-5",
                  client=_Boom())
    assert rec.error is not None
    assert rec.answer_text == ""


def test_runlog_roundtrip(tmp_path):
    rec = _run(_BY_ID["ktb-corp-tax-0003"])
    path = write_results([rec], str(tmp_path), model="m", timestamp="t")
    rows = load_results(path)
    assert rows[0]["question_id"] == "ktb-corp-tax-0003"
    assert rows[0]["final"]["total"] == 100.0
    # JSONL 직렬화 가능(버전핀 포함)
    assert json.loads(json.dumps(rows[0]))["scaffold"]["prompt_version"] == "v1"
