from __future__ import annotations

import re

from app.domain.entities.agreement import Risk
from app.domain.entities.agreement import RiskCategory, RiskSeverity


class DetectRisksUseCase:
    def __init__(self, llm_client: object | None = None) -> None:
        self.llm_client = llm_client

    def execute(self, content: str) -> list[Risk]:
        if not content.strip():
            return []

        llm_risks = self._detect_with_llm(content)
        heuristic_risks = self._detect_with_heuristics(content)

        # Merge both sources so the response includes all detectable risk types.
        if llm_risks and heuristic_risks:
            return self._dedupe(llm_risks + heuristic_risks)
        if llm_risks:
            return self._dedupe(llm_risks)
        return self._dedupe(heuristic_risks)

    def _detect_with_llm(self, content: str) -> list[Risk]:
        if self.llm_client is None or not hasattr(self.llm_client, "detect_risks"):
            return []
        try:
            raw_risks = self.llm_client.detect_risks(content)
        except Exception:
            return []

        if not isinstance(raw_risks, list):
            return []

        risks: list[Risk] = []
        for item in raw_risks:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title", "")).strip()
            description = str(item.get("description", "")).strip()
            if not title or not description:
                continue
            evidence = item.get("evidence")
            recommendation = item.get("recommendation")
            if evidence is not None:
                evidence = str(evidence).strip() or None
            if recommendation is not None:
                recommendation = str(recommendation).strip() or None

            risks.append(
                Risk(
                    category=self._to_category(item.get("category")),
                    title=title,
                    description=description,
                    severity=self._to_severity(item.get("severity")),
                    evidence=evidence,
                    recommendation=recommendation,
                )
            )

        return self._dedupe(risks)

    def _detect_with_heuristics(self, content: str) -> list[Risk]:
        # Broad pattern matching fallback for offline mode (no LLM/API key).
        pattern_specs = [
            {
                "name": "Automatic Renewal",
                "category": RiskCategory.SUBSCRIPTION,
                "severity": RiskSeverity.HIGH,
                "pattern": r"\b(auto(?:matic(?:ally)?)?\s*renew|renews\s+automatically|recurring\s+billing)\b",
                "description": "The document includes automatic renewal or recurring billing terms.",
                "recommendation": "Confirm the renewal notice period and cancellation process before accepting.",
            },
            {
                "name": "Restricted Refund Rights",
                "category": RiskCategory.CONSUMER_RIGHTS,
                "severity": RiskSeverity.HIGH,
                "pattern": r"\b(non[-\s]?refundable|no\s+refunds?|refunds?\s+(?:are\s+)?not\s+available)\b",
                "description": "Refund rights appear limited or excluded.",
                "recommendation": "Ask for written exceptions or a trial/cooling-off period.",
            },
            {
                "name": "Data Sharing with Third Parties",
                "category": RiskCategory.DATA_SHARING,
                "severity": RiskSeverity.HIGH,
                "pattern": r"\b(share\w*\s+.*third[-\s]?part(y|ies)|third[-\s]?part(y|ies)\s+.*access|sell\w*\s+.*data)\b",
                "description": "The agreement allows data sharing or external access to user data.",
                "recommendation": "Review opt-out controls, retention limits, and vendor categories.",
            },
            {
                "name": "Broad Liability Limitation",
                "category": RiskCategory.LEGAL,
                "severity": RiskSeverity.MEDIUM,
                "pattern": r"\b(not\s+liable|liability\s+is\s+limited|limitation\s+of\s+liability|as[-\s]?is)\b",
                "description": "Liability is restricted, which may limit remedies for losses.",
                "recommendation": "Check excluded damages and whether any mandatory protections still apply.",
            },
            {
                "name": "Unilateral Termination Powers",
                "category": RiskCategory.CONSUMER_RIGHTS,
                "severity": RiskSeverity.MEDIUM,
                "pattern": r"\b(terminate\w*\s+.*without\s+notice|suspend\w*\s+.*at\s+any\s+time|sole\s+discretion)\b",
                "description": "One party may suspend or terminate access with limited notice.",
                "recommendation": "Confirm notice requirements and appeal/remediation options.",
            },
            {
                "name": "Arbitration or Waiver Clauses",
                "category": RiskCategory.LEGAL,
                "severity": RiskSeverity.MEDIUM,
                "pattern": r"\b(arbitration|class\s+action\s+waiver|waive\s+.*jury\s+trial)\b",
                "description": "Dispute resolution may restrict court-based options.",
                "recommendation": "Review dispute venue, costs, and any opt-out window.",
            },
            {
                "name": "Penalty or Additional Fee Exposure",
                "category": RiskCategory.FINANCIAL,
                "severity": RiskSeverity.MEDIUM,
                "pattern": r"\b(late\s+fee|penalt(y|ies)|administrative\s+charge|processing\s+fee|service\s+fee)\b",
                "description": "Additional charges or penalties may apply.",
                "recommendation": "Check when fees trigger and whether fee caps are defined.",
            },
            {
                "name": "Extensive Data Collection",
                "category": RiskCategory.PRIVACY,
                "severity": RiskSeverity.MEDIUM,
                "pattern": r"\b(collect\w*\s+.*personal\s+data|track\w*\s+.*activity|location\s+data|behavioral\s+data)\b",
                "description": "The agreement permits broad personal data collection or tracking.",
                "recommendation": "Review data minimization, retention period, and deletion rights.",
            },
        ]

        sentences = self._split_sentences(content)
        risks: list[Risk] = []

        for sentence in sentences:
            for spec in pattern_specs:
                if not re.search(spec["pattern"], sentence, flags=re.IGNORECASE):
                    continue
                risks.append(
                    Risk(
                        category=spec["category"],
                        severity=spec["severity"],
                        title=spec["name"],
                        description=spec["description"],
                        evidence=sentence,
                        recommendation=spec["recommendation"],
                    )
                )

        return self._dedupe(risks)

    def _split_sentences(self, content: str) -> list[str]:
        parts = re.split(r"(?<=[.!?])\s+|\n+", content.strip())
        return [part.strip() for part in parts if part.strip()]

    def _to_category(self, value: object) -> RiskCategory:
        text = str(value or "").strip().lower()
        mapping = {
            "privacy": RiskCategory.PRIVACY,
            "privacy risk": RiskCategory.PRIVACY,
            "data sharing": RiskCategory.DATA_SHARING,
            "data sharing risk": RiskCategory.DATA_SHARING,
            "financial": RiskCategory.FINANCIAL,
            "financial risk": RiskCategory.FINANCIAL,
            "subscription": RiskCategory.SUBSCRIPTION,
            "subscription risk": RiskCategory.SUBSCRIPTION,
            "legal": RiskCategory.LEGAL,
            "legal risk": RiskCategory.LEGAL,
            "consumer rights": RiskCategory.CONSUMER_RIGHTS,
            "consumer rights risk": RiskCategory.CONSUMER_RIGHTS,
        }
        return mapping.get(text, RiskCategory.LEGAL)

    def _to_severity(self, value: object) -> RiskSeverity:
        text = str(value or "").strip().lower()
        if text == "high":
            return RiskSeverity.HIGH
        if text == "low":
            return RiskSeverity.LOW
        return RiskSeverity.MEDIUM

    def _dedupe(self, risks: list[Risk]) -> list[Risk]:
        seen: set[tuple[str, str]] = set()
        deduped: list[Risk] = []
        for risk in risks:
            key = (risk.title.strip().lower(), (risk.evidence or "").strip().lower())
            if key in seen:
                continue
            seen.add(key)
            deduped.append(risk)
        return deduped