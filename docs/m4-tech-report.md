# K-TaxBench: 한국 회계·세무 AI의 실무 신뢰도 평가 인프라

> M4 공개 트랙 기술 리포트 본문 (arXiv preprint 형). 골격: [m4-tech-report-outline.md](m4-tech-report-outline.md).
> 규칙([CLAUDE.md](../CLAUDE.md) Judge 규약): 모든 수치·결론은 레포 내 finding/ADR/DOMAIN 또는 공식 출처를 인용한다. 수치는 finding 발표값을 그대로 인용하며 본문에서 재산출하지 않는다.
> 상태: 초고(v0.1, 2026-06-12). 영문판은 후속.

**저자**: Yusung Jun · **공개 자료**: 리더보드 https://tax-benchmark.askewly.com · **상태**: 초기 단계(phase-1) 인프라 보고 — 외부 전문가 검수·다중 프로바이더 평가 예정(§7)

---

## Abstract

회계·세무 분야에 투입되는 AI 시스템은 빠르게 늘고 있으나, 그 시스템이 "한국 세법과 회계기준을 실제로 수행할 수 있는가"를 재현 가능하게 측정하는 표준은 부족하다. 일반 LLM 벤치마크나 자격시험 정답률은 "그럴듯하게 말하는가"는 측정하지만 "실무 검증을 통과했는가"는 측정하지 못한다. 답은 맞지만 근거가 틀린 경우, 계산은 맞지만 실무 설명이 위험한 경우, 조문은 찾았지만 적용이 틀린 경우, 개정세법을 반영하지 못한 경우, 불확실한 사안을 단정한 경우를 정답률 한 숫자로는 분리할 수 없다([positioning.md](positioning.md)).

K-TaxBench는 이 다섯 실패 모드를 분해해 측정하는 평가 인프라다. 한국 세무·회계 실무를 6개 도메인 × 7개 과제유형으로 분해한 101문항을, **정확성·근거성·실무성·리스크 인식·도구 사용성**의 다차원 루브릭으로 채점한다. 채점은 코드 채점(객관식·계산·근거 locator의 결정론적 채점)과 LLM-judge(7차원 루브릭)를 결합하되, 평가받는 모델이 자기 답을 채점하지 못하도록 judge를 후보군 밖 모델로 고정하고 후보·judge 실행 환경을 격리한다.

주요 결과: (1) 3개 모델(claude-opus-4-8 / sonnet-4-6 / haiku-4-5) 사이에서 **변별 spread 40.2점**(공통 118쌍 기준)이 관측됐다([findings/m3-rerun-101.md](findings/m3-rerun-101.md)). (2) 법령 원문을 주입하는 RAG 모드는 closed-book 대비 평균 **+8.6점**을 올렸고, 그 이득의 상당 부분은 가짜 출처(환각) 감소에서 왔다(citation 유형에서 fake_source 14→4건, −71%; [findings/m3-rag-vs-closed-book.md](findings/m3-rag-vs-closed-book.md)). (3) 도구 사용은 "강제 + 근거 매칭"으로만 신뢰성 있게 측정됨을 라이브 실험으로 보였다 — 약모델은 강제 게이트 하에서도 도구를 쓰지 않고 인용을 날조했고, 코드 단위 근거 대조만이 이를 잡아냈다([findings/agent-tool-forcing.md](findings/agent-tool-forcing.md)).

**범위와 강도(중요).** 본 리포트는 완성된 표준 벤치마크가 아니라 **초기 단계(phase-1) 평가 인프라 보고**다. 1차 범위는 Claude 계열 3모델 변별에 한정되며(타 프로바이더 교차 변별은 후속), judge 역시 Claude 계열(후보군 밖) — 즉 변별·self-eval 방지 주장은 *동일 패밀리 내부* 수준으로 읽어야 한다. 보고 수치는 신뢰구간·유의성 검정을 동반하지 않은 **점추정치이며, 결론은 "방향성"으로 한정**한다(§7). 핵심 findings·gold·holdout은 비공개 검증셋의 일부로 외부 직접 재현이 제한된다(공개 재현 범위는 §8).

---

## 1. 동기 — "정답률"이 아니라 "실무 신뢰도"

### 1.1 문제

회계·세무 AI는 늘지만, 시장에는 다음 질문에 답하는 표준이 없다([positioning.md](positioning.md) §문제):

- 이 AI가 한국 세법과 회계기준을 실제로 이해하는가?
- 계산과 세무조정을 틀리지 않는가?
- 법령·예규·판례·조세심판례를 정확히 찾고 인용하는가?
- 위험한 단정이나 환각을 피하는가?
- 세무사·회계사가 검토 가능한 형태로 답하는가?

