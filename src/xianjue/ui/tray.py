"""System tray icon with right-click menu."""

from __future__ import annotations

from typing import Callable, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter, QIcon, QPixmap, QPen
from PySide6.QtWidgets import QSystemTrayIcon, QMenu


def _make_icon(active: bool = True) -> QIcon:
    """Generate a simple tray icon (colored circle with 'X')."""
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    color = QColor(70, 130, 220) if active else QColor(120, 120, 130)
    painter.setPen(QPen(color, 3))
    painter.setBrush(color)
    painter.drawEllipse(4, 4, 24, 24)

    painter.setPen(QPen(QColor(255, 255, 255), 2))
    font = painter.font()
    font.setPixelSize(14)
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "X")
    painter.end()

    return QIcon(pixmap)


class TrayIcon(QSystemTrayIcon):
    """System tray icon with menu."""

    toggle_floating = Signal()
    open_main = Signal()
    toggle_pause = Signal(bool)
    quit_app = Signal()

    def __init__(self, config_get: Callable, parent: Optional[object] = None) -> None:
        super().__init__(_make_icon(), parent)
        self._config_get = config_get
        self._paused = False
        self._build_menu()
        self.activated.connect(self._on_activated)

    def _build_menu(self) -> None:
        menu = QMenu()
        from .i18n import tr
        lang = self._config_get("ui.language", "zh")
        self._toggle_floating_action = menu.addAction(tr("Show Floating Window", lang))
        self._toggle_floating_action.setCheckable(True)
        self._toggle_floating_action.triggered.connect(self.toggle_floating.emit)
        menu.addSeparator()
        self._pause_action = menu.addAction(tr("Pause Active Translation", lang))
        self._pause_action.setCheckable(True)
        self._pause_action.toggled.connect(self._on_pause_toggled)
        menu.addSeparator()
        self._open_main_action = menu.addAction(tr("Open Main Window", lang))
        self._open_main_action.triggered.connect(self.open_main.emit)
        self._auto_start_action = menu.addAction(tr("Auto Start", lang))
        self._auto_start_action.setCheckable(True)
        self._auto_start_action.setChecked(self._config_get("startup.auto_start", False))
        menu.addSeparator()
        self._quit_action = menu.addAction(tr("Quit", lang))
        self._quit_action.triggered.connect(self.quit_app.emit)
        self.setContextMenu(menu)

    def _on_activated(self, reason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.open_main.emit()

    def _on_pause_toggled(self, checked: bool) -> None:
        self._paused = checked
        self.toggle_pause.emit(checked)
        self._update_icon()

    def _update_icon(self) -> None:
        self.setIcon(_make_icon(active=not self._paused))
        self.setToolTip("XianJue (active)" if not self._paused else "XianJue (paused)")

    def set_paused(self, paused: bool) -> None:
        """External update (e.g. from focus mode or hotkey)."""
        self._paused = paused
        self._pause_action.setChecked(paused)
        self._update_icon()
