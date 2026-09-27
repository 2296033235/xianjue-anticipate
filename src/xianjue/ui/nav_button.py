"""Reusable icon based navigation button."""

from __future__ import annotations

from PySide6.QtCore import QByteArray, QEasingCurve, QPropertyAnimation, QRectF, QSize, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QToolButton


def make_icon(svg: str, color: str, size: int = 28) -> QIcon:
    """Render a stroke-based SVG icon as a pixmap-backed QIcon."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    renderer = QSvgRenderer(QByteArray(svg.replace("__COLOR__", color).encode("utf-8")))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer.render(painter, QRectF(0, 0, size, size))
    painter.end()
    return QIcon(pixmap)


class NavButton(QToolButton):
    """Vertical icon + text navigation button with hover scale and click feedback."""

    def __init__(self, key: str, label: str, svg: str) -> None:
        super().__init__()
        self._key = key
        self._svg = svg
        self._hovered = False
        self._pressed = False
        self._base_color = "#A0A0B0"
        self._active_color = "#70B0FF"

        self.setObjectName("navBtn")
        self.setText(label)
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.setIconSize(QSize(20, 20))
        self.setCheckable(True)
        self.setAutoExclusive(True)
        self.toggled.connect(lambda _: self._update_icon())
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(80, 64)

        self._animation = QPropertyAnimation(self, b"iconSize", self)
        self._animation.setDuration(120)
        self._animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self._update_icon()

    def _animate_icon_size(self, size: int) -> None:
        self._animation.stop()
        self._animation.setStartValue(self.iconSize())
        self._animation.setEndValue(QSize(size, size))
        self._animation.start()

    def _icon_color(self) -> str:
        if self._pressed or self.isChecked():
            return self._active_color
        if self._hovered:
            return self._active_color
        return self._base_color

    def _update_icon(self) -> None:
        size = max(1, self.iconSize().width())
        self.setIcon(make_icon(self._svg, self._icon_color(), size))

    def enterEvent(self, event) -> None:
        self._hovered = True
        self._update_icon()
        self._animate_icon_size(22)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._hovered = False
        self._update_icon()
        self._animate_icon_size(20)
        super().leaveEvent(event)

    def mousePressEvent(self, event) -> None:
        self._pressed = True
        self._update_icon()
        self._animate_icon_size(17)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        self._pressed = False
        self._update_icon()
        self._animate_icon_size(21 if self._hovered else 20)
        super().mouseReleaseEvent(event)


NAV_ICONS = {
    "home": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><g fill="none" stroke-linecap="round" stroke-linejoin="round"><path stroke="__COLOR__" stroke-width="1.6" d="M3 10.5V21h6v-6h6v6h6V10.5L12 3z"/><path stroke="__COLOR__" stroke-width="1.6" d="M9 21v-6h6v6"/></g></svg>',
    "translate": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><g fill="none" stroke-linecap="round" stroke-linejoin="round"><path stroke="__COLOR__" stroke-width="1.6" d="M2 5h12"/><path stroke="__COLOR__" stroke-width="1.6" d="M7 2h1"/><path stroke="__COLOR__" stroke-width="1.6" d="M5 8l6 6"/><path stroke="__COLOR__" stroke-width="1.6" d="M4 14l6-6 2-3"/><path stroke="__COLOR__" stroke-width="1.6" d="M22 22l-5-10-5 10"/><path stroke="__COLOR__" stroke-width="1.6" d="M14 18h6"/></g></svg>',
    "vocab": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><g fill="none" stroke-linecap="round" stroke-linejoin="round"><path stroke="__COLOR__" stroke-width="1.6" d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path stroke="__COLOR__" stroke-width="1.6" d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></g></svg>',
    "history": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><g fill="none" stroke-linecap="round" stroke-linejoin="round"><circle stroke="__COLOR__" stroke-width="1.6" cx="12" cy="12" r="9"/><path stroke="__COLOR__" stroke-width="1.6" d="M12 7v5l4 2"/></g></svg>',
    "settings": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><g fill="none" stroke-linecap="round" stroke-linejoin="round"><circle stroke="__COLOR__" stroke-width="1.6" cx="12" cy="12" r="3"/><path stroke="__COLOR__" stroke-width="1.6" d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09a1.65 1.65 0 0 0-1-1.51 1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.6 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.6 1.65 1.65 0 0 0 10 3.09V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9c.18.42.53.76.95.94H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></g></svg>',
}
