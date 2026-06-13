from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any

from app.infrastructure.llm.prompts import QUESTION_PROMPT, SUMMARY_PROMPT

try:
    import google.generativeai as genai  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    genai = None

@dataclass(slots=True)
class GeminiClient:
    api_key: str | None = None
    model_name: str = "gemini-1.5-flash"
    _model: object = field(init=False, default=None)

    def __post_init__(self) -> None:
        self.api_key = self.api_key or os.getenv("GEMINI_API_KEY")
        if genai is not None and self.api_key:
            genai.configure(api_key=self.api_key)
            self._model = genai.GenerativeModel(self.model_name)
        else:
            self._model = None

    def generate_summary(self, content: str) -> list[str]:
        prompt = f"{SUMMARY_PROMPT}\n\nAgreement:\n{content}"
        response = self._generate(prompt)
        return self._parse_bullets(response)

    def answer_question(self, question: str, context: str) -> str:
        prompt = f"{QUESTION_PROMPT}\n\nQuestion:\n{question}\n\nAgreement Context:\n{context}"
        response = self._generate(prompt)
        return self._strip_code_fences(response)

    def _generate(self, prompt: str) -> str:
        if self._model is None:
            return self._fallback_response(prompt)
        try:
            response = self._model.generate_content(prompt)
            text = getattr(response, "text", "") or ""
            return text.strip()
        except Exception as e:
            print(f"Gemini API error: {e}")
            return self._fallback_response(prompt)

    def _fallback_response(self, prompt: str) -> str:
        """Generate a simple fallback response based on keywords in the prompt"""
        if "summary" in prompt.lower():
            return "• Key terms and conditions identified\n• Review required before acceptance"
        elif "question" in prompt.lower():
            if "refund" in prompt.lower() or "cancel" in prompt.lower():
                return "Based on the agreement, please refer to the terms and conditions section for details on refunds and cancellations."
            elif "data" in prompt.lower() or "privacy" in prompt.lower():
                return "The agreement contains provisions regarding data handling. Please review the privacy section carefully."
            else:
                return "This question relates to the agreement terms. Please refer to the relevant sections for accurate information."
        return "Unable to generate response at this time."

    def _strip_code_fences(self, text: str) -> str:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
        return cleaned.strip()

    def _parse_bullets(self, text: str) -> list[str]:
        if not text:
            return []
        bullets: list[str] = []
        for line in text.splitlines():
            stripped = line.strip("-• \t")
            if stripped:
                bullets.append(stripped)
        return bullets or [text.strip()]
