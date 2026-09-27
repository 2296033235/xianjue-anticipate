"""Cloud translation through an OpenAI-compatible API."""

from __future__ import annotations

import time

from openai import OpenAI

from .base import LLMProvider, TranslationResult
from .deepseek_provider import _LANG_NAMES, _parse_structured
from .prompts import TRANSLATION_PROMPT, TRANSLATION_QUICK_PROMPT


class OpenAICompatibleProvider(LLMProvider):
    """Reuse the translation protocol while allowing custom base URLs."""

    def __init__(self, api_key: str, model: str, base_url: str) -> None:
        self._client = OpenAI(api_key=api_key, base_url=base_url)
        self._model = model

    @property
    def name(self) -> str:
        return f"Custom ({self._model})"

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
            return TranslationResult(
                translation=raw.strip(),
                engine=self.name,
                latency=time.monotonic() - start,
            )

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
        parsed = _parse_structured(raw)
        if parsed and "translation" in parsed:
            return TranslationResult(
                translation=parsed.get("translation", raw),
                terms=parsed.get("terms", []),
                sentence_pairs=parsed.get("sentence_pairs", []),
                word_map=parsed.get("word_map", []),
                engine=self.name,
                latency=time.monotonic() - start,
                structured=True,
            )
        return TranslationResult(translation=raw, engine=self.name, latency=time.monotonic() - start)
