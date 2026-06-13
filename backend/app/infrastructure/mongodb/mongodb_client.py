from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

try:
    from pymongo import MongoClient  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    MongoClient = None

from app.domain.entities.agreement import Agreement, AnalysisReport, QuestionRecord


@dataclass(slots=True)
class MongoDBClient:
    uri: str | None = None
    database_name: str = "trustlens"
    _memory: dict[str, dict[str, Any]] = field(default_factory=lambda: {"agreements": {}, "analysis_reports": {}, "questions": {}})
    _client: Any | None = field(default=None, init=False, repr=False)
    _db: Any | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        self._client = MongoClient(self.uri) if MongoClient is not None and self.uri else None
        self._db = self._client[self.database_name] if self._client is not None else None

    def save_agreement(self, agreement: Agreement) -> Agreement:
        if self._db is not None:
            self._db.agreements.update_one({"_id": agreement.id}, {"$set": self._agreement_to_dict(agreement)}, upsert=True)
            return agreement
        self._memory["agreements"][agreement.id] = agreement
        return agreement

    def get_agreement(self, agreement_id: str) -> Agreement | None:
        if self._db is not None:
            payload = self._db.agreements.find_one({"_id": agreement_id})
            return self._agreement_from_dict(payload) if payload else None
        return self._memory["agreements"].get(agreement_id)

    def save_analysis_report(self, report: AnalysisReport) -> AnalysisReport:
        if self._db is not None:
            self._db.analysis_reports.update_one({"agreement_id": report.agreement_id}, {"$set": self._report_to_dict(report)}, upsert=True)
            return report
        self._memory["analysis_reports"][report.agreement_id] = report
        return report

    def get_analysis_report(self, agreement_id: str) -> AnalysisReport | None:
        if self._db is not None:
            payload = self._db.analysis_reports.find_one({"agreement_id": agreement_id})
            return self._report_from_dict(payload) if payload else None
        return self._memory["analysis_reports"].get(agreement_id)

    def save_question(self, question: QuestionRecord) -> QuestionRecord:
        if self._db is not None:
            self._db.questions.insert_one(self._question_to_dict(question))
            return question
        self._memory["questions"].setdefault(question.agreement_id, []).append(question)
        return question

    def list_questions(self, agreement_id: str) -> list[QuestionRecord]:
        if self._db is not None:
            return [self._question_from_dict(item) for item in self._db.questions.find({"agreement_id": agreement_id})]
        return list(self._memory["questions"].get(agreement_id, []))

    def _agreement_to_dict(self, agreement: Agreement) -> dict[str, Any]:
        return {
            "_id": agreement.id,
            "content": agreement.content,
            "document_type": agreement.document_type,
            "summary": agreement.summary,
            "risks": [self._risk_to_dict(risk) for risk in agreement.risks],
            "consumer_safety_score": agreement.consumer_safety_score,
            "score_explanation": agreement.score_explanation,
            "recommendations": agreement.recommendations,
            "created_at": agreement.created_at,
            "updated_at": agreement.updated_at,
        }

    def _report_to_dict(self, report: AnalysisReport) -> dict[str, Any]:
        return {
            "agreement_id": report.agreement_id,
            "summary": report.summary,
            "risks": [self._risk_to_dict(risk) for risk in report.risks],
            "consumer_safety_score": report.consumer_safety_score,
            "score_explanation": report.score_explanation,
            "risk_level": report.risk_level,
            "recommendations": report.recommendations,
            "created_at": report.created_at,
        }

    def _risk_to_dict(self, risk: Any) -> dict[str, Any]:
        return {
            "category": risk.category.value,
            "severity": risk.severity.value,
            "title": risk.title,
            "description": risk.description,
            "evidence": risk.evidence,
            "recommendation": risk.recommendation,
        }

    def _question_to_dict(self, question: QuestionRecord) -> dict[str, Any]:
        return {
            "agreement_id": question.agreement_id,
            "question": question.question,
            "answer": question.answer,
            "sources": question.sources,
            "created_at": question.created_at,
        }

    def _agreement_from_dict(self, payload: dict[str, Any]) -> Agreement:
        return Agreement(
            id=payload["_id"],
            content=payload["content"],
            document_type=payload.get("document_type", "agreement"),
            summary=payload.get("summary", []),
            risks=[],
            consumer_safety_score=payload.get("consumer_safety_score", 100),
            score_explanation=payload.get("score_explanation", ""),
            recommendations=payload.get("recommendations", []),
            created_at=payload.get("created_at"),
            updated_at=payload.get("updated_at"),
        )

    def _report_from_dict(self, payload: dict[str, Any]) -> AnalysisReport:
        return AnalysisReport(
            agreement_id=payload["agreement_id"],
            summary=payload.get("summary", []),
            risks=[],
            consumer_safety_score=payload.get("consumer_safety_score", 100),
            score_explanation=payload.get("score_explanation", ""),
            risk_level=payload.get("risk_level", "Low"),
            recommendations=payload.get("recommendations", []),
            created_at=payload.get("created_at"),
        )

    def _question_from_dict(self, payload: dict[str, Any]) -> QuestionRecord:
        return QuestionRecord(
            agreement_id=payload["agreement_id"],
            question=payload["question"],
            answer=payload["answer"],
            sources=payload.get("sources", []),
            created_at=payload.get("created_at"),
        )
