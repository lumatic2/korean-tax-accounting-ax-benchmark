# Step 0: public-data-and-readme-boundary

## 읽어야 할 파일
- `CLAUDE.md` - 왜: Judge 규약과 코드 변경 검증 규칙이 이번 공개 정리의 상위 가드레일이다.
- `ROADMAP.md` - 왜: N1 publication-safe milestone의 DoD/Evidence가 여기 정의된다.
- `README.md` - 왜: 외부 포트폴리오 독자가 처음 보는 public-facing 설명이다.
- `data/README.md` - 왜: 추적되는 데이터와 비추적 holdout 경계를 명시해야 한다.
- `scripts/package_release.py` - 왜: 공개 샘플셋 게이트와 public_sample 기준을 재사용한다.
- `tests/` - 왜: tracked data를 공개 샘플로 좁힌 뒤 깨지는 기본 테스트를 조정해야 한다.

## 작업
Tracked repository state must be safe to make public:

- Keep only release-safe `public_sample` rows in tracked data.
- Preserve the full working dataset locally under ignored `data/private/` for the user's private workflow.
- Update README/data docs so outside readers understand the public sample, private holdout policy, and leaderboard split.
- Adjust tests and defaults only where they assumed tracked holdout rows.

## Acceptance Criteria
```bash
uv run python scripts/validate_questions.py data/sample-questions-v0.1.jsonl
uv run pytest
git ls-files | rg "^(data/private/|outputs/|CLAUDE\.local\.md)"
rg -n -i "(api[_-]?key|secret|token|password|bearer|sk-[A-Za-z0-9]|ghp_|github_pat_|ANTHROPIC_API_KEY|OPENAI_API_KEY|GEMINI_API_KEY|DATABASE_URL)" --glob "!.git/**" --glob "!.venv/**" --glob "!uv.lock"
```

## 검증 절차
1. AC 커맨드를 실행한다.
2. tracked data에 `visibility: "holdout"`가 0건인지 확인한다.
3. `phases/publication-safe-portfolio-release/index.json` step 업데이트:
   - 성공 -> `completed` + `summary`
   - 3회 실패 -> `error` + `error_message`
   - 사용자 개입 필요 -> `blocked` + `blocked_reason` + 즉시 중단

## 금지사항
- 비공개 holdout 문항 본문/정답을 새 tracked 파일로 복제하지 마라. 이유: 공개 전 데이터 경계 정리의 핵심 위험이다.
- 기존 unrelated dirty file을 되돌리지 마라. 이유: 사용자 작업일 수 있다.
