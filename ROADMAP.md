# ROADMAP — K-TaxBench

> 마지막 업데이트: 2026-06-16 (세션 15)
> 한국 회계·세무 AI가 "그럴듯하게 말하는가"가 아니라 **"실무 검증을 통과했는가"**를 재는 표준 평가 인프라.
> 회계법인 AI 부서가 벤더·자사 에이전트를 줄 세우는 잣대 → 포트폴리오이자 창업 아이템.
> 설계 근거: [docs/benchmark-design-principles.md](docs/benchmark-design-principles.md) · 데이터: [docs/data-strategy.md](docs/data-strategy.md) · 도메인: [docs/DOMAIN.md](docs/DOMAIN.md)

## 방향 결정

- **(2026-06-01)** 포트폴리오 증명 + 창업 검증 **병행** / 본인검수 먼저 → 외부 전문가(신뢰도 단계) / 평가 3모드(closed·rag·agent) 전부 / 방법론 기술리포트 공개 트랙 포함.
- **(2026-06-14) 북극성 = 공개 완결 먼저.** M0~M4 코어 완료. 다음 active 트랙은 **공개 샘플셋 릴리스·canary·리더보드 완성도**(가시적 결과물·코드로 즉시 가능). 신뢰도강화(외부검수·judge검증·통계)와 사업화는 그 뒤/병행.

---

## ✅ 완료 코어 — M0~M4 (압축)

> 기획 → 문항셋 → 실행기 → 평가 → 공개 트랙까지 한 사이클 완주. 상세는 변경 이력·각 docs.

