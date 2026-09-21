"""Local translation via Ollama native API (with think:false for speed)."""

from __future__ import annotations

import json
import time

import httpx

from .base import LLMProvider, TranslationResult
from .deepseek_provider import _parse_structured
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


class OllamaProvider(LLMProvider):
    """Uses Ollama's native /api/chat with think:false to skip reasoning."""

    def __init__(
        self,
        host: str = "http://localhost:11434",
        model: str = "qwen3.5:9b",
    ) -> None:
        self._host = host.rstrip("/")
        self._model = model

    @property
    def name(self) -> str:
        return f"Ollama ({self._model})"

    def test_connection(self) -> bool:
        try:
            resp = httpx.get(f"{self._host}/api/tags", timeout=3.0)
            return resp.status_code == 200
        except Exception:
            return False

    def list_models(self) -> list[str]:
        """Return installed model names."""
        try:
            resp = httpx.get(f"{self._host}/api/tags", timeout=3.0)
            if resp.status_code != 200:
                return []
            data = resp.json()
            return [m["name"] for m in data.get("models", [])]
        except Exception:
            return []

    def translate(
        self,
        text: str,
        source_lang: str = "auto",
        target_lang: str = "zh",
        timeout: float = 30.0,
        detailed: bool = False,
    ) -> TranslationResult:
        start = time.monotonic()
        target_name = _LANG_NAMES.get(target_lang, target_lang)

        if not detailed:
            prompt = TRANSLATION_QUICK_PROMPT.format(target_lang=target_name, text=text)
            payload = {
                "model": self._model,
                "messages": [{"role": "user", "content": prompt}],
                "think": False,
                "stream": False,
            }
            resp = httpx.post(f"{self._host}/api/chat", json=payload, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            raw = data.get("message", {}).get("content", "")
            latency = time.monotonic() - start
            return TranslationResult(translation=raw.strip(), engine=self.name, latency=latency, structured=False)

        # Detailed mode: full structured JSON output.
        prompt = TRANSLATION_PROMPT.format(target_lang=target_name, text=text)

        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": "You are a translator. Output only JSON."},
                {"role": "user", "content": prompt},
            ],
            "think": False,
            "stream": False,
        }

        resp = httpx.post(
            f"{self._host}/api/chat",
            json=payload,
            timeout=timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        raw = data.get("message", {}).get("content", "")
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

        return TranslationResult(
            translation=raw,
            engine=self.name,
            latency=latency,
            structured=False,
        )
