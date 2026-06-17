# korean-tax-accounting-ax-benchmark

> 한국 회계·세무 AX 시대에 AI 시스템의 실무 수행능력을 측정하는 표준형 평가 인프라 (K-TaxBench). (갈래: workflow + product/backend)

## 기술 스택
-

## 프로젝트 구조
-

## 개발 명령어
```bash
#
```

## 작업 방식
- 모든 출력은 `docs/DOMAIN.md` 의 표 또는 공식 도구 호출 결과를 인용해야 함
- playbook 의 `근거` 섹션 빈 채로 commit 금지
- 기준일 변경 시 즉시 `docs/DOMAIN.md` 갱신

## ⚠ Judge 규약
이 레포는 두 갈래가 겹친다 — 둘 다 강제한다.
> **(workflow — 문항·근거 데이터)** 외부 권위(법조문/기준서/예규/판례/공식 도구) 인용 없는 수치·결론은 답변 금지. 벤치마크 문항의 정답·근거·루브릭은 `docs/DOMAIN.md` 표 또는 공식 출처를 인용해야 한다. 모델 self-judgment 으로 정답 판정 금지 (self-eval 천장).
> **(product/backend — 평가 실행기·리더보드 코드)** 코드 변경은 lint·테스트 통과 전 완료 선언 금지. 새 기능은 재현 테스트 작성 후 통과로 검증.

## 의사결정 이력
"왜 X 안 함?" 같은 *의도적으로 안 한 선택*은 `docs/adr/` 에 ADR 로 보존.
