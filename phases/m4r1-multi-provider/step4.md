# Step 4: cross-provider-report-and-docs  (run — 문서, billing 0)

> R1 verify 산출물: **≥3 프로바이더 교차 변별 리포트** + judge-swap robustness. "단일 Claude 패밀리" 공격 해소를 문서로 박제하고 ROADMAP·ADR·README·기술리포트를 갱신.

## 읽어야 할 파일
- `phases/m4r1-multi-provider/step3.md` 결과(step3 summary) + `outputs/m4r1/*.jsonl` — 왜: 리포트의 수치 원천. 모든 수치는 이 raw 에서 인용(추정 금지).
- `docs/findings/m3-rerun-101.md` (있으면) — 왜: Claude 3모델 baseline. 교차변별 표의 Claude 열.
- `ROADMAP.md` (M4+ R1 §) — 왜: verify 기준 충족 표시·범위축소(line 65) 갱신.
- `docs/m4-tech-report.md`·`docs/m4-tech-report-en.md` — 왜: "단일 Claude 패밀리" 한계 문장을 교차변별 결과로 보강(KO+EN 동기).
- `README.md` — 왜: 프로바이더 수·교차변별 한 줄 최신화.

## 작업
- `docs/findings/m4r1-multi-provider.md` 작성: provider × mode 점수표(Claude·GPT·Gemini), spread, RAG 효과 재현 여부, judge-swap 일치도, 한계(small-n·공개셋 medium 편중). 모든 수치 `outputs/m4r1/` 인용.
- ROADMAP M4+ R1 → verify 충족 표시. line 65 범위축소 문구를 "ADR 0010 으로 재개방·R1 에서 교차변별 산출"로 갱신(supersede 문서화).
- 기술리포트 KO/EN: "단일 Claude 패밀리" 경계 문장 → 교차변별 1차 실증으로 강도 조정(과대주장 금지 — early-phase 프레이밍 유지).
- README provider 수 갱신.

## Acceptance Criteria
```bash
test -f docs/findings/m4r1-multi-provider.md && echo OK
uv run pytest   # 회귀 0 (문서 변경이 코드 안 깸)
```

## 검증 절차
1. finding 문서의 모든 수치가 `outputs/m4r1/` raw 와 일치(직접 대조).
2. ROADMAP R1 verify 기준(≥3 프로바이더 교차변별 + judge-swap 1건) 충족 명시.
3. `index.json` step4 → `completed` + summary. phase 전체 `completed` 로 `phases/index.json` 갱신.

## 금지사항
- raw 에 없는 수치·결론 작성 금지(Judge 규약 — 외부근거/도구결과 인용). 이유: self-judgment 천장.
- 교차변별이 약하게 나와도 과대해석 금지(small-n·공개셋 편중 한계 명시). 이유: reviewer 재공격.
- ROADMAP 변경이력 무한증식 금지(완료분 압축). 이유: 150줄 cap.
