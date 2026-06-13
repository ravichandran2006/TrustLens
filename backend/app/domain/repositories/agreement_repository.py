from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.domain.entities.agreement import Agreement, AnalysisReport


@runtime_checkable
class AgreementRepository(Protocol):
    def save_agreement(self, agreement: Agreement) -> Agreement:
        raise NotImplementedError

    def get_agreement(self, agreement_id: str) -> Agreement | None:
        raise NotImplementedError

    def save_analysis_report(self, report: AnalysisReport) -> AnalysisReport:
        raise NotImplementedError

    def get_analysis_report(self, agreement_id: str) -> AnalysisReport | None:
        raise NotImplementedError
