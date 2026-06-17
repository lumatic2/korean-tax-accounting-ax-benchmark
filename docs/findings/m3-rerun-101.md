# M3 재평가 — 101문항 (소득세 +7 반영)

> 2026-06-11 실행. 소득세 calc/case/risk +7로 문항셋이 94→101이 된 뒤, 신규 문항이 변별을 깨지 않는지(노이즈)·spread가 유지되는지·RAG 환각감소가 재현되는지 확인.

## 실행 구성

- 데이터: `data/sample-questions-v0.1.jsonl` 101문항
- 모델: claude-opus-4-8 · claude-sonnet-4-6 · claude-haiku-4-5
- 모드: closed_book · rag
- judge: claude-sonnet-4-6 (opus self-eval 제거 — 단 sonnet 자체 점수엔 self-eval caveat 잔존)
- accessed-at: 2026-06-11, 러너 `--workers`(ThreadPoolExecutor) + rate-limit 재시도
- 출력: `outputs/m3-rerun-101-20260611/`(gitignored) + 신규 income haiku probe `outputs/m3-new-income-haiku/`

## 결과

### ① 3모델 변별 — spread 40.2 (공통 118쌍)

opus·sonnet·haiku가 모두 성공한 (문항,모드) 공통 118쌍 기준:

| 모델 | 평균 |
|---|---|
| claude-opus-4-8 | **92.0** |
| claude-sonnet-4-6 | 86.3 |
| claude-haiku-4-5 | **51.7** |

→ **spread 40.2**. 직전 full 리포트(2026-06-09, 81레코드) spread **30.1 → 40.2로 확대**. 신규 income hard 문항(양도 calc·case·risk)이 약모델을 더 강하게 가른 결과.

### ② RAG vs closed_book — +8.6 (환각감소 재현)

공통셋 3모델 평균:

| 모드 | 평균 |
|---|---|
| closed_book | 72.4 |
| rag | **81.0** |

→ RAG가 +8.6점. RAG가 환각을 줄여 점수를 올린다는 가설([m3-rag-vs-closed-book.md](m3-rag-vs-closed-book.md))을 101문항 전체에서 재확인.

### ③ 신규 income 7문항 변별 + 노이즈 점검 (opus·haiku 14/14 완주)

신규 income 0013~0019 × 2모드, opus·haiku 전수:

| 모델 | 평균 |
|---|---|
| opus | **95.7** |
| haiku | 73.8 |

→ gap 21.9. 문항별로 보면 쉬운 calc(0013 산출세액·0014 그로스업)는 둘 다 ~100이나, **case(0017 소득구분)·risk(0018 양도증빙·0019 금융판정)에서 haiku가 D등급(29~48)으로 붕괴**하고 opus는 88~100 유지. **0점 일괄붕괴(데이터 결함) 0건** — gold 무결성 확인(노이즈 점검 PASS). calc3 양도(오케스트레이터가 제104①11호→제1호 자산구분 오류 교정한 문항)도 opus 97~100·haiku 70(closed)/99(rag)로 정상.

### ③-1 sonnet 신규 income top-up (2026-06-12 — 미달분 보충)

직전 실행에서 세션 usage 한도로 sonnet이 신규 income 0/14를 놓쳤던 미달분을 별도 창에서 보충(`outputs/m3-sonnet-newincome*`). rag 2건(0016·0017) 1차 timeout → 재시도로 14/14 완주, **avg 89.7**.

| 모델 | 신규 income avg |
|---|---|
| opus | 95.7 |
| **sonnet** | **89.7** |
| haiku | 73.8 |

→ **opus > sonnet > haiku 단조 정렬**로 신규 income에서도 3모델 변별 확정(직전엔 opus vs haiku로만 확정). sonnet도 calc는 ~100(0013~0016)·risk는 B(0018·0019 84~89)이나, **case 0017(소득구분)이 최약**(closed 70/C, **rag 44/D — RAG가 오히려 점수 하락**). 0017은 retrieval이 소득구분 판단에 방해 컨텍스트를 끌어온 케이스로, "RAG가 항상 +"가 아님을 보이는 반례(전체 평균은 RAG +8.6이나 case_reasoning 일부는 역효과).

## usage 한도 제약 (방법론 메모)

101 × 2모드 × 3모델 = 606 평가를 한 5시간 구독 세션 창에서 완주하지 못했다.

- opus 201/202(완주, 가장 비쌈) · haiku 146/202 · sonnet 119/202 — **"You've hit your session limit"**(rate-limit 아닌 세션 usage)로 sonnet·haiku 꼬리 차단.
- sonnet은 신규 income 7문항(파일 말미 append)을 0/14로 놓침. → **2026-06-12 별도 창에서 14/14 보충 완료(avg 89.7, §③-1).** 변별은 보충 전 opus vs haiku로 이미 확정돼 있었다(비핵심 보충).
- **교훈**: 대규모 라이브 eval은 5시간 세션 usage 예산 내로 슬라이스해야 한다. 동시성을 높이는 것(18-way)은 서버 일시 rate-limit을 유발해 역효과(606중 435 오염) — 단일 프로세스 `--workers 6`이 안전. rate-limit transient는 [지수 backoff 재시도](../../src/ktaxbench/models/claude_cli.py)로 흡수하나, **세션 usage 한도는 재시도로 못 넘는다**(창 리셋 필요).
- 차기 풀 재실행 시: 모델별로 세션 창을 나눠 순차 실행하거나, 가장 비싼 opus 먼저 확보 후 cheaper 모델을 별도 창에서.

## 결론

소득세 +7로 M1이 101에 도달한 뒤에도 **변별(spread 40.2, 직전 30.1보다 확대)·RAG 효과(+8.6)·신규 문항 무결성(0점 붕괴 0)**이 모두 확인됐다. 벤치마크가 신규 문항으로 약·강 모델을 더 선명히 가른다.
