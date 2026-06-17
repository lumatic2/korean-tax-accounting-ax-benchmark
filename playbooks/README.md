# playbooks/

반복 업무 하나당 한 문서. 4섹션(입력 / 절차 / 체크리스트 / 근거) — 템플릿:
[PLAYBOOK_TEMPLATE.md](PLAYBOOK_TEMPLATE.md).

## 인덱스

| # | 슬러그 | 도메인 | 마지막 적용 | 적용 횟수 |
|---|--------|--------|------------|----------|
| 1 | [question-authoring](question-authoring.md) | 문항 제작 (전 분야) | 2026-06-16 | 13 |

## 실행 원칙
- 근거 섹션 빈 채로 commit 금지 (judge 강제)
- 기준일 확인 → `docs/DOMAIN.md` 표와 cross-check 후 실행
- 결과는 `outputs/{기수}/{task-slug}-{YYYYMMDD}.{ext}` 에 저장
