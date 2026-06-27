# 0012 — 공개 레포 둘(포트폴리오 스냅샷 · 리더보드)을 통합하지 않는다

## Status
Accepted (2026-06-20). 공개 면(public face)은 레포 **둘**로 유지한다 — `korean-tax-accounting-ax-benchmark`(포트폴리오 스냅샷)와 `ktaxbench-leaderboard`(배포 사이트). 하나로 합치자는 안을 검토 후 기각.

## Context
레포 토폴로지(3개):

| 레포 | 가시성 | 정체 | 로컬 |
|---|---|---|---|
| `lumatic2/korean-tax-accounting-ax-benchmark-private` | private | 개발 본체 — 전체 소스·holdout·ROADMAP·CLAUDE.md | `~/projects/korean-tax-accounting-ax-benchmark-private` (이 레포) |
| `lumatic2/korean-tax-accounting-ax-benchmark` | public | 포트폴리오 공개 스냅샷 — sanitize된 src·공개샘플·이중언어 README·기술리포트 | `~/projects/korean-tax-accounting-ax-benchmark` |
| `lumatic2/ktaxbench-leaderboard` | public | 리더보드 정적 사이트 — `out/` 빌드 산출물만 (GitHub Pages) | **전용 클론 없음** (아래) |

"공개 레포가 둘이면 하나로 합쳐 포트폴리오 스냅샷에서 다 하면 되지 않나"라는 단순화 제안이 나왔다. 그러나 둘은 **중복이 아니라 종류가 다른 산출물**이다 — 전자는 *읽는 코드/데이터 레포*(재현용), 후자는 *배포된 정적 사이트*(`out/` 빌드물). repo-layout 표준(source ≠ build artifact)과 정확히 일치한다.

검증된 사실(2026-06-20):
- 라이브 도메인 **`tax-benchmark.askewly.com` 은 `ktaxbench-leaderboard` 에 바인딩**(`main` 루트 `/` 서빙, CNAME 설정 완료, HTTPS 인증서 발급·승인, 만료 2026-09-10). 포트폴리오 레포는 Pages 자체가 없음.
- 두 산출물의 **갱신 리듬이 다름** — 포트폴리오 스냅샷은 안정화 시점에, 리더보드는 데이터 갱신마다 재배포.

## Decision
**합치지 않고 분리 유지.** 통합 시 비용이 이득을 초과:

1. **라이브 커스텀 도메인 재설정 리스크** — CNAME·Pages 소스를 포트폴리오 레포로 이전 + **HTTPS 인증서 재발급**. 잘 도는 인증서 살아있는 인프라를 M5(공개 릴리스) 직전에 건드리는 것 = 다운타임 위험.
2. **Pages 경로 충돌** — 포트폴리오 루트엔 이미 README·src 존재 → Pages 루트 불가. `/docs`(기존 `docs/` 폴더와 충돌) 또는 `gh-pages` 브랜치 필요 → 구조 복잡화.
3. **source ↔ build artifact 혼입** — repo-layout 표준이 일부러 가르는 경계를 다시 섞음.

얻는 것은 "공개 레포 1개 감소"라는 마진 수준의 정돈뿐. "공개 얼굴 하나"가 목표라면 통합이 아니라 **포트폴리오 README를 정식 랜딩으로 두고 리더보드로 링크**(이미 거의 그 상태)가 더 깔끔.

## 리더보드 관리 모델 (왜 "직접 관리한 기억이 없는지")
`ktaxbench-leaderboard` 는 **개발하는 레포가 아니라 빌드 산출물만 받는 배포 타깃**(publish target)이다. 그래서 전용 로컬 클론이 없고, 거기서 코드를 짠 적도 없다.

- **소스는 이 private 레포 `leaderboard/`**(Next.js 정적 export)에 있다.
- 배포 흐름([leaderboard/README.md](../../leaderboard/README.md)):
  ```
  # 이 레포 leaderboard/ 에서:
  npm run data      # outputs → 공개 JSON 재생성(누수 가드)
  $env:PAGES_BASE_PATH='/ktaxbench-leaderboard'; npm run build   # → out/ (gitignored)
  # out/ 를 ktaxbench-leaderboard 원격에 push (out/ 을 git init+remote 하거나 publish dir 패턴)
  ```
- 공개 레포엔 **`out/` 만**. private source(`leaderboard/`)·CLAUDE.md·ROADMAP·내부 데이터 push 금지.

## Consequences
- ✅ 경계 명확 — 재현 코드/데이터 레포 ≠ 배포 사이트. 갱신 리듬 독립.
- ✅ 라이브 도메인·인증서 무손상(M5 릴리스 리스크 0).
- ⚠ 공개 레포 2개 유지비 — 단 리더보드는 publish target이라 "개발"하지 않음(빌드+push만).
- ⚠ 데이터 갱신 시 두 군데 동기화 책임(스냅샷 push + 리더보드 재배포)을 사람이 짊어짐 — 자동화 미정.
- 재검토 트리거: 리더보드를 Next 정적 export가 아닌 다른 호스팅으로 옮기거나, 포트폴리오 레포에 Pages를 새로 붙일 필요가 생기면.
