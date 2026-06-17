# Step 2: tech-report-outline

> 로컬·무billing. 기술 리포트(arXiv/블로그)의 **골격 outline**을 확정한다. 개념체계 spine·방법론·외부 벤치 비교의 섹션 구조와 각 섹션이 인용할 레포 내 근거(ADR·finding·DOMAIN)를 매핑한다. 본문 집필이 아니라 목차 + 근거 슬롯 채우기.

## 읽어야 할 파일
- `docs/positioning.md` + `docs/benchmark-design-principles.md` — 왜: 리포트의 "왜 이 벤치마크인가"(개념체계 spine)의 1차 소스. 기존 포지셔닝 논거 재사용.
- `docs/findings/m3-rerun-101.md` + `docs/findings/m3-rag-vs-closed-book.md` + `docs/findings/agent-tool-forcing.md` — 왜: 리포트 "결과" 섹션의 실증 근거(spread 40.2·RAG +8.6·도구강제 반증). 수치는 finding에서 인용(재산출 금지).
- `docs/adr/` (0001~0009) — 왜: "방법론" 섹션의 설계 결정 근거(vendor·claude-cli·calc 룰프록시·agent ReAct·forced·citation grader·격리·리더보드 정책)를 ADR로 각주.
- `ROADMAP.md` (M4 "개념체계 spine·방법론·외부벤치 비교") — 왜: 리포트가 충족할 마일스톤 항목 원문. **외부벤치 비교** = 어떤 벤치(예: 법률/세무 LLM 벤치, MMLU류)와 무엇을 다르게 했는지가 필수 섹션.

## 작업
### `docs/m4-tech-report-outline.md` 작성
섹션별로 (a) 한 줄 목적 (b) 인용할 레포 내 근거 경로 (c) 아직 없는 근거=TODO 슬롯. 권장 spine:
1. **Abstract** — 한국 회계·세무 AX 실무수행능력 표준 평가(K-TaxBench), 변별 입증.
2. **Motivation/개념체계 spine** — "그럴듯함" vs "실무검증 통과". (positioning·design-principles 인용)
3. **Benchmark 구성** — 101문항, 6도메인×7역량, 스키마·hash·visibility. (benchmark-schema·question-blueprint)
4. **방법론** — 3모드(closed/rag/agent)·다차원 채점(코드+judge)·self-eval 제거·격리. (ARCHITECTURE + ADR 0002·0005·0006·0007·0008)
5. **결과** — spread 40.2·RAG +8.6·도구강제 반증·calc 룰프록시 검출 사례. (findings 3건 인용)
6. **외부 벤치 비교** — 기존 LLM/법률·세무 벤치 대비 차별점(적시성 버전핀·근거강제·한국 실무·오염저항 canary). ★현행 외부벤치 목록은 미정 슬롯 → 별도 리서치 TODO 표시.
7. **한계·후속** — 본인 단독 검수(외부검수 step4)·홀드아웃 운영·표본설계.
8. **재현성** — 버전핀·공개셋(34)·리더보드 정책(ADR 0009).

각 섹션에 `근거:` 줄로 경로 박제. 비어있으면 `TODO(리서치):` 로 표시(judge 규약 — 추정 본문 금지).

## Acceptance Criteria
```bash
test -f docs/m4-tech-report-outline.md && echo "outline OK"
# 8섹션 + 외부벤치 비교 섹션 존재
grep -qE '외부.*벤치|external.*bench' docs/m4-tech-report-outline.md && echo "external-bench section OK"
# 모든 결과 수치가 finding 인용 경로를 동반(고아 수치 금지) — 최소 findings 3개 경로 참조
grep -c 'docs/findings/' docs/m4-tech-report-outline.md  # >=3
```

## 검증 절차
1. AC 실행.
2. "결과" 섹션의 모든 수치(40.2·8.6 등)에 finding 경로 각주가 붙었는지 확인. 없는 수치는 outline에 적지 말 것(TODO 슬롯으로).
3. 외부벤치 비교 섹션은 비교 대상이 미확정이면 본문 단정 금지 — `TODO(리서치)` 명시.
4. `phases/m4-public-track/index.json` step 2 → `completed` + `summary`.

## 금지사항
- **수치·결론을 새로 만들지 마라.** 이유: Judge 규약 — 모든 수치는 finding/DOMAIN/ADR 인용. outline 단계에서 추정 수치 박으면 본문에 그대로 누수.
- **외부벤치를 모르는 채 비교표를 단정하지 마라.** 이유: 미확인 비교는 리포트 신뢰도 파괴. 모르면 TODO.
- 본문 전체를 쓰지 마라. 이유: 이 step은 골격(목차+근거슬롯). 집필은 후속.
