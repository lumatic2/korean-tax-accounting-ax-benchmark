# M4+ R1 — 다중 프로바이더 교차변별 + judge-swap (Claude × GPT)

> 2026-06-13~14 실행·검증. 기존 101문항(closed/rag)에 타 벤더를 돌려 "단일 Claude 패밀리" 공격을 해소하고, judge 패밀리 교체에 따른 순위 안정성(robustness)을 측정. **Gemini 는 제외**([ADR 0011](../adr/0011-gemini-excluded-from-r1.md)).
>
> ⚠ **수정 고지**: 초안 리포트(외부 antigravity 아티팩트)는 "Same-Family Bias +24.8 / Claude judge 하 랭킹 역전(Claude 86.3 > GPT 68.0)"을 헤드라인으로 냈으나, 오케스트레이터 원문 재검증 결과 **그 수치는 N 불균형 + judge JSON 호출 실패의 silent 0.0 둔갑 아티팩트**임이 드러났다(§3·§3-1). 본 문서가 정정본이며 초안 헤드라인은 폐기한다. **근본 원인(파이프라인 버그)은 §3-1 에서 규명·수정 완료**(2026-06-14, R4 선행 디버그).

## 실행 구성

- 데이터: `data/sample-questions-v0.1.jsonl` 101문항 × {closed_book, rag} = 최대 202 (문항,모드) 쌍
- 후보: **claude-sonnet-4-6** (claude_cli) · **gpt-5.5** (codex_cli, `codex exec`) — [ADR 0010](../adr/0010-multi-vendor-cli-subprocess.md)
- judge: **claude-sonnet-4-6** ↔ **gpt-5.5** (교차) — judge-swap robustness
- 격리: 레포 밖 sandbox cwd + MCP/도구 차단(ADR 0008). 재채점은 `scripts/regrade_results.py`(동일 답안에 judge만 교체).
- 출력(gitignored): `outputs/m4r1/*.jsonl`, claude 원본은 `outputs/m3-rerun-101-20260611/claude-sonnet-4-6_20260611T124222Z.jsonl`

### 완주율 (★해석의 전제)

| 후보 | 완주 (문항,모드) | 비고 |
|---|---|---|
| GPT-5.5 | **202 / 202** | 전건 완주 |
| Claude-Sonnet-4.6 | **119 / 202** | M3 run 의 세션 usage 한도(rate-limit 아님) — 누락 83은 risk/case/calc 등 hard 편중 |

→ **완주 문항수가 다르다.** 따라서 모든 후보-간 비교는 **공통 119쌍**(양쪽 다 완주)으로만 한다. 전체평균(다른 N) 직접 비교는 금지.

## 결과

### ① 2-벤더 교차변별 — 공정 페어(clean-116, judge별)

같은 답안, **judge 만 교체**. 양쪽 후보가 완주한 공통 119 중, **judge JSON 실패 3건(아래 §3·R4)을 제외한 clean-116**이 최종 기준:

| 후보 | Claude judge | GPT judge |
|---|---|---|
| GPT-5.5 | **89.3** | **93.5** |
| Claude-Sonnet-4.6 | **88.6** | **86.5** |

→ **GPT 가 두 judge 모두에서 Claude 를 근소 우세**(judge 무관). 독립 벤더(OpenAI) 점수가 산출되어 "단일 Claude 패밀리" 공격 해소. **랭킹 역전 없음.**

> ⚠ **정밀화(2026-06-14, R4 선행 디버그)**: 종전 공통 119 표(GPT 89.1/93.5, Claude **86.3**/86.1)는 119 안에 섞인 judge-실패 3건(전부 Claude 답안의 claude judge)을 0.0 으로 집계해 Claude 의 claude-judge 를 86.3 으로 눌렀다. 제외한 clean-116 에서 Claude claude-judge 는 **88.6**. 방향성 결론은 불변.

### ② judge-swap robustness — 작지만 비대칭

clean-116 기준 judge 교체 시 점수 변화(swing):

| 후보 | Claude→GPT judge swing |
|---|---|
| GPT-5.5 | **+4.2** (89.3 → 93.5) |
| Claude-Sonnet-4.6 | **−2.1** (88.6 → 86.5) |

