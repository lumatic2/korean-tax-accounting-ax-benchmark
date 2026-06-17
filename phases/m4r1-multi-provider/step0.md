# Step 0: adr-and-cli-capability-handoff  (produce — billing 0)

> ADR 0010 으로 어댑터 방식을 확정하고, **두 CLI 의 병렬 안전성을 CLI 에 직접 물어 검증**하는 handoff 를 만든다. 이 step 은 문서만 생성(코드·라이브 호출 X). 병렬 안전성 답이 step1 어댑터의 `max_workers` 기본값과 동시성 가드를 결정한다.

## 읽어야 할 파일
- `docs/adr/0010-multi-vendor-cli-subprocess.md` — 왜: 이 step 이 구현하는 결정(CLI subprocess·구독 인증·격리 패리티). 어댑터 방식의 단일 출처.
- `docs/adr/0002-claude-cli-first.md` — 왜: 재개방 대상(범위축소). CLI-first 를 택한 원래 이유(키·비용 0)가 0010 (B) 선택의 근거.
- `docs/adr/0008-agent-eval-isolation.md` — 왜: 격리 원칙(sandbox cwd + MCP 차단). codex/gemini 격리 플래그가 이 패리티를 만족해야 함.
- `src/ktaxbench/models/claude_cli.py` — 왜: 신규 어댑터 2개가 본뜰 원형(rate-limit backoff·sandbox·isolated 기본·Response 계약).

## 작업
1. ADR 0010 + README 인덱스 — 완료(이 step 에서 작성).
2. **CLI capability HANDOFF 작성** → `phases/m4r1-multi-provider/HANDOFF.md`. 사용자가 Codex CLI·Gemini CLI 각각에 붙여넣어 답을 받는 자가완결 질의서. 반드시 포함:
   - 비대화형 호출 확인: `codex exec -m <model> -o out.txt "<prompt>"` / `gemini -p "<prompt>" -m <model> -o text` 가 stdout/파일로 최종답만 깨끗이 주는지.
   - ★ **병렬 안전성**: 같은 머신에서 8개 프로세스가 동시에 headless 호출 시 — 세션파일/락 충돌? 구독 동시성 한도(429/대기)? 권장 동시성?
   - 격리: 레포 밖 cwd + read-only/plan 으로 도구·MCP 실행이 정말 차단되는지(후보가 웹·파일·MCP 못 쓰게).
   - 인증 상태·사용 모델 ID 실값(`gpt-5.4`/`gemini-3-pro` 는 placeholder — 실제 받는 `-m` 값 확인).
   - 출력에 배너/사고로그가 섞이면 어떤 플래그로 억제하는지.

## Acceptance Criteria
```bash
test -f docs/adr/0010-multi-vendor-cli-subprocess.md && \
test -f phases/m4r1-multi-provider/HANDOFF.md && \
grep -q "0010" docs/adr/README.md && echo OK
```

## 검증 절차
1. AC 실행(파일 존재·인덱스 등록).
2. HANDOFF.md 가 자가완결인지 — 두 CLI 각각의 질의 블록이 있고, 병렬 안전성 질문이 명시됐는지 육안 확인.
3. `index.json` step0 → `completed` + summary(어떤 답을 받아야 step1 이 풀리는지).

## 금지사항
- 이 step 에서 어댑터 코드 작성 금지. 이유: 병렬 안전성 답이 동시성 가드 설계를 바꾼다(Think Before Coding).
- 라이브 CLI 호출(smoke 포함) 금지. 이유: billing·이 step 은 produce.
