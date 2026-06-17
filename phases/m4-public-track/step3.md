# Step 3: leaderboard-web (공개 리더보드 웹)

> ⏳ 후속 세션 실행 대기 — **이 파일은 실행 계획**(produce). 빌드·배포(run)는 사용자 opt-in 후. 데이터 소스는 `outputs/` results JSONL → `report.py` 집계 → 빌드타임 JSON. 웹은 **얇은 정적 뷰어**(채점 로직 재구현 금지 — 단일 진실원 `src/ktaxbench`).

## 잠긴 결정 (2026-06-12 합의)
- **스택**: Next.js + React, **정적 export**(`output: 'export'`) — SSR/서버 없음.
- **호스팅**: **별도 공개 레포**(`ktaxbench-leaderboard` 등) + **GitHub Pages**. 본 private 레포는 비공개 유지(holdout 보호). 빌드 산출물·공개 데이터만 공개 레포에 push. billing 0.
- **v1 범위**: **읽기전용 뷰어 + 정책 배지**. 셀프서비스 제출폼은 v2.

## 읽어야 할 파일
- `src/ktaxbench/report.py` — 왜: 웹이 소비할 집계 구조가 여기 정의됨. `aggregate_results`(by_model: avg_total·by_domain·by_mode·by_dimension·grades) + `discrimination`(spread·range·flag) + `error_cases`(type·id·model·mode·detail)가 그대로 data contract. 웹은 이 dict를 JSON으로 받아 렌더만.
- `scripts/make_report.py` — 왜: 현 출력은 markdown. 3.0에서 `--json` 출력 추가가 첫 작업.
- `docs/adr/0009-leaderboard-submission-policy.md` (step1) — 왜: 웹이 강제할 정책(버전핀 동결·holdout 순위·공개셋 별도표기·재현검증·철회불가). 배지·컬럼·문구가 이를 따라야 함.
- `docs/m4-public-sample-scope.md` (step0) — 왜: 공개셋 34만 노출, holdout은 집계값만(문항 본문·정답 비노출).
- `~/.claude/memory/deploy.md` + `~/.claude/memory/repo-layout.md` — 왜: 공개 레포 .gitignore 표준(CLAUDE.md·ROADMAP·내부회고 gitignored, install/build 필요 파일만 push)·배포 경로.

## 작업 (sub-phase — 실행 시 순차)

### 3.0 데이터 계약 — `make_report.py --json` (billing-free, 먼저 가능)
- `make_report.py`에 `--json <path>` 추가: `{"report": aggregate_results(...), "discrimination": discrimination(...), "errors": error_cases(...), "meta": {...버전핀·생성일·judge...}}` 덤프.
- 결정론 — 같은 입력 → 같은 JSON. 재현 테스트 추가(`tests/`). markdown 출력과 공존(기존 동작 무변경).
- 이 JSON이 웹의 **유일한 입력**. 웹은 절대 raw 답변/채점 재계산 안 함.

### 3.1 퍼블리시 결과셋 큐레이션
- 공개할 run 선정(예: M3 rerun 101). 버전핀(model id·data hash·scaffold·mode·accessed_at·judge) 포함 확인.
- holdout 레코드는 **집계값만** JSON에 포함(문항 id·본문·정답·답변 텍스트 제외). 공개셋(34)은 문항 메타 노출 가능.
- 누수 가드: JSON에 holdout 문항 본문/정답/answer_text가 없음을 스크립트로 assert.

### 3.2 Next.js 앱 스캐폴드 (정적 export)
- `output: 'export'`, project pages용 `basePath`/`assetPrefix`(`/ktaxbench-leaderboard`), `.nojekyll`.
- 페이지: **① 메인**(모델 랭킹 표 + 변별 spread/flag 배너) · **② 모델 드릴다운**(도메인×차원 히트맵 — Chart.js 또는 경량 라이브러리) · **③ 오류 사례**(환각·계산오류·근거오류 type별).
- 빌드타임에 3.0의 data.json import(fetch 아님 — 정적).

### 3.3 정책 배지·컬럼 (ADR 0009 강제)
- 각 모델 행: 버전핀 배지(model·날짜·scaffold·mode) + 재현상태(✓검증/⏳) + append-only(같은 모델 여러 행 허용).
- **holdout 순위 컬럼 + 공개셋 점수 별도 컬럼**(과적합 가시화). 철회불가 안내·ADR 0009 링크.

### 3.4 공개 레포 + GitHub Pages 배포 (opt-in 게이트)
- 공개 레포 생성, `.gitignore`에 CLAUDE.md·ROADMAP.md·내부 회고 명시(공개 레포 표준).
- 빌드 산출물(out/) + 공개 data.json만 push. GitHub Actions(`next build` → Pages) 또는 수동 gh-pages.
- 배포 전 최종 누수 점검: holdout 문항·private·canary 미공개 확인(step0 §4 릴리스 게이트 재사용).

## Acceptance Criteria (sub-phase별)
```bash
# 3.0
uv run python scripts/make_report.py outputs/<run>/*.jsonl --json outputs/leaderboard.json && test -f outputs/leaderboard.json
uv run pytest -q tests/ -k report   # json 결정론 테스트 green
# 3.1 누수 가드
uv run python -c "import json; d=json.load(open('outputs/leaderboard.json',encoding='utf-8')); assert 'answer_text' not in json.dumps(d)"  # holdout 본문 누수 0
# 3.2~3.3 (웹 레포)
npm run build && npx serve out   # 로컬 프리뷰 — 랭킹·히트맵·오류·배지 렌더
# 3.4 (배포, opt-in 후)
# Pages URL 200 + holdout 문항 미노출 수동 확인
```

## 의존
- step0(공개셋 34·누수 게이트) · step1(ADR 0009 정책) · step2(report 구조). 전부 완료(2026-06-12).

## 금지사항
- **opt-in 없이 배포(3.4) 금지.** 이유: 공개 노출은 되돌리기 어려움. 빌드·로컬 프리뷰까지는 자유.
- **holdout 문항 본문·정답·answer_text를 JSON/웹에 노출 금지.** 이유: 채점셋 해자 붕괴 = Leaderboard Illusion 과적합. 집계값만.
- **report 채점 로직을 웹에서 재구현 금지.** 이유: 단일 진실원(src/ktaxbench) 이중화 = 점수 불일치. 웹은 JSON 렌더만.
- **공개 레포에 CLAUDE.md·ROADMAP·내부 데이터 push 금지.** 이유: 내부 지시·계획 노출. install/build 필요 파일만(repo-layout 표준).
