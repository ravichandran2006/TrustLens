from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field
from typing import Iterable

try:
    from sentence_transformers import SentenceTransformer  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    SentenceTransformer = None


@dataclass(slots=True)
class EmbeddingService:
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    _model: object = field(init=False, default=None)

    def __post_init__(self) -> None:
        self._model = SentenceTransformer(self.model_name) if SentenceTransformer is not None else None

    def embed_text(self, text: str) -> list[float]:
        if self._model is not None:
            vector = self._model.encode([text], normalize_embeddings=True)[0]
            return [float(value) for value in vector]
        return self._fallback_embedding(text)

    def embed_many(self, texts: Iterable[str]) -> list[list[float]]:
        return [self.embed_text(text) for text in texts]

    def _fallback_embedding(self, text: str, dimensions: int = 16) -> list[float]:
        values = [0.0] * dimensions
        tokens = [token for token in text.lower().split() if token]
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            bucket = digest[0] % dimensions
            values[bucket] += 1.0
        norm = math.sqrt(sum(value * value for value in values)) or 1.0
        return [value / norm for value in values]
