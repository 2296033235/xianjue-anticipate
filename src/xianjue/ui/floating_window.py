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
    QTextBrowser, QSizePolicy, QApplication,
)
from PySide6.QtWidgets import QMenu

from ..providers.base import TranslationResult
from .i18n import tr as _tr_fn
from ..providers.prompts import TRANSLATION_QUICK_PROMPT


# --- styling ------------------------------------------------------------------

_STYLE = """
QWidget#floatingWindow {
    background-color: rgba(18, 21, 25, 245);
    border-radius: 16px;
}
QLabel#titleBar {
    color: #A9B6C3;
    font-size: 11px;
    padding: 4px 14px 0px 14px;
}
QTextBrowser#translationArea {
    background: transparent;
    color: #E6EDF3;
    background-color: rgba(255, 255, 255, 0.05);
    border-radius: 12px;
    padding: 10px 12px;
    border: none;
    font-size: 15px;
    selection-background-color: rgba(47, 214, 162, 0.35);
}
QLabel#detailSection {
    color: #A5B2C0;
    font-size: 12px;
    padding: 6px 14px;
}
QPushButton#controlBtn {
    background: rgba(255, 255, 255, 0.07);
    color: #A9B6C3;
    border: none;
    font-size: 12px;
    padding: 4px 10px;
    border-radius: 999px;
}
QPushButton#controlBtn:hover {
    background: rgba(255, 255, 255, 0.14);
    color: #E6EDF3;
}
QLabel#engineLabel {
    color: #7C8794;
    font-size: 10px;
    padding: 4px 14px 10px 14px;
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
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
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

        # Typewriter animation.
        self._type_timer = QTimer(self)
        self._type_timer.setSingleShot(False)
        self._type_timer.timeout.connect(self._type_tick)
        self._type_full_text = ""
        self._type_pos = 0
        self._typing = False

        # Current display state.
        self._pinned = config_get("floating_window.pinned", False)
        self._density = config_get("floating_window.density", "compact")
        self._current_result: Optional[TranslationResult] = None
        self._current_source = ""

        self._build_ui()
        self._load_position()

    # --- UI construction ------------------------------------------------------

    def _build_ui(self) -> None:
        self._lang = self._config_get("ui.language", "zh")
        self.setFixedWidth(360)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 12)
        layout.setSpacing(6)

        # Top bar: density | close
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(2, 0, 2, 0)
        top_bar.setSpacing(8)

        self._density_btn = QPushButton(self._tr("Detail") if self._density == "compact" else self._tr("Simple"))
        self._density_btn.setObjectName("controlBtn")
        self._density_btn.setToolTip(self._tr("Switch display density"))
        self._density_btn.clicked.connect(self._toggle_density)
        top_bar.addWidget(self._density_btn)

        top_bar.addStretch()

        self._close_btn = QPushButton(self._tr("Close"))
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
        self._text_area.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._text_area.customContextMenuRequested.connect(self._show_text_context_menu)
        layout.addWidget(self._text_area)

        self._terms_label = QLabel()
        self._terms_label.setObjectName("detailSection")
        self._terms_label.setWordWrap(True)
        layout.addWidget(self._terms_label)

        self._pairs_label = QLabel()
        self._pairs_label.setObjectName("detailSection")
        self._pairs_label.setWordWrap(True)
        self._pairs_label.setVisible(False)
        layout.addWidget(self._pairs_label)

        # Original text section (toggleable).
        self._original_label = QLabel()
        self._original_label.setObjectName("detailSection")
        self._original_label.setWordWrap(True)
        self._original_label.setVisible(False)
        layout.addWidget(self._original_label)

        # Engine indicator (privacy transparency).
        self._engine_label = QLabel()
        self._engine_label.setObjectName("engineLabel")
        layout.addWidget(self._engine_label)

    # --- display logic --------------------------------------------------------

    def show_translation(self, result: TranslationResult, source_text: str) -> None:
        """Show a translation result. Called by the pipeline."""
        self._current_result = result
        self._current_source = source_text

        # Start typewriter animation for the translation.
        self._start_typewriter(result.translation)

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

        # Show/hide original text section per setting.
        show_orig = self._config_get("floating_window.show_original_section", False)
        self._original_label.setVisible(show_orig)
        if show_orig:
            self._original_label.setText(f"<span style='color:#8090B0'>{source_text}</span>")

        # Show without stealing focus.
        self.show()
        self.raise_()

        # Auto-hide countdown starts after typing animation completes.

    def _start_typewriter(self, text: str) -> None:
        """Begin progressive text reveal."""
        self._type_full_text = text
        self._type_pos = 0
        self._typing = True
        self._text_area.setPlainText("")
        self._type_timer.start(30)

    def _type_tick(self) -> None:
        """Reveal 2-3 characters per tick."""
        if not self._typing:
            return
        self._type_pos = min(self._type_pos + 1, len(self._type_full_text))
        self._text_area.setPlainText(self._type_full_text[: self._type_pos])
        if self._type_pos >= len(self._type_full_text):
            self._typing = False
            self._type_timer.stop()
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

    # --- vocabulary marking -----------------------------------------------------

    def _show_text_context_menu(self, pos) -> None:
        """Show the standard text menu plus a vocabulary marking action."""
        selected = self._text_area.textCursor().selectedText().strip()
        if not selected:
            return
        menu = self._text_area.createStandardContextMenu()
        menu.addSeparator()
        mark_action = menu.addAction(self._tr("Mark as Vocabulary"))
        mark_action.triggered.connect(
            lambda: self.word_marked.emit(selected, self._current_source)
        )
        menu.exec(self._text_area.mapToGlobal(pos))

    # --- auto-hide countdown ----------------------------------------------------

    def _tr(self, text: str) -> str:
        """Translate a UI label using the configured language."""
        return _tr_fn(text, self._lang)

    def _start_countdown(self) -> None:
        if self._pinned:
            self._auto_hide_timer.stop()
            return
        if not self._config_get("floating_window.auto_hide", True):
            return
        if self._typing:
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

    def _toggle_density(self) -> None:
        self._density = "detailed" if self._density == "compact" else "compact"
        self._config_set("floating_window.density", self._density)
        show_detail = (self._density == "detailed")
        self._terms_label.setVisible(show_detail)
        self._density_btn.setText(self._tr("Simple") if show_detail else self._tr("Detail"))
        # Force recalc.
        self.adjustSize()

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
        path.addRoundedRect(QRectF(self.rect()), 16, 16)
        painter.fillPath(path, QColor(18, 21, 25, 245))
        super().paintEvent(event)