→ GPT 는 자기 패밀리(GPT) judge 에서 +4.2 상승, Claude 는 자기 패밀리(Claude) judge 에서 +2.1 높음. **각 후보가 자기 패밀리 judge 를 소폭 선호하는 *방향*은 존재하나 크기는 작다**(논문엔 "modest, directional"로). 두 벤더 모두 reviewer 에게 줄 메타 결과: judge 패밀리 선택이 ±2~4점을 움직인다.

### ③ ★초안 "+24.8" 헤드라인은 아티팩트 (정정)

초안은 GPT 를 **전체 202**(Claude 가 못 푼 83 포함)로 채점해 Claude judge 평균 68.0 → GPT judge 92.8 = **+24.8**, "Claude judge 하 GPT 68.0 < Claude 86.3 역전"을 주장했다. 그러나:

- 그 **+24.8 swing 의 거의 전부가 Claude 누락 83문항에 집중**(공통 119에선 +4.3뿐).
- 83문항 task_type 별 judge 격차가 **비현실적**:

| task_type (83문항) | Claude judge | GPT judge | Δ |
|---|---|---|---|
| risk_analysis (23) | **3.5** | 93.8 | +90.3 |
| case_reasoning (14) | **11.7** | 89.8 | +78.1 |
| calculation (18) | 58.8 | 98.4 | +39.6 |
| agent_workflow (20) | 64.7 | 87.8 | +23.1 |
| citation (8) | 66.9 | 84.9 | +18.0 |

→ risk_analysis 에서 Claude judge 3.5 vs GPT judge 93.8 같은 +90 격차는 "self-preference 관대함"으로 설명 불가 — **채점 파이프라인 아티팩트** 신호다. 초안의 +24.8 은 *벤더 편향*이 아니라 *그 83문항 채점 붕괴*가 GPT 의 전체평균을 끌어내린 것.

### ③-1 ★근본 원인 규명 완료 (2026-06-14, R4 선행 디버그)

raw 레코드 직접 검시로 원인 확정 — **fatal flag·forced 게이트가 아니다. judge 가 파싱 가능한 JSON 을 못 낸 호출 실패가 조용히 0.0/D 로 둔갑한 파이프라인 버그였다.**

- **메커니즘**: Claude judge(claude_cli)가 일부 레코드에서 비-JSON 응답 → `judge_answer` 가 `ValueError`(재시도도 실패) → 러너가 예외를 잡아 `judge={"error":…,"scores":{}}` 저장 → `combine()` 이 빈 scores 를 받아 전 차원 0.0 → `total=0.0/grade D`. 답안 자체는 2,300~2,500자로 멀쩡하고 GPT judge 는 같은 답을 83~100 으로 채점.
- **정량**: Claude judge **58/202** 레코드가 이 실패(GPT judge 는 **0/202**). task_type 분포 risk 22·calc 18·case 12·agent 4·citation 2.
- **왜 risk/case 가 최악인가**: risk_analysis·case_reasoning 은 **순수 주관 채점**(code_grader 없음) → judge 실패 = total 0. calculation 은 code_scores 가 차원을 메워 58.8 로 부분 생존. 이게 §3 표의 격차 순서(risk +90 > case +78 > calc +40 > agent +23)를 정확히 설명.
- **수정**(코드): 집계기 `report.aggregate_results` 가 judge-실패 레코드를 제외(`judge_failed()` 헬퍼, 구·신 데이터 공통 `judge.error` 시그널) + 생산자 `runner.py`·`scripts/regrade_results.py` 가 `final.judge_error` 마커 부착 + 소스 버그(`if judge and "scores" in judge` 가 error dict 도 통과) 차단. 재현 테스트 `tests/test_report.py::test_aggregate_excludes_judge_failed_records`. **picture 재집계**: GPT 의 Claude-judge 202 평균 naive 68.0 → judge-실패 제외 시 **88.1**(vs GPT judge 92.8 = +4.7) — +24.8 아티팩트가 집계 수준에서 해소.
- ⚠ **미규명 잔여**: *왜* Claude judge 가 비-JSON 을 냈는지(세션 usage cap 추정)는 당시 raw 미저장이라 비복원이었다 → **M6 에서 규명·해소**(§3-2). 재발 방지(원문 로깅·재시도/제외)는 M6 step0 에서 코드화됨.

