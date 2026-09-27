from __future__ import annotations

import pytest

from PySide6.QtWidgets import QApplication
from PySide6.QtWidgets import QToolButton

from src.xianjue.core.config import Config
from src.xianjue.providers.custom_cloud_provider import CustomCloudProvider
from src.xianjue.providers.factory import create_provider
from src.xianjue.ui.main_window import MainWindow


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture()
def window(qapp, tmp_path, monkeypatch):
    monkeypatch.setattr("src.xianjue.core.config._USER_PATH", tmp_path / "config.json")
    config = Config()
    window = MainWindow(
        config=config.get,
        config_set=config.set,
        on_translate_manual=lambda *args, **kwargs: None,
        db=type("DatabaseStub", (), {})(),
        refresh_provider=lambda: None,
    )
    window._set_settings_section("model")
    yield window
    window.deleteLater()


def test_model_config_is_visible_under_secondary_nav(window):
    assert window._settings_stack.count() == 3
    assert window._settings_stack.currentIndex() == 1
    assert window._model_type_combo is not None


def test_custom_config_saves_and_applies_active_provider(window):
    window._model_type_combo.setCurrentIndex(0)
    window._api_format_combo.setCurrentText("Chat Completions (/chat/completions)")
    window._api_base_input.setText("https://example.com/v1")
    window._api_key_input.setText("test-key")
    window._cloud_model_input.setText("demo-model")
    window._config_name_input.setText("Demo")

    window._save_cloud_config()
    configs = window._config_get("model.saved_cloud_configs")

    assert len(window._saved_config_rows) == 1
    assert configs[0]["name"] == "Demo"
    assert configs[0]["api_format"] == "chat_completions"
    assert window._config_get("model.active_config") == 0
    assert "Demo" in window._current_model_label.text()


def test_cloud_api_formats(window):
    texts = [
        window._api_format_combo.itemText(i)
        for i in range(window._api_format_combo.count())
    ]

    assert texts == [
        "Anthropic Messages (/v1/messages)",
        "Chat Completions (/chat/completions)",
        "Responses (/responses)",
    ]


def test_saved_config_rows_render_action_controls(window):
    window._model_type_combo.setCurrentIndex(0)
    window._api_format_combo.setCurrentText("Chat Completions (/chat/completions)")
    window._api_key_input.setText("test-key")
    window._cloud_model_input.setText("demo-model")
    window._config_name_input.setText("Demo")
    window._save_cloud_config()

    assert len(window._saved_config_rows) == 1
    row = window._saved_config_rows[0]
    assert row["row"].property("active") is True
    assert row["toggle"].isChecked() is True
    assert row["test"].text() == "测试"
    assert row["delete"].text() == ""

    window._set_active_cloud_config(0, False)
    assert window._config_get("model.active_config") is None
    assert window._saved_config_rows[0]["row"].property("active") is False


def test_saved_config_row_tests_saved_values(window, monkeypatch):
    window._model_type_combo.setCurrentIndex(0)
    window._api_key_input.setText("saved-key")
    window._cloud_model_input.setText("saved-model")
    window._config_name_input.setText("Saved")
    window._save_cloud_config()

    window._api_key_input.setText("changed-key")
    tested = []
    monkeypatch.setattr(window, "_test_cloud_config", lambda config: tested.append(config))

    window._test_saved_cloud_connection(0)

    assert tested[0]["api_key"] == "saved-key"


def test_cloud_fields_show_and_ollama_fields_hide(window):
    window._model_type_combo.setCurrentIndex(0)
    assert window._cloud_card.isVisibleTo(window._settings_stack)
    assert not window._ollama_card.isVisibleTo(window._settings_stack)

    window._model_type_combo.setCurrentIndex(1)
    assert not window._cloud_card.isVisibleTo(window._settings_stack)
    assert window._ollama_card.isVisibleTo(window._settings_stack)


def test_custom_provider_uses_saved_base_url():
    config_values = {
        "model.provider": "custom",
        "model.cloud.api_key": "test-key",
        "model.cloud.model": "demo-model",
        "model.cloud.base_url": "https://example.com/v1",
    }

    provider = create_provider(lambda path, default=None: config_values.get(path, default))

    assert type(provider).__name__ == "CustomCloudProvider"
    assert provider._api_format == "chat_completions"
    assert provider._sdk_base_url().rstrip("/").endswith("/v1")


def test_factory_reads_active_saved_config():
    config_values = {
        "model.provider": "custom",
        "model.active_config": 1,
        "model.saved_cloud_configs": [
            {"api_format": "chat_completions", "base_url": "https://old.example.com", "model": "old"},
            {
                "api_format": "anthropic_messages",
                "base_url": "https://api.anthropic.com",
                "api_key": "test-key",
                "model": "claude-3-haiku",
            },
        ],
    }

    provider = create_provider(lambda path, default=None: config_values.get(path, default))

    assert isinstance(provider, CustomCloudProvider)
    assert provider._api_format == "anthropic_messages"
    assert provider._anthropic_endpoint().endswith("/v1/messages")


def test_saved_config_delete(window):
    window._model_type_combo.setCurrentIndex(0)
    window._api_key_input.setText("test-key")
    window._cloud_model_input.setText("demo-model")
    window._config_name_input.setText("Demo")
    window._save_cloud_config()
    window._delete_cloud_config(0)

    assert len(window._saved_config_rows) == 0
    assert window._config_get("model.active_config") is None
    assert window._config_get("model.saved_cloud_configs", []) == []
