from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(slots=True)
class SummaryResult:
    bullets: list[str]


class GenerateSummaryUseCase:
    def __init__(self, llm_client: object | None = None, chunk_char_limit: int = 1800) -> None:
        self.llm_client = llm_client
        self.chunk_char_limit = chunk_char_limit

    def execute(self, content: str, max_sentences: int = 6) -> SummaryResult:
        normalized_content = self._normalize_whitespace(content)
        if not normalized_content:
            return SummaryResult(bullets=["The agreement does not contain enough structured text to summarize reliably."])

        # Hierarchical summarization: summarize semantic chunks first, then synthesize the chunk summaries into one final response.
        chunks = self._build_semantic_chunks(normalized_content)
        chunk_summaries = [summary for summary in (self._summarize_chunk(chunk) for chunk in chunks) if summary]
        if not chunk_summaries:
            chunk_summaries = self._extract_sentences(normalized_content)

        final_summary = self._reduce_summaries(chunk_summaries, normalized_content, max_sentences=max_sentences)
        bullets = self._normalize_sentences(final_summary)
        bullets = self._ensure_minimum_sentences(
            bullets,
            chunk_summaries=chunk_summaries,
            full_content=normalized_content,
            minimum_sentences=3,
            max_sentences=max_sentences,
        )
        if len(bullets) < max_sentences and len(chunk_summaries) > len(bullets):
            for sentence in self._normalize_sentences(chunk_summaries):
                if sentence not in bullets:
                    bullets.append(sentence)
                if len(bullets) >= max_sentences:
                    break
        return SummaryResult(
            bullets=bullets[:max_sentences] or ["The agreement does not contain enough structured text to summarize reliably."]
        )

    def _summarize_chunk(self, chunk: str) -> str:
        summary = self._invoke_llm(chunk, stage="map", max_sentences=1)
        if summary:
            return summary[0]
        sentences = self._extract_sentences(chunk)
        return sentences[0] if sentences else ""

    def _reduce_summaries(self, chunk_summaries: list[str], full_content: str, max_sentences: int) -> list[str]:
        merged_input = "\n".join(chunk_summaries)
        summary = self._invoke_llm(merged_input, stage="reduce", max_sentences=max_sentences)
        if summary:
            return summary
        return self._fallback_reduce(chunk_summaries or [full_content], max_sentences)

    def _invoke_llm(self, text: str, stage: str, max_sentences: int) -> list[str]:
        if self.llm_client is None or not hasattr(self.llm_client, "generate_summary"):
            return []

        generate_summary = getattr(self.llm_client, "generate_summary")
        try:
            response = generate_summary(text, stage=stage, max_sentences=max_sentences)
        except TypeError:
            try:
                response = generate_summary(text)
            except Exception:
                return []
        except Exception:
            return []
        return self._coerce_summary_response(response)

    def _coerce_summary_response(self, response: object) -> list[str]:
        if isinstance(response, str):
            return [response]
        if isinstance(response, list):
            return [str(item) for item in response if str(item).strip()]
        return []

    def _build_semantic_chunks(self, content: str) -> list[str]:
        sentences = self._extract_sentences(content)
        if not sentences:
            return [content] if content else []

        chunks: list[str] = []
        current_sentences: list[str] = []
        current_length = 0
        for sentence in sentences:
            sentence_length = len(sentence)
            if current_sentences and current_length + sentence_length + 1 > self.chunk_char_limit:
                chunks.append(" ".join(current_sentences))
                current_sentences = [sentence]
                current_length = sentence_length
            else:
                current_sentences.append(sentence)
                current_length += sentence_length + 1

        if current_sentences:
            chunks.append(" ".join(current_sentences))
        return chunks

    def _extract_sentences(self, content: str) -> list[str]:
        parts = re.split(r"(?<=[.!?])\s+|\n+", content.strip())
        return [part.strip() for part in parts if part.strip()]

    def _fallback_reduce(self, source_items: list[str], max_sentences: int) -> list[str]:
        sentences = self._normalize_sentences(source_items)
        if not sentences:
            return []
        selected = self._select_covering_sentences(sentences, max_sentences)
        return self._normalize_sentences(selected)

    def _ensure_minimum_sentences(
        self,
        bullets: list[str],
        chunk_summaries: list[str],
        full_content: str,
        minimum_sentences: int,
        max_sentences: int,
    ) -> list[str]:
        if len(bullets) >= minimum_sentences:
            return bullets

        for sentence in self._normalize_sentences(chunk_summaries):
            if sentence not in bullets:
                bullets.append(sentence)
            if len(bullets) >= minimum_sentences or len(bullets) >= max_sentences:
                return bullets

        for sentence in self._select_covering_sentences(self._extract_sentences(full_content), max_sentences):
            cleaned = self._ensure_terminal_punctuation(sentence)
            if cleaned not in bullets:
                bullets.append(cleaned)
            if len(bullets) >= minimum_sentences or len(bullets) >= max_sentences:
                break
        return bullets

    def _select_covering_sentences(self, sentences: list[str], max_sentences: int) -> list[str]:
        if len(sentences) <= max_sentences:
            return sentences
        if max_sentences <= 1:
            return [sentences[0]]

        count = min(max_sentences, len(sentences))
        indexes = {round(index * (len(sentences) - 1) / (count - 1)) for index in range(count)}
        return [sentences[index] for index in sorted(indexes)]

    def _normalize_sentences(self, items: list[str]) -> list[str]:
        normalized: list[str] = []
        for item in items:
            text = " ".join(str(item).split()).strip("-• ")
            if not text:
                continue
            for sentence in self._extract_sentences(text) or [text]:
                cleaned = self._ensure_terminal_punctuation(sentence.strip())
                if cleaned not in normalized:
                    normalized.append(cleaned)
        return normalized

    def _normalize_whitespace(self, content: str) -> str:
        return " ".join(content.split()).strip()

    def _ensure_terminal_punctuation(self, text: str) -> str:
        if text.endswith((".", "!", "?")):
            return text
        return f"{text}."
