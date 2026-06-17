# Step 3: release-and-reproduce-verify

★ RUN 이벤트 — 실제 공개 릴리스. **사용자 opt-in 받음**(세션12: "M5 릴리스까지 이번 세션 실행"). canary 삽입 → 공개 레포 push → 외부 재현 verify. side-effect(공개 push) 발생 — 이 step 진입 전 사용자에게 1줄 통지.

## 읽어야 할 파일
- 생성한 `scripts/insert_canary.py` + `scripts/package_release.py` — 왜: 이 step 은 두 스크립트를 *실행*해 실제 번들 생성. 코드는 step0/1 에서 검증됨.
- `docs/m4-public-sample-scope.md` (§4 릴리스 전 게이트 5항목) — 왜: push 전 마지막 결정론 게이트. 5항목 전부 PASS 여야 push.
- `phases/m4-public-track/index.json` (step3.4 배포 기록) — 왜: 공개 레포 lumatic2/ktaxbench-leaderboard 의 push 경로·인증(이미 배포 전례). data/public/ 는 그 레포 안.
- `~/.claude/memory/m4-ssh-keychain.md` 는 m4 한정 — 여기선 Windows 로컬 gh/git 인증 사용(step3.4 와 동일 경로).

## 작업
1. 파이프라인 실행: `export_public_set --out` → `insert_canary`(전역 sentinel 기록) → `package_release`(번들 dist/).
2. **릴리스 전 게이트**(§4 5항목): 카운트 == 34(또는 현재 재산출값) / 누수0(holdout·draft·private id) / 전 문항 license.public_release_allowed / canary 삽입 후 hash diff 0 / holdout 본문·정답 미포함. 하나라도 FAIL → 중단.
3. 공개 레포 `lumatic2/ktaxbench-leaderboard` 의 `data/public/` 에 release.jsonl + README + MANIFEST 추가 → commit → push.
4. **외부 재현 verify**: 공개 레포를 임시 위치에 fresh clone → release.jsonl 로드 → 채점 1문항 재현(또는 export 카운트 재산출 일치) → 라이브 raw URL 200 확인.
5. 전역 canary sentinel 값을 본 레포 비공개 기록(매니페스트/CLAUDE.local.md)에 보존 — 향후 오염 probe 대조용.

## Acceptance Criteria
```bash
# 게이트 PASS 후에만 push. 재현 verify:
git clone --depth 1 https://github.com/lumatic2/ktaxbench-leaderboard /tmp/ktb-verify
PYTHONPATH=src python -c "import json; rows=[json.loads(l) for l in open('/tmp/ktb-verify/data/public/release.jsonl',encoding='utf-8') if l.strip()]; print(len(rows))"
# raw URL 200
curl -sI https://raw.githubusercontent.com/lumatic2/ktaxbench-leaderboard/main/data/public/release.jsonl | head -1
```

## 검증 절차
1. 릴리스 게이트 5항목 PASS 로그.
2. fresh clone 재현 — 카운트 일치 + raw URL 200.
3. canary 오염탐지 경로 작동(전역 sentinel 박제 + probe 절차 문서화).
4. index.json step3 → completed + summary(release URL·canary 보존 위치·재현 결과). blocked 시 사유 기록 후 중단(인증·게이트 FAIL).

## 금지사항
- 게이트 5항목 미PASS 상태로 push 금지. 이유: 단 1건 누수가 채점셋 해자 붕괴.
- 본 private 레포(korean-tax-accounting-ax-benchmark)에 canary 삽입된 데이터·전역 sentinel 평문 커밋 금지. 이유: 본 데이터는 hash 누수 대조 기준 — 불변 유지. sentinel 은 gitignored 기록에만.
- 사용자 통지 없이 public push 금지. 이유: side-effect·opt-in 경계. 진입 전 1줄 통지 필수.
