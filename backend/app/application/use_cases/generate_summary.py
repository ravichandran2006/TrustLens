from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(slots=True)
class SummaryResult:
    bullets: list[str]


class GenerateSummaryUseCase:
    def __init__(self, llm_client: object | None = None) -> None:
        self.llm_client = llm_client

    def execute(self, content: str, max_bullets: int = 3) -> SummaryResult:
        if self.llm_client is not None and hasattr(self.llm_client, "generate_summary"):
            try:
                bullets = self.llm_client.generate_summary(content)
                cleaned = self._normalize_bullets(bullets)
                if cleaned:
                    return SummaryResult(bullets=cleaned[:max_bullets])
            except Exception:
                pass

        sentences = self._split_sentences(content)
        bullets = self._select_high_signal_sentences(sentences, max_bullets)
        if not bullets:
            bullets = ["The agreement did not contain enough structured text to summarize reliably."]
        return SummaryResult(bullets=self._normalize_bullets(bullets)[:max_bullets])

    def _split_sentences(self, content: str) -> list[str]:
        parts = re.split(r"(?<=[.!?])\s+|\n+", content.strip())
        return [part.strip() for part in parts if len(part.strip()) > 30]

    def _select_high_signal_sentences(self, sentences: list[str], max_bullets: int) -> list[str]:
        keywords = (
            "renew",
            "refund",
            "terminate",
            "share",
            "data",
            "privacy",
            "fee",
            "payment",
            "cancel",
            "subscription",
        )
        scored = sorted(
            sentences,
            key=lambda sentence: (sum(keyword in sentence.lower() for keyword in keywords), len(sentence)),
            reverse=True,
        )
        deduped: list[str] = []
        for sentence in scored:
            if sentence in deduped:
                continue
            deduped.append(sentence)
            if len(deduped) == max_bullets:
                break
        return deduped

    def _normalize_bullets(self, bullets: list[str], max_chars: int = 120) -> list[str]:
        concise: list[str] = []
        for bullet in bullets:
            text = " ".join(str(bullet).split()).strip("-• ")
            if not text:
                continue
            if len(text) > max_chars:
                text = text[: max_chars - 1].rstrip() + "..."
            if text not in concise:
                concise.append(text)
        return concise
