# 발견 — agent 도구 사용은 "강제"해야 신뢰성이 생긴다

> 실험일 2026-06-09 · [ADR 0005](../adr/0005-agent-react-loop.md) agent 러너 후속 검증
> 가설: *답이 외부 사실(조문·문단)을 필요로 하면 모델이 도구를 쓸 것이다.*

## 방법
3모델 × 2 agent 문항을 실제 `claude -p` agent 모드로 라이브 평가(workflow 병렬). judge는 후보군 밖(haiku·opus→sonnet, sonnet→opus). 도구 호출은 `agent_steps`로 객관 기록.

| 모델 | mixed-0001(개방형) 도구/tool_proc/총점 | corp-tax-0012(도구강제 의도) 도구/tool_proc/총점 |
|---|---|---|
| haiku | 0 / 13 / 68 | 0 / 8 / **30** |
| sonnet | 0 / 14 / 89 | 0 / 13 / 89 |
| opus | **4(법령조문)** / 15 / 84 | 0 / 10 / 82 |

## 결과

1. **러너 라이브 검증(성공)** — opus가 mixed-0001에서 `법령조문`을 **실제 4회 호출**(부가세법 §39·§52·법인세법 §25), 러너가 라이브 DRF로 실행·반영. step2에서 네트워크 끊김(WinError 10054)이 났으나 모델이 step3 재시도로 성공 → graceful 에러처리·재시도가 실전에서 작동. **agent 러너 + DRF 통합은 프로덕션 동작 확인.**

2. **가설 반증** — corp-tax-0012(감가상각 800만원·운행기록 1,500만원 한도)는 **3모델 전부 도구 0회**. opus 답변: *"핵심 규정이 모두 확인되어 추가 도구 호출은 불필요합니다."* — 유명 한도는 기억으로 답한다.

3. **역설** — 개방형(mixed-0001)이 특정형(A)보다 도구를 더 유발(opus 4 vs 0). 광범위한 종합검토는 grounding을 위해 조회를 부르지만, 아는 룰 계산은 안 부른다.

4. A는 **정확성으론 변별**(haiku 30 vs sonnet/opus 82~89 — 약모델이 기억으로 틀림)하나 **tool_process는 변별 못 함**(아무도 안 씀).

## 해석

**도구-강제 ≠ "검색 가능한 사실을 필요로 함".** 진짜 조건은 **모델이 그 사실을 *확실히 모름*** 이다. 유명 한도는 암기되어 있어 모델이 도구 없이 (강모델은 정확히, 약모델은 틀리게) 답한다. 모델의 자발적 도구 사용에 의존하면 측정이 불안정하다.

## 함의 (M4 구성타당도)

⑤도구 사용성은 **두 하위 구성**이다:
- **판단(when)** — 도구가 필요함을 인지하는가 → `agent`(자유) 모드 + *기억으로 못 푸는* 문항
- **실행역량(can)** — 강제되면 올바른 도구를 정확히 호출·통합하는가 → `agent_forced`(게이트) 모드

신뢰성 있는 측정은 **강제 + 근거매칭**에서 나온다([ADR 0006](../adr/0006-agent-forced-mode.md)): 권위 도구 사용을 게이트로 강제하고, 최종 답이 인용한 조문이 *실제로 조회된 것인지* 코드로 대조(기억-인용 vs 도구-근거). 자유 모드는 판단 측정용으로 병존한다(둘은 별개 점수축).

## 한계
- n=2 문항·3모델·단일 런 — 방향성 결론. judge 분산 존재.
- 강모델 1종(opus)만 자발적 도구 사용 — 표본 확대 필요.

---

# Phase 4 — agent_forced 강제모드 라이브 검증 (2026-06-09)

> [ADR 0006](../adr/0006-agent-forced-mode.md) 강제모드를 haiku·opus 라이브로 검증(judge=sonnet). 자유모드 finding(위)의 후속 — "강제하면 측정이 신뢰성 있어지는가?"