일반 LLM 벤치마크나 자격시험 정답률로는 이 질문에 답하기 어렵다. 회계·세무 실무에서 치명적인 오류는 "틀린 답"보다 **그럴듯하지만 검증되지 않은 답**이기 때문이다. 정답률 한 숫자는 다음 다섯 가지를 구분하지 못한다([positioning.md](positioning.md) §차별점):

1. 답은 맞지만 **근거가 틀린** 경우
2. 계산은 맞지만 **실무 설명이 위험한** 경우
3. 조문은 찾았지만 **사실관계 적용이 틀린** 경우
4. **최신 개정세법을 반영하지 못한** 경우
5. 불확실한 사안을 **단정한** 경우

### 1.2 5축 — 무엇을 재는가

K-TaxBench는 생성형 답변을 다섯 축으로 분해해 채점한다([positioning.md](positioning.md) §해결책):

| 축 | 질문 |
|---|---|
| **정확성** | 결론과 계산이 맞는가 |
| **근거성** | 조문·기준서·예규·판례 인용이 맞는가 |
| **실무성** | 실제 업무 맥락에서 쓸 수 있는 답인가 |
| **리스크 인식** | 불확실성·추가 확인사항·위험 조건을 구분하는가 |
| **도구 사용성** | RAG/Agent가 자료 검색과 검증을 제대로 수행하는가 |

핵심 메시지는 한 줄로 압축된다: **"잘 말한다"가 아니라 "검증을 통과했다"**가 필요하다([positioning.md](positioning.md) §핵심 메시지).

### 1.3 설계 원리를 회계 개념체계에서 빌려오다

이 벤치마크의 지적 출발점은, 회계가 이미 "신뢰할 수 있는 정보"의 조건을 정의해 두었다는 관찰이다 — 「재무보고를 위한 개념체계」의 **질적 특성**이다([benchmark-design-principles.md](benchmark-design-principles.md) §0). 재무정보에 요구하는 질적 특성을 AI 평가 정보에도 동일하게 요구한다. 단, 이 차용은 **설계 영감(design inspiration)**이며, 아래 매핑이 실증적으로 입증됐다는 주장은 아니다 — 특히 "점수 1점 차이 = 실무 신뢰도 1만큼"이라는 **구성 타당도는 현재 *가설·목표*이고, 그 실증(전문가 유용성 랭킹·inter-rater 일치 등)은 §7의 검증 로드맵에 둔다**.

- **목적적합성**(개념체계 2.6) → **구성 타당도**. 점수 1점 차이가 "실무에 1만큼 더 믿고 맡길 수 있음"을 의미해야 한다. 객관식 정답률이 높다고 세무조정을 맡길 수 있는 게 아니다.
- **표현충실성**(2.12) → **전문가 검수 정답**(목표 상태). 정답이 법령·기준서의 실질을 충실히 표현해야 한다. 정답이 틀린 벤치마크는 측정이 아니라 오염원이다. 모든 정답에 **기준일 도장**이 붙는다. *현재 상태*: 공개 34문항은 **저자 본인 검수** 완료(2026-06-12), holdout은 내부 검수 단계 — "전문가 검수 정답"은 외부 전문가 검수 통과분만 `version:1.0`으로 승격하는 *목표*다(§7).
- **비교가능성**(2.24) → **버전 핀**. 모델 A와 B를 같은 조건에서 재야 한다. 모드·기준일·데이터 버전·스캐폴드를 점수에 함께 기록한다.
- **검증가능성**(2.30) → **오염 저항 + 자동채점 우선**. 누가 채점해도 같은 점수가 나오고, 점수가 학습 누출이 아니라 실제 능력에서 나왔음을 보장해야 한다.
- **적시성**(2.33) → **시점 버전 관리**. 세법은 매년 바뀐다. 작년 기준 정답은 올해 오답일 수 있다.
- **이해가능성**(2.34) → **다차원 진단**. 점수의 소비자는 회계법인 의사결정자다. "총점 78점"이 아니라 *어디가 약한지*를 보여줘야 도입·개선을 결정한다.

이 셋이 의사결정 시 항상 먼저 따질 **load-bearing 3축**이다: 오염 저항(검증가능성), 다차원 채점(이해가능성), 전문가 검수 정답(표현충실성). 새 문항·채점 방식·기능을 설계할 때 항상 "이게 이 3축을 강화하는가, 훼손하는가"를 먼저 묻는다([benchmark-design-principles.md](benchmark-design-principles.md) §3).

---

## 2. 벤치마크 구성

### 2.1 문항 분포

