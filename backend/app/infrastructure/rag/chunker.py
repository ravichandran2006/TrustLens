from __future__ import annotations

from dataclasses import dataclass

from app.config.constants import DEFAULT_CHUNK_OVERLAP, DEFAULT_CHUNK_SIZE
from app.infrastructure.rag.retriever import AgreementChunk


@dataclass(slots=True)
class AgreementChunker:
    chunk_size: int = DEFAULT_CHUNK_SIZE
    overlap: int = DEFAULT_CHUNK_OVERLAP

    def chunk(self, content: str, agreement_id: str | None = None) -> list[AgreementChunk]:
        normalized = " ".join(content.split())
        if not normalized:
            return []

        chunks: list[AgreementChunk] = []
        start = 0
        index = 0
        while start < len(normalized):
            end = min(len(normalized), start + self.chunk_size)
            chunk_text = normalized[start:end].strip()
            if chunk_text:
                chunk_id = f"{agreement_id}_chunk_{index}" if agreement_id else f"chunk_{index}"
                chunks.append(
                    AgreementChunk(
                        id=chunk_id,
                        agreement_id=agreement_id or "",
                        text=chunk_text,
                        source=f"Clause {index + 1}",
                    )
                )
                index += 1
            if end >= len(normalized):
                break
            start = max(0, end - self.overlap)
        return chunks
