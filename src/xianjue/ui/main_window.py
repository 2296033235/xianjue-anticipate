"""Main application window with left navigation and content pages."""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget,
    QPushButton, QLabel, QComboBox, QSlider, QLineEdit, QCheckBox,
    QSpinBox, QGroupBox, QFormLayout, QScrollArea, QTableWidget,
    QTableWidgetItem, QTextEdit, QTabWidget, QHeaderView, QMessageBox,
)

from .i18n import tr as _tr


_STYLE = """
QMainWindow {
    background-color: #12151A;
}
QWidget#sidebar {
    background-color: #171B21;
    min-width: 210px;
    max-width: 220px;
    border-right: 1px solid rgba(255, 255, 255, 0.06);
}
QPushButton#navBtn {
    text-align: left;
    padding: 10px 14px;
    color: #A9B6C3;
    border: none;
    background: transparent;
    font-size: 14px;
    border-radius: 10px;
    min-height: 34px;
}
QPushButton#navBtn:hover {
    background-color: rgba(255, 255, 255, 0.07);
    color: #E6EDF3;
}
QPushButton#navBtnActive {
    text-align: left;
    padding: 10px 14px;
    border: none;
    background-color: rgba(47, 214, 162, 0.14);
    border: 1px solid rgba(47, 214, 162, 0.38);
    color: #9EF7D9;
    font-size: 14px;
    font-weight: bold;
    border-radius: 10px;
}
QWidget#contentArea {
    background-color: #12151A;
}
QLabel#brandTitle {
    color: #E6EDF3;
    font-size: 18px;
    font-weight: 800;
    padding: 0 6px 2px 6px;
}
QLabel#brandSubtitle {
    color: #7C8794;
    font-size: 12px;
    padding: 0 6px 14px 6px;
}
QLabel#pageTitle {
    color: #E6EDF3;
    font-size: 24px;
    font-weight: bold;
    letter-spacing: 0;
}
QLabel#sectionTitle {
    color: #C3D0DE;
    font-size: 15px;
    font-weight: bold;
}
QLabel#infoText {
    color: #A5B2C0;
    font-size: 13px;
}
QGroupBox {
    background-color: #171C22;
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 14px;
    margin-top: 12px;
    padding: 16px;
    color: #A9B6C3;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 4px;
}
QLineEdit, QComboBox, QTextEdit, QSpinBox {
    background-color: #1A1F26;
    color: #E6EDF3;
    border: 1px solid rgba(255, 255, 255, 0.10);
    border-radius: 10px;
    padding: 10px 12px;
    selection-background-color: rgba(47, 214, 162, 0.35);
}
QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QSpinBox:focus {
    border-color: rgba(47, 214, 162, 0.55);
}
QCheckBox, QRadioButton {
    color: #C3D0DE;
    spacing: 8px;
}
QPushButton {
    background-color: #1F252D;
    color: #E6EDF3;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    padding: 8px 14px;
    min-height: 34px;
}
QPushButton:hover {
    background-color: #27313A;
}
QPushButton:pressed {
    background-color: #212A33;
}
QPushButton#primaryBtn {
    background-color: #2FD6A2;
    color: #04110C;
    border: none;
    padding: 10px 18px;
    border-radius: 12px;
    font-size: 14px;
    font-weight: 700;
    min-height: 38px;
}
QPushButton#primaryBtn:hover {
    background-color: #46E0B0;
}
QPushButton#dangerBtn {
    background-color: rgba(255, 122, 122, 0.12);
    color: #FF8B8B;
    border: 1px solid rgba(255, 122, 122, 0.35);
}
QPushButton#neutralBtn {
    background-color: #1F252D;
    color: #A9B6C3;
    border: 1px solid rgba(255, 255, 255, 0.10);
}
QPushButton#successBtn {
    background-color: #2FD6A2;
    color: #04110C;
    border: none;
    font-weight: 700;
}
QWidget#reviewCard {
    background-color: #171C22;
    border: 1px solid rgba(47, 214, 162, 0.22);
    border-radius: 16px;
    padding: 18px;
}
QLabel#reviewWord {
    color: #E6EDF3;
    font-size: 34px;
    font-weight: 800;
}
QLabel#reviewContext {
    color: #A9B6C3;
    font-size: 14px;
}
QLabel#reviewAnswer {
    color: #7C8794;
    font-size: 13px;
}
QTableWidget {
    background-color: #171C22;
    color: #D5DFE9;
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 12px;
    gridline-color: rgba(255, 255, 255, 0.05);
    selection-background-color: rgba(47, 214, 162, 0.18);
    alternate-background-color: #1A2027;
}
QHeaderView::section {
    background-color: #1B2128;
    color: #A9B6C3;
    padding: 10px 8px;
    border: none;
    font-size: 12px;
}
QTableWidget::item {
    padding: 8px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.04);
}
QSlider::groove:horizontal {
    height: 4px;
    background: #2A323B;
    border-radius: 2px;
}
QSlider::sub-page:horizontal {
    background: #2FD6A2;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    width: 16px;
    height: 16px;
    margin: -7px 0;
    border-radius: 8px;
    background: #E6EDF3;
}
QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 2px;
}
QScrollBar::handle:vertical {
    background: #333E48;
    border-radius: 5px;
    min-height: 30px;
}
"""


