"""A compact switch control with predictable rounded rendering."""

from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QRectF, Qt, QVariantAnimation
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
        self._position = 0.0
        self._animation = QVariantAnimation(self)
        self._animation.setDuration(120)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._animation.valueChanged.connect(self._on_animation_value_changed)

    def _on_animation_value_changed(self, value) -> None:
        self._position = float(value)
        self.update()

    def _animate_to(self, target: float) -> None:
        self._animation.stop()
        self._animation.setStartValue(float(self.value()))
        self._animation.setEndValue(float(target))
        self._animation.start()

    def setValue(self, value: int) -> None:
        target = 1 if value else 0
        if self.isVisible() and target != self.value():
            self._animate_to(target)
        else:
            self._position = float(target)
        super().setValue(target)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.setValue(1 if self.value() == 0 else 0)
            event.accept()
            return
        super().mousePressEvent(event)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        track_color = (
            QColor("#00B96B")
            if self._position > 0.5
            else QColor("#C9CDD6")
        )
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(track_color)
        painter.drawRoundedRect(QRectF(0, 0, self.width(), self.height()), 12, 12)

        knob_size = 18
        left = 3
        right = self.width() - knob_size - 3
        x = left + (right - left) * self._position
        y = (self.height() - knob_size) / 2
        painter.setBrush(QColor("#FFFFFF"))
        painter.drawEllipse(QRectF(x, y, knob_size, knob_size))
