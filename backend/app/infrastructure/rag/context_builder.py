from __future__ import annotations

from dataclasses import dataclass

from app.config.constants import DEFAULT_MAX_CONTEXT_CHARS
from app.infrastructure.rag.retriever import AgreementChunk


@dataclass(slots=True)
class ContextBuilder:
    max_chars: int = DEFAULT_MAX_CONTEXT_CHARS

    def build(self, chunks: list[AgreementChunk]) -> str:
        lines: list[str] = []
        remaining = self.max_chars
        for chunk in chunks:
            line = f"[{chunk.source}] {chunk.text.strip()}"
            if len(line) > remaining:
                break
            lines.append(line)
            remaining -= len(line)
        return "\n\n".join(lines)
