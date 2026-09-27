"""A compact switch control with predictable rounded rendering."""

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QSlider


class ToggleSwitch(QSlider):
    """Draw a rounded switch instead of relying on QSS slider geometry."""

    def __init__(self, parent=None) -> None:
        super().__init__(Qt.Orientation.Horizontal, parent)
        self.setRange(0, 1)
        self.setPageStep(1)
        self.setFixedSize(44, 24)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setTracking(False)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        track_color = QColor("#00B96B") if self.value() == 1 else QColor("#C9CDD6")
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(track_color)
        painter.drawRoundedRect(QRectF(0, 0, self.width(), self.height()), 12, 12)

        knob_size = 18
        x = 3 if self.value() == 0 else self.width() - knob_size - 3
        y = (self.height() - knob_size) / 2
        painter.setBrush(QColor("#FFFFFF"))
        painter.drawEllipse(QRectF(x, y, knob_size, knob_size))
