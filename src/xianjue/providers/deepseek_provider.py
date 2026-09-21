"""Cloud translation via DeepSeek (OpenAI-compatible API)."""

from __future__ import annotations

import json
import time
from typing import Any

from openai import OpenAI

from .base import LLMProvider, TranslationResult
from .prompts import TRANSLATION_PROMPT, TRANSLATION_QUICK_PROMPT

_LANG_NAMES = {
    "zh": "Chinese",
    "en": "English",
    "ja": "Japanese",
    "ko": "Korean",
    "fr": "French",
    "de": "German",
    "es": "Spanish",
    "ru": "Russian",
}


def _parse_structured(raw: str) -> dict:
    """Best-effort JSON extraction from LLM output."""
    stripped = raw.strip()
    # Try direct parse.
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass
    # Try to find a JSON object between the first { and last }.
    first = stripped.find("{")
    last = stripped.rfind("}")
    if first != -1 and last > first:
        try:
            return json.loads(stripped[first : last + 1])
        except json.JSONDecodeError:
            pass
    # Markdown code block.
    if "```json" in stripped:
        start = stripped.find("```json") + len("```json")
        end = stripped.find("```", start)
        if end > start:
            try:
                return json.loads(stripped[start:end].strip())
            except json.JSONDecodeError:
                pass
    return {}


class DeepSeekProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "deepseek-chat") -> None:
        self._api_key = api_key
        self._model = model
        self._client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com",
        )

    @property
    def name(self) -> str:
        return f"DeepSeek ({self._model})"

    def test_connection(self) -> bool:
        try:
            self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=5,
            )
            return True
        except Exception:
            return False

    def translate(
        self,
        text: str,
        source_lang: str = "auto",
        target_lang: str = "zh",
        timeout: float = 15.0,
        detailed: bool = False,
    ) -> TranslationResult:
        start = time.monotonic()
        target_name = _LANG_NAMES.get(target_lang, target_lang)

        if not detailed:
            prompt = TRANSLATION_QUICK_PROMPT.format(target_lang=target_name, text=text)
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1024,
                temperature=0.3,
            )
            raw = response.choices[0].message.content or ""
            latency = time.monotonic() - start
            return TranslationResult(translation=raw.strip(), engine=self.name, latency=latency, structured=False)

        # Detailed mode: full structured JSON output.
        prompt = TRANSLATION_PROMPT.format(target_lang=target_name, text=text)

        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": "You are a translator. Output only JSON."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=2048,
            temperature=0.3,
        )
        raw = response.choices[0].message.content or ""
        latency = time.monotonic() - start

        parsed = _parse_structured(raw)
        if parsed and "translation" in parsed:
            return TranslationResult(
                translation=parsed.get("translation", raw),
                terms=parsed.get("terms", []),
                sentence_pairs=parsed.get("sentence_pairs", []),
                word_map=parsed.get("word_map", []),
                engine=self.name,
                latency=latency,
                structured=True,
            )

        # Fallback: treat the whole response as plain translation.
        return TranslationResult(
            translation=raw,
            engine=self.name,
            latency=latency,
            structured=False,
        )
