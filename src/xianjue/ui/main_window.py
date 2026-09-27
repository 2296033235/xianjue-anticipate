"""Main application window with left navigation and content pages."""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget,
    QPushButton, QLabel, QComboBox, QSlider, QLineEdit, QCheckBox, QFrame,
    QSpinBox, QGroupBox, QFormLayout, QScrollArea, QTableWidget,
    QTableWidgetItem, QTextEdit, QTabWidget, QHeaderView, QMessageBox,
    QToolButton,
)

from .i18n import tr as _tr
from .nav_button import NAV_ICONS, NavButton, make_icon
from .toggle_switch import ToggleSwitch


_STYLE = """
QMainWindow {
    background-color: #1E1E24;
}
QWidget#sidebar {
    background-color: #18181D;
    min-width: 96px;
    max-width: 96px;
}
QToolButton#navBtn {
    text-align: center;
    padding: 10px 12px;
    color: #A0A0B0;
    border: none;
    background: transparent;
    font-size: 12px;
    border-radius: 12px;
}
QToolButton#navBtn:hover {
    background-color: rgba(255, 255, 255, 0.06);
    color: #E6EDF3;
}
QToolButton#navBtn:pressed {
    background-color: rgba(255, 255, 255, 0.08);
}
QToolButton#navBtn:checked {
    background-color: rgba(70, 130, 220, 0.18);
    color: #70B0FF;
    font-weight: bold;
}
QFrame#secondaryNav {
    background-color: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
}
QPushButton#secondaryNavBtn {
    text-align: left;
    padding: 8px 10px;
    color: #A0A0B0;
    border: none;
    background-color: transparent;
    border-radius: 8px;
}
QPushButton#secondaryNavBtn:hover {
    background-color: rgba(255, 255, 255, 0.06);
    color: #E6EDF3;
}
QPushButton#secondaryNavBtn:checked {
    background-color: #4768B0;
    color: white;
    font-weight: bold;
}
QWidget#contentArea {
    background-color: #1E1E24;
}
QFrame#card {
    background-color: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
}
QLabel#cardTitle {
    color: #C0C0C8;
    font-size: 15px;
    font-weight: bold;
}
QLabel#statusChip {
    background-color: rgba(80, 170, 120, 0.25);
    color: #5FD59F;
    border-radius: 10px;
    padding: 4px 10px;
}
QFrame#modelConfigRow {
    background-color: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
}
QFrame#modelConfigRow[active="true"] {
    background-color: rgba(95, 213, 159, 0.10);
    border: 1px solid rgba(95, 213, 159, 0.60);
}
QFrame#modelAvatar {
    background-color: rgba(255, 255, 255, 0.08);
    border-radius: 10px;
}
QLabel#modelConfigTitle {
    color: #E6EDF3;
    font-size: 15px;
    font-weight: bold;
}
QLabel#modelConfigSubtitle {
    color: #8A8A98;
    font-size: 12px;
}
QPushButton#modelActionBtn {
    background-color: rgba(95, 213, 159, 0.18);
    color: #5FD59F;
    border: none;
    padding: 5px 12px;
    border-radius: 12px;
}
QPushButton#modelActionBtn:hover {
    background-color: rgba(95, 213, 159, 0.28);
}
QPushButton#modelDeleteBtn {
    background-color: transparent;
    color: #8A8A98;
    border: none;
    padding: 5px;
}
QPushButton#modelDeleteBtn:hover {
    color: #E6EDF3;
}
QLabel#pageTitle {
    color: #E0E0E5;
    font-size: 22px;
    font-weight: bold;
}
QLabel#sectionTitle {
    color: #C0C0C8;
    font-size: 15px;
    font-weight: bold;
}
QLabel#infoText {
    color: #909098;
    font-size: 13px;
}
QGroupBox {
    background-color: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    margin-top: 0;
    padding: 20px 16px 16px 16px;
    color: #B0B0B8;
}
QGroupBox::title {
    subcontrol-position: top left;
    left: 16px;
    top: 6px;
    padding: 0 4px;
}
QLineEdit, QComboBox, QTextEdit {
    background-color: rgba(255, 255, 255, 15);
    color: #E0E0E5;
    border: 1px solid rgba(80, 80, 100, 60);
    border-radius: 4px;
    padding: 6px 10px;
}
QCheckBox, QRadioButton {
    color: #C0C0C8;
}
QPushButton#primaryBtn {
    background-color: #4768B0;
    color: white;
    border: none;
    padding: 8px 20px;
    border-radius: 6px;
    font-size: 14px;
}
QPushButton#primaryBtn:hover {
    background-color: #5A7CC0;
}
QTableWidget {
    background-color: rgba(255, 255, 255, 5);
    color: #D0D0D5;
    border: 1px solid rgba(80, 80, 100, 60);
    border-radius: 4px;
}
QHeaderView::section {
    background-color: rgba(255, 255, 255, 10);
    color: #A0A0B0;
    padding: 4px;
    border: none;
}
"""


_NAV_ITEMS = [
    ("dashboard", "Dashboard", NAV_ICONS["home"]),
    ("translate", "Translate", NAV_ICONS["translate"]),
    ("review", "Review", NAV_ICONS["vocab"]),
    ("history", "History", NAV_ICONS["history"]),
    ("settings", "Settings", NAV_ICONS["settings"]),
]

_PAGE_KEYS = [
    "dashboard",
    "translate",
    "vocabulary",
    "review",
    "history",
    "settings",
]

_API_FORMAT_OPTIONS = [
    ("anthropic_messages", "Anthropic Messages (/v1/messages)"),
    ("chat_completions", "Chat Completions (/chat/completions)"),
    ("responses", "Responses (/responses)"),
]

_TRASH_ICON = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><g fill="none" stroke="__COLOR__" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M4 7h16"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M6 7l1 13h10l1-13"/><path d="M9 7V4h6v3"/></g></svg>'