## 결과 — 게이트는 날조에 안 속는다 (핵심)

corp-tax-0013(이월결손금 80% 한도, *적시성 함정*)을 강제모드로 돌린 최종 결과:

| 모델 | 실제 도구호출 | grounded | flags | 총점 | 행태 |
|---|---|---|---|---|---|
| **opus** | **2 (법령조문)** | 제13·14조 (ratio 0.67) | 없음 | **99** | DRF로 80%/100% 원문 확인 + 미확인부 정직 구분 |
| **haiku** | **0** | — | `forced_tool_unmet`(-15) | 78 | "법령조문 도구 확인 완료"라며 원문을 토씨까지 인용 — *실호출 0회(날조)* |

1. **강제 게이트가 실도구를 유발 — 단 모델 의존적.** opus는 강제 하에 **0→2회** 실제 호출하고 80% 한도를 *실제 조회*(`fetched=[제13,14조]`)에서 grounded. haiku는 게이트가 떠도(`forced_tool_unmet`) 날조로 우회.

2. **`authority_used`는 날조를 통과시키지 않는다.** haiku 답은 제13조 원문을 정확히 인용하고 "도구 확인 완료"라 적지만 `agent_steps`가 비어 `authority_used=false`. **grounding 게이트가 없으면 haiku의 *기억-인용*과 opus의 *도구-근거*는 텍스트상 구별 불가** — 이 코드 대조가 ⑤도구 측정 신뢰성의 전부다. ADR 0006 명제의 라이브 입증.

3. **감점 메커니즘 정확.** `forced_tool_unmet`(-15)·`ungrounded_citation`(-10)·`fake_source`(-20)·`assert_without_source`(-10) 점화·합산 모두 정확(1차 런 haiku corp-0012 = -10-20=**-30**, mixed = -15-10=**-25** 검산 일치).

## 발견한 버그 (라이브가 아니었으면 못 잡음)

1차 강제 런에서 corp-0013가 양 모델 모두 도구를 못 ground → 격리해보니 **`법령조문` 도구가 제13조에 章 제목(44자)만 반환**. 원인: DRF는 편/장/절 제목을 *같은 조문번호의 pseudo-조문단위(조문여부="전문")*로 인코딩 → 章 시작 조문(제13조)은 제목 전문이 먼저 매치. `_extract_article_branch`에 전문-skip 추가로 수정([fix 1d875aa], 재현 테스트 포함). 제25·34조는 章 시작이 아니라 무영향. **"도구 거부 vs 도구 고장"이 ①② 판정을 오염시킨 교란변수였고, 라이브 실행만이 이를 드러냈다.**

## 함의

