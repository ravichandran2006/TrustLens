from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.domain.entities.agreement import QuestionRecord


@runtime_checkable
class ReportRepository(Protocol):
    def save_question(self, question: QuestionRecord) -> QuestionRecord:
        raise NotImplementedError

    def list_questions(self, agreement_id: str) -> list[QuestionRecord]:
        raise NotImplementedError
