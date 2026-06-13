from __future__ import annotations

from fastapi import APIRouter, Depends

from app.application.dto.requests import AnalyzeRequest
from app.application.dto.responses import AnalyzeResponse, RiskDTO
from app.application.use_cases.analyze_agreement import AnalyzeAgreementUseCase
from app.infrastructure.dependencies import get_analyze_use_case

router = APIRouter(prefix="/api", tags=["analysis"])


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_agreement(
    payload: AnalyzeRequest,
    use_case: AnalyzeAgreementUseCase = Depends(get_analyze_use_case),
) -> AnalyzeResponse:
    result = use_case.execute(content=payload.content, document_type=payload.document_type)
    return AnalyzeResponse(
        agreement_id=result.agreement.id,
        summary=result.report.summary,
        risks=[
            RiskDTO(
                category=risk.category.value,
                severity=risk.severity.value,
                title=risk.title,
                description=risk.description,
                evidence=risk.evidence,
                recommendation=risk.recommendation,
            )
            for risk in result.report.risks
        ],
        consumer_safety_score=result.report.consumer_safety_score,
        score_explanation=result.report.score_explanation,
        risk_level=result.report.risk_level,
        recommendations=result.report.recommendations,
    )
