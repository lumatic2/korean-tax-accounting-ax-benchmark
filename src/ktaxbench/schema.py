"""문항 스키마 검증 — docs/benchmark-schema.md v0.1 의 코드판(SSOT는 그 문서).

표준 라이브러리만 사용(pydantic 등 신규 의존성 금지 — ADR 0001).
해시 산출은 재구현하지 않고 scripts/hash_question.py 의 content_hash 를 재사용한다.

검증은 두 단계로 나뉜다:
- **에러(violations)**: 구조·enum·무결성 위반. 항상 막는다.
- **경고(warnings)**: 완성도 미달. status가 검수 단계(internal_reviewed+)면 에러로 승격.
  draft는 작업 중이므로 경고로 둔다 — M1 게이트(검수분만 완성 강제)와 일치.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# scripts/hash_question.py 의 content_hash 재사용 (해시 기준 SSOT — 재구현 금지)
_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPTS = _REPO_ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
try:
    from hash_question import content_hash as _content_hash
except Exception:  # pragma: no cover - 해시 스크립트 부재 시 형식 검사만
    _content_hash = None

# ── enum (docs/benchmark-schema.md 와 정확히 일치) ──────────────────────────
DOMAINS = {
    "vat", "corp_tax", "income_tax", "basic_tax_law", "local_tax",
    "accounting", "audit", "commercial_law", "mixed",
}
TASK_TYPES = {
    "multiple_choice", "short_answer", "calculation", "case_reasoning",
    "citation", "risk_analysis", "agent_workflow",
}
VISIBILITIES = {"public_sample", "private", "holdout"}
STATUSES = {"draft", "internal_reviewed", "expert_reviewed", "retired"}
BENCHMARK_MODES = {"closed_book", "rag", "agent", "agent_forced"}
DIFFICULTIES = {"easy", "medium", "hard", "expert"}
SOURCE_TYPES = {
    "statute", "regulation", "ruling", "case_law", "tax_tribunal",
    "exam", "standard", "practice_case", "secondary",
}
# 외부 권위(법령·판례·기준서 등) — 근거로 인정되는 출처 타입 (Judge 규약)
AUTHORITATIVE_SOURCE_TYPES = {
    "statute", "regulation", "ruling", "case_law", "tax_tribunal", "standard",
}
# 완성도 규칙을 에러로 승격하는 상태(검수 단계)
REVIEWED_STATUSES = {"internal_reviewed", "expert_reviewed"}

REQUIRED_TOP = [
    "id", "version", "status", "visibility", "language", "jurisdiction",
    "benchmark_mode", "domain", "task_type", "difficulty", "time_basis",
    "question", "answer", "rubric", "sources", "tags", "review", "license", "hash",
]

# id 의 domain 세그먼트는 하이픈 표기(corp-tax), domain 필드는 언더스코어(corp_tax)
_ID_RE = re.compile(r"^ktb-([a-z-]+)-(\d{4})$")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


def lint_question(obj: dict) -> tuple[list[str], list[str]]:
    """문항 1개 검사. (errors, warnings) 반환. 예외를 던지지 않는다."""
    errors: list[str] = []
    warnings: list[str] = []

    # 1) 필수 최상위 필드
    for f in REQUIRED_TOP:
        if f not in obj:
            errors.append(f"필수 필드 누락: {f}")

    status = obj.get("status")
    reviewed = status in REVIEWED_STATUSES

    def _completeness(msg: str) -> None:
        (errors if reviewed else warnings).append(msg)

    # 2) enum
    if (d := obj.get("domain")) is not None and d not in DOMAINS:
        errors.append(f"enum 위반 domain: {d}")
    if (t := obj.get("task_type")) is not None and t not in TASK_TYPES:
        errors.append(f"enum 위반 task_type: {t}")
    if (v := obj.get("visibility")) is not None and v not in VISIBILITIES:
        errors.append(f"enum 위반 visibility: {v}")
    if status is not None and status not in STATUSES:
        errors.append(f"enum 위반 status: {status}")
    if (df := obj.get("difficulty")) is not None and df not in DIFFICULTIES:
        errors.append(f"enum 위반 difficulty: {df}")
    modes = obj.get("benchmark_mode")
    if isinstance(modes, list):
        for m in modes:
            if m not in BENCHMARK_MODES:
                errors.append(f"enum 위반 benchmark_mode: {m}")
    elif modes is not None:
        errors.append("benchmark_mode 는 리스트여야 함")

    # 3) id 형식 + domain 일치
    qid = obj.get("id", "")
    m = _ID_RE.match(qid) if isinstance(qid, str) else None
    if not m:
        errors.append(f"id 형식 위반(ktb-domain-NNNN): {qid}")
    elif obj.get("domain") and m.group(1).replace("-", "_") != obj["domain"]:
        errors.append(f"id 의 domain({m.group(1)}) 가 domain 필드({obj['domain']})와 불일치")

    # 4) time_basis 형식
    tb = obj.get("time_basis", "")
    if not (isinstance(tb, str) and _DATE_RE.match(tb)):
        errors.append(f"time_basis 형식 위반(YYYY-MM-DD): {tb}")

    # 5) rubric 합계 == total_points
    rubric = obj.get("rubric") or {}
    crit = rubric.get("criteria") or []
    total = rubric.get("total_points")
    s = sum(c.get("points", 0) for c in crit)
    if total is not None and s != total:
        errors.append(f"rubric 배점 합({s}) != total_points({total})")
    if not crit:
        _completeness("rubric.criteria 비어있음")

    # 6) sources: locator 존재 + 권위 출처 1개 이상
    sources = obj.get("sources") or []
    for i, sc in enumerate(sources):
        if sc.get("type") not in SOURCE_TYPES:
            errors.append(f"enum 위반 sources[{i}].type: {sc.get('type')}")
        if not str(sc.get("locator", "")).strip():
            errors.append(f"sources[{i}].locator 비어있음(근거 추적 불가)")
    if not sources:
        _completeness("sources 없음(근거 없는 문항)")
    elif not any(sc.get("type") in AUTHORITATIVE_SOURCE_TYPES for sc in sources):
        _completeness("권위 출처(statute/case_law/standard 등) 없음")

    # 7) hash 형식 + 내용 일치
    h = obj.get("hash", "")
    if not (isinstance(h, str) and _HASH_RE.match(h)):
        errors.append(f"hash 형식 위반(sha256:<64hex>): {h}")
    elif _content_hash is not None and "question" in obj and "answer" in obj:
        try:
            if _content_hash(obj) != h:
                errors.append("hash 내용 불일치(question/answer 변경 후 미갱신)")
        except Exception as e:  # pragma: no cover
            warnings.append(f"hash 검증 실패: {e}")

    # 8) 유형-필드 정합
    tt = obj.get("task_type")
    q = obj.get("question") or {}
    a = obj.get("answer") or {}
    if tt == "multiple_choice" and not q.get("choices"):
        errors.append("multiple_choice 인데 question.choices 비어있음")
    if tt == "calculation" and not a.get("calculation_steps"):
        _completeness("calculation 인데 answer.calculation_steps 비어있음")

    return errors, warnings


def validate_question(obj: dict) -> list[str]:
    """하드 위반(errors) 목록만 반환. 빈 리스트 = 통과."""
    return lint_question(obj)[0]


def is_valid(obj: dict) -> bool:
    return not validate_question(obj)
