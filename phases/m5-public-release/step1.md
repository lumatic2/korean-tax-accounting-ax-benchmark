# Step 1: release-bundle-packaging

외부인이 받아서 재현할 수 있는 **다운로드 가능한 릴리스 번들**을 만드는 패키징 스크립트. produce 단계 — 번들 *생성기*만 만들고 실제 공개 push 는 step3.

## 읽어야 할 파일
- `phases/m5-public-release/step0.md` + 생성한 `scripts/insert_canary.py` — 왜: 번들에 들어갈 release.jsonl 은 canary 삽입 산출물. 패키징은 그 위에서 README/매니페스트를 두름.
- `docs/m4-public-sample-scope.md` (§4 릴리스 전 게이트) — 왜: 번들 매니페스트가 게이트 5항목(카운트·누수0·license·hash diff0·holdout 미포함)을 기록·검증.
- `docs/adr/0009-leaderboard-submission-policy.md` — 왜: README 에 제출/재현 정책(버전핀·holdout 순위·재현검증 등재) 링크. 공개셋은 "연습·재현 데모"용이고 순위는 holdout 임을 명시.
- `scripts/export_public_set.py` — 왜: 공개 적격 추출 로직 재사용(번들 생성 파이프라인의 1단계).

## 작업
`scripts/package_release.py` 신규 — 출력 디렉터리(예 `dist/public-release-v1.0/`)에 번들 생성:
- `release.jsonl` — export_public_set → insert_canary 파이프라인 산출(canary 포함).
- `README.md` — 데이터셋 설명 / 재현 방법(다운로드→로드→채점 커맨드) / 라이선스 / **전역 canary sentinel 박제**(학습오염 탐지 안내) / holdout 순위·공개셋 별도 정책(ADR 0009 링크) / 기준일·버전.
- `MANIFEST.json` — `version: "1.0"`, 문항 수, 분포(domain/task_type/difficulty), 전역 sentinel, per-question hash 목록(또는 합산 hash), generated_at(KST), 게이트 결과(누수0·license·hash diff0).
- `LICENSE` — data-strategy 의 공개 라이선스(기존 license 필드 근거). 본문은 기존 레포 라이선스 정책 따름.
- 멱등·결정론: 같은 입력+seed → 같은 번들(canary 제외 hash 안정). `dist/` 는 gitignore(산출물).
- 재현테스트 `tests/test_package_release.py`: 번들 4파일 존재 / MANIFEST 카운트 == release.jsonl 행수 / 누수 가드(holdout·private·draft id 0건) / README 에 sentinel 포함.

## Acceptance Criteria
```bash
PYTHONPATH=src python -m pytest tests/test_package_release.py -q && PYTHONPATH=src python -m pytest -q
```

## 검증 절차
1. AC — 신규 테스트 + 전체 그린.
2. 번들을 임시로 한 번 생성(`dist/`, gitignored)해 4파일·누수가드 PASS 육안 확인. dist 는 커밋 안 함.
3. index.json step1 → completed + summary.

## 금지사항
- `dist/` 산출물을 git 에 커밋 금지. 이유: 산출물(레포 정리 표준 gitignore). 공개 push 는 step3 에서 별도 공개 레포로.
- holdout/draft/private 문항을 번들에 포함 금지. 이유: 채점셋 해자 붕괴(Leaderboard Illusion 공개셋 과적합). 누수가드로 강제.
- 기존 테스트 깨지 마라.
