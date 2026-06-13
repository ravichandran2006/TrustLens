from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional


class RiskCategory(str, Enum):
    PRIVACY = "Privacy Risk"
    DATA_SHARING = "Data Sharing Risk"
    FINANCIAL = "Financial Risk"
    SUBSCRIPTION = "Subscription Risk"
    LEGAL = "Legal Risk"
    CONSUMER_RIGHTS = "Consumer Rights Risk"


class RiskSeverity(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


@dataclass(slots=True)
class Risk:
    category: RiskCategory
    severity: RiskSeverity
    title: str
    description: str
    evidence: Optional[str] = None
    recommendation: Optional[str] = None


@dataclass(slots=True)
class Agreement:
    id: str
    content: str
    document_type: str = "agreement"
    summary: List[str] = field(default_factory=list)
    risks: List[Risk] = field(default_factory=list)
    consumer_safety_score: int = 100
    score_explanation: str = ""
    recommendations: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(slots=True)
class AnalysisReport:
    agreement_id: str
    summary: List[str]
    risks: List[Risk]
    consumer_safety_score: int
    score_explanation: str
    risk_level: str
    recommendations: List[str]
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(slots=True)
class QuestionRecord:
    agreement_id: str
    question: str
    answer: str
    sources: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