_NAV_ITEMS = [
    ("dashboard", "Dashboard"),
    ("translate", "Translate"),
    ("vocabulary", "Vocabulary"),
    ("review", "Review"),
    ("history", "History"),
    ("settings", "Settings"),
]


class MainWindow(QMainWindow):
    """Primary application window."""

    def __init__(
        self,
        config: Callable,
        config_set: Callable,
        on_translate_manual: Callable,
        db,
        refresh_provider: Callable,
    ) -> None:
        super().__init__()
        self.setWindowTitle("XianJue (先觉)")
        self.setMinimumSize(900, 640)
        self.setStyleSheet(_STYLE)

        self._config_get = config
        self._config_set = config_set
        self._db = db
        self._on_translate_manual = on_translate_manual
        self._refresh_provider = refresh_provider

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
        sidebar_layout.setContentsMargins(12, 20, 12, 20)
        sidebar_layout.setSpacing(8)

        # Logo/title.
        title = QLabel("XianJue")
        title.setObjectName("brandTitle")
        subtitle = QLabel("先觉")
        subtitle.setObjectName("brandSubtitle")
        sidebar_layout.addWidget(title)
        sidebar_layout.addWidget(subtitle)

        self._nav_buttons = {}
        self._stack = QStackedWidget()

        for key, label in _NAV_ITEMS:
            btn = QPushButton(self._tr(label))
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
        index = [k for k, _ in _NAV_ITEMS].index(key)
        self._stack.setCurrentIndex(index)
        for k, btn in self._nav_buttons.items():
            btn.setObjectName("navBtnActive" if k == key else "navBtn")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    # --- pages ------------------------------------------------------------------

    def _make_page(self, title: str) -> tuple[QWidget, QVBoxLayout]:
        """Create a scrollable page with title and content layout."""
        page = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(page)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title_label = QLabel(title)
        title_label.setObjectName("pageTitle")
        layout.addWidget(title_label)

        return scroll, layout

    # --- dashboard -------------------------------------------------------------

    def _build_dashboard_page(self) -> QWidget:
        scroll, layout = self._make_page(self._tr("Dashboard"))

        stats = QGroupBox(self._tr("Today"))
        stats_layout = QHBoxLayout(stats)

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

        layout.addWidget(stats)

        # Recent translations.
        recent_title = QLabel(self._tr("Recent Translations"))
        recent_title.setObjectName("sectionTitle")
        layout.addWidget(recent_title)

        self._recent_table = QTableWidget()
        self._recent_table.setColumnCount(3)
        self._recent_table.setHorizontalHeaderLabels([self._tr("Source"), self._tr("Result"), self._tr("Engine")])
        self._recent_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._recent_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._recent_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self._recent_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._recent_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self._recent_table)

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

        # Source text card.
        source_group = QGroupBox(self._tr("Source Text"))
        source_layout = QVBoxLayout(source_group)
        source_layout.setSpacing(10)

        self._translate_input = QTextEdit()
        self._translate_input.setPlaceholderText(self._tr("Source Text") + "...")
        self._translate_input.setMinimumHeight(140)
        source_layout.addWidget(self._translate_input)
        layout.addWidget(source_group)

        # Language selection and action.
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
        self._translate_btn.setMinimumWidth(120)
        self._translate_btn.clicked.connect(self._do_manual_translate)
        lang_layout.addWidget(self._translate_btn)
        layout.addLayout(lang_layout)

        # Result card.
        result_group = QGroupBox(self._tr("Result"))
        result_layout = QVBoxLayout(result_group)
        result_layout.setSpacing(10)

        self._translate_result = QTextEdit()
        self._translate_result.setReadOnly(True)
        self._translate_result.setMinimumHeight(180)
        result_layout.addWidget(self._translate_result)
        layout.addWidget(result_group)

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
        delete_btn.setObjectName("dangerBtn")
        delete_btn.clicked.connect(self._delete_selected_word)
        actions_layout.addWidget(refresh_btn)
        actions_layout.addWidget(delete_btn)
        actions_layout.addStretch()

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
        layout.addWidget(self._vocab_table)

        layout.addLayout(actions_layout)

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
        review_group.setObjectName("reviewCard")
        review_layout = QVBoxLayout(review_group)
        review_layout.setSpacing(14)

        self._review_word_label = QLabel()
        self._review_word_label.setObjectName("reviewWord")
        review_layout.addWidget(self._review_word_label)

        self._review_context_label = QLabel()
        self._review_context_label.setObjectName("reviewContext")
        self._review_context_label.setWordWrap(True)
        review_layout.addWidget(self._review_context_label)

        self._review_answer_label = QLabel()
        self._review_answer_label.setObjectName("reviewAnswer")
        self._review_answer_label.setWordWrap(True)
        review_layout.addWidget(self._review_answer_label)

        button_layout = QHBoxLayout()
        self._forgot_btn = QPushButton(self._tr("Forgot"))
        self._forgot_btn.setObjectName("dangerBtn")
        self._forgot_btn.clicked.connect(lambda: self._grade_current_word(1))
        self._fuzzy_btn = QPushButton(self._tr("Fuzzy"))
        self._fuzzy_btn.setObjectName("neutralBtn")
        self._fuzzy_btn.clicked.connect(lambda: self._grade_current_word(3))
        self._known_btn = QPushButton(self._tr("Known"))
        self._known_btn.setObjectName("primaryBtn")
        self._known_btn.clicked.connect(lambda: self._grade_current_word(4))
        self._easy_btn = QPushButton(self._tr("Easy"))
        self._easy_btn.setObjectName("successBtn")
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

        self._history_table = QTableWidget()
        self._history_table.setColumnCount(4)
        self._history_table.setHorizontalHeaderLabels([self._tr("Time"), self._tr("Source"), self._tr("Result"), self._tr("Engine")])
        self._history_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self._history_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._history_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self._history_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self._history_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self._history_table)

        refresh_btn = QPushButton(self._tr("Refresh"))
        refresh_btn.setObjectName("primaryBtn")
        refresh_btn.clicked.connect(self.refresh_history)
        layout.addWidget(refresh_btn)

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
        scroll, layout = self._make_page(self._tr("Settings"))

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

        # Engine group.
        engine_group = QGroupBox(self._tr("Translation Engine"))
        engine_layout = QVBoxLayout(engine_group)

        self._engine_combo = QComboBox()
        self._engine_combo.addItems([self._tr("Cloud (DeepSeek)"), self._tr("Local (Ollama)")])
        self._engine_combo.setCurrentIndex(0 if self._config_get("model.provider", "cloud") == "cloud" else 1)
        self._engine_combo.currentIndexChanged.connect(self._on_engine_changed)
        engine_layout.addWidget(self._engine_combo)

        self._key_row_widget = QWidget()
        key_row = QHBoxLayout(self._key_row_widget)
        key_row.setContentsMargins(0, 0, 0, 0)
        key_row.addWidget(QLabel(self._tr("API Key:")))
        self._api_key_input = QLineEdit(self._config_get("model.cloud.api_key", ""))
        self._api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        key_row.addWidget(self._api_key_input)
        test_btn = QPushButton(self._tr("Test"))
        test_btn.clicked.connect(self._test_connection)
        key_row.addWidget(test_btn)
        engine_layout.addWidget(self._key_row_widget)

        layout.addWidget(engine_group)
        self._key_row_widget.setVisible(self._config_get("model.provider", "cloud") == "cloud")

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
        ui_lang_group = QGroupBox(self._tr("UI Language"))
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
        for key, label in _NAV_ITEMS:
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
        self._navigate(current_page if current_page else "dashboard")

    def _on_length_input_changed(self) -> None:
        text = self._length_input.text().strip()
        try:
            value = int(text)
            value = max(10, min(500, value))
            self._slider.setValue(value)
            self._config_set("trigger_length", value)
        except ValueError:
            pass

    def _on_engine_changed(self, index: int) -> None:
        provider = "cloud" if index == 0 else "local"
        self._config_set("model.provider", provider)
        # Show/hide API key row based on engine selection.
        self._key_row_widget.setVisible(provider == "cloud")
        self._refresh_provider()

    def _test_connection(self) -> None:
        self._config_set("model.cloud.api_key", self._api_key_input.text().strip())
        import threading
        from ..providers.factory import create_provider

        def test():
            try:
                provider = create_provider(self._config_get)
                ok = provider.test_connection()
                msg = "OK" if ok else "Connection failed"
            except Exception as e:
                msg = str(e)
            from PySide6.QtCore import QTimer
            QTimer.singleShot(0, lambda: QMessageBox.information(
                self, self._tr("Test"), msg
            ))

        threading.Thread(target=test, daemon=True).start()

    # --- utils -------------------------------------------------------------------

    def refresh_all(self) -> None:
        self.refresh_dashboard()
        self.refresh_vocabulary()
        self.refresh_review()
        self.refresh_history()
