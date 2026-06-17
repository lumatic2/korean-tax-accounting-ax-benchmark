# question-authoring 플레이북

> `playbooks/question-authoring.md` — K-TaxBench 문항 1개를 제작하는 반복 업무를 *한 문서* 로 박제.
> [data-strategy.md](../docs/data-strategy.md) §3 파이프라인의 실행 절차판. 4섹션 모두 필수, 특히 **근거** 가 비면 commit 차단.
> 모범 산출물: `data/sample-questions-v0.1.jsonl` 의 `ktb-vat-0003`·`ktb-vat-0004` (실 locator + 실 URL + 검증 수치 + calculation_steps + 채운 근거).

## 입력 (Inputs)
- **시드** — 기출/실무에서 추출한 *쟁점·유형·난이도만* (지문·문장·수치 복제 금지 — [data-strategy §2.2](../docs/data-strategy.md)). 시드 없이 DOMAIN 쟁점에서 직접 출발해도 됨.
- **DOMAIN 앵커** — [docs/DOMAIN.md](../docs/DOMAIN.md) 핵심 법규 표의 해당 행(조항·세율·임계값·기준일).
- **대상 메타** — `domain` / `task_type`(객관식·계산·사례·근거·리스크·단답·agent) / `difficulty` / `time_basis`(현재 2026-01-01).
- **물어볼 것** — 새 조문이 DOMAIN.md 표에 없으면: 먼저 law.go.kr 로 검증할지(원칙 yes), 보강 후 진행.

## 절차 (Procedure)
1. **쟁점·유형 추출** — 시드/DOMAIN 에서 *법리·계산 구조*만. 표현은 버린다. *(판단)*
2. **근거 검증** — 인용할 조문 번호·세율·임계값을 **law.go.kr 로 1차 확인**. WebFetch `https://www.law.go.kr/법령/{법령명}/제{N}조`. DOMAIN.md 표에 없으면 검증 후 DOMAIN.md 보강(+개정이력·기준일). *(결정론 — 단 조문 적용 타당성은 판단)*
3. **표현 전면 재작성** — 사실관계(`facts`)·수치·선택지(`choices`)를 신규 생산. 원문 표현 0%. 용어 정확히(공급대가↔공급가액, 영세율↔면세, 결산조정↔신고조정). *(판단)*
4. **정답부 작성** — `final_answer`/`explanation`/`calculation_steps`(계산형 필수)/`key_points`/`common_wrong_answers`. 수치엔 근거. *(판단)*
5. **루브릭 작성** — `rubric.criteria`(배점 합 100) + `fatal_errors`(반드시 "존재하지 않는 조문·판례 생성" 포함). task_type 에 맞게 배점 조정(계산형은 calculation_or_process 비중↑). *(판단)*
6. **sources 채우기** — 각 근거를 `{type, title, locator:"제N조", url:"law.go.kr/법령/...", accessed_at, license_status}` 로. locator 는 절차 2에서 검증된 번호만.
7. **본인 검수** — 아래 체크리스트 전 항목 통과. fatal_errors 역으로 자가공격(가짜 조문·임계값 혼동·기준일 누락 없는지). *(판단)*
8. **도장·해시** — `time_basis` 확정, `status: internal_reviewed`, `version: 0.2`, `review.created_by`/`created_at`. `scripts/hash_question.py` 로 `hash` 등록.
9. **라우팅** — `visibility` 배정: 공개 샘플(`public_sample`, 오염 전제 "연습문제")인지 비공개(`holdout`/`private`)인지. easy·예시성=공개, 변별용=비공개([data-strategy §5](../docs/data-strategy.md)).

(절차 2·6·8·9 는 결정론적 → 부분 자동화 가능. 1·3·4·5·7 은 판단 필요.)

