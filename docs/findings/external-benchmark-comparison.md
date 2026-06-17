# 외부 벤치마크 비교 — K-TaxBench 차별점

> 2026-06-12 조사. 기술리포트([m4-tech-report-outline.md](../m4-tech-report-outline.md)) §6 "외부 벤치 비교"의 근거 문서. 한국/법률·세무·회계·일반 전문 LLM 벤치마크를 실측 조사해 K-TaxBench의 차별점을 표로 확정한다. 모든 항목은 논문/리포지터리 출처 + 접근일(2026-06-12)을 동반한다.

## 1. 조사한 벤치마크

### 1-1. KMMLU / KMMLU-Pro / KMMLU-Redux (한국 전문지식 MCQA)
- KMMLU: 한국 원전 시험 기반 다중과제, **45 카테고리·4 super(STEM/Applied/HUMSS/Other)**. 번역 아닌 한국어 원천. 최신 모델도 60% 미만(원시험 합격선 80%). (NAACL 2025)
- **KMMLU-Pro**: 한국 국가전문자격시험 기반, **2,822문항·MCQA·14개 직역/5도메인**. Tax & Accounting 도메인에 **세무사 238·공인회계사(CPA) 208·관세사 159문항** 포함. "최근 연도 시험만" 수록. 평가는 **정답 정확도 + 공식 합격기준(과목 40%·평균 60%) 합불만** — 추론 깊이·근거(citation) 검증 없음.
- KMMLU-Redux: 한국 국가기술자격시험 기반 2,587문항.
- 출처: [arxiv 2402.11548 (KMMLU)](https://arxiv.org/abs/2402.11548) · [arxiv 2507.08924 (Redux→Pro)](https://arxiv.org/abs/2507.08924) (접근 2026-06-12)

### 1-2. KBL — Korean Benchmark for Legal Language Understanding (한국 법률)
- 구성: **법률 지식 7과제(510) + 추론 4과제(288) + 한국 변호사시험(4도메인·53과제·2,510)**. 지식/추론 과제는 법률 전문가 협력 설계 + 변호사 검증.
- closed-book + **open-book(법률 corpus 동반)** 둘 다 평가. GPT-4·Claude-3도 한국 법률에서 한계. **open-book이 정확도를 최대 +8.6% 개선** — K-TaxBench의 RAG +8.6과 우연히 동일 크기(독립 벤치의 retrieval 효과 교차확인).
- 형식은 주로 MCQA/분류. 출처: [arxiv 2410.08731](https://arxiv.org/abs/2410.08731) (EMNLP 2024 Findings) · [github lbox-kr/kbl](https://github.com/lbox-kr/kbl) (접근 2026-06-12)

### 1-3. LegalBench (영미 법률 추론)
- **162과제·6개 법률추론 유형**, 40개 기여자가 법률 전문가 손으로 설계. 텍스트 유형(법령·판결문·계약서)·법 분야(증거·계약·민사절차 등) 다양. **영어/미국법**.
- 분류·추출·생성·함의 등 과제 혼합. 출처: [arxiv 2308.11462](https://arxiv.org/abs/2308.11462) (NeurIPS 2023) · [github HazyResearch/legalbench](https://github.com/HazyResearch/legalbench) (접근 2026-06-12)

### 1-4. PLAT — Predicting the Legitimacy of Additional Tax (한국 세무, 협소)
- **한국 세법** 대상 — 가산세(additional tax) 적법성 예측 **이진 분류** 과제. retrieval·self-reasoning·multi-agent 결합 시 개선되나 vanilla 모델은 포괄적 이해에 한계.
- 정답(분류) 정확도 중심. **근거 검증·시점 버전핀·오염 추적 없음**. 출처: [arxiv 2503.03444](https://arxiv.org/abs/2503.03444) (접근 2026-06-12)

### 1-5. (맥락) 한국 금융 오픈 리더보드
- 한국어 금융 특화 첫 오픈 리더보드 — **closed benchmark에 1,119 제출** 평가, 금융·회계 포함 5개 MCQA 카테고리. 공개 리더보드 운영 선례 → [ADR 0009](../adr/0009-leaderboard-submission-policy.md) 제출/철회 정책 설계의 참고. 출처: [arxiv 2503.17963 (₩on)](https://arxiv.org/abs/2503.17963) (접근 2026-06-12)

## 2. 비교 매트릭스

| 축 | KMMLU-Pro | KBL | LegalBench | PLAT | **K-TaxBench** |
|---|---|---|---|---|---|
| 관할/도메인 | 한국 전문자격(세무·회계 포함) | 한국 법률 | 영미 법률 | 한국 세무(가산세) | **한국 세무·회계 실무** |
| 과제 형식 | MCQA | MCQA/분류 | 분류·추출·생성·함의 | 이진 분류 | **생성형 다중출력**(결론·계산·근거·주의) |
| 평가 차원 | 정답 정확도·합불 | 정답 정확도 | 과제별 정답 | 분류 정확도 | **다차원**(정확성·근거성·실무성·리스크·도구) |
| 근거(citation) 강제 채점 | ✗ | ✗ | △(일부 추출) | ✗ | **✓ 조문·문단 매치 코드채점** |
| 계산 룰프록시 채점 | ✗(객관식) | ✗ | ✗ | ✗ | **✓**(산식 역산·결정론) |
| 리스크/불확실성 평가 | ✗ | ✗ | ✗ | ✗ | **✓**(risk_analysis 과제) |
| 모드 | closed | closed+open | closed | closed(+retrieval 실험) | **closed/rag/agent 3모드** |
| 적시성(시점 버전핀) | △(최근연도 시험) | ✗ | ✗ | ✗ | **✓ 문항별 time_basis + 버전핀** |
| 오염저항(canary) | ✗ | ✗ | ✗ | ✗ | **✓ 예약**(공개 릴리스 시 삽입) |
| self-eval 방지 | N/A(객관식) | N/A | N/A | N/A | **✓ judge=비self·환경격리** |

(△ = 부분적. K-TaxBench 칸은 현 구현 기준 — [ARCHITECTURE.md](../ARCHITECTURE.md)·ADR 0003·0006·0007·0008·0009.)

## 3. 차별점 요약

1. **객관식 정답률 → 생성형 실무 신뢰도**: KMMLU-Pro·KBL·PLAT는 MCQA/분류 정답 정확도(또는 합불)만 잰다. K-TaxBench는 생성형 답변을 **근거·계산·실무성·리스크·도구 사용**의 5축으로 분해 — "맞혔는가"가 아니라 "실무 검증을 통과했는가"([positioning.md](../positioning.md)).
2. **근거 강제 채점**: 조문·기준서 문단 단위로 인용 정확성을 코드 채점(ADR 0007). 위 벤치 중 근거 정확성을 직접 채점하는 것은 없음(환각·날조 인용 검출이 K-TaxBench의 핵심).
3. **적시성**: 세법은 매년 개정 — K-TaxBench는 문항별 `time_basis` + 버전핀으로 개정 추적. KMMLU-Pro의 "최근연도 시험"은 스냅샷일 뿐 시점 버전 관리는 아님.
4. **유일한 한국 세무·회계 실무 평가**: PLAT(가산세 분류)은 협소하고, KMMLU-Pro 세무·회계는 객관식 자격시험. **생성형·실무·다차원의 한국 세무·회계 벤치는 (조사 범위 내) K-TaxBench가 처음**.
5. **오염저항·self-eval 방지**: canary 예약 + judge 비self·환경격리(ADR 0008). 비교 벤치들은 오염추적·self-eval 가드를 다루지 않음.

## 4. 한계·주의

- 본 조사는 2026-06-12 웹 검색 범위 — 미공개·신규 벤치 누락 가능. "처음"류 단정은 "조사 범위 내"로 한정.
- KBL/KMMLU 수치는 논문 발표값 인용(K-TaxBench와 동일 모델·동일 조건 직접 재현은 아님) — 직접 점수 비교가 아니라 **설계·평가축 비교**로 한정한다.
- KMMLU-Pro HTML(v2)·PLAT PDF 본문 기반. 후속 개정판에서 수치 변동 가능 → 인용 시 버전 명시.
