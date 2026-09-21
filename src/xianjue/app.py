"""Main application orchestrator: config, pipeline, floating window, tray."""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QWidget, QVBoxLayout

from .core.config import Config
from .core.pipeline import TranslationPipeline
from .providers.factory import create_provider
from .ui.floating_window import FloatingWindow
from .ui.tray import TrayIcon


class XianJueApp:
    """Top-level application: owns config, pipeline, and all UI components."""

    def __init__(self, argv: list[str]) -> None:
        self.qt_app = QApplication(argv)
        self.qt_app.setApplicationName("XianJue")
        self.qt_app.setApplicationDisplayName("XianJue")
        self.qt_app.setQuitOnLastWindowClosed(False)

        self.config = Config()
        self.config_get = self.config.get
        self.config_set = self.config.set

        self._build_components()

    def _build_components(self) -> None:
        # Floating window.
        self.floating_window = FloatingWindow(
            config_get=self.config_get,
            config_set=self.config_set,
        )

        # Translation pipeline.
        self.provider = create_provider(self.config_get)
        self.pipeline = TranslationPipeline(
            config_get=self.config_get,
            provider=self.provider,
            on_result=self._on_translation_result,
        )

        # Tray.
        self.tray = TrayIcon(config_get=self.config_get)
        self.tray.toggle_floating.connect(self._toggle_floating)
        self.tray.toggle_pause.connect(self._set_paused)
        self.tray.quit_app.connect(self._quit)
        self.tray.setVisible(True)

        # Start the clipboard monitor.
        self.pipeline.start()

    def _on_translation_result(self, result, source_text: str) -> None:
        """Called from the pipeline thread; must be on the main thread."""
        QTimer.singleShot(0, lambda: self.floating_window.show_translation(result, source_text))

    def _toggle_floating(self) -> None:
        if self.floating_window.isVisible():
            self.floating_window.hide()
        elif self.floating_window._current_result:
            self.floating_window.show_translation(
                self.floating_window._current_result,
                self.floating_window._current_source,
            )

    def _set_paused(self, paused: bool) -> None:
        self.pipeline.paused = paused
        self.tray.set_paused(paused)

    def _quit(self) -> None:
        self.pipeline.stop()
        self.qt_app.quit()

    def run(self) -> int:
        return self.qt_app.exec()


def create_app() -> XianJueApp:
    import sys
    return XianJueApp(sys.argv)

