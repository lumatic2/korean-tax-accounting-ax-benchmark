"""judge 강건화 회귀(M6 step0) — 코드펜스·trailing prose·중첩 객체 파싱 + 비-JSON 미채점 유지.

세션11 silent-0 디버그 후속: 호출실패 *정식화*(미채점 분리)는 됐고, 여기선 파서/프롬프트
강건화로 *발생률*을 낮춘다. 진짜 비-JSON 은 여전히 error·raw_response 로 빠져야 한다.
"""
from __future__ import annotations

import pytest

from ktaxbench.models.base import Response
from ktaxbench.grading.judge import (
    parse_judge_json, _extract_json_object, build_judge_prompt, judge_answer,
)

_VALID = '{"scores": {"legal_basis": 30}, "memo": {"주요오류": "없음"}, "fatal_flags": []}'


def test_parse_strips_code_fence():
    txt = "```json\n" + _VALID + "\n```"
    data = parse_judge_json(txt)
    assert data["scores"]["legal_basis"] == 30


def test_parse_trailing_prose_after_object():
    # greedy '\\{.*\\}' 가 두 번째 '}' 까지 물어 깨지던 케이스
    txt = _VALID + " 이상으로 채점을 마칩니다. {참고: 추가 없음}"
    data = parse_judge_json(txt)
    assert data["scores"]["legal_basis"] == 30
    assert data["fatal_flags"] == []


def test_parse_nested_object_in_memo():
    txt = '머리말\n{"scores": {"x": 5}, "memo": {"세부": {"a": 1, "b": 2}}, "fatal_flags": []}'
    data = parse_judge_json(txt)
    assert data["memo"]["세부"]["b"] == 2


def test_extract_ignores_braces_inside_strings():
    txt = '{"memo": {"주요오류": "식 {x}+{y} 오류"}, "scores": {}, "fatal_flags": []}'
    obj = _extract_json_object(txt)
    assert obj == txt  # 문자열 내부 중괄호에 깊이 카운팅이 안 물림


def test_parse_non_json_still_raises():
    with pytest.raises(ValueError):
        parse_judge_json("죄송합니다. JSON 을 생성할 수 없습니다.")


def test_prompt_forbids_fence_and_prose():
    system, _ = build_judge_prompt({"task_type": "citation", "answer": {}, "rubric": {}}, "ans")
    assert "코드펜스" in system
    assert "JSON" in system


class _FixedClient:
    """미리 정한 응답들을 순서대로 반환하는 가짜 judge client."""
    def __init__(self, texts):
        self.name = "fake-judge"
        self._texts = list(texts)
        self.calls = 0

    def complete(self, system, prompt):
        t = self._texts[min(self.calls, len(self._texts) - 1)]
        self.calls += 1
        return Response(text=t, model=self.name, latency_s=0.0)


def _q():
    return {"task_type": "citation", "answer": {"final_answer": "x", "key_points": []},
            "rubric": {"fatal_errors": []}}


def test_judge_answer_recovers_fenced_json():
    client = _FixedClient(["```json\n" + _VALID + "\n```"])
    jr = judge_answer(_q(), "후보", judge_model_name="J", candidate_model_name="C", client=client)
    assert jr.error is None
    assert jr.scores["legal_basis"] == 30
    assert client.calls == 1  # 1회 만에 파싱 성공(재촉 불필요)


def test_judge_answer_non_json_flags_uncscored():
    # 두 번 다 비-JSON → error·raw_response 채워진 미채점(silent-0 아님)
    client = _FixedClient(["설명만 합니다", "여전히 설명입니다"])
    jr = judge_answer(_q(), "후보", judge_model_name="J", candidate_model_name="C", client=client)
    assert jr.error is not None
    assert jr.scores == {}
    assert jr.raw_response  # 원문 보존(사후 진단)
    assert client.calls == 2  # 재촉까지 시도
