# Architecture Decision Records

Michael Nygard ADR 포맷. 굵직한 의사결정·의도적 비활성·외부 제약을 보존.

각 ADR: Status / Context / Decision / Consequences. 한 번 쓰면 본문 수정 X
(supersede 만 허용). 자세한 가이드:
~/projects/agent-orchestration/docs/adr/README.md

## 인덱스
- [0001](0001-vendor-not-import-taxagent.md) — tax-agent 자산은 import가 아니라 vendor(복사)
- [0002](0002-claude-cli-first.md) — M2 모델 호출은 Claude CLI 단독으로 시작 (멀티프로바이더 전제 부분 supersede)
- [0003](0003-calculation-as-rule-proxy.md) — 계산문항은 룰 프록시로만, 순수 산수 최소화
- [0005](0005-agent-react-loop.md) — agent 러너는 ReAct 텍스트 루프
- [0006](0006-agent-forced-mode.md) — agent_forced 모드(권위게이트 + 근거매칭)
- [0007](0007-citation-grader-kifrs-paragraph.md) — citation 코드채점을 기준서-문단(K-IFRS)까지 확장
- [0008](0008-agent-eval-isolation.md) — 후보·judge `claude -p` 를 sandbox cwd + `--strict-mcp-config` 로 환경 격리
- [0009](0009-leaderboard-submission-policy.md) — 공개 리더보드 제출·철회·재현 정책(「Leaderboard Illusion」 4대 실패모드 차단)
- [0010](0010-multi-vendor-cli-subprocess.md) — 멀티벤더 교차변별(GPT·Gemini)을 CLI subprocess(구독 인증)로 재활성 (ADR 0002 범위축소 재개방)
- [0011](0011-gemini-excluded-from-r1.md) — Gemini 를 R1 평가셋에서 제외, Claude × GPT 2-벤더로 확정 (Antigravity headless 부적합·gemini CLI 한계)
- [0012](0012-two-public-repos-not-merged.md) — 공개 레포 둘(포트폴리오 스냅샷·리더보드)을 통합하지 않음 (source ≠ build artifact·라이브 도메인 바인딩)
- [0013](0013-authority-rag-mode-contract.md) — `authority_rag`는 benchmark-provided source pack으로만 평가하고 `closed_book`과 섞지 않음