> **★ 검증 우선 원칙 (punt 금지)**: "본인 검수 필요"로 미루기 전에, *검증 가능한 사실*(시행령 호 단위·예규 해석·임계값·계산 방식)은 **먼저 law.go.kr(DRF API)·국세청 예규로 확정**하라. 사실 검증은 self-judgment 이 아니라 외부 권위 인용이므로 Judge 규약에 부합한다. **진짜 판단**(가치판단·불확실한 해석·정책적 선택)만 본인 검수로 남긴다.
> 예: corp-tax-0004 "운행기록부 미작성 시 한도"를 본인 검수로 미루지 않고 **영§50의2⑦(1,500만÷관련비용)·⑩(감가×비율−800만)** 원문으로 확정해 정답을 정량화 → 본인 검수는 worked-example 사인오프만 남음.

## 체크리스트 (Checklist)
- [ ] 모든 `sources[].locator` 조문 번호를 law.go.kr 응답으로 검증함 (가짜 조문 0건)
- [ ] 기준일이 현재 유효한지 확인 (`docs/DOMAIN.md` 표 vs `time_basis`) — 2026 세율·임계값 적용
- [ ] 용어 혼동 없음 (공급대가/공급가액, 영세율/면세, 두 임계값 1억400 vs 4,800, 2025↔2026 세율)
- [ ] 계산형이면 `calculation_steps` 가 재현 가능 (각 단계 = 비교/연산 1개)
- [ ] 출력물의 모든 수치에 근거 인용
- [ ] `rubric.fatal_errors` 에 "존재하지 않는 조문·판례 생성" 포함
- [ ] 시드 원문 표현 복제 0% (사실관계·선택지 신규)
- [ ] `hash` 등록, `status` 검수 후 `internal_reviewed`, `visibility` 라우팅 완료
- [ ] 저장 위치: `data/sample-questions-v0.1.jsonl` (한 줄 1문항, append)

## 근거 (★ Judge — 빈 채로 commit 금지)
- 절차 spine: [data-strategy.md §3 문항 제작 파이프라인](../docs/data-strategy.md) — 시드→근거연결→재작성→정답·루브릭→검수→도장→라우팅·해시.
- 근거 우선순위: [config/sources.md](../config/sources.md) 1층(법령·판례=저작권법 §7 자유) → law.go.kr 원문.
- 도메인 기준: [docs/DOMAIN.md](../docs/DOMAIN.md) 핵심 법규 표(부가세 제30·5·48·49·61·69·21~26조 / 법인세 제55·13·15·19·60조, 2026 기준).
- 스키마: [docs/benchmark-schema.md](../docs/benchmark-schema.md) · 루브릭 세부: [docs/rubric-v0.1.md](../docs/rubric-v0.1.md).
- 모범 예시 호출 로그(0003): `WebFetch law.go.kr/법령/부가가치세법/제61조·제69조 → 간이과세 1억400만·납부면제 4,800만 확인 (2026-06-01)`.

---

## 메타
- 작성일: 2026-06-01
- 마지막 적용: 2026-06-16 (M8 문항확장 5~7차 배치 — 5차 법인세 case +12[ktb-corp-tax-0031~0042, §19의2·34·24·23·28·42 + 시행령], 6차 부가세 case +12[ktb-vat-0033~0044, §39·10·45·42·32·영81], 7차 소득세 citation +10[ktb-income-tax-0020~0029, §94·16·17·14·20·12·50·51·70·127]. 셀: 법인세③실무 6→18·부가세③실무 3→15·소득세②근거 5→15 전부 완성. law-mcp 30조문 전건 검증. 발견: 라이브 Workflow가 세션한도(자정 리셋)+StructuredOutput 루프로 부분실패(draft 7/12) → 정지 후 누락분은 오케스트레이터가 검증 ground truth로 직접 인라인 작성. 교훈: 대규모 case 배치는 '워크플로 draft → 부분실패 시 완료분 취득 + 누락분 인라인' 복구경로가 안정적; citation·case 모두 law-mcp 선검증 후 인라인이 토큰·한도 측면에서 더 견고. 이전 4차(국기법+12)는 f8a0b53까지 반영)
- 적용 횟수: 13
- 관련 ADR: (해당 시 `docs/adr/`)
