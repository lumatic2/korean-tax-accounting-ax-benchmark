# K-TaxBench 리더보드 (정적 뷰어)

🔗 **라이브: https://lumatic2.github.io/ktaxbench-leaderboard/** (공개 레포 `lumatic2/ktaxbench-leaderboard`, `out/`만 배포)

공개 리더보드 웹 v1 — **읽기전용 + 정책 배지**. Next.js 정적 export → GitHub Pages.
채점은 하지 않는다(단일 진실원 `src/ktaxbench`). 빌드타임 JSON만 렌더한다.

## 데이터 흐름
```
outputs/*.jsonl → scripts/build_leaderboard_data.py (누수 가드) → data/leaderboard-public.json → 정적 빌드
```
`data/leaderboard-public.json`은 **공개 안전**(holdout 문항 id·본문·answer_text 비노출, 순위는 holdout 집계·공개셋 별도). 그래서 이 레포에 커밋해도 안전하다.

## 개발
```bash
npm install
npm run data      # (선택) outputs에서 공개 JSON 재생성 — python 필요
npm run dev       # http://localhost:3000
npm run build     # 정적 export → out/
```

## 배포·갱신 (GitHub Pages)
공개 레포 `lumatic2/ktaxbench-leaderboard`의 `main` root에서 Pages 서빙. **데이터 갱신 시 재배포 흐름**:
```bash
# 1) 최신 결과로 공개 데이터 재생성(누수 가드 통과)
npm run data
# 2) basePath 박아 정적 빌드 (PowerShell — Git Bash는 /경로 MSYS 변환 주의)
#    PowerShell: $env:PAGES_BASE_PATH='/ktaxbench-leaderboard'; npm run build
# 3) out/ 를 공개 레포에 푸시
cd out && git add -A && git commit -m "deploy: <갱신내용>" && git push
```
> 공개 레포엔 `out/`(빌드 산출물)만. 본 private 레포의 source(`leaderboard/`)·CLAUDE.md·ROADMAP·내부 데이터는 push 금지(repo-layout 표준). `out/`은 private 레포에서 gitignored.

## 정책
순위·제출·철회 규칙은 [ADR 0009](../docs/adr/0009-leaderboard-submission-policy.md). holdout 보호는 [m4-public-sample-scope](../docs/m4-public-sample-scope.md).
