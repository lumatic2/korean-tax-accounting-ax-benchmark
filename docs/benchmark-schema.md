# K-TaxBench 문항 스키마 v0.1

## 목적

문항 스키마는 회계·세무 AI 평가 문항을 일관된 형식으로 저장하고, 추후 자동 채점·리더보드·기업 리포트로 확장하기 위한 기본 구조다.

초기 저장 형식은 `JSONL`을 권장한다.  
한 줄에 한 문항을 저장하면 버전 관리와 부분 로딩이 쉽다.

---

## 최상위 필드

```json
{
  "id": "ktb-vat-0001",
  "version": "0.1",
  "status": "draft",
  "visibility": "private",
  "language": "ko",
  "jurisdiction": "KR",
  "benchmark_mode": ["closed_book", "rag"],
  "domain": "vat",
  "task_type": "case_reasoning",
  "difficulty": "medium",
  "time_basis": "2026-01-01",
  "question": {},
  "answer": {},
  "rubric": {},
  "sources": [],
  "tags": [],
  "review": {},
  "license": {},
  "hash": "sha256:..."
}
```

---

## 필드 정의

### `id`

문항 고유 ID.

형식:

```text
ktb-{domain}-{number}
```

예시:

- `ktb-vat-0001`
- `ktb-corp-tax-0007`
- `ktb-accounting-0012`

### `version`

문항 버전.

예시:

- `0.1`: 초안
- `0.2`: 내부 검토 후 수정
- `1.0`: 전문가 검수 완료

### `status`

문항 상태.

허용값:

- `draft`: 작성 중
- `internal_reviewed`: 내부 검토 완료
- `expert_reviewed`: 전문가 검수 완료
- `retired`: 폐기 또는 비활성

### `visibility`

공개 여부.

허용값:

- `public_sample`: 공개 샘플셋
- `private`: 비공개 평가셋
- `holdout`: 리더보드용 비공개 홀드아웃

### `benchmark_mode`

평가 모드.

허용값:

- `closed_book`: 외부 검색 없이 답변
- `rag`: 제공 문서 또는 검색 시스템 사용 가능
- `agent`: 도구 사용, 계산, 검색, 보고서 작성 포함

### `domain`

분야.

초기 허용값:

- `vat`: 부가가치세
- `corp_tax`: 법인세
- `income_tax`: 소득세
- `basic_tax_law`: 국세기본법
- `local_tax`: 지방세
- `accounting`: 회계처리
- `audit`: 감사/내부통제
- `commercial_law`: 상법/회사법
- `mixed`: 복합 사례

### `task_type`

문항 유형.

초기 허용값:

- `multiple_choice`: 객관식
- `short_answer`: 단답형
- `calculation`: 계산형
- `case_reasoning`: 사례 판단형
- `citation`: 근거 제시형
- `risk_analysis`: 리스크 분석형
- `agent_workflow`: 에이전트형 과제

### `difficulty`

난이도.

허용값:

- `easy`: 기본 개념 또는 단순 적용
- `medium`: 복수 조건 적용 또는 계산 포함
- `hard`: 판례/예규/복합 세무조정 포함
- `expert`: 전문가 검토가 필요한 고난도 실무 사안

### `time_basis`

정답 기준일.

세법·회계기준은 시점에 따라 달라질 수 있으므로 필수로 둔다.

형식:

```text
YYYY-MM-DD
```

---

## `question` 객체

```json
{
  "title": "간이과세자의 부가가치세 신고 판단",
  "prompt": "문제 본문...",
  "facts": [
    "사업자는 개인 일반음식점이다.",
    "직전 연도 공급대가가 ...이다."
  ],
  "choices": [
    {"label": "A", "text": "..."},
    {"label": "B", "text": "..."}
  ],
  "required_output": [
    "결론",
    "계산 과정",
    "근거 조문",
    "실무상 주의점"
  ]
}
```

### 필드

- `title`: 문항 제목
- `prompt`: 모델에게 제공할 전체 문제
- `facts`: 사실관계 분리 목록
- `choices`: 객관식일 때만 사용
- `required_output`: 답변에 반드시 포함해야 할 항목

---

## `answer` 객체

```json
{
  "final_answer": "정답 또는 결론",
  "acceptable_answers": ["허용 가능한 대체 표현"],
  "explanation": "해설",
  "calculation_steps": [
    "1단계 계산",
    "2단계 계산"
  ],
  "key_points": [
    "간이과세자 요건 확인",
    "공급대가 기준 확인"
  ],
  "common_wrong_answers": [
    "일반과세자 기준을 잘못 적용",
    "기준시점 누락"
  ]
}
```

---

## `rubric` 객체

