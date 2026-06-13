from __future__ import annotations

from dataclasses import dataclass

from app.config.constants import DEFAULT_RISK_LEVEL_HIGH_THRESHOLD, DEFAULT_RISK_LEVEL_MEDIUM_THRESHOLD
from app.domain.entities.agreement import Risk, RiskSeverity


@dataclass(slots=True)
class ScoreResult:
    score: int
    explanation: str
    risk_level: str


class CalculateTrustScoreUseCase:
    def execute(self, risks: list[Risk]) -> ScoreResult:
        score = 100
        deductions: list[str] = []

        for risk in risks:
            deduction = self._deduction_for_severity(risk.severity)
            score -= deduction
            deductions.append(f"{risk.title} (-{deduction})")

        score = max(0, score)
        risk_level = self._derive_risk_level(score)
        explanation = self._build_explanation(score, deductions, risk_level)
        return ScoreResult(score=score, explanation=explanation, risk_level=risk_level)

    def _deduction_for_severity(self, severity: RiskSeverity) -> int:
        if severity == RiskSeverity.HIGH:
            return 25
        if severity == RiskSeverity.MEDIUM:
            return 15
        return 5

    def _derive_risk_level(self, score: int) -> str:
        if score < DEFAULT_RISK_LEVEL_HIGH_THRESHOLD:
            return "High"
        if score < DEFAULT_RISK_LEVEL_MEDIUM_THRESHOLD:
            return "Medium"
        return "Low"

    def _build_explanation(self, score: int, deductions: list[str], risk_level: str) -> str:
        if not deductions:
            return f"No major risks were detected, so the score remains {score}/100 and the overall risk level is {risk_level}."
        joined_deductions = ", ".join(deductions)
        return f"The score starts at 100 and deducts points for detected risks: {joined_deductions}. Final score: {score}/100. Risk level: {risk_level}."
