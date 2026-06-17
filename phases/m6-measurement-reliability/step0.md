# Step 0: judge-prompt-hardening

LLM-judge 의 JSON 응답 성공률을 올린다. 세션11 규명: Claude judge 58/202 비-JSON 파싱실패가 silent-0 오염의 원흉. 호출실패 *정식화*는 됐고(미채점 분리), 이제 *발생률 자체*를 낮춘다. 순수 헬퍼 강화 — 무billing·테스트 가능.

## 읽어야 할 파일
- `src/ktaxbench/grading/judge.py` — 왜: 강화 대상. `build_judge_prompt`(시스템/유저 프롬프트)·`parse_judge_json`(정규식 추출)·`judge_answer`(2회 재시도 루프). 비결정 호출은 judge_answer 만, 나머지는 순수.
- `tests/test_*.py` 중 judge 관련 — 왜: parse_judge_json·build_judge_prompt 회귀 테스트 위치 확인 후 케이스 추가.
- `~/.claude/memory/...judge-failure-silent-zero` (MEMORY 인덱스) — 왜: silent-0 의 근본원인·왜 호출실패를 0점으로 두면 안 되는지. 강화 방향의 근거.

## 작업 (시그니처 수준)
1. **프롬프트 강화** (`build_judge_prompt` system/말미): "출력은 `{` 로 시작해 `}` 로 끝나야 한다. 코드펜스(```)·설명·머리말 금지. JSON 외 텍스트 출력 시 무효." 차원명/스키마는 그대로.
2. **파서 강건화** (`parse_judge_json`): 코드펜스(```json … ```) 스트립 → balanced-brace 추출(첫 `{`부터 매칭되는 `}`까지, 중첩 카운팅)으로 greedy `.*` 가 trailing prose 에 물리는 경우 방지. 실패 시 기존대로 ValueError.
3. **재시도 강화** (`judge_answer`): 현 2회(빈+1재촉) → 재촉 문구를 더 강한 JSON-only 지시로. (선택) OpenAI 계열 client 가 response_format=json_object 지원 시 그 경로 — 단 어댑터 추상화 깨지 말 것(과설계 금지, base.complete 시그니처 유지).
4. **재현테스트** `tests/test_judge_hardening.py`: ① 코드펜스 감싼 JSON 파싱 성공 ② trailing prose 붙은 JSON 정확 추출 ③ 중첩 객체(memo 안 객체) 파싱 ④ 진짜 비-JSON 은 여전히 error·raw_response 반환(silent-0 안 됨).

## Acceptance Criteria
```bash
PYTHONPATH=src python -m pytest tests/test_judge_hardening.py -q && PYTHONPATH=src python -m pytest -q
```

## 검증 절차
1. AC — 신규 + 전체 그린.
2. 비-JSON 입력이 여전히 미채점(error 채워짐)으로 빠지는지 회귀(judge_failed 분리 불변).
3. index.json step0 → completed + summary(강화 항목·테스트 수). step2(heal)가 이 working judge 를 씀.

## 금지사항
- 비-JSON 응답을 빈 scores 로 "통과"시키지 마라. 이유: silent-0 재발(세션11 버그 원흉). 실패는 error+raw_response 로.
- 어댑터 추상화(base.complete) 시그니처 변경 금지. 이유: 4개 CLI/API 클라이언트 동시 의존. 과설계 금지(Karpathy simplicity).
- 기존 judge 테스트 깨지 마라.