현재 v0.1 문항셋은 101문항이다([README.md](../README.md), `data/sample-questions-v0.1.jsonl`).

**도메인별** — 부가세 22 · 법인세 22 · 소득세 19 · 회계처리 16 · 기초세법 12 · 복합 10.

**과제유형별** — 근거제시(citation) 27 · 사례판단(case) 23 · 리스크분석(risk) 20 · 계산(calc) 17 · 에이전트(agent) 12 · 객관식(MC) 1 · 단답(short) 1.

단순 지식 암기형(MC·short)은 기초 변별용으로만 최소화하고, 실무 타당도는 사례·리스크·에이전트형이 담당한다([benchmark-design-principles.md](benchmark-design-principles.md) §1.1). 계산 문항은 "룰 프록시"로만 채택한다 — 산식을 역산해 결정론적으로 채점할 수 있는 경우에 한한다([adr/0003](adr/0003-calculation-as-rule-proxy.md)).

### 2.2 스키마 — 오염 추적과 적시성을 문항에 박다

각 문항은 측정 신뢰성을 위한 메타데이터를 갖는다([benchmark-schema.md](benchmark-schema.md)):

- **visibility** (`public_sample` / `holdout` / `private`) — 공개 샘플과 비공개 검증셋을 분리한다(§2.4).
- **hash** — 문항 내용 해시로 오염·표절을 추적한다.
- **time_basis** — 정답이 어느 시점 시행 법령 기준인지를 문항 단위로 못박는다. 세법은 매년 개정되므로, 시점 없는 정답은 표현충실성·적시성 위반이다.

### 2.3 공개 34 vs holdout 분리

공개 릴리스 집합은 화이트리스트 규칙으로 결정론적으로 산출된다 — `visibility=public_sample` ∧ `public_release_allowed` ∧ `status ∈ {internal_reviewed, expert_reviewed}` = **34문항**(2026-06-12 기준; [m4-public-sample-scope.md](m4-public-sample-scope.md)).

공개 34문항 분포: 소득세 8 · 회계 7 · 법인세 6 · 부가세 5 · 기초 5 · 복합 3 / 근거 13 · 계산 7 · 사례 6 · 리스크 6 · MC 1 · 단답 1 / 난이도 medium 31 · hard 1 · easy 2.

설계 의도는 명확하다: **hard·expert 문항은 holdout에 집중**시킨다. 공개셋은 "연습문제"로 취급하고 시간이 지나면 오염을 전제하며 주기 교체한다. 진짜 변별력과 적시성은 비공개 검증셋이 담당한다 — 이 분리가 경쟁자가 따라올 수 없는 해자다([benchmark-design-principles.md](benchmark-design-principles.md) §4).

---

## 3. 방법론

### 3.1 3모드 — closed-book / RAG / agent

같은 문항을 세 모드로 실행해 *도구 사용이 신뢰도에 주는 효과*를 분해한다([ARCHITECTURE.md](ARCHITECTURE.md)):

- **closed-book** — 모델 내부 지식만으로 답한다.
- **rag** — 법제처 DRF 라이브 retrieval로 법령 원문을 주입한 뒤 답한다(`retriever.py`).
- **agent** — ReAct 루프에서 모델이 스스로 도구를 호출해 조회·검증한다([adr/0005](adr/0005-agent-react-loop.md)).

모드는 섞어 비교하지 않는다. 같은 모드끼리만 줄 세운다(비교가능성).

### 3.2 다차원 채점 — 코드 채점 + LLM-judge

채점은 두 층으로 나뉜다([rubric-v0.1.md](rubric-v0.1.md)):

- **코드 채점(결정론)** — 객관식 정답, 계산 결과(산식 역산), 근거 locator(인용한 조문·기준서 문단이 정답 집합과 일치하는지)를 프로그램으로 채점한다. 계산을 "룰 프록시"로 채점하는 근거는 [adr/0003](adr/0003-calculation-as-rule-proxy.md), 인용을 K-IFRS 문단 단위로 채점하는 근거는 [adr/0007](adr/0007-citation-grader-kifrs-paragraph.md).
- **LLM-judge(7차원 루브릭)** — 결론 정확성·근거 정확성·계산 과정·사실관계 반영·불확실성 처리·실무 활용성 등을 statement-level 부분점수로 채점한다. "결론은 맞고 근거 일부만 맞음"을 점수로 표현한다.

에이전트 신뢰도는 1회 정답이 아니라 반복 일관성(pass^k)으로 본다([benchmark-design-principles.md](benchmark-design-principles.md) §2.2).

### 3.3 self-eval 제거와 환경 격리

