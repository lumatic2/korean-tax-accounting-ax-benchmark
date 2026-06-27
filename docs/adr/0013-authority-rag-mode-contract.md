# 0013 — `authority_rag`는 benchmark-provided source pack으로만 평가하고 `closed_book`과 섞지 않는다

## Status
Accepted (2026-06-26)

## Context
302문항 재평가에서 `gpt-5.5 closed_book`은 완료됐지만, 다음 단계인 `authority_rag`는 기존 `rag`와 같은 의미로 실행하면 안 된다. 기존 `rag`는 law.go.kr DRF 중심의 live retrieval였고, 회계 K-IFRS·심판례·예규·판례 문항을 같은 품질로 덮지 못한다. 또한 retriever가 임의로 고른 문서를 주입하면 모델 능력과 retrieval 품질이 얽혀 리더보드 해석이 흐려진다.

외부 벤치마크 조사([evaluation-mode-design-2026-06-26](../findings/evaluation-mode-design-2026-06-26.md))도 같은 결론을 준다. closed-book, open-book/RAG, agent/tool-use는 같은 평균으로 섞지 않고, dataset split·tool/scaffold·source contract를 함께 고정해야 한다.

## Decision
K-TaxBench의 모드 계약을 `config/evaluation-mode-contracts.json`으로 고정한다.

1. **`closed_book`**
   - 모델 입력은 문항 본문, 사실관계, 선택지, 요구 출력, 기준일뿐이다.
   - 외부 자료, retrieval, source pack은 없다.
   - 현재 공개 리더보드의 1차 순위 기준이다.

2. **`authority_rag`**
   - 모델은 benchmark가 미리 제공한 authority pack만 볼 수 있다.
   - authority pack은 문항별 `source_pack_version`, `question_hash`, `time_basis`, `authority_entries`를 포함한다.
   - 후보 생성에 보이는 authority entry는 source metadata와 `source_excerpt` 또는 full text뿐이다. gold answer, key points, rubric, judge memo, 다른 모델 답안, visibility는 절대 포함하지 않는다.
   - `source_excerpt`가 비어 있거나 `source_text_status != provided`인 authoritative entry가 있으면 해당 문항은 generation-ready가 아니다.
   - 모델이 pack에 없는 근거를 지어내면 `closed_book`보다 더 강하게 감점될 수 있다. pack이 부족하면 부족하다고 말해야 한다.
   - `closed_book`과 평균을 섞지 않는다. 별도 `authority_rag` view로 공개한다.

3. **`agent`**
   - 모델이 직접 도구를 호출하는 system benchmark다.
   - `toolset_version`, `max_steps`, `pass_k`, scaffold version을 함께 고정해야 한다.
   - 모델-only 행과 같은 순위표에서 비교하지 않는다.

## Consequences
- ✅ `authority_rag`가 “검색 잘한 시스템”인지 “근거를 읽는 모델”인지 혼동되지 않는다. retriever는 benchmark-provided source pack으로 고정된다.
- ✅ 기존 `closed_book` 리더보드가 깨지지 않는다. `authority_rag`는 별도 view가 준비될 때까지 ranking-eligible이 아니다.
- ✅ source text가 없는 locator-only pack을 RAG 성능으로 오인하는 일을 막는다.
- ⚠ `authority_rag` 실행 전에 source excerpt/full text 채우기 단계가 필요하다. 현재 `build_authority_pack`은 manifest-level pack을 만들 수 있지만, generation-ready pack은 별도 조회/검증을 통과해야 한다.
- ⚠ 공개 리더보드 UI는 `closed_book_baseline`, `authority_rag`, `agent_workflow` view를 명시적으로 분리해야 한다.
