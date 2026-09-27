from __future__ import annotations

import pytest

from PySide6.QtWidgets import QApplication

from src.xianjue.core.config import Config
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
    window._api_format_combo.setCurrentText("OpenAI compatible")
    window._api_base_input.setText("https://example.com/v1")
    window._api_key_input.setText("test-key")
    window._cloud_model_input.setText("demo-model")
    window._config_name_input.setText("Demo")

    window._save_cloud_config()
    configs = window._config_get("model.saved_cloud_configs")

    assert window._saved_configs_table.rowCount() == 1
    assert configs[0]["name"] == "Demo"
    assert configs[0]["api_format"] == "openai_compatible"
    assert window._config_get("model.active_config") == 0
    assert "Demo" in window._current_model_label.text()


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

    assert type(provider).__name__ == "OpenAICompatibleProvider"
    assert provider._client.base_url.path.rstrip("/").endswith("/v1")


def test_saved_config_delete(window):
    window._model_type_combo.setCurrentIndex(0)
    window._api_key_input.setText("test-key")
    window._cloud_model_input.setText("demo-model")
    window._config_name_input.setText("Demo")
    window._save_cloud_config()
    window._delete_cloud_config(0)

    assert window._saved_configs_table.rowCount() == 0
    assert window._config_get("model.active_config") is None
    assert window._config_get("model.saved_cloud_configs", []) == []
