"""report 결정론 테스트(fixture 기반, 풀런 없음)."""
from __future__ import annotations

from pathlib import Path

import json

from ktaxbench.runlog import load_results
from ktaxbench.report import (
    aggregate_results, build_public_payload, discrimination, error_cases,
    judge_failed, to_json, to_markdown,
)

_FIX = str(Path(__file__).resolve().parents[0] / "fixtures" / "sample_results.jsonl")


def _records():
    return load_results(_FIX)


def test_aggregate_models_and_avg():
    rep = aggregate_results(_records())
    assert rep["models"] == ["modelA", "modelB", "modelC"]
    assert rep["by_model"]["modelA"]["avg_total"] == 92.5
    assert rep["by_model"]["modelC"]["avg_total"] == 42.5
    # 분야별 분해
    assert rep["by_model"]["modelA"]["by_domain"]["vat"] == 95.0


def test_discrimination_ok():
    disc = discrimination(aggregate_results(_records()))
    assert disc["flag"] == "ok"
    assert disc["spread"] == 50.0


def test_discrimination_saturation_and_floor():
    high = [{"model": m, "error": None, "domain": "vat", "task_type": "calculation",
             "final": {"total": 90.0, "grade": "A", "per_dimension": {}, "flags": []}}
            for m in ("a", "b", "c")]
    assert discrimination(aggregate_results(high))["flag"] == "saturation"
    low = [{"model": m, "error": None, "domain": "vat", "task_type": "calculation",
            "final": {"total": 30.0, "grade": "D", "per_dimension": {}, "flags": []}}
           for m in ("a", "b", "c")]
    assert discrimination(aggregate_results(low))["flag"] == "floor"


def test_error_cases_found():
    errs = error_cases(_records())
    types = {e["type"] for e in errs}
    assert "hallucination" in types   # modelC unverified_citation
    assert "calc_error" in types      # modelC conclusion 0 on calculation
    assert "citation_error" in types  # modelC legal_basis 0 on citation


def test_judge_failed_detects_error_shapes():
    # 신 데이터: final.judge_error 마커
    assert judge_failed({"judge": {"scores": {}}, "final": {"total": 0.0, "judge_error": True}})
    # 구·신 공통: judge.error 키 (regrade/runner 가 박는 모양)
    assert judge_failed({"judge": {"error": "judge: judge 응답에 JSON 없음", "scores": {}},
                         "final": {"total": 0.0}})
    # 정상 레코드는 실패 아님
    assert not judge_failed({"judge": {"scores": {"legal_basis": 20}}, "final": {"total": 90.0}})
    assert not judge_failed({"final": {"total": 70.0}})  # judge 없는 코드채점 전용


def test_aggregate_excludes_judge_failed_records():
    # R4 선행 디버그 재현: judge 파싱 실패 → final.total 0.0 은 미채점이지 정당한 0점이 아니다.
    # 집계에 포함되면 평균을 끌어내려 +24.8 같은 아티팩트를 만든다 → 반드시 제외.
    good = {"model": "gpt", "error": None, "domain": "vat", "mode": "closed_book",
            "task_type": "risk_analysis",
            "judge": {"scores": {"conclusion_accuracy": 24}, "memo": {}, "fatal_flags": []},
            "final": {"total": 96.0, "grade": "A", "per_dimension": {}, "flags": []}}
    # judge 가 JSON 실패 → scores={} → combine 이 0.0/D 로 둔갑(버그 입력 모양)
    failed = {"model": "gpt", "error": None, "domain": "vat", "mode": "closed_book",
              "task_type": "risk_analysis",
              "judge": {"error": "judge: judge 응답에 JSON 없음", "scores": {}, "fatal_flags": []},
              "final": {"total": 0.0, "grade": "D", "judge_error": True,
                        "per_dimension": {"conclusion_accuracy": 0.0}, "flags": []}}
    rep = aggregate_results([good, failed])
    # 실패 레코드 제외 → n=1, 평균 96.0 (0.0 혼입 시 48.0 이 됐을 것)
    assert rep["by_model"]["gpt"]["n"] == 1
    assert rep["by_model"]["gpt"]["avg_total"] == 96.0
    # n_errors 에 judge 실패가 잡힌다
    assert rep["n_errors"] == 1


