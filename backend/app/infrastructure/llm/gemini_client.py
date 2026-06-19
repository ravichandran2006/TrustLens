from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from typing import Any

from app.infrastructure.llm.prompts import QUESTION_PROMPT, RISK_DETECTION_PROMPT, SUMMARY_PROMPT

try:
    import google.generativeai as genai  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    genai = None

@dataclass(slots=True)
class GeminiClient:
    api_key: str | None = None
    model_name: str = "gemini-1.5-pro"
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

    def detect_risks(self, content: str) -> list[dict[str, Any]]:
        prompt = f"{RISK_DETECTION_PROMPT}\n\nAgreement:\n{content}"
        response = self._generate(prompt)
        parsed = self._parse_json_payload(response)
        if isinstance(parsed, list):
            return [item for item in parsed if isinstance(item, dict)]
        if isinstance(parsed, dict) and isinstance(parsed.get("risks"), list):
            return [item for item in parsed["risks"] if isinstance(item, dict)]
        return []

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
        lower_prompt = prompt.lower()
        if "output format" in lower_prompt and "category" in lower_prompt and "severity" in lower_prompt:
            return "[]"

        if "agreement context:" in prompt:
            context = prompt.split("Agreement Context:\n", 1)[-1].strip()
            if not context:
                return "The agreement does not provide sufficient information."
            first_sentence = re.split(r"(?<=[.!?])\s+|\n+", context)[0].strip()
            return first_sentence or "The agreement does not provide sufficient information."

        if "agreement:" in lower_prompt:
            content = prompt.split("Agreement:\n", 1)[-1].strip()
            sentences = [
                sentence.strip()
                for sentence in re.split(r"(?<=[.!?])\s+|\n+", content)
                if sentence.strip()
            ]
            selected = sentences[:5]
            if selected:
                return "\n".join(f"- {line}" for line in selected)
            return "No reliable summary could be generated from the provided agreement text."

        return "The agreement does not provide sufficient information."

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

    def _parse_json_payload(self, text: str) -> Any:
        cleaned = self._strip_code_fences(text)
        if not cleaned:
            return []

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        first_array = cleaned.find("[")
        last_array = cleaned.rfind("]")
        if first_array != -1 and last_array != -1 and last_array > first_array:
            candidate = cleaned[first_array:last_array + 1]
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                pass

        first_obj = cleaned.find("{")
        last_obj = cleaned.rfind("}")
        if first_obj != -1 and last_obj != -1 and last_obj > first_obj:
            candidate = cleaned[first_obj:last_obj + 1]
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                pass

        return []