- ⑤도구 **실행역량(can)** 축은 강제모드 + grounding으로 *측정 가능*함이 확인됐다(opus 99 vs haiku 78, 근거가 진짜냐로 갈림).
- agent 문항(Task D) 확충 시 **corp-0013(A') 패턴이 본보기** — 적시성 함정 + 강제모드면 강모델은 도구로 grounding, 약모델은 날조→감점으로 변별된다.
- haiku의 날조 행태는 별도 추적 가치 — *약모델은 강제 하에서 도구사용을 "연기"한다*.

## 한계
- corp-0013 단일 문항 깨끗한 런 — mixed-0001·corp-0012는 1차 런에서 도구 고장·judge 분산 섞임(재실행 권장).
- haiku 1종만 날조 관측 — sonnet 등 중간 모델 표본 필요.

## 후속 스모크 — 하네스 오염 발견 (vat-0017·mixed-0002, opus forced)

신규 agent 문항 2개를 opus 강제 스모크한 결과, opus가 **블라인드 에이전트가 아니라 "벤치마크
검증 리포트"로 응답**했다(예: *"검증 결과: 모델 답안 정확 … 모델 인용 ↔ 도구 조회 원문 대조 표 …
agent_forced 게이트 핵심 통과"*). 원인 추정:
1. **CLAUDE.md 오염** — 후보 모델을 벤치마크 레포 cwd 에서 `claude -p` 로 실행 → 레포 CLAUDE.md
   (judge 규약·게이트·환각·루브릭 어휘)를 읽고 자신을 *문항 검증자*로 프레이밍.
2. **MCP 우회** — eval 의 ReAct `[도구]` 프로토콜 대신 환경의 `law-mcp` MCP 로 조회 → `agent_steps`
   에 안 잡혀 `n_tool=0`·`forced_tool_unmet` **오탐**(실제론 MCP 로 조회·검증함).

**판정**: 문항 자체는 유효(opus 가 88,000원·60%vs80% 분별을 독립 재현 → **gold 정확성 확인**). 그러나
agent_forced *eval* 은 CLI+MCP 모델에서 신뢰 불가. Phase 4·corp-0013 재실행 땐 정상 ReAct(n_tool≥1)
였는데 이번엔 오염 — **모델/런 편차**라 더 위험(같은 모델이 런마다 다르게 행동).

**다음 세션 선결**: 에이전트 eval 격리 — ① 후보 `claude -p` 를 레포 밖 cwd 또는 CLAUDE.md 미주입으로
실행 ② 경쟁 MCP(law-mcp) 차단해 eval ReAct 도구만 노출 ③ 그 후 신규 6개 agent 문항 재스모크.

### 해소 (2026-06-10) — 격리 후 재스모크로 오염 제거 입증 ([ADR 0008](../adr/0008-agent-eval-isolation.md))

진단 확정: `prompts.py` 의 agent 시스템 프롬프트는 깨끗(순수 세무 전문가 + `[도구]` 지시) — 오염은
100% 환경발. 행동 probe(haiku)로 두 벡터를 분리 확인:

| 환경 | MCP | 프로젝트 CLAUDE.md |
|---|---|---|
| 레포 cwd, 격리 없음(현행) | `law-mcp(6)`·notion·playwright·google 등 전부 | `CLAUDE로드`(전역+프로젝트+메모리) |
| sandbox cwd + `--strict-mcp-config` | **도구없음** | **CLAUDE없음** |

수정: `ClaudeCLIClient(isolated=True)` — 레포·home 밖 빈 sandbox cwd(`C:/ktaxbench-sandbox`) +
`--strict-mcp-config`. 구독 인증 유지. 전 모드+judge 일괄.

**재스모크(opus, agent_forced, judge=sonnet, 오염 보였던 2문항) — 3게이트 전부 PASS:**

| 게이트 | ktb-vat-0017 | ktb-mixed-0002 |
|---|---|---|
| ① 검증자 프레이밍 | 소멸 — 블라인드 `[최종]` 답(간이과세 판단) | 소멸 — 블라인드 `[최종]` 답(기타소득 원천징수) |
| ② ReAct `[도구]` 포착 | **n=2**(부가세법 §61·시행령 §109) | **n=4**(소득세법 §21·시행령 §87·§129·§129①6호) |
| ③ `forced_tool_unmet` 오탐 | `authority_used=True`·ratio 1.0·`flags=[]` | `authority_used=True`·ratio 0.75·`flags=[]` |
| 총점/등급 | 92/A | 88/B |

오염 run 의 `n_tool=0`·검증자-리포트·오탐이 격리로 사라지고, opus 가 eval ReAct 로만 조회해
인용을 실조회에 grounding(vat 1.0·mixed 0.75). 답변도 정직 — vat-0017 "자료만으론 확정 불가"
(리스크 인식), mixed-0002 "도구로 확인한 것/못한 것 구분" + 88,000원 정확. 출력
`outputs/agentforced-isolation-smoke/`(gitignored). **agent_forced eval 신뢰성 회복.**

**잔여**: ⚠ Claude Code 내장도구(Read/Bash)는 sandbox 에 남으나 빈 디렉토리라 세무 답에 무용 →
ReAct 폴백 확인됨. 누설 관측 시 `--disallowedTools`(후속). 신규 agent 문항(B 단계)은 이 격리
러너로 스모크한다.
