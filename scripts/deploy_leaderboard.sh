#!/usr/bin/env bash
#
# deploy_leaderboard.sh — K-TaxBench 공개 리더보드 빌드 + GitHub Pages 공개레포 배포
#
# 공개레포(lumatic2/ktaxbench-leaderboard)는 custom domain tax-benchmark.askewly.com 의
# 정적 사이트다. 배포는 leaderboard/out/ 를 공개레포 main 루트에 통째로 싣는다.
#
# ⚠ 덮어쓰기 함정 가드:
#   공개셋 릴리스 번들(data/public/*)은 leaderboard/public/data/public/ 에 빌드자산으로 박혀
#   있어 `next build` 가 out/data/public/ 으로 자동 복사한다. 이 스크립트는 빌드 후
#   out/data/public/release.jsonl 존재를 ASSERT 하고, 없으면 push 하지 않고 즉시 FAIL 한다.
#   (번들이 빠진 out/ 을 push 하면 직접 push 한 공개셋이 날아간다 — 세션 12 함정.)
#
# 사용법:
#   bash scripts/deploy_leaderboard.sh            # 빌드 + out 검증 + 클론 동기화 + 커밋 (push 안 함)
#   bash scripts/deploy_leaderboard.sh --data     # leaderboard-public.json 까지 재생성 후 위 전체
#   bash scripts/deploy_leaderboard.sh --push     # 위 전체 + 공개레포 push (배포 확정)
#   환경변수 DEPLOY_CLONE 으로 공개레포 클론 경로 override (기본 tmp/leaderboard-deploy)
#
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LB="$REPO_ROOT/leaderboard"
CLONE="${DEPLOY_CLONE:-$REPO_ROOT/tmp/leaderboard-deploy}"
PUBLIC_REMOTE="lumatic2/ktaxbench-leaderboard"
RELEASE_REL="data/public/release.jsonl"

DO_DATA=0
DO_PUSH=0
for arg in "$@"; do
  case "$arg" in
    --data) DO_DATA=1 ;;
    --push) DO_PUSH=1 ;;
    *) echo "알 수 없는 인자: $arg" >&2; exit 2 ;;
  esac
done

say() { echo -e "\n\033[1;36m▶ $*\033[0m"; }

# ── 1. (옵션) 리더보드 데이터 재생성 ──────────────────────────────────
if [[ "$DO_DATA" == 1 ]]; then
  say "리더보드 데이터 재생성 (npm run data)"
  ( cd "$LB" && npm run data )
fi

# ── 2. 정적 사이트 빌드 (custom domain → basePath 루트) ───────────────
say "정적 사이트 빌드 (npm run build)"
( cd "$LB" && npm run build )

# ── 3. 덮어쓰기 함정 가드: out 에 릴리스 번들이 실렸는지 ASSERT ────────
say "빌드 산출물 검증: out/$RELEASE_REL"
OUT_RELEASE="$LB/out/$RELEASE_REL"
if [[ ! -s "$OUT_RELEASE" ]]; then
  echo "✗ FAIL: $OUT_RELEASE 없음/빈 파일 — 공개셋 번들이 빌드에서 빠졌다." >&2
  echo "  leaderboard/public/$RELEASE_REL 가 있는지 확인 후 재빌드할 것." >&2
  exit 1
fi
ROWS="$(grep -c . "$OUT_RELEASE" || true)"
echo "✓ 번들 포함 확인 — release.jsonl ${ROWS}행"

# ── 4. 공개레포 클론 준비 (origin/main 으로 동기화) ───────────────────
say "공개레포 클론 동기화: $CLONE"
if [[ ! -d "$CLONE/.git" ]]; then
  echo "✗ 클론 없음: $CLONE" >&2
  echo "  git clone https://github.com/$PUBLIC_REMOTE.git \"$CLONE\" 후 재실행." >&2
  exit 1
fi
REMOTE_URL="$(git -C "$CLONE" remote get-url origin)"
if [[ "$REMOTE_URL" != *"$PUBLIC_REMOTE"* ]]; then
  echo "✗ 클론 origin 이 $PUBLIC_REMOTE 가 아님: $REMOTE_URL" >&2
  exit 1
fi
git -C "$CLONE" fetch origin --quiet
git -C "$CLONE" checkout main --quiet
git -C "$CLONE" reset --hard origin/main --quiet

# ── 5. out/ → 클론 동기화 (.git 보존, 나머지 전체 교체) ───────────────
say "사이트 파일 교체"
find "$CLONE" -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +
cp -R "$LB/out/." "$CLONE/"

# ── 6. 커밋 ───────────────────────────────────────────────────────────
git -C "$CLONE" add -A
if git -C "$CLONE" diff --cached --quiet; then
  say "변경 없음 — 배포 스킵"
  exit 0
fi
STAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
git -C "$CLONE" commit --quiet -m "deploy: 리더보드 재배포 (release.jsonl ${ROWS}행, $STAMP)"
echo "✓ 커밋 생성: $(git -C "$CLONE" rev-parse --short HEAD)"

# ── 7. (옵션) push ────────────────────────────────────────────────────
if [[ "$DO_PUSH" == 1 ]]; then
  say "공개레포 push"
  git -C "$CLONE" push origin main
  echo "✓ 배포 완료 → https://tax-benchmark.askewly.com"
else
  say "커밋까지 완료 (push 안 함)"
  echo "  배포 확정하려면:  git -C \"$CLONE\" push origin main"
  echo "  또는 재실행:      bash scripts/deploy_leaderboard.sh --push"
fi