### ③-2 ★heal 재채점 + 신뢰구간 (2026-06-14, M6 step2~3)

§3-1 은 judge-실패 58건을 *집계 제외*해 생존 144건으로 88.1 을 냈다. M6 에서 judge 파서를 강건화(코드펜스·trailing prose·balanced-brace 추출, step0)하고 `regrade_results.py --only-failed`(judge-only·답안 보존·`--workers`)로 그 58건만 재채점했다 — **judge_failed 58 → 0, 잔존 0**. 이제 제외 없이 full-202 산출 가능.

| 집합 | avg | 95% CI (bootstrap, n=3000, seed=0) |
|---|---|---|
| GPT-5.5 × claude judge, **heal후 full-202** | **87.92** | [86.22, 89.57] |
| ├ survivors 144 (heal 전에도 정상) | 88.07 | [86.06, 90.02] |
| └ healed 58 (종전 silent-0) | 87.54 | [84.11, 90.36] |

- **healed 58 ≈ survivors 144 (CI 광범위 겹침)** → 종전 "58 제외"가 **편향 없는** 처리였음을 사후 검증. silent-0 아티팩트는 *품질 신호가 아니라 순수 호출/파싱 실패*였다는 §3-1 결론의 1차 실증(construct validity).
- **재호출+강화파서로 58/58 복구·잔존 0** → 실패 원인이 영구적 truncation 이 아니라 *일시적/파싱 취약성* 쪽이었음을 시사(미규명 잔여 해소).
- **judge-swap full-202 (paired, 같은 GPT 답안)**: GPT judge − claude judge = **+4.87** [4.20, 5.52], p≈0.0 → §2 의 "modest, directional self-preference"가 full-N·CI 로 재확인(0 미포함=유의, 크기는 ~5점으로 작음). 종전 부분-N +4.7 과 일치.

> 방법: CI 는 `ktaxbench.stats.bootstrap_ci`/`paired_bootstrap_diff`(scipy 무의존·시드 고정 결정론, M6 step1). 재집계는 `report.ci_summary`(judge_failed 제외 — 이제 0). raw: `outputs/m4r1/gpt-5.5_20260613T092709Z_regraded.jsonl`(gitignored).

### ③-3 ★run-to-run 비결정성(variance) — temp=0 에도 단일런 노이즈 큼 (2026-06-15, M6 옵션)

§3-2 의 bootstrap CI 는 *어떤 문항이 뽑혔나*(샘플링) 불확실성을 잰다. 이는 *같은 입력을 다시 돌리면 점수가 달라지나*(재실행 비결정성)와는 **다른 불확실성 원천**이다. 후자를 직접 측정했다 — 같은 (문항, mode)를 N=5 회 채점(`scripts/variance_run.py`, candidate `claude-haiku-4-5` × judge `claude-sonnet-4-6`, closed_book, **temperature=0**, 도메인별 1문항 6개). 활성 eval 경로(CLI subprocess + 구독 인증, ADR 0002/0010) 그대로 N 회 반복.

| 지표 | 값 |
|---|---|
| 완전안정 문항(std=0) | **0 / 6 (0%)** |
| 문항별 점수 std | 평균 11.71 · **최대 19.84** (100점 척도) |
| 문항별 점수 range(max−min) | **최대 60.0** (income-tax-0001: 61↔1) |
| run-mean std (집계 평균의 run간 진동) | **8.62** (run-means = 64.4·39.7·50.3·43.3·45.2) |
| pooled total 95% CI | [38.79, 56.87] |

