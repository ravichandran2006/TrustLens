from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class RiskDTO(BaseModel):
    category: str
    severity: str
    title: str
    description: str
    evidence: str | None = None
    recommendation: str | None = None


class AnalyzeResponse(BaseModel):
    agreement_id: str | None = None
    summary: list[str] = Field(default_factory=list)
    risks: list[RiskDTO] = Field(default_factory=list)
    consumer_safety_score: int
    score_explanation: str
    risk_level: str
    recommendations: list[str] = Field(default_factory=list)


class QuestionResponse(BaseModel):
    answer: str
    sources: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
