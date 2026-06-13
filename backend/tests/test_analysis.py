from __future__ import annotations

import unittest

from app.application.use_cases.analyze_agreement import AnalyzeAgreementUseCase
from app.application.use_cases.calculate_trust_score import CalculateTrustScoreUseCase
from app.application.use_cases.detect_risks import DetectRisksUseCase
from app.infrastructure.mongodb.mongodb_client import MongoDBClient
from app.infrastructure.rag.chunker import AgreementChunker
from app.infrastructure.rag.context_builder import ContextBuilder
from app.infrastructure.rag.retriever import InMemoryAgreementRetriever


class AnalysisTests(unittest.TestCase):
    def test_detect_risks_and_score(self) -> None:
        content = (
            'This subscription renews automatically unless cancelled. We may share data with third-party vendors. '
            'All fees are non-refundable and late payment penalties may apply.'
        )
        risks = DetectRisksUseCase().execute(content)
        self.assertGreaterEqual(len(risks), 3)

        score = CalculateTrustScoreUseCase().execute(risks)
        self.assertLess(score.score, 100)
        self.assertIn(score.risk_level, {'Low', 'Medium', 'High'})

    def test_analyze_use_case_returns_report(self) -> None:
        repository = MongoDBClient(uri=None)
        retriever = InMemoryAgreementRetriever()
        use_case = AnalyzeAgreementUseCase(
            agreement_repository=repository,
            retriever=retriever,
            chunker=AgreementChunker(),
            context_builder=ContextBuilder(),
        )
        result = use_case.execute(
            content='The subscription renews automatically. Refunds are not available. We share data with vendors.',
            document_type='subscription_agreement',
        )
        self.assertTrue(result.agreement.id.startswith('agr_'))
        self.assertGreater(len(result.report.summary), 0)
        self.assertGreater(len(result.report.risks), 0)


if __name__ == '__main__':
    unittest.main()