```json
{
  "total_points": 100,
  "criteria": [
    {
      "name": "conclusion_accuracy",
      "points": 25,
      "description": "최종 결론이 맞는가?"
    },
    {
      "name": "legal_basis",
      "points": 20,
      "description": "관련 법령·예규·판례 근거가 정확한가?"
    }
  ],
  "fatal_errors": [
    "존재하지 않는 조문 또는 판례를 생성",
    "계산 결과가 정답과 20% 이상 차이"
  ]
}
```

세부 기준은 `docs/rubric-v0.1.md`를 따른다.

---

## `sources` 배열

```json
[
  {
    "type": "statute",
    "title": "부가가치세법",
    "locator": "제61조",
    "url": "https://...",
    "accessed_at": "2026-05-23",
    "license_status": "public_law"
  }
]
```

### `type` 허용값

- `statute`: 법령
- `regulation`: 시행령/시행규칙
- `ruling`: 예규/질의회신
- `case_law`: 법원 판례
- `tax_tribunal`: 조세심판례
- `exam`: 시험 기출
- `standard`: 회계기준/감사기준
- `practice_case`: 자체 제작 실무 사례
- `secondary`: 해설서/논문/기사 등 2차 자료

---

## `tags` 배열

태그 예시:

```json
[
  "부가가치세",
  "간이과세자",
  "계산형",
  "근거인용",
  "기준시점필수"
]
```

초기에는 한국어 태그를 우선 사용한다.

---

## `review` 객체

```json
{
  "created_by": "yusung",
  "created_at": "2026-05-23",
  "reviewers": [],
  "expert_review_required": true,
  "expert_reviewed_at": null,
  "notes": "초안. 전문가 검수 전."
}
```

---

## `license` 객체

```json
{
  "source_copyright_risk": "medium",
  "reuse_policy": "transformed_question",
  "public_release_allowed": false,
  "notes": "기출문제 구조를 참고하되 원문 복제 금지"
}
```

### `source_copyright_risk`

- `low`: 법령/판례 등 공개 원문 중심
- `medium`: 시험문제 구조 참고, 변형 필요
- `high`: 유료 교재/해설/비공개 자료 기반

### `reuse_policy`

- `original`: 자체 제작
- `public_domain_reference`: 법령/판례 기반
- `transformed_question`: 원자료를 변형해 새 문항화
- `do_not_publish`: 공개 금지

---

## `hash` (오염 추적)

문항 내용의 content hash. 공개셋↔비공개셋 누수 대조와 공개 시점 기록에 쓴다([data-strategy.md](data-strategy.md) §4·§5).

```text
"hash": "sha256:<hex>"
```

- 산출 기준: `{"question": <question 객체>, "final_answer": <answer.final_answer>}` 를 canonical JSON(키 정렬·공백 제거)으로 직렬화한 뒤 SHA-256.
- 산출·backfill 도구: `scripts/hash_question.py` (결정론 — 같은 내용 → 같은 해시).
- `hash` 자체는 산출 기준에서 제외되므로 재실행해도 안정적.

### `canary` (M4 deferred)

공개셋에 삽입하는 고유 추적 문자열(향후 학습데이터 오염 추적). **필드 예약만** 해 두고 값 삽입은 공개 릴리스(M4) 시점에 한다 — 그 전에는 넣지 않는다.

```text
"canary": null   // M4 공개 시 "KTAXBENCH-CANARY-<uuid>" 삽입
```

---

## 최소 예시

```json
{"id":"ktb-vat-0001","version":"0.1","status":"draft","visibility":"private","language":"ko","jurisdiction":"KR","benchmark_mode":["closed_book","rag"],"domain":"vat","task_type":"case_reasoning","difficulty":"medium","time_basis":"2026-01-01","question":{"title":"부가가치세 공급시기 판단","prompt":"다음 사실관계에서 공급시기와 신고기간을 판단하라.","facts":["계약일은 2026-01-10이다.","대금 수령일은 2026-02-05이다.","재화 인도일은 2026-03-01이다."],"required_output":["결론","근거","실무상 주의점"]},"answer":{"final_answer":"재화의 공급시기는 원칙적으로 재화가 인도되는 때이다.","acceptable_answers":[],"explanation":"구체적 법령 검토 필요. 초안 예시.","calculation_steps":[],"key_points":["공급시기","신고기간"],"common_wrong_answers":["계약일을 공급시기로 봄"]},"rubric":{"total_points":100,"criteria":[],"fatal_errors":["존재하지 않는 조문 생성"]},"sources":[],"tags":["부가가치세","공급시기"],"review":{"created_by":"yusung","created_at":"2026-05-23","reviewers":[],"expert_review_required":true,"expert_reviewed_at":null,"notes":"초안"},"license":{"source_copyright_risk":"low","reuse_policy":"original","public_release_allowed":false,"notes":"예시 문항"}}
```
