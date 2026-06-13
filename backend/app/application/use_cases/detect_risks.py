from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from app.domain.entities.agreement import Risk, RiskCategory, RiskSeverity


@dataclass(slots=True)
class RiskPattern:
    category: RiskCategory
    severity: RiskSeverity
    title: str
    description: str
    recommendation: str
    patterns: tuple[str, ...]


class DetectRisksUseCase:
    def __init__(self, patterns: Iterable[RiskPattern] | None = None) -> None:
        self.patterns = tuple(patterns or _default_patterns())

    def execute(self, content: str) -> list[Risk]:
        lowered_content = content.lower()
        risks: list[Risk] = []
        for pattern in self.patterns:
            if any(re.search(regex, lowered_content, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL) for regex in pattern.patterns):
                evidence = self._find_evidence(content, pattern.patterns)
                risks.append(
                    Risk(
                        category=pattern.category,
                        severity=pattern.severity,
                        title=pattern.title,
                        description=pattern.description,
                        evidence=evidence,
                        recommendation=pattern.recommendation,
                    )
                )
        return self._deduplicate(risks)

    def _find_evidence(self, content: str, patterns: tuple[str, ...]) -> str | None:
        for line in content.splitlines():
            normalized = line.strip()
            if not normalized:
                continue
            lowered = normalized.lower()
            if any(re.search(regex, lowered, flags=re.IGNORECASE) for regex in patterns):
                return normalized[:240]
        return None

    def _deduplicate(self, risks: list[Risk]) -> list[Risk]:
        seen: set[tuple[str, str]] = set()
        unique_risks: list[Risk] = []
        for risk in risks:
            key = (risk.category.value, risk.title)
            if key in seen:
                continue
            seen.add(key)
            unique_risks.append(risk)
        return unique_risks


def _default_patterns() -> tuple[RiskPattern, ...]:
    return (
        RiskPattern(
            category=RiskCategory.SUBSCRIPTION,
            severity=RiskSeverity.HIGH,
            title="Auto Renewal Detected",
            description="The agreement appears to renew automatically unless the user cancels in time.",
            recommendation="Review cancellation windows and renewal notices before subscribing.",
            patterns=(r"auto\s*renew", r"automatic\s*renewal", r"renews?\s+automatically"),
        ),
        RiskPattern(
            category=RiskCategory.DATA_SHARING,
            severity=RiskSeverity.HIGH,
            title="Third-Party Data Sharing",
            description="The agreement appears to allow sharing personal data with third parties.",
            recommendation="Check what data is shared, with whom, and whether opt-out options exist.",
            patterns=(r"third[- ]party", r"share[s]?\s+.*data", r"disclose[s]?\s+.*data", r"partners?"),
        ),
        RiskPattern(
            category=RiskCategory.CONSUMER_RIGHTS,
            severity=RiskSeverity.MEDIUM,
            title="No Refund Policy",
            description="The agreement may restrict refunds or make them hard to obtain.",
            recommendation="Verify refund eligibility, timelines, and exceptions before purchase.",
            patterns=(r"no\s+refund", r"non[- ]refundable", r"refund(s)?\s+.*not\s+available"),
        ),
        RiskPattern(
            category=RiskCategory.FINANCIAL,
            severity=RiskSeverity.MEDIUM,
            title="Late Payment Penalty",
            description="The agreement may charge penalties or fees for late payments.",
            recommendation="Understand late fees, grace periods, and total cost impact.",
            patterns=(r"late\s+payment", r"penalt(y|ies)", r"late\s+fee(s)?"),
        ),
        RiskPattern(
            category=RiskCategory.PRIVACY,
            severity=RiskSeverity.MEDIUM,
            title="Broad Privacy Permission",
            description="The agreement may collect or process broad categories of personal information.",
            recommendation="Review the scope of collected data and whether it is strictly necessary.",
            patterns=(r"personal\s+information", r"personal\s+data", r"collect(s)?\s+.*data", r"track(s)?\s+user"),
        ),
        RiskPattern(
            category=RiskCategory.LEGAL,
            severity=RiskSeverity.LOW,
            title="Unilateral Terms Change",
            description="The agreement may allow the company to change terms unilaterally.",
            recommendation="Monitor future notices and keep a copy of the terms in force at sign-up.",
            patterns=(r"modify\s+these\s+terms", r"change\s+the\s+terms", r"at\s+any\s+time"),
        ),
    )
