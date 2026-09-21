"""Background clipboard monitor with self-write suppression and debounce."""

from __future__ import annotations

import threading
import time
from typing import Callable, Optional

import pyperclip

from .intent_filter import should_skip
from .text_repair import repair


class ClipboardMonitor:
    """Polls the system clipboard and emits filtered, repaired text.

    Features:
      - self-write suppression: writes made by this app are ignored
      - debounce: rapid successive copies only fire the last one
      - intent filtering via `should_skip`
      - text repair via `repair` before emission
    """

    def __init__(
        self,
        config_get: Callable,
        on_text: Callable[[str, str], None],
        poll_interval: float = 0.3,
        debounce_seconds: float = 0.8,
    ) -> None:
        """
        Args:
            config_get: callable that returns config values (e.g. trigger_length).
            on_text: callback(raw_text, repaired_text) for valid text.
            poll_interval: seconds between clipboard checks.
            debounce_seconds: minimum gap between emissions.
        """
        self._config_get = config_get
        self._on_text = on_text
        self._poll_interval = poll_interval
        self._debounce_seconds = debounce_seconds

        self._running = False
        self._paused = False
        self._last_clipboard = ""
        self._last_emit_time = 0.0
        # Set to True briefly when we ourselves write to the clipboard,
        # so the next poll cycle ignores that write.
        self._suppress_next = False
        self._suppress_until = 0.0

        self._thread: Optional[threading.Thread] = None

    @property
    def running(self) -> bool:
        return self._running

    @property
    def paused(self) -> bool:
        return self._paused

    @paused.setter
    def paused(self, value: bool) -> None:
        self._paused = value

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        # Prime the baseline so we don't fire on the current clipboard content.
        try:
            self._last_clipboard = pyperclip.paste()
        except Exception:
            self._last_clipboard = ""
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

    def suppress_next_write(self) -> None:
        """Call before the app itself writes to the clipboard to prevent a loop."""
        self._suppress_next = True
        self._suppress_until = time.time() + 1.0

    def _poll_loop(self) -> None:
        while self._running:
            try:
                current = pyperclip.paste()
            except Exception:
                print(f"[clipboard] paste error")
                time.sleep(self._poll_interval)
                continue

            if current == self._last_clipboard:
                time.sleep(self._poll_interval)
                continue

            self._last_clipboard = current

            if self._paused:
                time.sleep(self._poll_interval)
                continue

            # Suppress writes we just made ourselves.
            if self._suppress_next and time.time() < self._suppress_until:
                self._suppress_next = False
                time.sleep(self._poll_interval)
                continue
            self._suppress_next = False

            if not current or not current.strip():
                print("[clipboard] empty, skipping")
                time.sleep(self._poll_interval)
                continue

            # Debounce: require a minimum gap since last emission.
            now = time.time()
            if now - self._last_emit_time < self._debounce_seconds:
                time.sleep(self._poll_interval)
                continue

            raw = current

            # Check trigger length (user-configurable).
            trigger_length = self._config_get("trigger_length", 30)
            if len(raw.strip()) < trigger_length:
                print(f"[clipboard] too short ({len(raw.strip())} < {trigger_length})")
                time.sleep(self._poll_interval)
                continue

            # Cap at 500 chars for MVP (long text -> manual mode).
            if len(raw.strip()) > 500:
                print(f"[clipboard] too long, truncating to 500")
                raw = raw.strip()[:500]

            if should_skip(raw):
                print(f"[clipboard] intent filter rejected: {raw.strip()[:40]}")
                time.sleep(self._poll_interval)
                continue

            repaired = repair(raw)
            if not repaired:
                print("[clipboard] repair returned empty")
                time.sleep(self._poll_interval)
                continue

            self._last_emit_time = time.time()
            self._on_text(raw, repaired)

            time.sleep(self._poll_interval)
