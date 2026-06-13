from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from app.infrastructure.embeddings.embedding_service import EmbeddingService
from app.infrastructure.vector_db.pinecone_client import PineconeVectorStore


@dataclass(slots=True)
class AgreementChunk:
    id: str
    agreement_id: str
    text: str
    source: str
    embedding: list[float] | None = None


class AgreementRetriever(Protocol):
    def index(self, agreement_id: str, chunks: list[AgreementChunk]) -> None:
        raise NotImplementedError

    def retrieve(self, agreement_id: str, query: str, top_k: int = 5) -> list[AgreementChunk]:
        raise NotImplementedError


@dataclass(slots=True)
class PineconeAgreementRetriever:
    embedding_service: EmbeddingService
    vector_store: PineconeVectorStore
    _memory_chunks: dict[str, list[AgreementChunk]] = field(default_factory=dict)

    def index(self, agreement_id: str, chunks: list[AgreementChunk]) -> None:
        vectors = []
        for chunk in chunks:
            chunk.embedding = self.embedding_service.embed_text(chunk.text)
            vectors.append(
                {
                    "id": chunk.id,
                    "values": chunk.embedding,
                    "metadata": {"agreement_id": agreement_id, "text": chunk.text, "source": chunk.source},
                }
            )
        self._memory_chunks[agreement_id] = chunks
        self.vector_store.upsert(agreement_id, vectors)

    def retrieve(self, agreement_id: str, query: str, top_k: int = 5) -> list[AgreementChunk]:
        query_vector = self.embedding_service.embed_text(query)
        matches = self.vector_store.query(query_vector, top_k=top_k, agreement_id=agreement_id)
        if not matches:
            chunks = self._memory_chunks.get(agreement_id, [])
            return chunks[:top_k]
        ordered: list[AgreementChunk] = []
        for match in matches:
            metadata = match.get("metadata", {})
            ordered.append(
                AgreementChunk(
                    id=match.get("id", ""),
                    agreement_id=metadata.get("agreement_id", agreement_id),
                    text=metadata.get("text", ""),
                    source=metadata.get("source", ""),
                )
            )
        return ordered[:top_k]


@dataclass(slots=True)
class InMemoryAgreementRetriever:
    embedding_service: EmbeddingService | None = None
    _store: dict[str, list[AgreementChunk]] = field(default_factory=dict)

    def index(self, agreement_id: str, chunks: list[AgreementChunk]) -> None:
        self._store[agreement_id] = chunks

    def retrieve(self, agreement_id: str, query: str, top_k: int = 5) -> list[AgreementChunk]:
        chunks = self._store.get(agreement_id, [])
        if not chunks:
            return []
        if self.embedding_service is None:
            return chunks[:top_k]
        query_terms = set(query.lower().split())
        ranked = sorted(
            chunks,
            key=lambda chunk: len(query_terms.intersection(set(chunk.text.lower().split()))),
            reverse=True,
        )
        return ranked[:top_k]
