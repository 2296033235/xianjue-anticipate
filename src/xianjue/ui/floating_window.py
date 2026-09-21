"""Frameless floating translation window (Snipaste-style).

Design decisions:
  - Qt.Tool + WindowStaysOnTopHint + FramelessWindowHint: no taskbar,
    no focus steal on show, always on top.
  - WA_TranslucentBackground for rounded corners via stylesheet.
  - Auto-hide timer (configurable, default 8s), paused on hover.
  - Pin mode: skip auto-hide entirely.
  - Drag anywhere to reposition; position persisted.
  - Compact (translation only) vs Detailed (translation + terms + pairs).
"""

from __future__ import annotations

from typing import Callable, Optional

from PySide6.QtCore import Qt, QTimer, QPoint, Signal, QRectF
from PySide6.QtGui import QColor, QPainter, QPainterPath, QBrush, QPen, QCursor, QIcon, QPixmap
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextBrowser, QSizePolicy, QApplication, QComboBox,
)

from ..providers.base import TranslationResult
from ..providers.prompts import TRANSLATION_QUICK_PROMPT


# --- styling ------------------------------------------------------------------

_STYLE = """
QWidget#floatingWindow {
    background-color: rgba(30, 30, 35, 235);
    border-radius: 12px;
}
QLabel#titleBar {
    color: rgba(200, 200, 210, 180);
    font-size: 11px;
    padding: 4px 8px 0px 12px;
}
QTextBrowser#translationArea {
    background: transparent;
    color: #E8E8EA;
    border: none;
    font-size: 14px;
    selection-background-color: rgba(80, 120, 200, 120);
}
QLabel#detailSection {
    color: #B8B8C0;
    font-size: 12px;
    padding: 4px 12px;
}
QPushButton#controlBtn {
    background: transparent;
    color: rgba(180, 180, 190, 160);
    border: none;
    font-size: 14px;
    padding: 2px 6px;
    border-radius: 4px;
}
QPushButton#controlBtn:hover {
    background: rgba(255, 255, 255, 30);
    color: #FFFFFF;
}
QPushButton#pinBtnActive {
    background: rgba(80, 130, 220, 80);
    color: #70B0FF;
}
QLabel#engineLabel {
    color: rgba(140, 160, 200, 100);
    font-size: 9px;
    padding: 0px 12px 4px 12px;
}
"""