- **temperature=0 인데도** 모든 문항이 run 마다 흔들렸다(완전안정 0%). CLI subprocess/서버측 샘플링의 잔여 비결정성 — 결정론 설정이 결정론 채점을 보장하지 않는다.
- **단일런 점수로 모델을 순위매기는 것은 위험**하다: 문항 수준 std 가 최대 ~20점, 집계 평균조차 run 간 std 8.6 → 두 모델의 ~5점 차(§3-2 judge-swap 크기와 동급)는 단일런이면 noise 에 묻힌다. **다회 평균 + CI(§3-2)·페어 검정(같은 답안 고정)이 필수**임을 경험적으로 뒷받침.
- **한계(파일럿)**: 6문항·1모델·N=5 소규모. 측정값은 candidate 생성 + judge 채점의 **end-to-end 합성 분산**(둘을 분리하지 않음). 더 큰 N·문항·모델별 특성화·candidate↔judge 분산 분해는 M8 흡수 가능.

> 방법·raw: `scripts/variance_run.py` → `outputs/m6-variance/claude-haiku-4-5_20260614T184542Z/`(run별 jsonl + `variance_report.json`, gitignored). 실패 run(transient error·judge 실패)은 silent-0 아닌 *제외* 처리([[judge-failure-silent-zero]], §3-1).

### ④ R4(judge 검증)와의 관계 — 정정

종전 §4 는 위 극단 불일치를 "**주관 채점 차원에서 LLM-judge 신뢰성 자체가 낮다**"의 단서로 읽었으나, §3-1 로 그 해석은 **기각**된다 — 불일치의 정체는 judge 의 *품질 판단 차이*가 아니라 judge **호출 실패**(인프라/파싱)였다. 따라서 이 아티팩트는 R4(전문가 인간채점 ↔ LLM-judge κ)의 근거가 아니다. R4 는 **judge 가 정상 채점한 레코드**에 대해 인간 채점과의 일치도를 따로 측정해야 하며, 그 전제로 judge 응답 신뢰성(JSON 성공률·재시도)을 먼저 확보해야 한다.

## Gemini (제외 — provisional)

[ADR 0011](../adr/0011-gemini-excluded-from-r1.md): Antigravity CLI(`agy`)는 headless 부적합(행), Gemini CLI 는 gemini-2.5 한정·쿼터 락·격리 P0 미해결. 수집된 gemini-2.5-flash 182/202(GPT judge 70.3)는 **격리 미검증·구버전**이라 정식 점수로 쓰지 않는다. 3번째 벤더는 Gemini API 키 경로 또는 Antigravity headless 개선 시 후속.

## 한계

- **small-n·공개셋 medium 편중** — 변별 폭의 일반화 주의(M4+ 전반 한계).
- **Claude 119 vs GPT 202** — 공통 119로만 비교했으나, Claude 의 누락 83(hard 편중)을 Claude 가 풀었다면 결과가 달라질 수 있음. 향후 Claude 풀 완주 재실행 필요.
- **judge-swap 1쌍**(Claude↔GPT) — Gemini-as-judge 미실시.
- **GPT 자기채점(gpt-judge-on-gpt)은 bias *측정* probe** — 정답 인증 아님(Judge 규약). 리더보드 점수로 쓰지 말 것.
- ~~risk/case 채점 붕괴의 근본 원인은 미규명~~ → **규명 완료**(§3-1): judge JSON 호출 실패의 silent 0.0 둔갑(파이프라인 버그, 수정됨). 잔여는 *왜 비-JSON 이었나*(judge 응답 원문 미저장 → 비복원).

## R1 verify 충족

- ✅ ≥2 독립 벤더(Anthropic·OpenAI) 교차변별 리포트 산출 → "단일 패밀리" 공격 해소. (≥3 목표는 ADR 0011 로 2-벤더 축소.)
- ✅ judge-swap robustness 1건(Claude↔GPT, 공통 119 페어).

## 인용 (raw)

- `outputs/m4r1/gpt-5.5_20260613T092709Z.jsonl` (GPT, claude judge, 202)
- `outputs/m4r1/gpt-5.5_regraded_gpt_judge.jsonl` (GPT, gpt judge, 202)
- `outputs/m4r1/claude-sonnet-4-6_regraded_gpt_judge.jsonl` (Claude, gpt judge, 119)
- `outputs/m3-rerun-101-20260611/claude-sonnet-4-6_20260611T124222Z.jsonl` (Claude, claude judge, 119)
- `outputs/m4r1/gemini-2.5-flash_20260613T140934Z.jsonl` (Gemini, 제외·provisional)
