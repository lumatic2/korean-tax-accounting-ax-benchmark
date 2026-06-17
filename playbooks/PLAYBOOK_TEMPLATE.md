# {task-slug} 플레이북

> `playbooks/{task}.md` — 한 반복 업무를 *한 문서* 로 박제.
> 4섹션 모두 필수. 특히 **근거** 가 비면 commit 차단(또는 사람 review 강제).

## 입력 (Inputs)
- {필요한 자료 1} — {형식·출처}
- {필요한 자료 2}
- {질문 받아야 할 것 — 사용자에게 물어볼 항목}

## 절차 (Procedure)
1. {단계 1} — {도구/명령}
2. {단계 2}
3. {단계 3}

(각 단계가 결정론적이면 자동화 가능. 판단 필요한 단계는 별도 표시)

## 체크리스트 (Checklist)
- [ ] 입력 자료 누락 없는지 확인
- [ ] 기준일이 현재 시점에 유효한지 확인 (`docs/DOMAIN.md` 의 표 vs 오늘 날짜)
- [ ] 계산 결과를 *공식 도구* 와 1회 cross-check
- [ ] 출력물의 모든 수치에 근거 인용 달림
- [ ] 출력물 저장 위치: `outputs/{기수}/{task-slug}-{YYYYMMDD}.{ext}`

## 근거 (★ Judge — 빈 채로 commit 금지)
- 법조문: [{법령명} 제○조 ○항](https://...) — {왜 이 조항이 적용되나}
- 기준일: YYYY-MM-DD 시행분 적용
- 공식 도구 호출 로그:
  ```
  {tool-name} {args}
  → {result}
  ```
- 참고: `docs/DOMAIN.md#{anchor}`

---

## 메타
- 작성일: YYYY-MM-DD
- 마지막 적용: YYYY-MM-DD
- 적용 횟수: {n}
- 관련 ADR: `docs/adr/{n}-{title}.md` (해당 시)