class FloatingWindow(QWidget):
    """The always-on-top translation popup."""

    word_marked = Signal(str, str)
    text_selected = Signal(str)
    open_main_requested = Signal()
    position_changed = Signal(int, int)

    def __init__(
        self,
        config_get: Callable,
        config_set: Callable,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._config_get = config_get
        self._config_set = config_set

        self.setWindowFlags(
            Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setObjectName("floatingWindow")
        self.setStyleSheet(_STYLE)

        # Drag state.
        self._drag_start_pos = None
        self._drag_start_window_pos = None
        self._is_dragging = False

        # Auto-hide timer.
        self._auto_hide_timer = QTimer(self)
        self._auto_hide_timer.setSingleShot(False)
        self._auto_hide_timer.timeout.connect(self._tick_countdown)
        self._countdown_remaining = 0

        # Current display state.
        self._pinned = config_get("floating_window.pinned", False)
        self._density = config_get("floating_window.density", "compact")
        self._current_result: Optional[TranslationResult] = None
        self._current_source = ""

        self._build_ui()
        self._load_position()

    # --- UI construction ------------------------------------------------------

    def _build_ui(self) -> None:
        self.setFixedWidth(380)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(0)

        # Top bar: pin | density | close
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(8, 2, 8, 2)

        self._pin_btn = QPushButton("pin")
        self._pin_btn.setObjectName("controlBtn")
        if self._pinned:
            self._pin_btn.setObjectName("pinBtnActive")
            self._pin_btn.setText("pinned")
        self._pin_btn.setToolTip("Pin: keep window visible")
        self._pin_btn.clicked.connect(self._toggle_pin)
        top_bar.addWidget(self._pin_btn)

        # Language switcher (source -> target).
        self._lang_combo = QComboBox()
        self._lang_combo.addItems(["EN -> ZH", "ZH -> EN"])
        self._lang_combo.setFixedHeight(22)
        self._lang_combo.setStyleSheet(
            "QComboBox { background: rgba(255,255,255,20); color: rgba(200,200,210,180);"
            " border: none; border-radius: 3px; font-size: 11px; padding: 0px 4px; }"
            "QComboBox QAbstractItemView { background: #2A2A30; color: #D0D0D8;"
            " selection-background-color: rgba(70,130,220,80); }"
        )
        # Restore last selection.
        saved_lang = self._config_get("language.pair", "en_zh")
        if saved_lang == "zh_en":
            self._lang_combo.setCurrentIndex(1)
        self._lang_combo.currentIndexChanged.connect(self._on_lang_changed)
        top_bar.addWidget(self._lang_combo)

        self._density_btn = QPushButton("detail" if self._density == "compact" else "simple")
        self._density_btn.setObjectName("controlBtn")
        self._density_btn.setToolTip("Switch display density")
        self._density_btn.clicked.connect(self._toggle_density)
        top_bar.addWidget(self._density_btn)

        top_bar.addStretch()

        self._close_btn = QPushButton("close")
        self._close_btn.setObjectName("controlBtn")
        self._close_btn.clicked.connect(self.hide)
        top_bar.addWidget(self._close_btn)

        self._top_bar_widget = QWidget()
        self._top_bar_widget.setLayout(top_bar)
        layout.addWidget(self._top_bar_widget)

        # Translation area (QTextBrowser for selection + rich text support).
        self._text_area = QTextBrowser()
        self._text_area.setObjectName("translationArea")
        self._text_area.setOpenLinks(False)
        self._text_area.setOpenExternalLinks(False)
        self._text_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self._text_area.setReadOnly(True)
        self._text_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        layout.addWidget(self._text_area)

        # Detailed sections (hidden in compact mode).
        self._detail_widget = QWidget()
        detail_layout = QVBoxLayout(self._detail_widget)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        detail_layout.setSpacing(2)

        self._terms_label = QLabel()
        self._terms_label.setObjectName("detailSection")
        self._terms_label.setWordWrap(True)
        detail_layout.addWidget(self._terms_label)

        self._pairs_label = QLabel()
        self._pairs_label.setObjectName("detailSection")
        self._pairs_label.setWordWrap(True)
        detail_layout.addWidget(self._pairs_label)

        self._detail_widget.setVisible(False)
        layout.addWidget(self._detail_widget)

        # Engine indicator (privacy transparency).
        self._engine_label = QLabel()
        self._engine_label.setObjectName("engineLabel")
        layout.addWidget(self._engine_label)

    # --- display logic --------------------------------------------------------

    def show_translation(self, result: TranslationResult, source_text: str) -> None:
        """Show a translation result. Called by the pipeline."""
        self._current_result = result
        self._current_source = source_text

        # Update translation text.
        display_text = result.translation
        self._text_area.setPlainText(display_text)

        # Update detail sections (visible only in detailed mode).
        terms_html = ""
        if result.terms:
            items = []
            for t in result.terms[:5]:
                items.append(f"<b>{t.get('original', '')}</b>: {t.get('translation', '')} <i>{t.get('explanation', '')}</i>")
            terms_html = "<br>".join(items)
        self._terms_label.setText(terms_html)

        pairs_html = ""
        if result.sentence_pairs:
            items = []
            for p in result.sentence_pairs:
                items.append(f"<span style='color:#8090B0'>{p.get('source', '')}</span><br>{p.get('target', '')}")
            pairs_html = "<hr style='border:1px solid rgba(80,80,100,60)'>".join(items)
        self._pairs_label.setText(pairs_html)

        # Engine indicator.
        self._engine_label.setText(result.engine)

        # Position near the cursor.
        self._position_near_cursor()

        # Show without stealing focus.
        self.show()
        self.raise_()

        # Start auto-hide countdown (unless pinned).
        self._start_countdown()

    def _position_near_cursor(self) -> None:
        """Position the window near the mouse cursor, clamped to screen bounds."""
        cursor = QCursor.pos()
        screen = QApplication.screenAt(cursor)
        if screen is None:
            screen = QApplication.primaryScreen()
        geo = screen.availableGeometry()

        x = cursor.x() + 12
        y = cursor.y() + 16
        w = self.width()
        h = self.sizeHint().height()

        # Clamp.
        if x + w > geo.right():
            x = cursor.x() - w - 12
        if y + h > geo.bottom():
            y = cursor.y() - h - 16
        x = max(geo.left(), x)
        y = max(geo.top(), y)

        self.move(x, y)

    # --- auto-hide countdown ----------------------------------------------------

    def _start_countdown(self) -> None:
        if self._pinned:
            self._auto_hide_timer.stop()
            return
        seconds = self._config_get("floating_window.auto_hide_seconds", 8)
        self._countdown_remaining = seconds * 10  # 100ms ticks
        self._auto_hide_timer.start(100)

    def _tick_countdown(self) -> None:
        self._countdown_remaining -= 1
        if self._countdown_remaining <= 0:
            self._auto_hide_timer.stop()
            self.hide()

    def _pause_countdown(self) -> None:
        self._auto_hide_timer.stop()

    def _resume_countdown(self) -> None:
        if not self._pinned and self._countdown_remaining > 0 and self.isVisible():
            self._auto_hide_timer.start(100)

    # --- controls ----------------------------------------------------------------

    def _toggle_pin(self) -> None:
        self._pinned = not self._pinned
        self._config_set("floating_window.pinned", self._pinned)
        if self._pinned:
            self._pin_btn.setObjectName("pinBtnActive")
            self._pin_btn.setText("pinned")
            self._auto_hide_timer.stop()
        else:
            self._pin_btn.setObjectName("controlBtn")
            self._pin_btn.setText("pin")
            self._start_countdown()
        # Refresh stylesheet.
        self._pin_btn.style().unpolish(self._pin_btn)
        self._pin_btn.style().polish(self._pin_btn)

    def _toggle_density(self) -> None:
        self._density = "detailed" if self._density == "compact" else "compact"
        self._config_set("floating_window.density", self._density)
        show_detail = (self._density == "detailed")
        self._detail_widget.setVisible(show_detail)
        self._density_btn.setText("simple" if show_detail else "detail")
        # Force recalc.
        self.adjustSize()

    def _on_lang_changed(self, index: int) -> None:
        """Update target language in config so the pipeline routes correctly."""
        pair = "en_zh" if index == 0 else "zh_en"
        self._config_set("language.pair", pair)
        if index == 0:
            self._config_set("language.source", "auto")
            self._config_set("language.target", "zh")
        else:
            self._config_set("language.source", "auto")
            self._config_set("language.target", "en")

    # --- drag ----------------------------------------------------------------

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.globalPosition().toPoint()
            self._drag_start_window_pos = self.pos()
            self._is_dragging = True
            self._pause_countdown()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._is_dragging and self._drag_start_pos:
            delta = event.globalPosition().toPoint() - self._drag_start_pos
            new_pos = self._drag_start_window_pos + delta
            self.move(new_pos)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if self._is_dragging:
            self._is_dragging = False
            self._drag_start_pos = None
            self.position_changed.emit(self.x(), self.y())
            self._resume_countdown()
        super().mouseReleaseEvent(event)

    # --- hover pause ------------------------------------------------------------

    def enterEvent(self, event) -> None:
        self._pause_countdown()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._resume_countdown()
        super().leaveEvent(event)

    # --- position persistence ------------------------------------------------

    def _load_position(self) -> None:
        x = self._config_get("floating_window.last_x")
        y = self._config_get("floating_window.last_y")
        if x is not None and y is not None:
            self.move(x, y)

    # --- painting ------------------------------------------------------------

    def paintEvent(self, event) -> None:
        """Draw the rounded-rect background for translucent windows."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), 12, 12)
        painter.fillPath(path, QColor(30, 30, 35, 235))
        super().paintEvent(event)
