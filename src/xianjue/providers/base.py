"""Abstract base for all LLM providers (cloud and local)."""

from __future__ import annotations

import abc
from dataclasses import dataclass, field


@dataclass
class TranslationResult:
    """Structured output from a translation request."""

    # Full translated text.
    translation: str
    # List of terms: [{"original": "...", "translation": "...", "explanation": "..."}]
    terms: list = field(default_factory=list)
    # Sentence-level alignment: [{"source": "...", "target": "..."}]
    sentence_pairs: list = field(default_factory=list)
    # Word-level mapping: [{"source_word": "...", "target_word": "..."}]
    word_map: list = field(default_factory=list)
    # Which engine produced this result.
    engine: str = ""
    # Latency in seconds.
    latency: float = 0.0
    # True if the full structured output was parsed; False if fallback used.
    structured: bool = False


class LLMProvider(abc.ABC):
    """Common interface for translation and chat providers."""

    @abc.abstractmethod
    def translate(
        self,
        text: str,
        source_lang: str = "auto",
        target_lang: str = "zh",
        timeout: float = 15.0,
        detailed: bool = False,
    ) -> TranslationResult:
        """Translate text. If detailed=True, returns structured output (slower).

        Quick mode (detailed=False) is optimized for the floating window:
        minimal latency, plain translation only.
        Detailed mode includes terms, sentence pairs, and word alignment.
        Must be thread-safe."""
        ...

    @abc.abstractmethod
    def test_connection(self) -> bool:
        """Quick health check. Returns True if the provider is reachable."""
        ...

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Human-readable provider name for UI display."""
        ...
