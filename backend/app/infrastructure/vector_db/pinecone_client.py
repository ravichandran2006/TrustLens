from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

try:
    from pinecone import Pinecone, ServerlessSpec  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    Pinecone = None
    ServerlessSpec = None


@dataclass(slots=True)
class PineconeVectorStore:
    api_key: str | None = None
    index_name: str = "trustlens-agreements"
    namespace: str = "default"
    dimension: int = 384
    cloud: str = "aws"
    region: str = "us-east-1"
    _memory_store: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    _client: object = field(init=False, default=None)
    _index: object = field(init=False, default=None)

    def __post_init__(self) -> None:
        self._client = Pinecone(api_key=self.api_key) if Pinecone is not None and self.api_key else None
        self._index = self._ensure_index() if self._client is not None else None

    def _ensure_index(self) -> object | None:
        if self._client is None:
            return None
        if not self._client.has_index(self.index_name):
            if ServerlessSpec is None:
                print(f"[Pinecone] ServerlessSpec unavailable, cannot create missing index {self.index_name}")
                return None
            print(
                f"[Pinecone] Creating missing index {self.index_name} with dimension {self.dimension} "
                f"in {self.cloud}/{self.region}"
            )
            self._client.create_index(
                name=self.index_name,
                dimension=self.dimension,
                metric="cosine",
                spec=ServerlessSpec(cloud=self.cloud, region=self.region),
            )
        return self._client.Index(self.index_name)

    def upsert(self, agreement_id: str, vectors: list[dict[str, Any]]) -> None:
        if self._index is not None:
            self._index.upsert(vectors=vectors, namespace=self.namespace)
            print(
                f"[Pinecone] Upserted {len(vectors)} chunks for agreement {agreement_id} "
                f"into index {self.index_name} namespace {self.namespace}"
            )
            for vector in vectors:
                metadata = vector.get("metadata", {})
                print(
                    f"[Pinecone] chunk_id={vector.get('id', '')} "
                    f"text={metadata.get('text', '')[:120]}"
                )
            return
        self._memory_store[agreement_id] = vectors
        print(
            f"[Pinecone] Pinecone client unavailable, stored {len(vectors)} vectors in memory "
            f"for agreement {agreement_id}"
        )

    def query(self, vector: list[float], top_k: int = 5, agreement_id: str | None = None) -> list[dict[str, Any]]:
        if self._index is not None:
            filter_payload = {"agreement_id": {"$eq": agreement_id}} if agreement_id else None
            response = self._index.query(vector=vector, top_k=top_k, namespace=self.namespace, include_metadata=True, filter=filter_payload)
            matches = getattr(response, "matches", []) or []
            return [
                {
                    "id": match.id,
                    "score": getattr(match, "score", 0.0),
                    "metadata": getattr(match, "metadata", {}) or {},
                }
                for match in matches
            ]

        stored = self._memory_store.get(agreement_id or "", [])
        return stored[:top_k]
