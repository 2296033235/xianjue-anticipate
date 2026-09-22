"""Main application orchestrator: config, pipeline, floating window, tray."""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from .core.config import Config
from .core.pipeline import TranslationPipeline
from .models.database import Database
from .providers.factory import create_provider
from .ui.floating_window import FloatingWindow
from .ui.tray import TrayIcon
from .ui.main_window import MainWindow


class _MainThreadCaller(QObject):
    """Thread-safe bridge: emits a callable to be executed on the main thread."""

    execute = __import__("PySide6").QtCore.Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self.execute.connect(self._run)

    def call(self, fn) -> None:
        self.execute.emit(fn)

    @staticmethod
    def _run(fn) -> None:
        fn()


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
        self.db = Database()
        self._caller = _MainThreadCaller()

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

        # Main window.
        self.main_window = MainWindow(
            config=self.config_get,
            config_set=self.config_set,
            on_translate_manual=self._on_manual_translate,
            db=self.db,
        )

        # Tray.
        self.tray = TrayIcon(config_get=self.config_get)
        self.tray.toggle_floating.connect(self._toggle_floating)
        self.tray.toggle_pause.connect(self._set_paused)
        self.tray.open_main.connect(self._show_main)
        self.tray.quit_app.connect(self._quit)
        self.tray.setVisible(True)

        # Start the clipboard monitor.
        self.pipeline.start()

    def _on_translation_result(self, result, source_text: str) -> None:
        """Called from the pipeline thread; must be on the main thread."""
        self._caller.call(lambda: self._show_translation_result(result, source_text))

    def _show_translation_result(self, result, source_text: str) -> None:
        """Runs on the main thread."""
        self.floating_window.show_translation(result, source_text)
        self.db.add_history(source_text, result.translation, "auto", "auto", result.engine)
        print(f"[app] shown in floating window ({len(result.translation)} chars)")

    def _on_manual_translate(self, text: str, source_lang: str, target_lang: str) -> None:
        """Manual translation from the main window."""
        import threading
        from .core.text_repair import repair

        def worker():
            try:
                repaired = repair(text)
                result = self.provider.translate(repaired, source_lang, target_lang, detailed=True)
                self.db.add_history(repaired, result.translation, source_lang, target_lang, result.engine)
                self._caller.call(lambda: self.main_window.show_manual_result(result, repaired))
            except Exception as e:
                error_str = str(e)
                self._caller.call(lambda: self.main_window.show_manual_error(error_str))

        threading.Thread(target=worker, daemon=True).start()

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

    def _show_main(self) -> None:
        self.main_window.show()
        self.main_window.raise_()
        self.main_window.refresh_all()

    def _quit(self) -> None:
        self.pipeline.stop()
        self.db.close()
        self.qt_app.quit()

    def run(self) -> int:
        return self.qt_app.exec()


def create_app() -> XianJueApp:
    import sys
    return XianJueApp(sys.argv)
