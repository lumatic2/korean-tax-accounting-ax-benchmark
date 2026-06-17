# 발견 — RAG가 환각을 줄이는가 (closed_book vs rag, M3)

> 실험일 2026-06-09 · 데이터 `outputs/rag_compare/claude-haiku-4-5_20260609T042729Z.jsonl`(gitignored)
> 핵심 가설: **법령 원문을 주입하면 약한 모델의 환각(가짜 조문·인용)이 줄어드는가?**

## 방법

| 항목 | 값 |
|---|---|
| 후보 모델 | `claude-haiku-4-5` (환각이 집중되는 티어 — M3 2차 기준) |
| judge | `claude-sonnet-4-6` (후보군 밖 → self-eval 차단 + fake_source 판정 신뢰성↑) |
| 비교 | `--modes closed_book,rag` (동일 invocation = apples-to-apples) |
| 문항 | `task_type=citation` 8문항 (환각=측정 실패모드인 유형) |
| retriever | 법제처 DRF 라이브(`retriever.py`), `accessed_at=2026-06-09`, `outputs/rag_cache` |

환각 지표 두 층:
- **`fake_source`** = judge fatal_flag — *존재하지 않는 근거·인용문 생성* = 진짜 환각 (rubric −20)
- **`unverified_citation:제N조`** = code 채점(`grade_citation`) — gold에 없는 조문 인용 (실재 조문일 수 있어 약신호)

## 결과

| 지표 | closed_book | rag | 변화 |
|---|---|---|---|
| **fake_source 건수** | **14** | **4** | **−71%** |
| 평균 총점(8문항) | 24.9 | 60.25 | **+35** |
| unverified_citation 건수 | 10 | 11 | flat |

문항별 총점:

| 문항 | closed_book | rag | Δ | 성격 |
|---|---|---|---|---|
| ktb-vat-0007 | 0 | 89 | **+89** | 답=조문(부가세법) |
| ktb-corp-tax-0005 | 7 | 93 | **+86** | 답=조문(법인세법) |
| ktb-income-tax-0003 | 38 | 90 | **+52** | 답=조문(소득세법) |
| ktb-income-tax-0004 | 49 | 84 | **+35** | 답=조문(소득세법·시행령) |
| ktb-corp-tax-0006 | 32 | 46 | +14 | 답=조문(법인세법) |
| ktb-basic-tax-law-0003 | 0 | 36 | +36 | 절차형(국기법) — 단, 새 혼동 오류 |
| ktb-basic-tax-law-0002 | 18 | 9 | **−9** | 절차·판례형(국기법) |
| ktb-basic-tax-law-0001 | 55 | 35 | **−20** | 정당한 사유·판례형(국기법) |

## 해석

1. **핵심 가설 지지** — 법령 원문을 주입하니 *가짜 출처 생성이 71% 감소*(14→4), 평균 총점 2.4배. closed_book에서 fake_source로 0~7점이던 statute-citation 문항(vat-0007·corp-0005)이 RAG에서 84~93점으로 정상화. `unverified_citation`이 flat인 것은 정상 — RAG에선 *실재하는* 조문을 인용하되 gold 집합 밖일 뿐(환각 아님).

2. **단서 — RAG는 만능이 아니다.** 국세기본법 reasoning 문항(0001·0002)은 RAG로 **오히려 하락**, 0002·0003은 rag에서 fake_source·혼동(`수정신고/경정청구 혼동`)이 *증가*. 이 문항들의 답은 *정당한 사유·절차·심판례 판단*이라 DRF가 주는 **법령 조문만으로는 부족**하고, 주입된 조문이 모델을 엉뚱하게 앵커링한다. → **RAG 이득은 "답=조문"인 statute-citation에 집중**되며, 판례·절차형은 *판례 retrieval*이 따로 필요하다(법령 DRF로 불충분).

## 한계

- n=8, 단일 모델(haiku), 단일 런 — *방향성* 결론. judge 분산 존재.
- 깨끗한 확정엔 ① opus 컨트롤(강모델은 RAG로 안 변해야 함) ② 반복 실행 ③ 도메인 균형 표본 필요.

## 함의 (M4 방법론 리포트)

"RAG가 환각을 줄이지만 문항 유형에 따라 다르다"는 **구성 타당도(construct validity)** 근거다 — 벤치마크가 모드별 차이를 *분해*해서 보여준다는 증거. 후속: ① 판례·심판례 retrieval 소스 추가 검토 ② statute-citation vs 절차·판례형 분류 축을 리포트에 노출.
