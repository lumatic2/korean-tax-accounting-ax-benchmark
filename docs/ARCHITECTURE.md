# 아키텍처

> K-TaxBench 평가 실행기(M2~M3). 설계 결정은 [adr/](adr/) 참조. 문항 데이터·스키마는 [benchmark-schema.md](benchmark-schema.md), 채점 기준은 [rubric-v0.1.md](rubric-v0.1.md).

## 디렉토리 구조
```
src/ktaxbench/
  schema.py        # 문항 dataclass + benchmark-schema.md enum 검증
  loader.py        # JSONL 로드/필터 (domain·task_type·visibility·status)
  models/          # 모델 어댑터 (M2: claude_cli / M3: openai·google)
    base.py        #   ModelClient 프로토콜: complete(system, prompt) -> Response
    claude_cli.py  #   Claude CLI subprocess (tax-agent vendor)
    registry.py    #   config/models.yaml 로더 + 버전핀
  prompts.py       # build_prompt(question, mode): closed_book / rag / agent
  rag/retriever.py # 법제처 DRF 라이브 검색 → 근거 컨텍스트 (tax-agent law_client vendor)
  grading/
    rubric.py      #   task_type별 가중 criteria + 감점규칙
    code_grader.py #   MC/계산/근거 결정론 채점
    judge.py       #   LLM-judge (self-eval 가드)
    aggregate.py   #   code+judge 결합, statement-level 부분점, pass^k
  runner.py        # run(question, mode, model) -> RunRecord (버전핀 부착)
  report.py        # 분야×차원 분해, 변별(점수 분산), 오류 사례
  runlog.py        # runs/results JSONL 영속화
scripts/           # validate_questions.py / run_eval.py / make_report.py / hash_question.py
tests/             # pytest (code-grader 결정론 등)
data/              # sample-questions-*.jsonl (추적), data/private/ (비추적)
config/models.yaml # 모델 버전핀
outputs/           # runs·results (gitignored)
phases/            # harness step 파일 (execute.py)
```

## 패턴
- **단방향 파이프라인**: loader → prompts → models → grading → runlog → report. 각 단계는 순수 함수 우선(부작용은 runlog/report 경계에 격리).
- **결정론 분리**: 코드 채점(MC·계산·근거 locator)은 결정론(같은 입력→같은 점수, pytest 강제). LLM-judge는 비결정론 → 재현성 분산을 로깅하고 본인 스팟체크로 보정.
- **vendor over import**: `tax-agent` 자산은 import하지 않고 trimmed copy로 들여온다 ([adr/0001](adr/0001-vendor-not-import-taxagent.md)).

## 데이터 흐름
```
문항 JSONL → (mode별 프롬프트 + RAG 근거) → 모델 응답 → code-grader + LLM-judge → 버전핀 결과(JSONL) → 진단 리포트(MD)
```

## 외부 의존성
- **Claude CLI** (subprocess) — M2 모델 호출. 키 불필요(구독). [adr/0002](adr/0002-claude-cli-first.md)
- **법제처 DRF API** (`law.go.kr/DRF`, `LAW_API_OC`) — RAG 근거 라이브 조회. `accessed_at`으로 핀.
- **OpenAI·Google SDK** — M3(Step 8) 멀티프로바이더. API 키 필요.

## 상태 관리
- **불변 입력**: 문항 JSONL은 평가 중 읽기 전용. `hash` 필드로 오염 추적.
- **버전핀**: 각 결과 레코드에 model id·data hash·scaffold(prompt_version)·mode를 박아 재현성·비교가능성 보장.
- **결과 산출물**: `outputs/`(gitignored)에 runs(raw)·results(graded) JSONL로 누적.