평가받는 모델이 자기 답을 채점하면 점수에 천장(self-preference)이 생긴다. 이를 막기 위해 **judge는 항상 후보군 밖 모델**로 둔다(예: opus 후보 → sonnet judge; sonnet 후보 → opus judge; [CLAUDE.md](../CLAUDE.md) Judge 규약).

더 미묘한 오염은 *실행 환경*에서 왔다. 후보 모델을 벤치마크 레포 디렉토리에서 `claude -p`로 실행하면, 모델이 레포의 CLAUDE.md(judge 규약·게이트·루브릭 어휘)를 읽고 자신을 "문항 검증자"로 프레이밍하거나, 환경의 경쟁 MCP(law-mcp)로 우회 조회해 eval이 도구 호출을 못 잡는 현상이 관측됐다([findings/agent-tool-forcing.md](findings/agent-tool-forcing.md) §하네스 오염). 완화책은 후보·judge를 레포·home 밖 빈 sandbox 디렉토리 + `--strict-mcp-config`로 격리하는 것이다([adr/0008](adr/0008-agent-eval-isolation.md)). 격리 후 재스모크에서 *관측됐던* 검증자 프레이밍·도구 오탐 경로가 해소됐다 — 이는 이 하네스에서 관측된 특정 누출 경로의 완화이며, 모든 오염을 제거했다는 주장은 아니다(잔여 누출 경로는 §7; §5.4).

### 3.4 도구 강제 모드 — 권위 게이트 + 근거 매칭

자유 agent 모드는 "도구가 필요함을 인지하는가(판단)"를 측정하지만, "강제되면 올바른 도구를 정확히 호출·통합하는가(실행역량)"는 별도 축이다. 후자는 **권위 도구 사용을 게이트로 강제하고, 최종 답이 인용한 조문이 실제로 조회된 것인지를 코드로 대조**하는 강제 모드(`agent_forced`)로 측정한다([adr/0006](adr/0006-agent-forced-mode.md)). 기억-인용과 도구-근거는 텍스트상 구별 불가능하므로, 이 코드 대조가 도구 측정 신뢰성의 전부다(§5.3).

### 3.5 재현성 — 버전 핀

모든 점수에 모델 id·데이터 hash·스캐폴드·모드가 함께 기록된다([ARCHITECTURE.md](ARCHITECTURE.md) §상태관리). 스캐폴드를 고정·기록하지 않으면 비교가 거짓말이 된다는 것은 외부 벤치(SWE-bench)에서 이미 확인된 교훈이다.

---

## 4. 결과

> 아래 수치는 2026-06-11 M3 재평가(101문항) 및 부속 finding의 발표값을 인용한다. 본 리포트에서 재산출하지 않는다([findings/m3-rerun-101.md](findings/m3-rerun-101.md)).
>
> **통계적 강도(중요).** 보고 수치는 **점추정치**이며 신뢰구간·반복분산·유의성 검정을 동반하지 않는다 — LLM-judge에 런 간 분산이 있고(§7), small-n ablation은 단일 런이다. 따라서 모든 결론은 "방향성 증거"로 한정하며, 통계적 유의성을 주장하지 않는다. 핵심 수치의 CI·paired test는 후속 과제다(§7).

### 4.1 3모델 변별 — spread 40.2

opus·sonnet·haiku가 모두 성공한 공통 118쌍(문항×모드) 기준 평균:

| 모델 | 평균 |
|---|---|
| claude-opus-4-8 | **92.0** |
| claude-sonnet-4-6 | 86.3 |
| claude-haiku-4-5 | **51.7** |

→ **spread 40.2점**(표의 모델 평균은 소수 첫째자리 반올림 표시값이고, spread 40.2는 반올림 전 평균의 차이다 — 표시값 산술 92.0−51.7=40.3과의 0.1 차이는 반올림 표시 때문). 직전 full 리포트(2026-06-09, 81레코드)의 30.1에서 확대됐다. 신규 소득세 hard 문항(양도 계산·소득구분·증빙 리스크)이 약모델을 더 강하게 가른 결과다([findings/m3-rerun-101.md](findings/m3-rerun-101.md) §①). 벤치마크가 신규 문항으로 약·강 모델을 더 선명하게 가른다는 것은 saturation의 반대 신호 — 헤드룸이 살아있다는 뜻이다.

### 4.2 RAG vs closed-book — +8.6 (환각 감소 재현)

공통셋 3모델 평균:

| 모드 | 평균 |
|---|---|
| closed_book | 72.4 |
| rag | **81.0** |