def test_to_markdown_contains_models():
    rep = aggregate_results(_records())
    md = to_markdown(rep, discrimination(rep), error_cases(_records()))
    assert "K-TaxBench 진단 리포트" in md
    assert "modelA" in md
    assert "변별" in md


def _payload():
    recs = _records()
    rep = aggregate_results(recs)
    return to_json(rep, discrimination(rep), error_cases(recs),
                   {"n_records": rep["n_records"], "models": rep["models"]})


def test_to_json_structure():
    p = _payload()
    assert p["schema_version"] == "leaderboard-v0.1"
    assert p["discrimination"]["spread"] == 50.0
    assert p["discrimination"]["flag"] == "ok"
    assert isinstance(p["discrimination"]["range"], list)  # tuple → list 직렬화
    assert p["report"]["by_model"]["modelA"]["avg_total"] == 92.5
    assert p["meta"]["models"] == ["modelA", "modelB", "modelC"]


def test_to_json_deterministic_and_serializable():
    # 같은 입력 → 같은 직렬화(결정론)
    a = json.dumps(_payload(), ensure_ascii=False, sort_keys=True)
    b = json.dumps(_payload(), ensure_ascii=False, sort_keys=True)
    assert a == b


def test_to_json_no_answer_text_leak():
    # 집계 payload엔 raw 답변 텍스트가 새지 않는다(holdout 보호의 1차선)
    assert "answer_text" not in json.dumps(_payload(), ensure_ascii=False)


def _public_records():
    # 합성 레코드: hq-* = holdout, pq-* = public_sample
    def rec(qid, model, total, tt="citation", flags=None, per=None):
        return {"question_id": qid, "model": model, "error": None,
                "domain": "vat", "mode": "closed_book", "task_type": tt,
                "final": {"total": total, "grade": "A" if total >= 85 else "D",
                          "per_dimension": per or {}, "flags": flags or []}}
    recs = [
        rec("hq-1", "opus", 90.0), rec("hq-2", "opus", 88.0),
        rec("hq-1", "haiku", 40.0,
            flags=["unverified_citation"], per={"legal_basis": 0}),
        rec("pq-1", "opus", 95.0),
        rec("pq-1", "haiku", 30.0, flags=["fake_source"], per={"legal_basis": 0}),
    ]
    vmap = {"hq-1": "holdout", "hq-2": "holdout", "pq-1": "public_sample"}
    return recs, vmap


def test_public_payload_no_holdout_id_leak():
    recs, vmap = _public_records()
    p = build_public_payload(recs, vmap)
    blob = json.dumps(p, ensure_ascii=False)
    # holdout 문항 id는 공개 payload 어디에도 없어야
    assert "hq-1" not in blob and "hq-2" not in blob
    # 공개셋 문항 id는 오류 사례에 노출 가능
    assert "pq-1" in blob
    assert "answer_text" not in blob


def test_public_payload_ranking_uses_holdout():
    recs, vmap = _public_records()
    p = build_public_payload(recs, vmap)
    assert p["ranking"]["basis"] == "holdout"
    # 순위 집계는 holdout 레코드만(opus 2 + haiku 1 = 3)
    assert p["ranking"]["report"]["n_records"] == 3
    # 공개셋은 별도(opus 1 + haiku 1 = 2)
    assert p["public_sample"]["report"]["n_records"] == 2
    # holdout 오류는 type별 카운트만(citation_error: haiku hq-1)
    assert p["errors_holdout_agg"]["by_type"].get("citation_error") == 1
    # 공개셋 오류는 id 포함(haiku pq-1 hallucination)
    assert any(e["id"] == "pq-1" for e in p["errors_public"])


def test_public_payload_version_pins():
    recs, vmap = _public_records()
    # 합성 레코드에 scaffold 부여
    for r in recs:
        r["scaffold"] = {"prompt_version": "v1", "judge_model": "claude-sonnet-4-6"}
    p = build_public_payload(recs, vmap)
    assert p["version_pins"]["opus"]["prompt_version"] == ["v1"]
    assert p["version_pins"]["opus"]["judge_model"] == ["claude-sonnet-4-6"]
    assert "closed_book" in p["version_pins"]["opus"]["modes"]
