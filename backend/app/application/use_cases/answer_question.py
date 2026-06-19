from __future__ import annotations

import re
from dataclasses import dataclass

from app.infrastructure.rag.context_builder import ContextBuilder
from app.infrastructure.rag.retriever import AgreementRetriever


@dataclass(slots=True)
class QuestionAnswerResult:
    answer: str
    sources: list[str]


class AnswerQuestionUseCase:
    def __init__(
        self,
        retriever: AgreementRetriever,
        context_builder: ContextBuilder,
        llm_client: object | None = None,
    ) -> None:
        self.retriever = retriever
        self.context_builder = context_builder
        self.llm_client = llm_client

    def execute(
        self,
        agreement_id: str,
        question: str,
    ) -> QuestionAnswerResult:

        chunks = self.retriever.retrieve(
            agreement_id=agreement_id,
            query=question,
            top_k=8,
        )

        if not chunks:
            return QuestionAnswerResult(
                answer="No relevant information was found in the document.",
                sources=[],
            )

        context = self.context_builder.build(chunks)

        if not context.strip():
            return QuestionAnswerResult(
                answer="No relevant information was found in the document.",
                sources=[],
            )

        try:
            if (
                self.llm_client is not None
                and hasattr(self.llm_client, "answer_question")
            ):
                answer = self.llm_client.answer_question(
                    question=question,
                    context=context,
                )
            else:
                answer = self._fallback_answer(question, chunks)

        except Exception:
            answer = self._fallback_answer(question, chunks)

        if answer.strip() == "The agreement does not provide sufficient information.":
            rescued = self._fallback_answer(question, chunks)
            if rescued.strip() != "The agreement does not provide sufficient information.":
                answer = rescued

        if not answer or not answer.strip():
            answer = self._fallback_answer(question, chunks)

        sources = list(
            dict.fromkeys(
                [
                    chunk.source
                    for chunk in chunks
                    if getattr(chunk, "source", None)
                ]
            )
        )

        return QuestionAnswerResult(
            answer=answer,
            sources=sources,
        )

    def _fallback_answer(
        self,
        question: str,
        chunks: list[object],
    ) -> str:
        """
        Generic fallback that returns the most relevant chunk
        when an LLM is unavailable.
        """

        question_words = {
            self._normalize_token(word)
            for word in re.findall(r"[a-zA-Z0-9']+", question.lower())
            if len(word) > 2
        }

        best_chunk = None
        best_score = -1

        for chunk in chunks:
            text = getattr(chunk, "text", "")

            chunk_words = {
                self._normalize_token(word)
                for word in re.findall(r"[a-zA-Z0-9']+", text.lower())
            }

            score = len(question_words.intersection(chunk_words))

            if score > best_score:
                best_score = score
                best_chunk = text

        if best_score <= 0:
            return "The agreement does not provide sufficient information."

        if best_chunk:
            return best_chunk[:1500]

        combined_text = "\n\n".join(
            getattr(chunk, "text", "")
            for chunk in chunks
        )

        if combined_text.strip():
            return combined_text[:1500]

        return "No relevant information was found in the document."

    def _normalize_token(self, token: str) -> str:
        normalized = token.strip("'")
        if len(normalized) > 5 and normalized.endswith("ing"):
            normalized = normalized[:-3]
        elif len(normalized) > 4 and normalized.endswith("ed"):
            normalized = normalized[:-2]
        elif len(normalized) > 4 and normalized.endswith("es"):
            normalized = normalized[:-2]
        elif len(normalized) > 3 and normalized.endswith("s"):
            normalized = normalized[:-1]
        return normalized