→ RAG가 **+8.6점**([findings/m3-rerun-101.md](findings/m3-rerun-101.md) §②). 이 이득의 메커니즘은 별도 ablation에서 드러난다. haiku(환각이 집중되는 티어)를 citation 8문항에 대해 closed-book vs RAG로 비교했을 때, judge가 *존재하지 않는 근거를 생성*했다고 판정한 `fake_source`가 **14건→4건(−71%)**, 평균 총점이 24.9→60.25로 올랐다([findings/m3-rag-vs-closed-book.md](findings/m3-rag-vs-closed-book.md)). 즉 RAG는 정답을 "더 알게" 만든다기보다 **가짜 출처 생성을 억제**해 점수를 올린다.

단, **RAG는 만능이 아니다.** 답이 곧 조문인 statute-citation 문항(부가세·법인세·소득세 조문)에서는 RAG 이득이 크지만(+52~+89), 답이 정당한 사유·절차·심판례 판단인 국세기본법 reasoning 문항에서는 오히려 하락했다(−9, −20). 법령 조문만 주입하면 판례·절차형 문항에서 모델이 엉뚱하게 앵커링되기 때문이다 — 이 유형은 판례 retrieval이 따로 필요하다([findings/m3-rag-vs-closed-book.md](findings/m3-rag-vs-closed-book.md) §해석). 신규 소득세 소득구분 문항(0017)에서도 sonnet이 RAG로 오히려 하락(closed 70 → rag 44)한 반례가 재현됐다([findings/m3-rerun-101.md](findings/m3-rerun-101.md) §③-1). 모드별 차이를 *분해*해 보여주는 것은 구성 타당도 가설과 일관된 정황이다(점수↔실무 유용성의 직접 실증은 아니다 — §7 검증 로드맵).

### 4.3 도구 강제 ≠ 검색 가능한 사실

"답이 외부 사실(조문)을 필요로 하면 모델이 도구를 쓸 것"이라는 가설은 반증됐다. 감가상각·운행기록 한도처럼 *유명한 룰*을 묻는 문항(corp-tax-0012)에서는 3모델 전부 도구를 0회 호출했다 — opus의 답변은 "핵심 규정이 모두 확인되어 추가 도구 호출은 불필요합니다"였다([findings/agent-tool-forcing.md](findings/agent-tool-forcing.md) §결과). 도구-강제의 진짜 조건은 "검색 가능한 사실"이 아니라 **모델이 그 사실을 확실히 모름**이다. 유명 한도는 암기되어 있어, 강모델은 정확히·약모델은 틀리게 도구 없이 답한다. 따라서 모델의 자발적 도구 사용에 의존하면 측정이 불안정하다 — 도구 사용성 축은 강제 모드로 측정해야 한다(§5.3).

### 4.4 계산 룰 프록시의 외부 검증 가치

코드 채점(계산 룰 프록시)은 self-eval 천장을 넘는 외부 검증 사례를 만들어냈다. 양도소득 문항에서 오케스트레이터가 자산구분 오류(소득세법 제104①11호 → 제1호)를 교정했고, 기부금 문항에서 final 값과 explanation의 모순을 포착했다([ROADMAP.md](../ROADMAP.md) 세션5·6). 모델 self-judgment로는 잡히지 않는, 결정론적 산식 대조만이 잡는 유형의 오류다.

### 4.5 신규 소득세 7문항 변별 + 무결성

신규 소득세 0013~0019(× 2모드)에서도 3모델이 단조 정렬됐다:

| 모델 | 신규 income 평균 |
|---|---|
| opus | **95.7** |
| sonnet | 89.7 |
| haiku | 73.8 |

쉬운 계산(산출세액·그로스업)은 세 모델 모두 ~100이지만, 사례(소득구분)·리스크(양도증빙·금융판정)에서 **haiku가 D등급(29~48)으로 붕괴**하고 opus는 88~100을 유지한다([findings/m3-rerun-101.md](findings/m3-rerun-101.md) §③, §③-1). 중요한 무결성 신호: **0점 일괄 붕괴(데이터 결함)가 0건** — 신규 문항이 gold 무결성을 깨지 않았다(노이즈 점검 PASS).

---

## 5. 측정 신뢰성을 만든 라이브 검증들

결과(§4)가 의미를 가지려면 측정 장치 자체가 신뢰할 수 있어야 한다. 다음은 그 장치를 라이브로 검증한 기록이다.

### 5.1 RAG 모드 정상화

§4.2의 fake_source −71%는 RAG retrieval 파이프라인(법제처 DRF 라이브)이 의도대로 작동함을 보인다.

### 5.2 agent 러너 프로덕션 동작