class MainWindow(QMainWindow):
    """Primary application window."""

    model_status_ready = Signal(bool, str)
    ollama_models_ready = Signal(list, str)

    def __init__(
        self,
        config: Callable,
        config_set: Callable,
        on_translate_manual: Callable,
        db,
        refresh_provider: Callable,
    ) -> None:
        super().__init__()
        self.setWindowTitle("XianJue")
        self.setMinimumSize(900, 640)
        self.setStyleSheet(_STYLE)

        self._config_get = config
        self._config_set = config_set
        self._db = db
        self._on_translate_manual = on_translate_manual
        self._refresh_provider = refresh_provider
        self.model_status_ready.connect(self._set_model_status)
        self.ollama_models_ready.connect(self._refresh_ollama_models)

        # UI language: read once, labels are built in the chosen language.
        self._lang = config("ui.language", "zh")

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- sidebar ---
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(8, 16, 8, 16)
        sidebar_layout.setSpacing(6)

        # Logo/title.
        title = QLabel("XianJue")
        title.setStyleSheet("""
            QLabel {
                color: #E6EDF3;
                font-family: "Segoe Script", cursive;
                font-size: 14px;
                font-weight: bold;
                letter-spacing: 0;
                padding: 0 4px 12px 4px;
            }
        """)
        sidebar_layout.addWidget(title)
        sidebar_layout.addSpacing(8)

        self._nav_buttons = {}
        self._stack = QStackedWidget()
        self._current_page = "dashboard"

        for key, label, icon in _NAV_ITEMS:
            btn = NavButton(key, self._tr(label), icon)
            btn.setObjectName("navBtn")
            btn.clicked.connect(lambda checked, k=key: self._navigate(k))
            sidebar_layout.addWidget(btn)
            self._nav_buttons[key] = btn

        sidebar_layout.addStretch()
        main_layout.addWidget(sidebar)

        # --- content stack ---
        content = QWidget()
        content.setObjectName("contentArea")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self._stack.addWidget(self._build_dashboard_page())
        self._stack.addWidget(self._build_translate_page())
        self._stack.addWidget(self._build_vocabulary_page())
        self._stack.addWidget(self._build_review_page())
        self._stack.addWidget(self._build_history_page())
        self._stack.addWidget(self._build_settings_page())

        content_layout.addWidget(self._stack)
        main_layout.addWidget(content)

        # Default page.
        self._navigate("dashboard")

    def _tr(self, text: str) -> str:
        """Translate a UI label using the configured language."""
        return _tr(text, self._lang)

    # --- navigation -----------------------------------------------------------

    def _navigate(self, key: str) -> None:
        self._current_page = key
        index = _PAGE_KEYS.index(key)
        self._stack.setCurrentIndex(index)
        for k, btn in self._nav_buttons.items():
            btn.setChecked(k == key)

    # --- pages ------------------------------------------------------------------

    def _make_page(self, title: str) -> tuple[QWidget, QVBoxLayout]:
        """Create a scrollable page with title and content layout."""
        page = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(page)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title_label = QLabel(title)
        title_label.setObjectName("pageTitle")
        layout.addWidget(title_label)

        return scroll, layout

    def _make_card(
        self,
        parent_layout: QVBoxLayout,
        title: str | None = None,
    ) -> tuple[QFrame, QVBoxLayout]:
        """Create a rounded content card and add it to the page layout."""
        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(12)
        if title:
            title_label = QLabel(title)
            title_label.setObjectName("cardTitle")
            card_layout.addWidget(title_label)
        parent_layout.addWidget(card)
        return card, card_layout

    # --- dashboard -------------------------------------------------------------

    def _build_dashboard_page(self) -> QWidget:
        scroll, layout = self._make_page(self._tr("Dashboard"))

        stats, stats_card_layout = self._make_card(layout, self._tr("Today"))
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(16)
        stats_card_layout.addLayout(stats_layout)

        self._stat_translations = QLabel(f"0\n{self._tr('Translations')}")
        self._stat_translations.setObjectName("sectionTitle")
        self._stat_translations.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stats_layout.addWidget(self._stat_translations)

        self._stat_due = QLabel(f"0\n{self._tr('To Review')}")
        self._stat_due.setObjectName("sectionTitle")
        self._stat_due.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stats_layout.addWidget(self._stat_due)

        self._stat_streak = QLabel(f"0\n{self._tr('Day Streak')}")
        self._stat_streak.setObjectName("sectionTitle")
        self._stat_streak.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stats_layout.addWidget(self._stat_streak)

        # Recent translations.
        _, recent_layout = self._make_card(layout, self._tr("Recent Translations"))
        self._recent_table = QTableWidget()
        self._recent_table.setColumnCount(3)
        self._recent_table.setHorizontalHeaderLabels([self._tr("Source"), self._tr("Result"), self._tr("Engine")])
        self._recent_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._recent_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._recent_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self._recent_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._recent_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        recent_layout.addWidget(self._recent_table)

        layout.addStretch()
        return scroll

    def refresh_dashboard(self) -> None:
        """Update dashboard stats."""
        history = self._db.get_history(limit=10)
        self._recent_table.setRowCount(len(history))
        for i, h in enumerate(history):
            self._recent_table.setItem(i, 0, QTableWidgetItem(h["source_text"][:50]))
            self._recent_table.setItem(i, 1, QTableWidgetItem(h["target_text"][:50]))
            self._recent_table.setItem(i, 2, QTableWidgetItem(h["engine"]))
        self._stat_due.setText(f"{self._db.count_due()}\n{self._tr('To Review')}")
        self._stat_streak.setText(f"{self._db.get_streak()}\n{self._tr('Day Streak')}")
        self._stat_translations.setText(f"{len(history)}\n{self._tr('Translations')}")

    # --- translate --------------------------------------------------------------

    def _build_translate_page(self) -> QWidget:
        scroll, layout = self._make_page(self._tr("Translate"))

        # Source text.
        _, source_layout = self._make_card(layout, self._tr("Source Text"))

        self._translate_input = QTextEdit()
        self._translate_input.setPlaceholderText(self._tr("Source Text") + "...")
        self._translate_input.setMinimumHeight(120)
        source_layout.addWidget(self._translate_input)

        # Language selection.
        lang_layout = QHBoxLayout()
        lang_layout.addWidget(QLabel(self._tr("From:")))
        self._source_lang_combo = QComboBox()
        self._source_lang_combo.addItems([self._tr(l) for l in ["Auto", "English", "Chinese", "Japanese", "Korean", "French", "German", "Spanish", "Russian"]])
        lang_layout.addWidget(self._source_lang_combo)
        lang_layout.addWidget(QLabel(self._tr("To:")))
        self._target_lang_combo = QComboBox()
        self._target_lang_combo.addItems([self._tr(l) for l in ["Chinese", "English", "Japanese", "Korean", "French", "German", "Spanish", "Russian"]])
        lang_layout.addWidget(self._target_lang_combo)
        lang_layout.addStretch()

        self._translate_btn = QPushButton(self._tr("Translate"))
        self._translate_btn.setObjectName("primaryBtn")
        self._translate_btn.clicked.connect(self._do_manual_translate)
        lang_layout.addWidget(self._translate_btn)
        source_layout.addLayout(lang_layout)

        # Result.
        _, result_layout = self._make_card(layout, self._tr("Result"))

        self._translate_result = QTextEdit()
        self._translate_result.setReadOnly(True)
        self._translate_result.setMinimumHeight(150)
        result_layout.addWidget(self._translate_result)

        layout.addStretch()
        return scroll

    def _do_manual_translate(self) -> None:
        text = self._translate_input.toPlainText().strip()
        if not text:
            return
        src_idx = self._source_lang_combo.currentIndex()
        tgt_idx = self._target_lang_combo.currentIndex()
        src_map = ["auto", "en", "zh", "ja", "ko", "fr", "de", "es", "ru"]
        tgt_map = ["zh", "en", "ja", "ko", "fr", "de", "es", "ru"]
        source_lang = src_map[src_idx]
        target_lang = tgt_map[tgt_idx]
        self._translate_result.setPlainText(self._tr("Translating..."))
        self._on_translate_manual(text, source_lang, target_lang)

    def show_manual_result(self, result, source_text: str) -> None:
        """Called when manual translation completes."""
        self._translate_result.setPlainText(result.translation)
        if result.structured and result.terms:
            terms_text = "\n\nTerms:\n" + "\n".join(
                f"  {t.get('original', '')}: {t.get('translation', '')}" for t in result.terms
            )
            self._translate_result.setPlainText(result.translation + terms_text)

    def show_manual_error(self, error: str) -> None:
        """Called when manual translation fails."""
        self._translate_result.setPlainText(f"Error: {error}")

    # --- vocabulary ---------------------------------------------------------------

    def _build_vocabulary_page(self) -> QWidget:
        scroll, layout = self._make_page(self._tr("Vocabulary"))

        actions_layout = QHBoxLayout()
        refresh_btn = QPushButton(self._tr("Refresh"))
        refresh_btn.setObjectName("primaryBtn")
        refresh_btn.clicked.connect(self.refresh_vocabulary)
        delete_btn = QPushButton(self._tr("Delete"))
        delete_btn.clicked.connect(self._delete_selected_word)
        actions_layout.addWidget(refresh_btn)
        actions_layout.addWidget(delete_btn)
        actions_layout.addStretch()

        _, vocab_layout = self._make_card(layout)

        self._vocab_table = QTableWidget()
        self._vocab_table.setColumnCount(5)
        self._vocab_table.setHorizontalHeaderLabels([
            self._tr("Word"), self._tr("Marked"), self._tr("Context"),
            self._tr("Reps"), self._tr("Next Review"),
        ])
        self._vocab_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self._vocab_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._vocab_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self._vocab_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self._vocab_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self._vocab_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._vocab_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._vocab_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        vocab_layout.addWidget(self._vocab_table)
        vocab_layout.addLayout(actions_layout)

        return scroll

    def refresh_vocabulary(self) -> None:
        words = self._db.get_all_words()
        self._vocab_table.setRowCount(len(words))
        import time as _time
        for i, w in enumerate(words):
            self._vocab_table.setItem(i, 0, QTableWidgetItem(w["word"]))
            self._vocab_table.setItem(i, 1, QTableWidgetItem(_time.strftime("%m-%d %H:%M", _time.localtime(w["marked_at"]))))
            self._vocab_table.setItem(i, 2, QTableWidgetItem(w["context_sentence"][:40]))
            self._vocab_table.setItem(i, 3, QTableWidgetItem(str(w["repetitions"])))
            nr = w["next_review"]
            if nr <= _time.time():
                nr_text = self._tr("Due now")
            else:
                nr_text = f"in {int((nr - _time.time()) / 86400)}d"
            self._vocab_table.setItem(i, 4, QTableWidgetItem(nr_text))

    def _delete_selected_word(self) -> None:
        row = self._vocab_table.currentRow()
        if row < 0:
            return
        word = self._vocab_table.item(row, 0).text()
        if self._db.delete_word(word):
            self.refresh_vocabulary()

    # --- review -------------------------------------------------------------------

    def _build_review_page(self) -> QWidget:
        scroll, layout = self._make_page(self._tr("Review"))

        self._review_status = QLabel(self._tr("No words due for review."))
        self._review_status.setObjectName("infoText")
        layout.addWidget(self._review_status)

        review_group = QGroupBox(self._tr("Review"))
        review_layout = QVBoxLayout(review_group)

        self._review_word_label = QLabel()
        self._review_word_label.setObjectName("pageTitle")
        review_layout.addWidget(self._review_word_label)

        self._review_context_label = QLabel()
        self._review_context_label.setWordWrap(True)
        review_layout.addWidget(self._review_context_label)

        self._review_answer_label = QLabel()
        self._review_answer_label.setWordWrap(True)
        review_layout.addWidget(self._review_answer_label)

        button_layout = QHBoxLayout()
        self._forgot_btn = QPushButton(self._tr("Forgot"))
        self._forgot_btn.clicked.connect(lambda: self._grade_current_word(1))
        self._fuzzy_btn = QPushButton(self._tr("Fuzzy"))
        self._fuzzy_btn.clicked.connect(lambda: self._grade_current_word(3))
        self._known_btn = QPushButton(self._tr("Known"))
        self._known_btn.clicked.connect(lambda: self._grade_current_word(4))
        self._easy_btn = QPushButton(self._tr("Easy"))
        self._easy_btn.clicked.connect(lambda: self._grade_current_word(5))
        for btn in [self._forgot_btn, self._fuzzy_btn, self._known_btn, self._easy_btn]:
            button_layout.addWidget(btn)

        review_layout.addLayout(button_layout)
        layout.addWidget(review_group)
        layout.addStretch()
        return scroll

    def refresh_review(self) -> None:
        self._review_words = self._db.get_due_words(limit=50)
        self._review_index = 0
        if not self._review_words:
            self._review_status.setText(self._tr("No words due for review."))
            self._review_word_label.setText("")
            self._review_context_label.setText("")
            self._review_answer_label.setText("")
            self._review_word_label.hide()
            self._review_context_label.hide()
            self._review_answer_label.hide()
            self._forgot_btn.hide()
            self._fuzzy_btn.hide()
            self._known_btn.hide()
            self._easy_btn.hide()
            return
        self._review_status.setText(self._tr("Due now") + f": {len(self._review_words)}")
        self._review_word_label.show()
        self._review_context_label.show()
        self._review_answer_label.show()
        self._forgot_btn.show()
        self._fuzzy_btn.show()
        self._known_btn.show()
        self._easy_btn.show()
        self._show_current_review_word()

    def _show_current_review_word(self) -> None:
        if self._review_index >= len(self._review_words):
            self._review_status.setText(self._tr("Review complete"))
            self._review_word_label.setText("")
            self._review_context_label.setText("")
            self._review_answer_label.setText("")
            return
        word = self._review_words[self._review_index]
        self._review_word_label.setText(word["word"])
        context = word.get("context_sentence") or ""
        self._review_context_label.setText(context if context else self._tr("No context available."))
        self._review_answer_label.setText(self._tr("Select how well you remembered it."))

    def _grade_current_word(self, quality: int) -> None:
        if self._review_index >= len(self._review_words):
            return
        word = self._review_words[self._review_index]
        try:
            self._db.review_word(word["word"], quality)
        except ValueError:
            pass
        self._review_index += 1
        self._show_current_review_word()

    # --- history -------------------------------------------------------------------

    def _build_history_page(self) -> QWidget:
        scroll, layout = self._make_page(self._tr("History"))

        _, history_layout = self._make_card(layout)

        self._history_table = QTableWidget()
        self._history_table.setColumnCount(4)
        self._history_table.setHorizontalHeaderLabels([self._tr("Time"), self._tr("Source"), self._tr("Result"), self._tr("Engine")])
        self._history_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self._history_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._history_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self._history_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self._history_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        history_layout.addWidget(self._history_table)

        refresh_btn = QPushButton(self._tr("Refresh"))
        refresh_btn.setObjectName("primaryBtn")
        refresh_btn.clicked.connect(self.refresh_history)
        history_layout.addWidget(refresh_btn)

        return scroll

    def refresh_history(self) -> None:
        history = self._db.get_history(limit=50)
        self._history_table.setRowCount(len(history))
        import time as _time
        for i, h in enumerate(history):
            t = _time.strftime("%m-%d %H:%M", _time.localtime(h["created_at"]))
            self._history_table.setItem(i, 0, QTableWidgetItem(t))
            self._history_table.setItem(i, 1, QTableWidgetItem(h["source_text"][:60]))
            self._history_table.setItem(i, 2, QTableWidgetItem(h["target_text"][:60]))
            self._history_table.setItem(i, 3, QTableWidgetItem(h["engine"]))

    # --- settings -------------------------------------------------------------------

    def _build_settings_page(self) -> QWidget:
        shell = QWidget()
        shell_layout = QHBoxLayout(shell)
        shell_layout.setContentsMargins(0, 0, 0, 0)
        shell_layout.setSpacing(16)

        nav = QFrame()
        nav.setObjectName("secondaryNav")
        nav.setFixedWidth(120)
        nav_layout = QVBoxLayout(nav)
        nav_layout.setContentsMargins(8, 8, 8, 8)
        nav_layout.setSpacing(8)

        self._settings_stack = QStackedWidget()
        self._settings_stack.addWidget(self._build_general_settings_page())
        self._settings_stack.addWidget(self._build_model_settings_page())
        self._settings_stack.addWidget(self._build_app_settings_page())

        self._settings_section_buttons = {}
        for key, label in [
            ("general", self._tr("General")),
            ("model", self._tr("Model Config")),
            ("about", self._tr("App Related")),
        ]:
            btn = QPushButton(label)
            btn.setObjectName("secondaryNavBtn")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked=False, k=key: self._set_settings_section(k))
            nav_layout.addWidget(btn)
            self._settings_section_buttons[key] = btn
        nav_layout.addStretch()

        shell_layout.addWidget(nav)
        shell_layout.addWidget(self._settings_stack, 1)
        self._set_settings_section("general")
        return shell

    def _set_settings_section(self, key: str) -> None:
        index = ["general", "model", "about"].index(key)
        self._settings_stack.setCurrentIndex(index)
        for section, btn in self._settings_section_buttons.items():
            btn.setChecked(section == key)

    def _build_general_settings_page(self) -> QWidget:
        scroll, layout = self._make_page(self._tr("General"))

        # Trigger length group.
        trigger_group = QGroupBox(self._tr("Trigger Settings"))
        trigger_layout = QHBoxLayout(trigger_group)

        trigger_layout.addWidget(QLabel(self._tr("Sensitivity:")))
        self._preset_combo = QComboBox()
        self._preset_combo.addItems([
            self._tr("Sensitive (10)"), self._tr("Balanced (30)"), self._tr("Conservative (100)"),
        ])
        self._preset_combo.currentIndexChanged.connect(self._on_preset_changed)
        trigger_layout.addWidget(self._preset_combo)

        trigger_layout.addWidget(QLabel(self._tr("Length:")))
        self._trigger_slider = QSlider(Qt.Orientation.Horizontal)
        self._trigger_slider.setMinimum(10)
        self._trigger_slider.setMaximum(500)
        self._trigger_slider.setValue(self._config_get("trigger_length", 30))
        self._trigger_slider.valueChanged.connect(self._on_slider_changed)
        trigger_layout.addWidget(self._trigger_slider)

        self._length_input = QLineEdit(str(self._config_get("trigger_length", 30)))
        self._length_input.setFixedWidth(60)
        self._length_input.editingFinished.connect(self._on_length_input_changed)
        trigger_layout.addWidget(self._length_input)

        layout.addWidget(trigger_group)

        layout.addWidget(trigger_group)

        # Floating window group.
        float_group = QGroupBox(self._tr("Floating Window"))
        float_layout = QVBoxLayout(float_group)

        self._show_orig_check = QCheckBox(self._tr("Show original during translation"))
        self._show_orig_check.setChecked(self._config_get("floating_window.show_original_section", False))
        self._show_orig_check.toggled.connect(lambda v: self._config_set("floating_window.show_original_section", v))
        float_layout.addWidget(self._show_orig_check)

        self._focus_mode_check = QCheckBox(self._tr("Pause floating window when main window is active (Focus Mode)"))
        self._focus_mode_check.setChecked(self._config_get("focus_mode", True))
        self._focus_mode_check.toggled.connect(lambda v: self._config_set("focus_mode", v))
        float_layout.addWidget(self._focus_mode_check)

        self._auto_hide_check = QCheckBox(self._tr("Enable auto-hide"))
        self._auto_hide_check.setChecked(self._config_get("floating_window.auto_hide", True))
        self._auto_hide_check.toggled.connect(lambda v: self._config_set("floating_window.auto_hide", v))
        float_layout.addWidget(self._auto_hide_check)

        layout.addWidget(float_group)

        # UI Language group.
        ui_lang_group = QGroupBox("系统语言")
        ui_lang_layout = QHBoxLayout(ui_lang_group)
        ui_lang_layout.addWidget(QLabel(self._tr("Language") + ":"))
        self._ui_lang_combo = QComboBox()
        self._ui_lang_combo.addItems(["中文 (Chinese)", "English"])
        self._ui_lang_combo.setCurrentIndex(0 if self._config_get("ui.language", "zh") == "zh" else 1)
        self._ui_lang_combo.currentIndexChanged.connect(self._on_ui_lang_changed)
        ui_lang_layout.addWidget(self._ui_lang_combo)
        apply_lang_btn = QPushButton(self._tr("Refresh"))
        apply_lang_btn.setObjectName("primaryBtn")
        apply_lang_btn.setFixedHeight(30)
        apply_lang_btn.clicked.connect(self._apply_ui_language)
        ui_lang_layout.addWidget(apply_lang_btn)
        ui_lang_layout.addStretch()
        layout.addWidget(ui_lang_group)

        layout.addStretch()
        return scroll

    def _build_model_settings_page(self) -> QWidget:
        scroll, layout = self._make_page(self._tr("Model Config"))

        current_card, current_layout = self._make_card(layout, self._tr("Current Model"))
        self._model_type_combo = QComboBox()
        self._model_type_combo.addItems([
            self._tr("Custom (Cloud Model)"),
            self._tr("Ollama (Local Model)"),
        ])
        self._model_type_combo.setCurrentIndex(
            0 if self._config_get("model.provider", "cloud") != "local" else 1
        )
        current_layout.addWidget(self._model_type_combo)

        current_row = QHBoxLayout()
        self._current_model_label = QLabel(self._provider_display_text())
        current_row.addWidget(self._current_model_label)
        current_row.addStretch()
        self._model_status_label = QLabel(self._tr("Not tested"))
        self._model_status_label.setObjectName("statusChip")
        current_row.addWidget(self._model_status_label)
        current_layout.addLayout(current_row)

        # --- custom cloud model ---------------------------------------------
        self._cloud_card, cloud_layout = self._make_card(
            layout, self._tr("Custom (Cloud Model)")
        )
        cloud_form = QFormLayout()
        cloud_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._api_format_combo = QComboBox()
        for _, label in _API_FORMAT_OPTIONS:
            self._api_format_combo.addItem(label)
        self._api_format_combo.currentIndexChanged.connect(self._update_api_placeholders)
        cloud_form.addRow(self._tr("API Format"), self._api_format_combo)

        self._api_base_input = QLineEdit()
        self._api_base_input.setPlaceholderText("https://api.openai.com/v1")
        cloud_form.addRow(self._tr("API Address"), self._api_base_input)
        self._update_api_placeholders()

        self._api_key_input = QLineEdit()
        self._api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        cloud_form.addRow(self._tr("API Key:"), self._api_key_input)

        self._cloud_model_input = QLineEdit()
        self._cloud_model_input.setPlaceholderText("gpt-4o-mini")
        cloud_form.addRow(self._tr("Model Name"), self._cloud_model_input)

        cloud_layout.addLayout(cloud_form)

        cloud_buttons = QHBoxLayout()
        save_btn = QPushButton(self._tr("Save Config"))
        save_btn.setObjectName("primaryBtn")
        save_btn.clicked.connect(self._save_cloud_config)
        cloud_buttons.addWidget(save_btn)
        cloud_buttons.addStretch()
        cloud_layout.addLayout(cloud_buttons)

        self._cloud_configs_card, cloud_configs_layout = self._make_card(
            layout, self._tr("Saved Configs")
        )
        self._saved_configs_container = QWidget()
        self._saved_configs_layout = QVBoxLayout(self._saved_configs_container)
        self._saved_configs_layout.setContentsMargins(0, 0, 0, 0)
        self._saved_configs_layout.setSpacing(8)
        cloud_configs_layout.addWidget(self._saved_configs_container)

        # --- local Ollama ---------------------------------------------------
        self._ollama_card, ollama_layout = self._make_card(
            layout, self._tr("Ollama (Local Model)")
        )
        intro_label = QLabel(self._tr("Ollama is a local model runtime."))
        intro_label.setWordWrap(True)
        ollama_layout.addWidget(intro_label)

        download_link = QLabel(
            f'<a href="https://ollama.com/download">{self._tr("Download Ollama")}</a>'
        )
        download_link.setOpenExternalLinks(True)
        ollama_layout.addWidget(download_link)

        self._ollama_models_card, models_layout = self._make_card(
            layout, self._tr("Detected Models")
        )
        models_header = QHBoxLayout()
        models_header.addWidget(QLabel(self._tr("Select a model to use")))
        models_header.addStretch()
        refresh_btn = QPushButton(self._tr("Refresh"))
        refresh_btn.clicked.connect(self._detect_ollama_models)
        models_header.addWidget(refresh_btn)
        models_layout.addLayout(models_header)

        self._ollama_models_table = QTableWidget(0, 1)
        self._ollama_models_table.setHorizontalHeaderLabels([self._tr("Model Name")])
        self._ollama_models_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._ollama_models_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._ollama_models_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._ollama_models_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._ollama_models_table.itemSelectionChanged.connect(self._on_ollama_model_selected)
        models_layout.addWidget(self._ollama_models_table)

        self._model_type_combo.currentIndexChanged.connect(self._on_model_type_changed)
        self._on_model_type_changed(self._model_type_combo.currentIndex())
        self._refresh_cloud_configs()

        layout.addStretch()
        return scroll

    def _update_api_placeholders(self) -> None:
        if self._api_format_combo.currentIndex() == 0:
            self._api_base_input.setPlaceholderText("https://api.anthropic.com/v1")
        else:
            self._api_base_input.setPlaceholderText("https://api.openai.com/v1")

    def _build_app_settings_page(self) -> QWidget:
        scroll, layout = self._make_page(self._tr("App Related"))

        _, about_layout = self._make_card(layout, self._tr("About"))
        about_label = QLabel(
            self._tr("XianJue is a translation and vocabulary learning tool built around a quick floating window and a focused main window.")
        )
        about_label.setWordWrap(True)
        about_layout.addWidget(about_label)

        layout.addStretch()
        return scroll

    def _provider_display_text(self) -> str:
        provider = self._config_get("model.provider", "cloud")
        if provider == "local":
            model = self._config_get("model.local.model", "")
            if model:
                return f"Ollama ({model})"
            return self._tr("Ollama not configured")

        configs = self._config_get("model.saved_cloud_configs", [])
        active = self._config_get("model.active_config", 0)
        if isinstance(active, int) and 0 <= active < len(configs):
            config = configs[active]
            name = config.get("name", "Custom")
            model = config.get("model", "")
            return f"{name} ({model})"
        return self._tr("No model configured")

    def _update_current_model_label(self) -> None:
        if hasattr(self, "_current_model_label"):
            self._current_model_label.setText(self._provider_display_text())

    def _on_model_type_changed(self, index: int) -> None:
        provider = "custom" if index == 0 else "local"
        self._config_set("model.provider", provider)
        self._update_cloud_fields_visibility()
        self._update_ollama_fields_visibility()
        self._update_current_model_label()
        self._refresh_provider()
        self._set_model_status(False, self._tr("Not tested"))
        if index == 1:
            self._detect_ollama_models()

    def _update_cloud_fields_visibility(self) -> None:
        is_custom = self._model_type_combo.currentIndex() == 0
        self._cloud_card.setVisible(is_custom)
        self._cloud_configs_card.setVisible(is_custom)

    def _update_ollama_fields_visibility(self) -> None:
        is_local = self._model_type_combo.currentIndex() == 1
        self._ollama_card.setVisible(is_local)
        self._ollama_models_card.setVisible(is_local)

    def _cloud_config_from_form(self) -> dict:
        option = _API_FORMAT_OPTIONS[self._api_format_combo.currentIndex()]
        model = self._cloud_model_input.text().strip()
        return {
            "name": model,
            "api_format": option[0],
            "base_url": self._api_base_input.text().strip(),
            "api_key": self._api_key_input.text().strip(),
            "model": model,
        }

    def _load_cloud_config_into_form(self, config: dict) -> None:
        index = 0
        for row, (format_key, _) in enumerate(_API_FORMAT_OPTIONS):
            if format_key == config.get("api_format", "chat_completions"):
                index = row
                break
        self._api_format_combo.setCurrentIndex(index)
        self._api_base_input.setText(config.get("base_url", ""))
        self._api_key_input.setText(config.get("api_key", ""))
        self._cloud_model_input.setText(config.get("model", ""))

    def _refresh_cloud_configs(self) -> None:
        configs = self._config_get("model.saved_cloud_configs", [])
        active = self._config_get("model.active_config", None)
        self._saved_config_rows = []

        while self._saved_configs_layout.count():
            item = self._saved_configs_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()

        for row, config in enumerate(configs):
            row_widget, toggle, test_btn, delete_btn = self._make_cloud_config_row(
                config,
                row,
                active == row,
            )
            self._saved_configs_layout.addWidget(row_widget)
            self._saved_config_rows.append({
                "row": row_widget,
                "toggle": toggle,
                "test": test_btn,
                "delete": delete_btn,
            })

    def _format_label(self, api_format: str) -> str:
        for format_key, label in _API_FORMAT_OPTIONS:
            if format_key == api_format:
                return label
        return _API_FORMAT_OPTIONS[1][1]

    def _make_cloud_config_row(
        self,
        config: dict,
        row: int,
        is_active: bool,
    ) -> tuple[QFrame, ToggleSwitch, QPushButton, QPushButton]:
        row_widget = QFrame()
        row_widget.setObjectName("modelConfigRow")
        row_widget.setProperty("active", is_active)
        row_widget.setCursor(Qt.CursorShape.PointingHandCursor)
        row_widget.mousePressEvent = lambda event, index=row: self._load_cloud_config_row(index)

        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(12, 10, 12, 10)
        row_layout.setSpacing(12)

        avatar = QFrame()
        avatar.setObjectName("modelAvatar")
        avatar.setFixedSize(34, 34)
        row_layout.addWidget(avatar)

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)
        title = QLabel(config.get("name") or config.get("model", ""))
        title.setObjectName("modelConfigTitle")
        subtitle = QLabel(
            f"{self._format_label(config.get('api_format', 'chat_completions'))} · {config.get('base_url', '')}"
        )
        subtitle.setObjectName("modelConfigSubtitle")
        subtitle.setWordWrap(True)
        text_layout.addWidget(title)
        text_layout.addWidget(subtitle)
        row_layout.addLayout(text_layout, 1)

        toggle = ToggleSwitch()
        toggle.setObjectName("modelToggle")
        toggle.setValue(1 if is_active else 0)
        toggle.valueChanged.connect(lambda value, index=row: self._set_active_cloud_config(index, bool(value)))
        row_layout.addWidget(toggle)

        test_btn = QPushButton(self._tr("Test"))
        test_btn.setObjectName("modelActionBtn")
        test_btn.clicked.connect(lambda checked=False, index=row: self._test_saved_cloud_connection(index))
        row_layout.addWidget(test_btn)

        delete_btn = QPushButton()
        delete_btn.setObjectName("modelDeleteBtn")
        delete_btn.setIcon(make_icon(_TRASH_ICON, "#8A8A98", 16))
        delete_btn.setFixedSize(30, 30)
        delete_btn.clicked.connect(lambda checked=False, index=row: self._delete_cloud_config(index))
        row_layout.addWidget(delete_btn)

        self._polish_widget(row_widget)
        return row_widget, toggle, test_btn, delete_btn

    def _polish_widget(self, widget: QWidget) -> None:
        widget.style().unpolish(widget)
        widget.style().polish(widget)

    def _load_cloud_config_row(self, row: int) -> None:
        configs = self._config_get("model.saved_cloud_configs", [])
        if 0 <= row < len(configs):
            self._load_cloud_config_into_form(configs[row])

    def _apply_active_row_state(self) -> None:
        active = self._config_get("model.active_config", None)
        for index, row in enumerate(self._saved_config_rows):
            is_active = active == index
            row["row"].setProperty("active", is_active)
            self._polish_widget(row["row"])
            row["toggle"].setValue(1 if is_active else 0)

    def _clear_cloud_form(self) -> None:
        self._api_format_combo.setCurrentIndex(0)
        self._api_base_input.clear()
        self._api_key_input.clear()
        self._cloud_model_input.clear()

    def _set_active_cloud_config(self, row: int, checked: bool) -> None:
        configs = self._config_get("model.saved_cloud_configs", [])
        if row < 0 or row >= len(configs):
            return

        active = self._config_get("model.active_config", None)
        if checked:
            self._config_set("model.active_config", row)
        elif active == row:
            self._config_set("model.active_config", None)

        self._config_set("model.provider", "custom")
        self._apply_active_row_state()
        self._update_current_model_label()
        self._refresh_provider()

    def _save_cloud_config(self) -> None:
        config = self._cloud_config_from_form()
        if not config["model"]:
            QMessageBox.information(self, self._tr("Save Config"), self._tr("Please enter a model name"))
            return

        configs = self._config_get("model.saved_cloud_configs", [])
        configs.append(config)
        active = len(configs) - 1

        self._config_set("model.saved_cloud_configs", configs)
        self._config_set("model.active_config", active)
        self._config_set("model.provider", "custom")
        self._refresh_cloud_configs()
        self._update_current_model_label()
        self._refresh_provider()
        self._clear_cloud_form()

    def _delete_cloud_config(self, row: int) -> None:
        configs = self._config_get("model.saved_cloud_configs", [])
        if row < 0 or row >= len(configs):
            return

        confirmed = QMessageBox.question(
            self,
            self._tr("Delete"),
            self._tr("Are you sure you want to delete this model?"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirmed != QMessageBox.StandardButton.Yes:
            return

        configs.pop(row)
        self._config_set("model.saved_cloud_configs", configs)
        active = self._config_get("model.active_config", 0)
        if isinstance(active, int) and active >= len(configs):
            self._config_set("model.active_config", None if not configs else len(configs) - 1)
        self._refresh_cloud_configs()
        self._update_current_model_label()
        self._refresh_provider()

    def _test_saved_cloud_connection(self, row: int) -> None:
        configs = self._config_get("model.saved_cloud_configs", [])
        if 0 <= row < len(configs):
            self._set_model_status(True, self._tr("Testing..."))
            self._test_cloud_config(configs[row])

    def _test_cloud_config(self, config: dict) -> None:
        import threading
        import time as _time
        from ..providers.custom_cloud_provider import CustomCloudProvider

        def worker():
            start = _time.monotonic()
            ok = False
            error = ""
            try:
                provider = CustomCloudProvider(
                    api_key=config.get("api_key", ""),
                    model=config.get("model", ""),
                    base_url=config.get("base_url", ""),
                    api_format=config.get("api_format", "chat_completions"),
                )
                ok, error, latency = provider.test_connection_detailed()
            except Exception as exc:
                error = str(exc)
                latency = int((_time.monotonic() - start) * 1000)

            message = (
                f"{self._tr('Connected')} · {latency} ms"
                if ok
                else f"{self._tr('Connection failed')}: {error or self._tr('Unknown error')}"
            )
            self.model_status_ready.emit(ok, message)

        threading.Thread(target=worker, daemon=True).start()

    def _set_model_status(self, ok: bool, message: str) -> None:
        self._model_status_label.setText(message)
        if ok:
            self._model_status_label.setStyleSheet(
                "QLabel#statusChip { background-color: rgba(80, 170, 120, 0.25); color: #5FD59F; border-radius: 10px; padding: 4px 10px; }"
            )
        else:
            self._model_status_label.setStyleSheet(
                "QLabel#statusChip { background-color: rgba(230, 100, 100, 0.2); color: #FF9A9A; border-radius: 10px; padding: 4px 10px; }"
            )

    def _detect_ollama_models(self) -> None:
        import threading
        from ..providers.ollama_provider import OllamaProvider

        host = self._config_get("model.local.host", "http://localhost:11434")
        self._set_ollama_models_status(self._tr("Detecting..."))

        def worker():
            provider = OllamaProvider(host=host, model="")
            models, error, _ = provider.list_models_detailed()
            self.ollama_models_ready.emit(models, error)

        threading.Thread(target=worker, daemon=True).start()

    def _refresh_ollama_models(self, models: list[str], error: str = "") -> None:
        self._ollama_models_table.blockSignals(True)
        self._ollama_models_table.setRowCount(len(models))
        for row, model in enumerate(models):
            self._ollama_models_table.setItem(row, 0, QTableWidgetItem(model))
        self._ollama_models_table.blockSignals(False)

        if error:
            self._set_ollama_models_status(self._tr("Connection failed") + f": {error}")
        elif models:
            if self._config_get("model.local.model", "") not in models:
                self._config_set("model.local.model", models[0])
                self._update_current_model_label()
                self._refresh_provider()
            self._set_ollama_models_status("")
        else:
            self._set_ollama_models_status(self._tr("No Ollama models found"))

    def _set_ollama_models_status(self, message: str) -> None:
        if message:
            self._ollama_models_table.setRowCount(0)
            self._ollama_models_table.setRowCount(1)
            self._ollama_models_table.setItem(0, 0, QTableWidgetItem(message))
            self._ollama_models_table.item(0, 0).setFlags(Qt.ItemFlag.ItemIsEnabled)
        else:
            self._ollama_models_table.setRowCount(0)

    def _on_ollama_model_selected(self) -> None:
        row = self._ollama_models_table.currentRow()
        if row < 0:
            return
        model_item = self._ollama_models_table.item(row, 0)
        if not model_item:
            return
        model = model_item.text().strip()
        if not model:
            return
        self._config_set("model.provider", "local")
        self._config_set("model.local.model", model)
        self._update_current_model_label()
        self._refresh_provider()

    # --- settings callbacks --------------------------------------------------------

    def _on_preset_changed(self, index: int) -> None:
        values = [10, 30, 100]
        self._trigger_slider.setValue(values[index])
        self._length_input.setText(str(values[index]))
        self._config_set("trigger_length", values[index])

    def _on_slider_changed(self, value: int) -> None:
        self._length_input.setText(str(value))
        self._config_set("trigger_length", value)

    def _on_ui_lang_changed(self, index: int) -> None:
        new_lang = "zh" if index == 0 else "en"
        self._config_set("ui.language", new_lang)

    def _apply_ui_language(self) -> None:
        """Rebuild the entire UI with the currently selected language."""
        self._lang = "zh" if self._ui_lang_combo.currentIndex() == 0 else "en"
        self._config_set("ui.language", self._lang)
        current_page = self._current_page

        # Rebuild nav buttons.
        for key, label, _ in _NAV_ITEMS:
            btn = self._nav_buttons[key]
            btn.setText(self._tr(label))

        # Rebuild pages.
        while self._stack.count() > 0:
            widget = self._stack.widget(0)
            self._stack.removeWidget(widget)
            if widget:
                widget.deleteLater()

        self._stack.addWidget(self._build_dashboard_page())
        self._stack.addWidget(self._build_translate_page())
        self._stack.addWidget(self._build_vocabulary_page())
        self._stack.addWidget(self._build_review_page())
        self._stack.addWidget(self._build_history_page())
        self._stack.addWidget(self._build_settings_page())
        if current_page == "vocabulary":
            current_page = "review"
        self._navigate(current_page if current_page else "dashboard")

    def _on_length_input_changed(self) -> None:
        text = self._length_input.text().strip()
        try:
            value = int(text)
            value = max(10, min(500, value))
            self._trigger_slider.setValue(value)
            self._config_set("trigger_length", value)
        except ValueError:
            pass

    # --- utils -------------------------------------------------------------------

    def refresh_all(self) -> None:
        self.refresh_dashboard()
        self.refresh_vocabulary()
        self.refresh_review()
        self.refresh_history()
