from __future__ import annotations

import unittest

from app.application.use_cases.answer_question import AnswerQuestionUseCase
from app.infrastructure.mongodb.mongodb_client import MongoDBClient
from app.infrastructure.rag.chunker import AgreementChunker
from app.infrastructure.rag.context_builder import ContextBuilder
from app.infrastructure.rag.retriever import InMemoryAgreementRetriever

class QuestionTests(unittest.TestCase):
    def test_answer_question_returns_insufficient_information_when_needed(self) -> None:
        repository = MongoDBClient(uri=None)
        retriever = InMemoryAgreementRetriever()
        retriever.index(
            'agr_1',
            AgreementChunker().chunk('This agreement covers account access and support.', agreement_id='agr_1'),
        )
        use_case = AnswerQuestionUseCase(
            retriever=retriever,
            context_builder=ContextBuilder(),
            llm_client=None,
        )
        result = use_case.execute('agr_1', 'Can I get a refund?')
        self.assertEqual(result.answer, 'The agreement does not provide sufficient information.')

if __name__ == '__main__':
    unittest.main()
