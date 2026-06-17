"""K-TaxBench — 한국 회계·세무 AI 평가 실행기.

문항(JSONL) 로드 → 모드별 프롬프트(closed_book/rag/agent) → 모델 호출 →
채점(code-grader + LLM-judge) → 버전핀 결과 영속화 → 진단 리포트.
"""

__version__ = "0.1.0"
