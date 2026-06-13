from __future__ import annotations

from dataclasses import dataclass

from app.application.use_cases.detect_risks import DetectRisksUseCase
from app.infrastructure.rag.context_builder import ContextBuilder
from app.infrastructure.rag.retriever import AgreementRetriever


@dataclass(slots=True)
class QuestionAnswerResult:
    answer: str
    sources: list[str]


class AnswerQuestionUseCase:
    def __init__(self, retriever: AgreementRetriever, context_builder: ContextBuilder, llm_client: object | None = None) -> None:
        self.retriever = retriever
        self.context_builder = context_builder
        self.llm_client = llm_client

    def execute(self, agreement_id: str, question: str) -> QuestionAnswerResult:
        chunks = self.retriever.retrieve(agreement_id=agreement_id, query=question, top_k=5)
        if not chunks:
            return QuestionAnswerResult(answer="The agreement does not provide sufficient information.", sources=[])

        context = self.context_builder.build(chunks)
        if not context.strip():
            return QuestionAnswerResult(answer="The agreement does not provide sufficient information.", sources=[])

        if self.llm_client is not None and hasattr(self.llm_client, "answer_question"):
            answer = self.llm_client.answer_question(question=question, context=context)
        else:
            answer = self._rule_based_answer(question, chunks)

        if not answer.strip():
            answer = "The agreement does not provide sufficient information."

        if answer.strip().lower() == "the agreement does not provide sufficient information.":
            return QuestionAnswerResult(answer=answer, sources=[])

        sources = [chunk.source for chunk in chunks if getattr(chunk, "source", None)]
        return QuestionAnswerResult(answer=answer, sources=sources)

    def _rule_based_answer(self, question: str, chunks: list[object]) -> str:
        lowered_question = question.lower()
        candidate_text = "\n".join(getattr(chunk, "text", "") for chunk in chunks)
        lowered_candidate = candidate_text.lower()
        if any(keyword in lowered_question for keyword in ("refund", "money back")) and ("refund" in lowered_candidate or "refund" in candidate_text.lower()):
            return self._extract_relevant_sentence(candidate_text, ("refund", "money back"))
        if any(keyword in lowered_question for keyword in ("data", "third party", "shared")) and ("data" in lowered_candidate or "third" in lowered_candidate):
            return self._extract_relevant_sentence(candidate_text, ("data", "third party", "share"))
        if any(keyword in lowered_question for keyword in ("cancel", "terminate", "end account")):
            return self._extract_relevant_sentence(candidate_text, ("cancel", "terminate", "end", "suspend"))
        if any(keyword in lowered_question for keyword in ("renew", "auto renew", "subscription")):
            return self._extract_relevant_sentence(candidate_text, ("renew", "subscription", "automatic"))
        return "The agreement does not provide sufficient information."

    def _extract_relevant_sentence(self, text: str, keywords: tuple[str, ...]) -> str:
        sentences = [sentence.strip() for sentence in text.replace("\n", " ").split(".") if sentence.strip()]
        for sentence in sentences:
            lowered = sentence.lower()
            if any(keyword in lowered for keyword in keywords):
                return sentence[:480].rstrip(" ,;:") + "."
        return "The agreement does not provide sufficient information."
