from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from app.application.use_cases.calculate_trust_score import CalculateTrustScoreUseCase, ScoreResult
from app.application.use_cases.detect_risks import DetectRisksUseCase
from app.application.use_cases.generate_summary import GenerateSummaryUseCase
from app.domain.entities.agreement import Agreement, AnalysisReport, Risk
from app.domain.repositories.agreement_repository import AgreementRepository
from app.infrastructure.rag.chunker import AgreementChunker
from app.infrastructure.rag.context_builder import ContextBuilder
from app.infrastructure.rag.retriever import AgreementRetriever, AgreementChunk


@dataclass(slots=True)
class AnalyzeAgreementResult:
    agreement: Agreement
    report: AnalysisReport
    chunks: list[AgreementChunk]


class AnalyzeAgreementUseCase:
    def __init__(
        self,
        agreement_repository: AgreementRepository,
        summary_use_case: GenerateSummaryUseCase | None = None,
        detect_risks_use_case: DetectRisksUseCase | None = None,
        trust_score_use_case: CalculateTrustScoreUseCase | None = None,
        chunker: AgreementChunker | None = None,
        retriever: AgreementRetriever | None = None,
        context_builder: ContextBuilder | None = None,
    ) -> None:
        self.agreement_repository = agreement_repository
        self.summary_use_case = summary_use_case or GenerateSummaryUseCase()
        self.detect_risks_use_case = detect_risks_use_case or DetectRisksUseCase()
        self.trust_score_use_case = trust_score_use_case or CalculateTrustScoreUseCase()
        self.chunker = chunker or AgreementChunker()
        self.retriever = retriever
        self.context_builder = context_builder or ContextBuilder()

    def execute(self, content: str, document_type: str = "agreement") -> AnalyzeAgreementResult:
        agreement = Agreement(id=self._new_agreement_id(), content=content, document_type=document_type)
        summary = self.summary_use_case.execute(content).bullets
        risks = self.detect_risks_use_case.execute(content)
        score_result = self.trust_score_use_case.execute(risks)
        recommendations = self._build_recommendations(risks)

        agreement.summary = summary
        agreement.risks = risks
        agreement.consumer_safety_score = score_result.score
        agreement.score_explanation = score_result.explanation
        agreement.recommendations = recommendations

        report = AnalysisReport(
            agreement_id=agreement.id,
            summary=summary,
            risks=risks,
            consumer_safety_score=score_result.score,
            score_explanation=score_result.explanation,
            risk_level=score_result.risk_level,
            recommendations=recommendations,
        )

        saved_agreement = self.agreement_repository.save_agreement(agreement)
        self.agreement_repository.save_analysis_report(report)

        chunks = self.chunker.chunk(saved_agreement.content, agreement_id=saved_agreement.id)
        if self.retriever is not None and hasattr(self.retriever, "index"):
            self.retriever.index(saved_agreement.id, chunks)

        return AnalyzeAgreementResult(agreement=saved_agreement, report=report, chunks=chunks)

    def _new_agreement_id(self) -> str:
        return f"agr_{uuid4().hex[:12]}"

    def _build_recommendations(self, risks: list[Risk]) -> list[str]:
        if not risks:
            return ["No major red flags detected. Review the full agreement before accepting it."]
        recommendations: list[str] = []
        for risk in risks:
            if risk.recommendation and risk.recommendation not in recommendations:
                recommendations.append(risk.recommendation)
        return recommendations