opus가 mixed-0001에서 `법령조문` 도구를 실제 4회 호출(부가세법 §39·§52·법인세법 §25)했고, 러너가 라이브 DRF로 실행·반영했다. 중간에 네트워크 끊김(WinError 10054)이 났으나 모델이 다음 step 재시도로 성공 — graceful 에러 처리와 재시도가 실전에서 작동함을 확인했다([findings/agent-tool-forcing.md](findings/agent-tool-forcing.md) §결과 1).

### 5.3 강제 게이트는 날조에 속지 않는다 (핵심)

적시성 함정 문항(corp-tax-0013, 이월결손금 80% 한도)을 강제 모드로 돌린 결과:

| 모델 | 실제 도구호출 | grounded | flags | 총점 |
|---|---|---|---|---|
| **opus** | **2 (법령조문)** | 제13·14조 | 없음 | **99** |
| **haiku** | **0** | — | `forced_tool_unmet`(−15) | 78 |

haiku는 게이트가 떠도 **제13조 원문을 토씨까지 정확히 인용하며 "도구 확인 완료"라 적었지만 실제 호출은 0회 — 날조**였다. `agent_steps`가 비어 `authority_used=false`였고, grounding 게이트가 이를 잡았다. 만약 이 코드 대조가 없었다면 haiku의 기억-인용과 opus의 도구-근거는 텍스트상 구별 불가능했을 것이다 — 이 대조가 도구 측정 신뢰성의 전부라는 [adr/0006](adr/0006-agent-forced-mode.md) 명제의 라이브 입증이다([findings/agent-tool-forcing.md](findings/agent-tool-forcing.md) Phase 4).

이 과정에서 라이브 실행이 아니었으면 못 잡았을 버그도 드러났다: `법령조문` 도구가 章 시작 조문(제13조)에서 章 제목만 반환하던 인코딩 문제로, "도구 거부"와 "도구 고장"이 판정을 오염시키고 있었다. 재현 테스트와 함께 수정했다([findings/agent-tool-forcing.md](findings/agent-tool-forcing.md) §발견한 버그).

### 5.4 환경 격리로 하네스 오염 완화

§3.3에서 설명한 환경 오염은 격리(`isolated=True`, sandbox cwd + `--strict-mcp-config`) 후 재스모크에서 *관측된 누출 경로가* 해소됐다. 오염을 보였던 2문항이 3게이트(검증자 프레이밍 소멸 / ReAct 도구 포착 / `forced_tool_unmet` 오탐 제거)를 모두 통과했다:

| 문항 | ReAct 도구 포착 | grounding ratio | 총점/등급 |
|---|---|---|---|
| ktb-vat-0017 | n=2 (부가세법 §61·시행령 §109) | 1.0 | 92/A |
| ktb-mixed-0002 | n=4 (소득세법 §21·시행령 §87·§129 등) | 0.75 | 88/B |

답변도 정직해졌다 — vat-0017은 "자료만으론 확정 불가"(리스크 인식), mixed-0002는 "도구로 확인한 것/못한 것 구분" + 정답(88,000원) 도출([adr/0008](adr/0008-agent-eval-isolation.md), [findings/agent-tool-forcing.md](findings/agent-tool-forcing.md) §해소).

---

## 6. 외부 벤치마크와의 비교

> 2026-06-12 실측 조사. 전체 출처·매트릭스: [findings/external-benchmark-comparison.md](findings/external-benchmark-comparison.md).

조사한 인접 벤치마크와 출처:

- **KMMLU-Pro** — 한국 국가전문자격시험 기반 2,822문항 MCQA. Tax & Accounting 도메인에 세무사 238·공인회계사 208·관세사 159문항 포함. 평가는 정답 정확도 + 공식 합격기준(과목 40%·평균 60%) 합불만 잰다([arXiv 2507.08924](https://arxiv.org/abs/2507.08924)).
- **KBL** — 한국 법률 벤치. closed-book + open-book(법률 corpus 동반) 둘 다 평가하며, open-book이 정확도를 최대 **+8.6%** 개선([arXiv 2410.08731](https://arxiv.org/abs/2410.08731)).
- **LegalBench** — 영미 법률 추론 162과제, 법률 전문가 주도 설계([arXiv 2308.11462](https://arxiv.org/abs/2308.11462)).
- **PLAT** — 한국 세법 대상이나 가산세 적법성 **이진 분류**로 협소([arXiv 2503.03444](https://arxiv.org/abs/2503.03444)).

### 핵심 차별점 5

1. **객관식 정답률 → 생성형 실무 신뢰도.** 비교 벤치는 MCQA/분류 정답·합불만 잰다. K-TaxBench는 생성형 답변을 정확성·근거성·실무성·리스크·도구의 5축으로 분해 채점한다.
2. **근거 강제 채점.** 조문·기준서 문단 단위로 인용 정확성을 코드 채점한다([adr/0007](adr/0007-citation-grader-kifrs-paragraph.md)). 비교 벤치 중 인용 정확성을 직접 채점하는 것은 없다 — 환각·날조 인용 검출이 K-TaxBench의 핵심이다.
3. **적시성.** 문항별 `time_basis` + 버전 핀으로 개정을 추적한다. KMMLU-Pro의 "최근 연도 시험"은 스냅샷일 뿐 시점 버전 관리가 아니다.
4. **(조사 범위 내) 유일한 생성형·다차원 한국 세무·회계 실무 벤치.** PLAT은 가산세로 협소하고, KMMLU-Pro 세무·회계는 객관식 자격시험이다.
5. **오염 저항(canary)·self-eval 방지(judge 비self·격리).** 비교 벤치들은 오염 추적·self-eval 가드를 다루지 않는다.

독립 교차확인(방향성): KBL도 open-book(retrieval)으로 정확도를 개선했다(+8.6%p) — retrieval가 환각을 줄여 점수를 올린다는 효과가 독립된 한국어 법률 벤치에서도 같은 방향으로 나타난다. (본 벤치의 +8.6점과 수치가 같으나 단위가 달라 — 정확도 백분율점 vs 루브릭 점수 — 우연이며 의미를 부여하지 않는다.)

> **한계(중요).** 이는 점수 직접 비교가 아니라 **설계·평가축 비교**다. KBL/KMMLU 수치는 각 논문 발표값이며 K-TaxBench와 동일 모델·동일 조건으로 재현한 것이 아니다. "처음"류 단정은 모두 "2026-06-12 조사 범위 내"로 한정한다([findings/external-benchmark-comparison.md](findings/external-benchmark-comparison.md) §4).

---

## 7. 한계와 후속

- **검수 단계.** 공개 34문항에 대한 본인 검수 라운드를 완료했다(2026-06-12; law-mcp/kifrs 원문 대조로 정확성·근거성·적시성·내부정합성·루브릭 5축 검증). 다음 단계는 외부 세무·회계 전문가 검수 프로토콜 도입이며, 전문가 검수를 통과한 문항만 `version:1.0`으로 승격한다([phases/m4-public-track/step4.md](../phases/m4-public-track/step4.md), [ROADMAP.md](../ROADMAP.md) M4).
- **judge 비결정성.** LLM-judge는 런마다 점수 분산이 있다. 재현 분산 로깅 + 전문가 스팟체크로 보정하며, 여러 finding의 결론을 "방향성"으로 한정한다(n이 작은 ablation은 단일 런).
- **표본 설계.** holdout 운영·로테이션·분야별 신뢰구간을 위한 표본 설계는 진행형이다. 분야별 신뢰구간을 주장하려면 주요 도메인별 표본을 더 키워야 한다([benchmark-design-principles.md](benchmark-design-principles.md) §7).
- **멀티프로바이더 + 단일 패밀리 한계.** 1차 범위는 Claude 계열 3모델 변별에 집중했고 judge도 Claude 계열이다. 따라서 (a) 변별 spread는 *동일 패밀리 내부* 관측이며 프로바이더 간 일반화는 미검증이고, (b) non-self judge 안전장치도 "same-family non-self" 수준이라 패밀리 단위 선호 편향(same-family preference)을 완전히 배제하지 못한다. GPT·Gemini 교차 변별 + judge-swap robustness가 후속 핵심 과제다([adr/0002](adr/0002-claude-cli-first.md), ROADMAP 2026-06-02 범위 결정).
- **통계적 강도.** 본문 핵심 수치(spread 40.2·RAG +8.6 등)는 신뢰구간·반복분산·유의성 검정이 없는 **점추정치**다. 결론은 "방향성"으로만 주장한다. 핵심 수치의 run-level variance 로깅·bootstrap CI·paired test는 후속 과제이며, 그 전까지 제목급 주장의 강도를 그에 맞춰 낮춘다.
- **construct validity 실증.** "점수 1점 = 실무 신뢰도 1"은 아직 *가설*이다. 검증 로드맵: 외부 전문가의 pairwise 유용성 랭킹과 본 점수의 상관, inter-rater 일치도, 실제 업무 위험도와의 상관 분석. IFRS 질적특성 차용은 설계 영감이며 이 매핑의 실증은 본 로드맵에 둔다(§1.3).
- **재현성 경계.** 공개 트랙(공개 34 + 리더보드 + 정책)은 재현 가능하나, 핵심 findings·holdout 문항·내부 설계기록은 비공개 검증셋의 일부로 외부 직접 재현이 제한된다. 즉 "완전 재현 가능 표준"이 아니라 **부분 재현 가능한 공개 트랙 + 비공개 검증 코어**다. 공개/비공개 재현 범위 구분과 public-34 최소 재현 절차는 §8.
- **잔여 누출·오염 경로.** 격리·canary·비self judge는 *관측된 특정* 누출을 완화할 뿐 완전 해결이 아니다. 남은 경로: ① same-family judge 선호 편향 ② 공개 법령의 모델 암기(도구 없이도 정답 → 도구 측정 우회) ③ prompt 채널 누출 ④ 로테이션 전 공개셋 오염 ⑤ canary는 공개 릴리스 시점에만 삽입되어 그 전 기간은 미적용. 각 경로의 모니터링·완화는 진행형이다.

---

## 8. 재현성

> **재현 범위(중요).** 본 벤치마크는 *부분 재현 가능*하다. **공개 재현 가능**: 공개 34문항 샘플·리더보드·제출 정책·버전 핀 규약. **외부 직접 재현 제한**: 핵심 finding의 원자료(per-run 로그)·holdout 문항·gold·내부 설계기록(ADR)은 비공개 검증셋의 일부다(채점셋 해자 + 오염 방지 목적). 공개 34만으로 재현 가능한 최소 실험 절차와 기대 출력은 공개 배포처에 동반한다.

- **버전 핀** — 모델 id·데이터 hash·스캐폴드·모드를 점수에 함께 기록한다(§3.5).
- **공개셋 34 릴리스** — 결정론적 화이트리스트로 산출되며, 공개 릴리스 시점에만 canary(`KTAXBENCH-CANARY-<uuid>` + 전역 sentinel)를 삽입한다. canary는 hash 산출 기준에서 제외되어 삽입 후에도 문항 hash가 불변이다([m4-public-sample-scope.md](m4-public-sample-scope.md)).
- **리더보드 정책** — Leaderboard Illusion의 4대 실패모드(재시도 best-pick·선택적 철회 은폐·접근 비대칭·공개셋 과적합)를 5규칙(버전핀 동결·holdout 순위 별도표기·철회불가 supersede·재현검증 등재·동일 공개셋)으로 차단한다([adr/0009](adr/0009-leaderboard-submission-policy.md)). 공개 리더보드가 이를 UI로 강제한다(https://tax-benchmark.askewly.com).
- **usage 예산 교훈** — 101 × 2모드 × 3모델 = 606 평가는 단일 5시간 구독 세션 창을 초과한다. 동시성을 과하게 높이면 서버 rate-limit을 유발해 역효과이며, 단일 프로세스 `--workers 6` + 지수 backoff 재시도가 안전하다. 세션 usage 한도는 재시도로 못 넘으므로, 차기 풀 재실행은 모델별로 세션 창을 나눠 순차 실행한다([findings/m3-rerun-101.md](findings/m3-rerun-101.md) §usage).

---

## 부록 — 근거 인덱스

| 섹션 | 주요 근거 |
|---|---|
| §1 동기 | [positioning.md](positioning.md), [benchmark-design-principles.md](benchmark-design-principles.md) |
| §2 구성 | [README.md](../README.md), [benchmark-schema.md](benchmark-schema.md), [question-blueprint.md](question-blueprint.md), [m4-public-sample-scope.md](m4-public-sample-scope.md) |
| §3 방법론 | [ARCHITECTURE.md](ARCHITECTURE.md), [rubric-v0.1.md](rubric-v0.1.md), [adr/0003](adr/0003-calculation-as-rule-proxy.md)·[0005](adr/0005-agent-react-loop.md)·[0006](adr/0006-agent-forced-mode.md)·[0007](adr/0007-citation-grader-kifrs-paragraph.md)·[0008](adr/0008-agent-eval-isolation.md) |
| §4–5 결과·검증 | [findings/m3-rerun-101.md](findings/m3-rerun-101.md), [findings/m3-rag-vs-closed-book.md](findings/m3-rag-vs-closed-book.md), [findings/agent-tool-forcing.md](findings/agent-tool-forcing.md) |
| §6 외부비교 | [findings/external-benchmark-comparison.md](findings/external-benchmark-comparison.md) |
| §7–8 한계·재현 | [phases/m4-public-track/step4.md](../phases/m4-public-track/step4.md), [adr/0002](adr/0002-claude-cli-first.md)·[0009](adr/0009-leaderboard-submission-policy.md) |
