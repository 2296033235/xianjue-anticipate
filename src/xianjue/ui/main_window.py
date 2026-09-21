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


_STYLE = """
QMainWindow {
    background-color: #1E1E24;
}
QWidget#sidebar {
    background-color: #18181D;
    min-width: 180px;
    max-width: 180px;
}
QPushButton#navBtn {
    text-align: left;
    padding: 10px 16px;
    color: #A0A0B0;
    border: none;
    background: transparent;
    font-size: 14px;
    border-radius: 6px;
}
QPushButton#navBtn:hover {
    background-color: rgba(255, 255, 255, 10);
}
QPushButton#navBtnActive {
    text-align: left;
    padding: 10px 16px;
    border: none;
    background-color: rgba(70, 130, 220, 40);
    color: #70B0FF;
    font-size: 14px;
    font-weight: bold;
    border-radius: 6px;
}
QWidget#contentArea {
    background-color: #1E1E24;
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
    border: 1px solid rgba(80, 80, 100, 60);
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 16px;
    color: #B0B0B8;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
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
    grid-line-color: rgba(80, 80, 100, 30);
}
QHeaderView::section {
    background-color: rgba(255, 255, 255, 10);
    color: #A0A0B0;
    padding: 4px;
    border: none;
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
    ) -> None:
        super().__init__()
        self.setWindowTitle("XianJue (先觉)")
        self.setMinimumSize(900, 640)
        self.setStyleSheet(_STYLE)

        self._config_get = config
        self._config_set = config_set
        self._db = db
        self._on_translate_manual = on_translate_manual

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
        sidebar_layout.setSpacing(2)

        # Logo/title.
        title = QLabel("XianJue (先觉)")
        title.setStyleSheet("color: #70B0FF; font-size: 16px; font-weight: bold; padding: 0 8px 12px 8px;")
        sidebar_layout.addWidget(title)

        self._nav_buttons = {}
        self._stack = QStackedWidget()

        for key, label in _NAV_ITEMS:
            btn = QPushButton(label)
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

    # --- navigation -----------------------------------------------------------

    def _navigate(self, key: str) -> None:
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
        scroll, layout = self._make_page("Dashboard")

        stats = QGroupBox("Today")
        stats_layout = QHBoxLayout(stats)

        self._stat_translations = QLabel("0\nTranslations")
        self._stat_translations.setObjectName("sectionTitle")
        self._stat_translations.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stats_layout.addWidget(self._stat_translations)

        self._stat_due = QLabel("0\nTo Review")
        self._stat_due.setObjectName("sectionTitle")
        self._stat_due.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stats_layout.addWidget(self._stat_due)

        self._stat_streak = QLabel("0\nDay Streak")
        self._stat_streak.setObjectName("sectionTitle")
        self._stat_streak.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stats_layout.addWidget(self._stat_streak)

        layout.addWidget(stats)

        # Recent translations.
        recent_title = QLabel("Recent Translations")
        recent_title.setObjectName("sectionTitle")
        layout.addWidget(recent_title)

        self._recent_table = QTableWidget()
        self._recent_table.setColumnCount(3)
        self._recent_table.setHorizontalHeaderLabels(["Source", "Translation", "Engine"])
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
        self._stat_due.setText(f"{self._db.count_due()}\nTo Review")
        self._stat_streak.setText(f"{self._db.get_streak()}\nDay Streak")
        self._stat_translations.setText(f"{len(history)}\nTranslations")

    # --- translate --------------------------------------------------------------

    def _build_translate_page(self) -> QWidget:
        scroll, layout = self._make_page("Translate")

        # Source text.
        src_label = QLabel("Source Text")
        src_label.setObjectName("sectionTitle")
        layout.addWidget(src_label)

        self._translate_input = QTextEdit()
        self._translate_input.setPlaceholderText("Paste or type text to translate...")
        self._translate_input.setMinimumHeight(120)
        layout.addWidget(self._translate_input)

        # Language selection.
        lang_layout = QHBoxLayout()
        lang_layout.addWidget(QLabel("From:"))
        self._source_lang_combo = QComboBox()
        self._source_lang_combo.addItems(["Auto", "English", "Chinese", "Japanese", "Korean", "French", "German", "Spanish", "Russian"])
        lang_layout.addWidget(self._source_lang_combo)
        lang_layout.addWidget(QLabel("To:"))
        self._target_lang_combo = QComboBox()
        self._target_lang_combo.addItems(["Chinese", "English", "Japanese", "Korean", "French", "German", "Spanish", "Russian"])
        lang_layout.addWidget(self._target_lang_combo)
        lang_layout.addStretch()

        self._translate_btn = QPushButton("Translate")
        self._translate_btn.setObjectName("primaryBtn")
        self._translate_btn.clicked.connect(self._do_manual_translate)
        lang_layout.addWidget(self._translate_btn)
        layout.addLayout(lang_layout)

        # Result.
        result_label = QLabel("Result")
        result_label.setObjectName("sectionTitle")
        layout.addWidget(result_label)

        self._translate_result = QTextEdit()
        self._translate_result.setReadOnly(True)
        self._translate_result.setMinimumHeight(150)
        layout.addWidget(self._translate_result)

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
        self._translate_result.setPlainText("Translating...")
        self._on_translate_manual(text, source_lang, target_lang)

    def show_manual_result(self, result, source_text: str) -> None:
        """Called when manual translation completes."""
        self._translate_result.setPlainText(result.translation)
        if result.structured and result.terms:
            terms_text = "\n\nTerms:\n" + "\n".join(
                f"  {t.get('original', '')}: {t.get('translation', '')}" for t in result.terms
            )
            self._translate_result.setPlainText(result.translation + terms_text)

    # --- vocabulary ---------------------------------------------------------------

    def _build_vocabulary_page(self) -> QWidget:
        scroll, layout = self._make_page("Vocabulary")

        self._vocab_table = QTableWidget()
        self._vocab_table.setColumnCount(5)
        self._vocab_table.setHorizontalHeaderLabels(["Word", "Marked", "Context", "Reps", "Next Review"])
        self._vocab_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self._vocab_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._vocab_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self._vocab_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self._vocab_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self._vocab_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self._vocab_table)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.setObjectName("primaryBtn")
        refresh_btn.clicked.connect(self.refresh_vocabulary)
        layout.addWidget(refresh_btn)

        return scroll

    def refresh_vocabulary(self) -> None:
        words = self._db.get_all_words()
        self._vocab_table.setRowCount(len(words))
        import time as _time
        for i, w in enumerate(words):
            self._vocab_table.setItem(i, 0, QTableWidgetItem(w["word"]))
            self._vocab_table.setItem(i, 1, QTableWidgetItem(w["context_sentence"][:40]))
            self._vocab_table.setItem(i, 2, QTableWidgetItem(str(w["repetitions"])))
            nr = w["next_review"]
            if nr <= _time.time():
                nr_text = "Due now"
            else:
                nr_text = f"in {int((nr - _time.time()) / 86400)}d"
            self._vocab_table.setItem(i, 3, QTableWidgetItem(str(nr)))
            self._vocab_table.setItem(i, 4, QTableWidgetItem(nr_text))

    # --- review -------------------------------------------------------------------

    def _build_review_page(self) -> QWidget:
        scroll, layout = self._make_page("Review")

        info = QLabel("No words due for review.")
        info.setObjectName("infoText")
        layout.addWidget(info)
        layout.addStretch()
        return scroll

    # --- history -------------------------------------------------------------------

    def _build_history_page(self) -> QWidget:
        scroll, layout = self._make_page("History")

        self._history_table = QTableWidget()
        self._history_table.setColumnCount(4)
        self._history_table.setHorizontalHeaderLabels(["Time", "Source", "Translation", "Engine"])
        self._history_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self._history_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._history_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self._history_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self._history_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self._history_table)

        refresh_btn = QPushButton("Refresh")
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
        scroll, layout = self._make_page("Settings")

        # Trigger length group.
        trigger_group = QGroupBox("Trigger Settings")
        trigger_layout = QHBoxLayout(trigger_group)

        trigger_layout.addWidget(QLabel("Sensitivity:"))
        self._preset_combo = QComboBox()
        self._preset_combo.addItems(["Sensitive (10)", "Balanced (30)", "Conservative (100)"])
        self._preset_combo.currentIndexChanged.connect(self._on_preset_changed)
        trigger_layout.addWidget(self._preset_combo)

        trigger_layout.addWidget(QLabel("Length:"))
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
        engine_group = QGroupBox("Translation Engine")
        engine_layout = QVBoxLayout(engine_group)

        self._engine_combo = QComboBox()
        self._engine_combo.addItems(["Cloud (DeepSeek)", "Local (Ollama)"])
        self._engine_combo.setCurrentIndex(0 if self._config_get("model.provider", "cloud") == "cloud" else 1)
        self._engine_combo.currentIndexChanged.connect(self._on_engine_changed)
        engine_layout.addWidget(self._engine_combo)

        key_row = QHBoxLayout()
        key_row.addWidget(QLabel("API Key:"))
        self._api_key_input = QLineEdit(self._config_get("model.cloud.api_key", ""))
        self._api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        key_row.addWidget(self._api_key_input)
        test_btn = QPushButton("Test")
        test_btn.clicked.connect(self._test_connection)
        key_row.addWidget(test_btn)
        engine_layout.addLayout(key_row)

        layout.addWidget(engine_group)

        # Floating window group.
        float_group = QGroupBox("Floating Window")
        float_layout = QVBoxLayout(float_group)

        self._hover_pause_check = QCheckBox("Pause countdown on hover")
        self._hover_pause_check.setChecked(self._config_get("floating_window.hover_pause_countdown", True))
        self._hover_pause_check.toggled.connect(lambda v: self._config_set("floating_window.hover_pause_countdown", v))
        float_layout.addWidget(self._hover_pause_check)

        self._hover_orig_check = QCheckBox("Hover shows original text")
        self._hover_orig_check.setChecked(self._config_get("floating_window.hover_show_original", True))
        self._hover_orig_check.toggled.connect(lambda v: self._config_set("floating_window.hover_show_original", v))
        float_layout.addWidget(self._hover_orig_check)

        self._show_orig_check = QCheckBox("Show original text section (default off)")
        self._show_orig_check.setChecked(self._config_get("floating_window.show_original_section", False))
        self._show_orig_check.toggled.connect(lambda v: self._config_set("floating_window.show_original_section", v))
        float_layout.addWidget(self._show_orig_check)

        self._focus_mode_check = QCheckBox("Pause floating window when main window is active (Focus Mode)")
        self._focus_mode_check.setChecked(self._config_get("focus_mode", True))
        self._focus_mode_check.toggled.connect(lambda v: self._config_set("focus_mode", v))
        float_layout.addWidget(self._focus_mode_check)

        layout.addWidget(float_group)

        layout.addStretch()
        return scroll

    # --- settings callbacks --------------------------------------------------------

    def _on_preset_changed(self, index: int) -> None:
        values = [10, 30, 100]
        self._slider.setValue(values[index])
        self._length_input.setText(str(values[index]))
        self._config_set("trigger_length", values[index])

    def _on_slider_changed(self, value: int) -> None:
        self._length_input.setText(str(value))
        self._config_set("trigger_length", value)

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

    def _test_connection(self) -> None:
        self._config_set("model.cloud.api_key", self._api_key_input.text().strip())
        QMessageBox.information(self, "Test", "Key saved. Connection test will be implemented in the next version.")

    # --- utils -------------------------------------------------------------------

    def refresh_all(self) -> None:
        self.refresh_dashboard()
        self.refresh_vocabulary()
        self.refresh_history()
