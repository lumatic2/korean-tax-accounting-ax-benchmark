# K-TaxBench 기술 리포트 — 골격 (M4)

> M4 공개 트랙 산출물. arXiv/블로그용 기술 리포트의 **목차 + 근거 슬롯**. 본문 집필 아님. 규칙: 모든 수치·결론은 레포 내 finding/DOMAIN/ADR을 `근거:`로 인용. 근거 없는 칸은 `TODO(리서치):` — 추정 본문 금지.

## 0. 메타
- 제목(안): *K-TaxBench: 한국 회계·세무 AI의 실무 신뢰도 평가 인프라*
- 저자: 본인(세무·회계 자격). venue: arXiv(preprint) + 블로그 요약본.
- 상태: 골격. 본문은 외부벤치 리서치(§6) 후 집필.

## 1. Abstract
- 목적: "그럴듯하게 말하는가"가 아니라 "실무 검증을 통과했는가"를 재현가능하게 측정.
- 핵심 결과: 101문항·6도메인×7역량, 3모델 변별 spread 40.2, RAG 환각감소 +8.6.
- 근거: [PRD.md](PRD.md), [findings/m3-rerun-101.md](findings/m3-rerun-101.md).

## 2. Motivation / 개념체계 spine
- "정답률이 아니라 실무 신뢰도" — 답 맞지만 근거 틀림/계산 맞지만 위험한 설명/조문 찾았지만 적용 틀림/개정세법 미반영/불확실 단정.
- 5축: 정확성·근거성·실무성·리스크 인식·도구 사용성.
- 근거: [positioning.md](positioning.md) §차별점·§해결책, [benchmark-design-principles.md](benchmark-design-principles.md).

## 3. Benchmark 구성
- 101문항 분포: domain(vat22·corp22·income19·accounting16·basic12·mixed10), task_type(citation27·case23·risk20·calc17·agent12·MC1·short1). 근거: [README.md](../README.md), `data/sample-questions-v0.1.jsonl`.
- 스키마: visibility(public_sample/holdout/private)·hash 오염추적·time_basis 적시성. 근거: [benchmark-schema.md](benchmark-schema.md).
- 역량×도메인 커버리지 매트릭스. 근거: [question-blueprint.md](question-blueprint.md) §6.
- 공개셋 34 vs holdout 분리. 근거: [m4-public-sample-scope.md](m4-public-sample-scope.md).

## 4. 방법론
- 3모드: closed_book / rag / agent. 근거: [ARCHITECTURE.md](ARCHITECTURE.md), [adr/0005](adr/0005-agent-react-loop.md).
- 다차원 채점: 코드 채점(MC·계산·근거 locator, 결정론) + LLM-judge(7차원 루브릭) + statement-level 부분점·pass^k. 근거: [rubric-v0.1.md](rubric-v0.1.md), [adr/0003](adr/0003-calculation-as-rule-proxy.md), [adr/0007](adr/0007-citation-grader-kifrs-paragraph.md).
- self-eval 제거(judge=비self 모델) + 후보·judge 환경 격리. 근거: [adr/0008](adr/0008-agent-eval-isolation.md).
- agent 도구강제 모드(권위게이트+근거매칭). 근거: [adr/0006](adr/0006-agent-forced-mode.md).
- 버전핀(model id·data hash·scaffold·mode) 재현성. 근거: [ARCHITECTURE.md](ARCHITECTURE.md) §상태관리.

## 5. 결과
- ① 3모델 변별 **spread 40.2**(opus 92.0·sonnet 86.3·haiku 51.7, 공통 118쌍; 직전 30.1→확대). 근거: [findings/m3-rerun-101.md](findings/m3-rerun-101.md) §①.
- ② RAG vs closed_book **+8.6**(72.4→81.0, 환각감소 재현). 근거: [findings/m3-rerun-101.md](findings/m3-rerun-101.md) §②, [findings/m3-rag-vs-closed-book.md](findings/m3-rag-vs-closed-book.md).
- ③ 도구강제 ≠ 검색가능 사실(유명룰은 3모델 도구 0회) — 가설 반증. 근거: [findings/agent-tool-forcing.md](findings/agent-tool-forcing.md).
- ④ calc 룰프록시 검출 사례(양도 자산구분 오류 교정·기부금 final↔explanation 모순 포착) — self-eval 천장 넘는 외부검증 가치.
- ⑤ 신규 income 변별(opus95.7 vs haiku73.8, case·risk서 haiku D붕괴, 0점 데이터결함 0). 근거: [findings/m3-rerun-101.md](findings/m3-rerun-101.md) §③.

## 6. 외부 벤치 비교
> 실측 조사 완료(2026-06-12). 전체 근거·출처·매트릭스: [findings/external-benchmark-comparison.md](findings/external-benchmark-comparison.md).

조사 벤치(출처 동반): **KMMLU-Pro**(한국 전문자격 MCQA, 세무사238·CPA208·관세사159 포함 — [arxiv 2507.08924](https://arxiv.org/abs/2507.08924)) · **KBL**(한국 법률, closed+open-book, open-book +8.6% — [arxiv 2410.08731](https://arxiv.org/abs/2410.08731)) · **LegalBench**(영미 법률추론 162과제 — [arxiv 2308.11462](https://arxiv.org/abs/2308.11462)) · **PLAT**(한국 가산세 적법성 이진분류 — [arxiv 2503.03444](https://arxiv.org/abs/2503.03444)).

핵심 차별점:
1. **객관식 정답률 → 생성형 실무 신뢰도** — 비교 벤치는 MCQA/분류 정답·합불만, K-TaxBench는 정확성·근거성·실무성·리스크·도구 5축 생성형 채점.
2. **근거 강제 채점**(조문·문단 매치) — 비교 벤치 중 인용 정확성 직접 채점 부재(환각 검출이 핵심).
3. **적시성**(문항별 time_basis·버전핀) — KMMLU-Pro "최근연도"는 스냅샷일 뿐 시점관리 아님.
4. **(조사 범위 내) 유일한 생성형·다차원 한국 세무·회계 실무 벤치** — PLAT은 협소(가산세), KMMLU-Pro 세무·회계는 객관식 자격시험.
5. **오염저항(canary)·self-eval 방지(judge 비self·격리)** — 비교 벤치 미다룸.

비교 매트릭스(10축 × 5벤치)는 finding 문서 §2 참조. 흥미로운 외부 교차확인: KBL의 open-book +8.6%가 본 벤치 RAG +8.6과 동일 크기(독립 벤치의 retrieval 효과 재현).

> 주의(한계): 점수 직접 비교가 아니라 **설계·평가축 비교**(KBL/KMMLU 수치는 논문 발표값). "처음"류 단정은 "조사 범위 내" 한정. 본문 집필 시 finding §4 한계 반영.

## 7. 한계 · 후속
- 본인 단독 검수 단계 — 외부 전문가 검수 도입 예정.
- holdout 운영·로테이션·표본설계는 진행형. judge 비결정성은 재현분산 로깅+스팟체크로 보정.
- 멀티프로바이더(GPT/Gemini) 교차변별은 1차 범위 제외. 근거: [adr/0002](adr/0002-claude-cli-first.md).

## 8. 재현성
- 버전핀·공개셋 34 릴리스·실행기(`scripts/run_eval.py`)·리더보드 정책. 근거: [m4-public-sample-scope.md](m4-public-sample-scope.md), [adr/0009](adr/0009-leaderboard-submission-policy.md).
- usage 예산 내 슬라이스 운영 교훈(606 평가 단일창 초과). 근거: [findings/m3-rerun-101.md](findings/m3-rerun-101.md) §usage.
