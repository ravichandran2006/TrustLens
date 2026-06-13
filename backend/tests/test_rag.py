from __future__ import annotations

import unittest

from app.infrastructure.rag.chunker import AgreementChunker
from app.infrastructure.rag.context_builder import ContextBuilder
from app.infrastructure.rag.retriever import AgreementChunk, InMemoryAgreementRetriever, PineconeAgreementRetriever


class _FakeEmbeddingService:
    def embed_text(self, text: str) -> list[float]:
        return [float(len(text))]


class _FakeVectorStore:
    def __init__(self) -> None:
        self.upsert_calls: list[tuple[str, list[dict[str, object]]]] = []
        self.query_result: list[dict[str, object]] = []

    def upsert(self, agreement_id: str, vectors: list[dict[str, object]]) -> None:
        self.upsert_calls.append((agreement_id, vectors))

    def query(self, vector: list[float], top_k: int = 5, agreement_id: str | None = None) -> list[dict[str, object]]:
        return self.query_result[:top_k]


class RagTests(unittest.TestCase):
    def test_chunker_and_retriever_work_together(self) -> None:
        retriever = InMemoryAgreementRetriever()
        chunker = AgreementChunker()
        chunks = chunker.chunk(
            'The subscription renews automatically unless cancelled. Refunds are not provided. '
            'The company may share data with third-party vendors.',
            agreement_id='agr_1',
        )
        retriever.index('agr_1', chunks)
        result = retriever.retrieve('agr_1', 'Will the subscription renew automatically?')
        self.assertTrue(result)
        context = ContextBuilder().build(result)
        self.assertIn('Clause', context)

    def test_pinecone_retriever_queries_vector_store_without_memory_cache(self) -> None:
        vector_store = _FakeVectorStore()
        retriever = PineconeAgreementRetriever(
            embedding_service=_FakeEmbeddingService(),
            vector_store=vector_store,
        )
        chunks = [
            AgreementChunk(id='chunk_0', agreement_id='agr_1', text='First clause', source='Clause 1'),
            AgreementChunk(id='chunk_1', agreement_id='agr_1', text='Second clause', source='Clause 2'),
        ]

        retriever.index('agr_1', chunks)
        vector_store.query_result = [
            {
                'id': 'chunk_1',
                'score': 0.98,
                'metadata': {'agreement_id': 'agr_1', 'text': 'Second clause', 'source': 'Clause 2'},
            }
        ]

        result = retriever.retrieve('agr_1', 'second clause')

        self.assertEqual(len(vector_store.upsert_calls), 1)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, 'chunk_1')
        self.assertEqual(result[0].text, 'Second clause')


if __name__ == '__main__':
    unittest.main()