- **M0 기획·설계** ✅ — 설계원리(회계 개념체계 spine)·외부벤치 8종 리서치·데이터전략(저작권 안전선: 기출=시드·표현 재작성)·DOMAIN(부가세·법인세 2026 검증).
- **M1 문항셋** ✅ — **101문항** 6도메인(vat·corp·income·accounting·basic·mixed) × 6 task_type(citation·case·risk·calc·agent·MCQA). 전 문항 law.go.kr DRF·kifrs DB 검증 + 기준일·hash·visibility 라우팅. 공개 34문항 본인검수(`internal_reviewed`). 스키마 [benchmark-schema.md](docs/benchmark-schema.md)·확충 청사진 [question-blueprint.md](docs/question-blueprint.md).
- **M2 실행기(3모드)** ✅ — closed_book/rag/agent 러너 + 버전핀 + code+judge 채점(statement 부분점·pass^k) + 격리([ADR 0008] sandbox cwd·strict-mcp). ReAct agent([ADR 0005·0006]). 결정론 테스트.
- **M3 파일럿 평가** ✅ — Claude 티어 변별 성립(spread 40.2 · RAG +8.6 환각감소 · 노이즈 0). 벤치마크가 실패모드(환각·계산오류·근거오류)를 검출함을 증명.
- **M4 공개 트랙** ✅(코어) — **리더보드 라이브** [tax-benchmark.askewly.com](https://tax-benchmark.askewly.com)([ADR 0009] 「Leaderboard Illusion」 4대 실패모드 차단) + 기술리포트([블로그 라이브](https://askewly.com/blog/tax-ai-verify-not-fluent)·KO [m4-tech-report.md](docs/m4-tech-report.md)·**EN** [m4-tech-report-en.md](docs/m4-tech-report-en.md)) + citation grader([ADR 0007]). **잔여 → M5**: canary 삽입·공개 샘플셋 릴리스.
- **M4+ R1 다중 프로바이더** ✅ — Claude×GPT 2-벤더 교차변별([ADR 0010] CLI 어댑터, [ADR 0011] Gemini 제외) + judge-swap. "단일 패밀리" 공격 해소. 근본원인 규명까지 닫힘(세션 11). finding [m4r1-multi-provider.md](docs/findings/m4r1-multi-provider.md).

**완료 verify**: M1 채점가능 고품질셋 ✅ / M2 같은입력→같은점수 ✅ / M3 유의미 변별 ✅ / M4 공개·인용가능 게시 ✅(릴리스 잔여) / R1 2독립벤더 교차변별 ✅.

---

## 앞으로 — 공개완결 · 신뢰도 · 사업화

> 북극성 = **공개 완결 먼저**. 경로: **M5 ✅ ∥ M6 ✅ → M7 섭외(리드타임·active) → M8(M7 게이트) → M9(병행)**. arXiv 제출은 M8. **다음 P0 = M7 외부검수(네트워킹 병목).**

## Active Milestones

<!-- harness:milestone id="N1-publication-safe-portfolio-release" status="completed" priority="P0" evidence="uv run pytest; validate_questions; package_release; git ls-files boundary; strict secret scan" -->
### N1 — Publication-safe portfolio release
- DoD: README is public-facing; tracked public data contains only release-safe rows; private/holdout assets are excluded or moved to ignored paths; targeted secret/data-boundary scan passes; validation/test smoke passes.
- Evidence: uv run pytest; validate_questions; package_release; git ls-files boundary; strict secret scan
- Gap: The repo is still private, but publication would currently expose internal holdout rows and an internally oriented README.
- Status: [x]
- Completed at: 2026-06-18
- Summary: Publication-safe tracked tree: README public-facing, data sample public_sample-only, private holdout ignored, validation gates passed.

### M5 (P0 · 코드) 공개 완결·릴리스 ★북극성 — ✅ 완료(세션 12)
- [x] canary 삽입 스크립트(`scripts/insert_canary.py` 멱등·hash 불변) → [x] 릴리스 번들 패키징(`scripts/package_release.py`) → [x] **공개 샘플셋 34문항 v1.0 릴리스**(`lumatic2/ktaxbench-leaderboard` data/public/, fa60507) → [x] 리더보드 두 컬럼 라이브(이미 구현).
- ✅ **verify 충족**: 외부 fresh clone 34행 재현·raw/Pages URL 200 / canary 오염탐지 경로(공개 MANIFEST sentinel + 비공개 probe 기록) / 리더보드 holdout순위+공개셋 두 컬럼 라이브([tax-benchmark.askewly.com](https://tax-benchmark.askewly.com)).
- 운영함정 수정: Pages 재배포가 직접 push 한 data/ 를 덮을 위험 → 번들을 `leaderboard/public/data/` 빌드자산으로 포함(영구). 상세 [m4-public-sample-scope.md](docs/m4-public-sample-scope.md).
- 후속(세션 13) ✅: 재배포 **자동화** `scripts/deploy_leaderboard.sh`(빌드→`out/data/public/release.jsonl` assert→클론 동기화→커밋→`--push`). rsync 무의존 git diff 동기화. 재빌드가 공개셋 4파일 안 덮음을 origin diff로 실증.

### M6 (P1 · 코드) 측정 신뢰성 — judge + 통계 — ✅ 완료(세션 12)
- [x] judge 강건화(`grading/judge.py` balanced-brace 파서·코드펜스 스트립·프롬프트 강화 — JSON 성공률↑) → [x] **58 judge-fail 재채점**(`regrade_results.py --only-failed` 신규, claude judge, **58→0 잔존0**) → [x] 통계강도(`ktaxbench/stats.py` bootstrap CI·paired diff·spread CI, 무scipy·결정론).
- ✅ **verify 충족**: 핵심수치 CI 동반(GPT×claude-judge full-202=87.92 [86.2,89.6] / judge-swap +4.87 [4.2,5.5] p≈0) + healed58≈survivors144(제외 unbiased 실증). finding §3-2.
- 잔여(옵션) 후속(세션 13) ✅: variance 반복런 `scripts/variance_run.py` 라이브 N=5(haiku×sonnet, closed_book, **temp=0**) — 문항별 std 최대 19.84·range 최대 60·집계 run-mean std 8.62·완전안정 0% → 단일런 순위 위험·다회평균+CI 필수 실증(finding §3-3). judge 인간채점 κ는 M8.

### M7 (P0 병목 · 네트워킹, 코드 아님) 외부 권위 검수 — gold 신뢰성
- [단계] 외부 세무·회계 전문가 1~2인 섭외 → step4 프로토콜(`phases/m4-public-track/step4`)로 공개34 + 신규 검수 → `status:expert_reviewed`·`version:1.0` 승격.
- → **verify**: ≥30문항 expert_reviewed(`reviewers[]`에 외부인), 본인검수 → 외부검수 2단 게이트 작동.
- **리드타임 긴 병목 — 지금부터 병렬 섭외.** 저자 외 권위 = 진짜 병목, **M8 게이트**(없으면 영원히 self-review).

### M8 (P1 · M7 게이트) 문항확장 + judge 인간검증 + arXiv
- 🔄 문항확장(구 R3, **M7 독립 — 진행 중**): blueprint §6 목표(100)는 실측 101로 달성 → §6-4에 **가중치 ×3 목표 300·신규 199** 명세 고정. 누적 **101→173 (+72)**: 세션14 +26(101→127), **세션15 +46(127→173)** = 국기법 citation +12·법인세 case +12·부가세 case +12·소득세 citation +10. 완성 셀: 부가세②근거 / 회계③실무(부분) / 법인세②근거·③실무 / 국기법②근거 / 부가세③실무 / 소득세②근거. hard/expert를 holdout에 집중(공개셋은 medium 유지). 잔여 갭 ~127. judge κ 부분만 M7 게이트.
- judge 인간채점 검증(구 R4 본): 전문가 인간채점 ↔ LLM-judge 일치도(상관·Cohen's κ, M7 표본 재활용). ※ 세션 11 규명대로 judge **호출 신뢰성(M6)** 선확보가 전제 — 정상 채점 레코드에 대해서만 κ 측정.
- arXiv 제출: M6~M8 선결 후. 정정 수치(공정페어 **clean-116**) 반영, LaTeX·endorsement(cs.CL)·영문 정독.
- → **verify**: 도메인×역량 매트릭스 목표 셀 충족 + judge-인간 일치 metric(construct validity 1차 실증) + arXiv 게시.

### M9 (병행) 사업화·고객 검증
- Big4/세무법인 1곳+ 파일럿(자사·벤더 에이전트 평가) + 기업 평가리포트 서비스 + 인증배지(Bronze/Silver/Gold) + 비공개 검증셋 운영(로테이션·제출제한).
- → **verify**: 파일럿 1곳 이상 성사, 기업 평가리포트 1건 전달. **신뢰자산(M6~M8)이 판매셋 신뢰도와 공통 자산.**

---

## 가로지르는 원칙

- **judge 규약**: 모든 문항·정답·수치는 외부 권위 인용 + 기준일. self-eval 금지. (CLAUDE.md)
- **적시성**: 법 개정마다 v2025/v2026 버전. 신선 문항 = 오염저항 + 해자.
- **저작권**: 기출=시드, 표현 전면 재작성. 상업화 전 변호사 검토(data-strategy §2.4).
- **남은 [확인]**: 법령 Open API 약관, 예규 §7 지위, DeonticBench 구조, 분야별 표본설계.

## 변경 이력

- 2026-06-16 (세션 15) — **M8 문항확장 4배치 +46(127→173)**: 셀 5개 완성 — ① 국기법 citation +12[law-mcp, basic-tax-law-0013~0024, 셀②근거 6→18] ② 법인세 case_reasoning +12[corp-tax-0031~0042, 셀③실무 6→18] ③ 부가세 case_reasoning +12[vat-0033~0044, 셀③실무 3→15] ④ 소득세 citation +10[income-tax-0020~0029, 셀②근거 5→15]. law-mcp 30조문(국기법·법인세·부가세·소득세 + 시행령) 전건 선검증. **핵심학습**: 라이브 Workflow가 세션한도(자정 리셋)+StructuredOutput 루프로 부분실패(법인세 draft 7/12, resume도 stuck) → **복구경로 확립**: TaskStop→완료분 취득→누락분 오케스트레이터 인라인 작성. 부가세·소득세는 아예 *law-mcp 전건 선검증→인라인*으로 yield 100%·한도 리스크 0 — **대규모 배치는 워크플로보다 선검증+인라인이 견고**([[workflow-question-authoring-batch]] 갱신). `outputs/m8/assemble_general.py`(도메인 파라미터화) 신설. verify 양방향 오류 재확인(국기법 0014 §28③6호 false-pos→accept 오버라이드, 0019 5년상한 §47의4⑦ false-neg→외과제거). 7커밋 origin/main push(d89419d..8c78611). 173문항 validate 0 violations·129 tests green·게이트 PASS.
- 2026-06-15 (세션 14) — **M8 문항확장 착수 — 3배치 +26(101→127)**: blueprint §6 목표(100)가 실측 101로 이미 달성됨을 확인 → 확장 재정의(빈셀채우기 아님, 셀당 깊이 확보: 셀당 3.4→~10). §6-4에 가중치 ×3 명세 고정(목표 300·신규 199). harness workflow-B(`question-authoring` 플레이북, `verify-run.py` 게이트 PASS)로 3배치: ① 부가세 citation +10[law-mcp, vat-0023~0032, yield 10/12] ② 회계 case_reasoning +8[kifrs MCP down→로컬 kifrs.db 직접조회, accounting-0017~0024, yield 8/14] ③ 법인세 citation +8[law-mcp, corp-tax-0023~0030, yield 8/12]. 파이프라인=Workflow draft(opus)+독립verify(opus)+오케스트레이터 권위 전건 재검증. **핵심학습**: 오케스트레이터 결정적 재검증이 Opus verify(law-mcp 보유)도 놓친 항호오류 검출(`법§60②7호` 부존재·`법§31`=비상위험준비금 오라벨)→accept도 재검증 대상([[workflow-verify-false-positive-recheck]] 갱신). draft가 검증백엔드 자가확인하면 yield↑. 부가세②근거 6→16·회계③실무 7→15·법인세②근거 6→14. 5커밋 origin/main push(d15252d..d89419d). 129 tests green.
- 2026-06-15 (세션 13) — **M5·M6 잔여 닫음(코드) + README 최신화 push**: M7(외부검수) 건너뛰고 M5·M6 코드 잔여 처리. **M5 후속**: 재배포 자동화 `scripts/deploy_leaderboard.sh`(빌드→`out/data/public/release.jsonl` assert로 공개셋 덮어쓰기 차단→클론 동기화→커밋→`--push`; Git Bash rsync 무의존 git diff 방식). 재빌드 결과가 origin/main 대비 빌드 매니페스트 6파일만 바뀌고 data/public 4파일은 동일 → 덮어쓰기 함정 코드로 닫힘 실증. **M6 잔여**: variance 반복런 `scripts/variance_run.py`(같은 입력 N회·실패run 제외 silent-0 아님) 라이브 N=5(haiku candidate×sonnet judge, closed_book, temp=0): 문항별 std 최대 19.84·range 최대 60·집계 run-mean std 8.62·완전안정 0% → temp=0에도 단일런 노이즈 큼, 다회평균+CI 필수 실증(finding §3-3 신설). 1차 시도는 세션한도+`.claude.json` config race로 중단(자동복구 확인) → CLAUDE.md 규약대로 검증된 `--workers 8` 병렬로 완료(Workflow는 CLI-subprocess eval 측정대상 변경+세션한도 우회불가로 부적합 판단). README 현황 블록 M4✅·M5·M6·M7 + tests 129 갱신·origin push(d15252d). 129 tests.
- 2026-06-01~12 (세션 1~8, 압축) — **M0→M1(101문항)→M2 실행기→M3 평가→M4 공개트랙 라이브**: M0 방향·설계원리(회계 개념체계 spine)·외부벤치8종 / M1 101문항 6도메인×6task_type(Workflow draft+독립verify+오케스트레이터 law-mcp/kifrs 결정적 재검증 3단게이트) / M2 runner+버전핀+rate-limit backoff+agent ReAct([ADR 0005·0006])+격리([ADR 0008]) / M3 재평가(spread 40.2·RAG +8.6·노이즈0) / M4 공개 리더보드 라이브([ADR 0009])+기술리포트+citation grader([ADR 0007]). [ADR 0001~0003]. ~81 tests.
- 2026-06-13 (세션 9) — **공개34 본인검수 + 기술리포트 EN판·Codex 적대적리뷰 반영 + M4+ 신뢰도 마일스톤 분해**: 공개셋 34문항 본인검수(Workflow verify→refute + 오케스트레이터 opus 원문 재검증, false-positive 2 걸러냄·진짜결함 1 수정 v0.3) / EN 리포트(저자 Independent Researcher·References 4종·'early-phase 인프라 보고'로 강도 하향) / M4+ R1~R5 분해(핵심병목=저자 외 권위).
- 2026-06-14 (세션 10) — **M4+ R1 다중 프로바이더 평가 완료(Claude×GPT)**: CLI subprocess 어댑터([ADR 0010])·Gemini 제외([ADR 0011], Antigravity headless 부적합)·초안 finding 정정(오케스트레이터 원문 재검증: '+24.8 same-family bias'는 N불균형 아티팩트, 공정페어 GPT 근소우세·judge민감도 GPT+4.3/Claude−0.2). 95 tests.
- 2026-06-14 (세션 12) — **M5 공개 완결(북극성) + M6 측정 신뢰성 — 둘 다 완료**: harness product 2-phase. **M5**: canary 삽입(`insert_canary.py` 멱등·hash 불변)·릴리스 패키징(`package_release.py`) → 공개 샘플셋 34문항 v1.0 **실제 릴리스**(공개레포 data/public, 게이트 5/5 PASS·외부 fresh clone 재현·raw/Pages 200) + 리더보드 두 컬럼 라이브 검증 + Pages 재배포 덮어쓰기 함정 수정(빌드자산 포함). **M6**: judge 강건화(balanced-brace 파서·코드펜스 — JSON 성공률↑) + `regrade_results.py --only-failed` 신규로 58 judge-fail 재채점(**58→0 잔존0**, step0 파서가 전건 복구) + `stats.py`(bootstrap CI·paired diff·spread CI, 무scipy 결정론). 재집계: full-202=87.92 CI[86.2,89.6]·judge-swap +4.87[4.2,5.5] p≈0·**healed≈survivors→제외 unbiased 실증**(finding §3-2). **129 tests**. 다음 P0=M7 외부검수.
- 2026-06-14 (세션 11) — **R4 선행 디버그(judge silent-0 버그 규명·수정) + 로드맵 재편**: ① **근본원인 규명** — '+24.8' 헤드라인의 정체는 벤더편향이 아니라 **judge JSON 호출실패가 total 0.0/D로 둔갑한 파이프라인 버그**(Claude judge 58/202 파싱실패, GPT 0/202; risk/case는 code폴백 없어 최악). `report.judge_failed` 집계제외 + runner/regrade `judge_error` 마커 + 소스버그 차단 + 재현테스트. finding clean-116 재집계(GPT Claude-judge 68.0→88.1, +24.8 집계수준 해소; 공통119 내 judge-fail 3건이 Claude judge를 86.3으로 눌렀음→88.6). ② **judge 실패 정식화** — `JudgeResult.error/raw_response`(원문 보존·no raise), heal이 judge-fail도 재실행(98 tests). ③ **로드맵 재편** — M0~M4 완료 압축, 북극성=공개완결, 앞으로 M5 공개완결(active)·M6 측정신뢰성·M7 외부검수(병목)·M8 확장+judge검증+arXiv·M9 사업화.
