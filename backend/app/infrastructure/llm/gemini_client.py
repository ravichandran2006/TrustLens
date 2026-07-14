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

    def generate_summary(self, content: str, stage: str = "final", max_sentences: int = 6) -> list[str]:
        prompt = self._build_summary_prompt(content, stage=stage, max_sentences=max_sentences)
        response = self._generate(prompt)
        return self._parse_bullets(response)

    def _build_summary_prompt(self, content: str, stage: str, max_sentences: int) -> str:
        if stage == "map":
            task = (
                "Summarize this semantic chunk in one short complete sentence. "
                "Keep the key idea and do not copy wording from the input."
            )
        elif stage == "reduce":
            task = (
                f"Combine these chunk summaries into one final summary in up to {max_sentences} complete sentences. "
                "Write in your own words, keep it simple, and cover the whole document without mentioning chunks."
            )
        else:
            task = (
                f"Read the full document and write one final summary in {max_sentences} complete sentences. "
                "Write in simple English, cover the beginning, middle, and end, and do not copy text verbatim."
            )

        return f"{SUMMARY_PROMPT}\n\nStage: {stage}\nTarget sentences: {max_sentences}\nTask: {task}\n\nInput:\n{content}"

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

        if "stage:" in lower_prompt and "input:" in lower_prompt:
            stage = self._extract_stage(prompt)
            content = prompt.split("Input:\n", 1)[-1].strip()
            sentences = self._split_sentences(content)
            if not sentences:
                return "No reliable summary could be generated from the provided agreement text."

            target_count = self._extract_target_sentences(prompt)
            if stage == "map":
                return sentences[0]

            selected = self._select_covering_sentences(sentences, target_count)
            if selected:
                return "\n".join(f"- {line}" for line in selected)
            return "No reliable summary could be generated from the provided agreement text."

        return "The agreement does not provide sufficient information."

    def _extract_stage(self, prompt: str) -> str:
        match = re.search(r"^Stage:\s*([A-Za-z_]+)$", prompt, flags=re.MULTILINE)
        return match.group(1).strip().lower() if match else "final"

    def _extract_target_sentences(self, prompt: str) -> int:
        match = re.search(r"^Target sentences:\s*(\d+)$", prompt, flags=re.MULTILINE)
        if match:
            try:
                return max(1, int(match.group(1)))
            except ValueError:
                pass
        return 6

    def _split_sentences(self, content: str) -> list[str]:
        parts = re.split(r"(?<=[.!?])\s+|\n+", content.strip())
        return [sentence.strip() for sentence in parts if sentence.strip()]

    def _select_covering_sentences(self, sentences: list[str], target_count: int) -> list[str]:
        if len(sentences) <= target_count:
            return sentences
        if target_count <= 1:
            return [sentences[0]]

        indexes = {round(index * (len(sentences) - 1) / (target_count - 1)) for index in range(target_count)}
        return [sentences[index] for index in sorted(indexes)]

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
