"""법제처 DRF 라이브 조회로 근거 컨텍스트 구성.

vendored DRF 패턴 from tax-agent/src/tax_agent/agent/law_client.py (2026-06-02).
재현성: accessed_at 은 호출자가 주입(코드에 now() 박지 않음). 조회 결과는
outputs/rag_cache/{mst}_{accessed_at}.json 에 캐시 → 같은 기준일 재실행 시 동일.
키 없음/네트워크 실패 시 빈 컨텍스트 반환(예외로 죽지 않음).
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv()

_OC = os.getenv("LAW_API_OC", "8307").strip()
_BASE = "https://www.law.go.kr/DRF"
_REPO = Path(__file__).resolve().parents[3]
_CACHE_DIR = _REPO / "outputs" / "rag_cache"

_ARTICLE_RE = re.compile(r"제\s*(\d+)\s*조")
_IMG_RE = re.compile(r"<img[^>]*>")


def _clean(text: str) -> str:
    text = _IMG_RE.sub("", text)
    return re.sub(r"[ \t]+", " ", text).strip()


def _search_law_mst(name: str, *, timeout: int = 15) -> str | None:
    r = httpx.get(f"{_BASE}/lawSearch.do",
                  params={"OC": _OC, "target": "law", "query": name,
                          "type": "JSON", "display": "3"}, timeout=timeout)
    r.raise_for_status()
    rows = (r.json().get("LawSearch", {}) or {}).get("law", [])
    if isinstance(rows, dict):
        rows = [rows]
    for row in rows:
        if str(row.get("법령명한글", "")).strip() == name:
            return str(row.get("법령일련번호") or row.get("법령ID"))
    if rows:
        return str(rows[0].get("법령일련번호") or rows[0].get("법령ID"))
    return None


def _fetch_law(mst: str, accessed_at: str, *, timeout: int = 30) -> dict:
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache = _CACHE_DIR / f"{mst}_{accessed_at}.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    r = httpx.get(f"{_BASE}/lawService.do",
                  params={"OC": _OC, "target": "law", "MST": mst, "type": "JSON"},
                  timeout=timeout)
    r.raise_for_status()
    data = r.json()
    cache.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return data


def _extract_article(law_json: dict, article_no: str) -> str | None:
    law = law_json.get("법령", law_json)
    arts = (law.get("조문", {}) or {}).get("조문단위", [])
    if isinstance(arts, dict):
        arts = [arts]
    prefix = f"제{article_no}조"
    # 같은 조문번호 entry가 여러 개일 수 있다(장/절 구분자 포함). 실제 조문 entry 우선:
    # 조문내용이 "제N조"로 시작하거나 항이 있는 것을 고른다.
    candidates = [a for a in arts if str(a.get("조문번호", "")) == str(article_no)]
    best = None
    for a in candidates:
        content = str(a.get("조문내용", ""))
        if content.lstrip().startswith(prefix) or a.get("항"):
            best = a
            break
    if best is None and candidates:
        best = candidates[0]
    if best is None:
        return None
    chunks: list[str] = []
    if best.get("조문내용"):
        chunks.append(_clean(str(best["조문내용"])))
    hangs = best.get("항")
    if hangs:
        hangs = hangs if isinstance(hangs, list) else [hangs]
        for h in hangs:
            c = h.get("항내용")
            if c:
                chunks.append(_clean(str(c)))
    return "\n".join(chunks)


def retrieve_context(question: dict, *, accessed_at: str, limit: int = 5) -> dict:
    """question.sources 의 (법령명, 제N조)로 DRF 조회 → 근거 컨텍스트.

    반환: {"context_text": str, "retrieved": [{law, article, excerpt, url}],
           "accessed_at": str, "warnings": [str]}
    """
    targets: list[tuple[str, str]] = []
    seen = set()
    for sc in question.get("sources") or []:
        law_name = str(sc.get("title", "")).strip()
        m = _ARTICLE_RE.search(str(sc.get("locator", "")))
        if not (law_name and m):
            continue
        key = (law_name, m.group(1))
        if key not in seen:
            seen.add(key)
            targets.append(key)
    targets = targets[:limit]

    retrieved: list[dict] = []
    warnings: list[str] = []
    mst_cache: dict[str, str | None] = {}
    for law_name, art_no in targets:
        try:
            if law_name not in mst_cache:
                mst_cache[law_name] = _search_law_mst(law_name)
            mst = mst_cache[law_name]
            if not mst:
                warnings.append(f"법령 미발견: {law_name}")
                continue
            law_json = _fetch_law(mst, accessed_at)
            excerpt = _extract_article(law_json, art_no)
            if excerpt:
                retrieved.append({
                    "law": law_name,
                    "article": f"제{art_no}조",
                    "excerpt": excerpt,
                    "url": f"https://www.law.go.kr/법령/{law_name}/제{art_no}조",
                })
            else:
                warnings.append(f"조문 미추출: {law_name} 제{art_no}조")
        except Exception as e:  # 네트워크·키 실패 — graceful
            warnings.append(f"조회 실패({law_name} 제{art_no}조): {e}")

    context_text = "\n\n".join(
        f"[{r['law']} {r['article']}]\n{r['excerpt']}" for r in retrieved
    )
    return {
        "context_text": context_text,
        "retrieved": retrieved,
        "accessed_at": accessed_at,
        "warnings": warnings,
    }
