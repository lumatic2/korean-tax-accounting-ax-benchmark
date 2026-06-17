# HANDOFF — agy(Antigravity) CLI 배치-eval 적합성 점검 (네 인증 TTY에서)

> **배경**: agy 는 Gemini 3.x(3.5 Flash·3.1 Pro)+Claude 4.6+GPT-OSS 를 가진 멀티모델 에이전트 CLI. 하지만 **non-TTY subprocess(배치 러너가 쓰는 방식)에서 `agy --print` 가 응답 없이 행(hang)** 함(2026-06-13 확인, EXIT 124·출력 0). 원인 후보: 인증이 GUI/TTY 세션에만 걸림 / `--print` 가 권한·도구 대기로 멈춤. **네 인증된 터미널에서 아래를 돌려, agy 가 스크립트 eval 어댑터로 쓸 수 있는지 판정**한다.
>
> **판정 기준 (이게 다 ✅여야 agy 어댑터 시도)**: ① `--print` 가 깨끗한 텍스트 답을 주고 **즉시 종료** ② Gemini 3.x 모델을 `--model` 로 지정 가능 ③ 도구(웹검색 등) 없이 순수 텍스트 강제 가능(격리) ④ 동시 N개 실행 시 충돌 없음. 하나라도 ✗면 **gemini-2.5-pro(gemini CLI) 유지**가 결론.
>
> **실행 위치**: 레포 밖 빈 폴더에서 (격리 흉내) — `cd C:\ktaxbench-sandbox`

---

## 점검 명령 (순서대로, TTY에서)

```powershell
cd C:\ktaxbench-sandbox

# 0) 버전 + 모델 목록 (★ --model 에 넣을 정확한 ID 문자열 — picker의 "Gemini 3.1 Pro (High)"가 아니라 CLI가 받는 실제 토큰)
agy --version
agy models

# 1) ★핵심: headless --print 가 TTY에선 응답+즉시종료 하나? (non-TTY에선 행이었음)
agy --print "What is 2+2? Answer with only the digit, nothing else."

# 2) Gemini 3.x 모델 지정 headless (위 models에서 본 Pro ID로 교체)
agy --print "What is 2+2? Only the digit." --model "<Gemini 3.1 Pro ID>"

# 3) 출력이 깔끔한가 — 답만? 아니면 에이전트 잡담/마크다운/사고로 래핑되나?
agy --print "한 줄로만 답: 한국 종합소득세 과세표준 최고구간의 세율은 몇 %?" --model "<Gemini 3.x ID>"

# 4) 격리: 도구를 쓰려는 질문에 sandbox로 — 웹검색 안 하고 지식/거절로 답하면 격리 가능
agy --print "지금 USD/KRW 환율 실시간으로 알려줘" --model "<Gemini 3.x ID>" --sandbox

# 5) 동시성: 두 개를 동시에 (PowerShell). 둘 다 정상 답이면 병렬 가능 신호
Start-Job { agy --print "Say A only" }; Start-Job { agy --print "Say B only" }; Get-Job | Wait-Job | Receive-Job
```

> 막히면(행) `Ctrl+C` 로 끊고 그 항목에 "행"이라고 적어줘. 각 명령이 **몇 초만에 끝나는지**도 적어주면 좋음(배치 101문항 시간 산정).

---

## 결과 기록 (여기 채워줘 → 내가 판정·다음 단계)

- **agy --version**: 1.0.8
- **agy models** (정확한 --model ID들, 특히 Gemini 3.x): **확인 불가 (행)**. subprocess 실행 시 무한 대기(hang)에 빠지며, stdin을 `< NUL`로 리다이렉트 시 출력 없이 즉시 종료(Exit 0)됨.
- **1) --print 기본** — 답 나옴? 즉시 종료? (행이면 "행"): **행** (stdin 리다이렉션 `< NUL` 적용 시 출력 없이 즉시 종료)
- **2) --model Gemini 3.x** — 됨? 답: **확인 불가 (행)**
- **3) 출력 깔끔함** — 답만? 아니면 어떻게 래핑됨? (그대로 붙여줘): **확인 불가** (출력이 전혀 없음)
- **4) --sandbox 격리** — 웹검색 시도함? 순수 텍스트로 답함?: **확인 불가 (행)**
- **5) 동시 2개** — 둘 다 정상? 충돌·에러?: **확인 불가 (행)**
- **체감 속도** (문항당 몇 초): **측정 불가**

### 판정 (내가 채움)
- agy 어댑터 시도 가능? (①~④ 충족 여부): **아니오 (충족 불가)**
  - 비대화형(non-TTY) subprocess 환경에서 `agy`가 멈추거나(hang) stdin 리디렉션 시 무출력 종료되어 배치 평가 러너 어댑터로 사용하는 것이 원천적으로 불가능함.
- 아니면 gemini-2.5-pro 유지 확정: **gemini-2.5-pro (Gemini CLI) 유지 확정**
```
