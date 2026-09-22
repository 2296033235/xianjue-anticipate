"""Translation pipeline orchestrator: repair -> filter -> detect -> translate."""

from __future__ import annotations

import threading
from typing import Callable, Optional

from .clipboard_monitor import ClipboardMonitor
from .intent_filter import should_skip
from .language import detect_language
from .text_repair import repair
from ..providers.base import LLMProvider, TranslationResult


class TranslationPipeline:
    """Coordinates the full flow from clipboard copy to translation result."""

    def __init__(
        self,
        config_get: Callable,
        provider: LLMProvider,
        on_result: Callable[[TranslationResult, str], None],
        on_skip: Optional[Callable[[str, str], None]] = None,
    ) -> None:
        """
        Args:
            config_get: dot-path config accessor.
            provider: LLM provider instance.
            on_result: callback(result, repaired_source) on success.
            on_skip: optional callback(raw_text, reason) when filtered out.
        """
        self._config_get = config_get
        self._provider = provider
        self._on_result = on_result
        self._on_skip = on_skip

        self._monitor = ClipboardMonitor(
            config_get=config_get,
            on_text=self._handle_text,
        )
        self._last_translation_cache: dict[str, TranslationResult] = {}
        self._cache_max = 20
        # Track the in-flight request thread so we can abandon stale ones.
        self._request_generation = 0
        self._lock = threading.Lock()

    @property
    def monitor(self) -> ClipboardMonitor:
        return self._monitor

    def start(self) -> None:
        self._monitor.start()

    def stop(self) -> None:
        self._monitor.stop()

    @property
    def paused(self) -> bool:
        return self._monitor.paused

    @paused.setter
    def paused(self, value: bool) -> None:
        self._monitor.paused = value

    def translate_manual(
        self,
        text: str,
        source_lang: str = "auto",
        target_lang: str = "zh",
        callback: Optional[Callable[[TranslationResult, str], None]] = None,
    ) -> None:
        """Manual translation (bypasses clipboard monitor and trigger length)."""
        def worker():
            repaired = repair(text)
            result = self._provider.translate(repaired, source_lang, target_lang, detailed=True)
            cb = callback or self._on_result
            cb(result, repaired)
        threading.Thread(target=worker, daemon=True).start()

    def _handle_text(self, raw: str, repaired: str) -> None:
        """Called by clipboard monitor when a valid text is detected."""
        print(f"[pipeline] _handle_text called, len={len(repaired)}", flush=True)
        # Increment generation to cancel any in-flight translation.
        with self._lock:
            self._request_generation += 1
            current_gen = self._request_generation

        # Deduplicate: if we already translated this exact text recently, reuse.
        cache_key = repaired
        if cache_key in self._last_translation_cache:
            cached = self._last_translation_cache[cache_key]
            self._on_result(cached, repaired)
            return

        # Detect source language.
        target_lang = self._config_get("language.target", "zh")
        source_lang = self._config_get("language.source", "auto")
        if source_lang == "auto":
            source_lang = detect_language(repaired)

        # Skip if source == target (no point translating to itself).
        if source_lang == target_lang:
            if self._on_skip:
                self._on_skip(raw, f"source==target ({source_lang})")
            print(f"[pipeline] SKIPPED: source==target ({source_lang})", flush=True)
            return

        if source_lang == "unknown":
            if self._on_skip:
                self._on_skip(raw, "unknown language")
            print("[pipeline] SKIPPED: unknown language", flush=True)
            return

        # Run translation in a background thread.
        def _do_translate():
            print(f"[pipeline] translating ({source_lang} -> {target_lang}): {repaired[:80]}...", flush=True)
            try:
                # Quick mode for the floating window (fast, plain translation).
                result = self._provider.translate(repaired, source_lang, target_lang, detailed=False)
                # Only deliver if no newer request has been made.
                with self._lock:
                    is_current = (current_gen == self._request_generation)
                if is_current:
                    # Cache.
                    self._last_translation_cache[cache_key] = result
                    if len(self._last_translation_cache) > self._cache_max:
                        # Evict oldest (dict preserves insertion order).
                        first_key = next(iter(self._last_translation_cache))
                        del self._last_translation_cache[first_key]
                    print(f"[pipeline] done: {len(result.translation)} chars, {result.latency:.2f}s", flush=True)
                    self._on_result(result, repaired)
            except Exception as e:
                error_msg = f"Translation error: {e}"
                print(f"[pipeline] error: {error_msg}", flush=True)
                error_result = TranslationResult(translation=error_msg, engine="error", latency=0)
                with self._lock:
                    is_current = (current_gen == self._request_generation)
                if is_current:
                    self._on_result(error_result, repaired)

        threading.Thread(target=_do_translate, daemon=True).start()
