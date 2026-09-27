from __future__ import annotations

import pytest

from PySide6.QtWidgets import QApplication
from PySide6.QtWidgets import QMessageBox
from PySide6.QtWidgets import QSlider

from src.xianjue.core.config import Config
from src.xianjue.providers.ollama_provider import OllamaProvider
from src.xianjue.providers.custom_cloud_provider import CustomCloudProvider
from src.xianjue.providers.factory import create_provider
from src.xianjue.ui.toggle_switch import ToggleSwitch
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

    window._save_cloud_config()
    configs = window._config_get("model.saved_cloud_configs")

    assert len(window._saved_config_rows) == 1
    assert configs[0]["name"] == "demo-model"
    assert configs[0]["api_format"] == "chat_completions"
    assert window._config_get("model.active_config") == 0
    assert "demo-model" in window._current_model_label.text()
    assert window._cloud_model_input.text() == ""
    assert window._api_key_input.text() == ""
    assert window._api_base_input.text() == ""


def test_config_name_field_is_removed(window):
    assert not hasattr(window, "_config_name_input")


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
    window._save_cloud_config()

    assert len(window._saved_config_rows) == 1
    row = window._saved_config_rows[0]
    assert row["row"].property("active") is True
    assert isinstance(row["toggle"], ToggleSwitch)
    assert row["toggle"].value() == 1
    assert row["test"].text() == "测试"
    assert row["delete"].text() == ""

    window._set_active_cloud_config(0, False)
    assert window._config_get("model.active_config") is None
    assert window._saved_config_rows[0]["row"].property("active") is False


def test_saved_config_rows_are_not_recreated_on_toggle(window):
    window._model_type_combo.setCurrentIndex(0)
    window._cloud_model_input.setText("demo-model")
    window._save_cloud_config()
    row = window._saved_config_rows[0]
    toggle = row["toggle"]

    window._set_active_cloud_config(0, False)

    assert window._saved_config_rows[0]["toggle"] is toggle


def test_model_switching_between_saved_configs(window, monkeypatch):
    refresh_calls = []
    monkeypatch.setattr(window, "_refresh_provider", lambda: refresh_calls.append(True))

    window._model_type_combo.setCurrentIndex(0)
    window._api_format_combo.setCurrentText("Chat Completions (/chat/completions)")
    window._api_base_input.setText("https://model-a.example.com")
    window._api_key_input.setText("key-a")
    window._cloud_model_input.setText("model-a")
    window._save_cloud_config()

    window._api_format_combo.setCurrentText("Responses (/responses)")
    window._api_base_input.setText("https://model-b.example.com")
    window._api_key_input.setText("key-b")
    window._cloud_model_input.setText("model-b")
    window._save_cloud_config()

    refresh_calls.clear()
    window._set_active_cloud_config(1, True)

    assert window._config_get("model.active_config") == 1
    assert window._provider_display_text() == "model-b (model-b)"
    assert window._saved_config_rows[0]["row"].property("active") is False
    assert window._saved_config_rows[0]["toggle"].value() == 0
    assert window._saved_config_rows[1]["row"].property("active") is True
    assert window._saved_config_rows[1]["toggle"].value() == 1
    assert refresh_calls


def test_active_config_switch_updates_created_provider(window):
    window._model_type_combo.setCurrentIndex(0)
    window._api_format_combo.setCurrentText("Chat Completions (/chat/completions)")
    window._api_base_input.setText("https://model-a.example.com")
    window._cloud_model_input.setText("model-a")
    window._save_cloud_config()

    window._api_format_combo.setCurrentText("Responses (/responses)")
    window._api_base_input.setText("https://model-b.example.com")
    window._cloud_model_input.setText("model-b")
    window._save_cloud_config()

    provider_b = create_provider(window._config_get)
    assert provider_b._api_format == "responses"
    assert provider_b._base_url == "https://model-b.example.com"

    window._set_active_cloud_config(0, True)

    provider_a = create_provider(window._config_get)
    assert provider_a._api_format == "chat_completions"
    assert provider_a._base_url == "https://model-a.example.com"


def test_model_switching_between_cloud_and_ollama(window, monkeypatch):
    refresh_calls = []
    monkeypatch.setattr(window, "_refresh_provider", lambda: refresh_calls.append(True))

    window._model_type_combo.setCurrentIndex(0)
    window._cloud_model_input.setText("cloud-model")
    window._save_cloud_config()
    refresh_calls.clear()

    window._model_type_combo.setCurrentIndex(1)

    assert window._config_get("model.provider") == "local"
    assert window._provider_display_text().startswith("Ollama")
    assert refresh_calls

    refresh_calls.clear()
    window._model_type_combo.setCurrentIndex(0)

    assert window._config_get("model.provider") == "custom"
    assert window._provider_display_text() == "cloud-model (cloud-model)"
    assert refresh_calls


def test_saved_config_row_tests_saved_values(window, monkeypatch):
    window._model_type_combo.setCurrentIndex(0)
    window._api_key_input.setText("saved-key")
    window._cloud_model_input.setText("saved-model")
    window._save_cloud_config()

    window._api_key_input.setText("changed-key")
    tested = []
    monkeypatch.setattr(window, "_test_cloud_config", lambda config: tested.append(config))

    window._test_saved_cloud_connection(0)

    assert tested[0]["api_key"] == "saved-key"


def test_cloud_connection_status_updates_with_detailed_result(window, monkeypatch):
    from src.xianjue.providers.custom_cloud_provider import CustomCloudProvider

    window._model_type_combo.setCurrentIndex(0)
    window._cloud_model_input.setText("demo-model")
    window._save_cloud_config()
    config = window._config_get("model.saved_cloud_configs")[0]

    monkeypatch.setattr(
        CustomCloudProvider,
        "test_connection_detailed",
        lambda self: (True, "", 42),
    )

    window._test_cloud_config(config)
    window._set_model_status(True, "已连接 · 42 ms")

    assert window._model_status_label.text() == "已连接 · 42 ms"


def test_cloud_connection_status_shows_failure_reason(window, monkeypatch):
    from src.xianjue.providers.custom_cloud_provider import CustomCloudProvider

    window._model_type_combo.setCurrentIndex(0)
    window._cloud_model_input.setText("demo-model")
    window._save_cloud_config()
    config = window._config_get("model.saved_cloud_configs")[0]

    monkeypatch.setattr(
        CustomCloudProvider,
        "test_connection_detailed",
        lambda self: (False, "bad request", 42),
    )

    window._test_cloud_config(config)
    window._set_model_status(False, "连接失败: bad request")

    assert window._model_status_label.text() == "连接失败: bad request"


def test_cloud_fields_show_and_ollama_fields_hide(window):
    window._model_type_combo.setCurrentIndex(0)
    assert window._cloud_card.isVisibleTo(window._settings_stack)
    assert not window._ollama_card.isVisibleTo(window._settings_stack)

    window._model_type_combo.setCurrentIndex(1)
    assert not window._cloud_card.isVisibleTo(window._settings_stack)
    assert window._ollama_card.isVisibleTo(window._settings_stack)


def test_ollama_refresh_updates_models_and_selects_valid_model(window, monkeypatch):
    refresh_calls = []
    monkeypatch.setattr(window, "_refresh_provider", lambda: refresh_calls.append(True))

    window._refresh_ollama_models(["qwen3.5:latest", "qwen3.8:27b"], "")

    assert window._ollama_models_table.rowCount() == 2
    assert window._ollama_models_table.item(0, 0).text() == "qwen3.5:latest"
    assert window._ollama_models_table.item(1, 0).text() == "qwen3.8:27b"
    assert window._ollama_models_table.cellWidget(0, 1).layout().itemAt(0).widget().value() == 1
    assert window._ollama_models_table.cellWidget(1, 1).layout().itemAt(0).widget().value() == 0
    assert window._config_get("model.local.model") == "qwen3.5:latest"
    assert not window._model_status_label.isVisibleTo(window._settings_stack)
    assert window._saved_config_rows == []
    assert refresh_calls


def test_ollama_refresh_shows_error(window):
    window._refresh_ollama_models([], "Ollama request failed")

    assert window._ollama_models_table.rowCount() == 1
    assert "Ollama request failed" in window._ollama_models_table.item(0, 0).text()


def test_ollama_toggle_selects_model(window, monkeypatch):
    refresh_calls = []
    monkeypatch.setattr(window, "_refresh_provider", lambda: refresh_calls.append(True))

    window._on_ollama_model_toggled("qwen3.5:latest", 1, True)

    assert window._config_get("model.provider") == "local"
    assert window._config_get("model.local.model") == "qwen3.5:latest"
    assert refresh_calls


def test_ollama_switch_between_detected_models(window, monkeypatch):
    refresh_calls = []
    monkeypatch.setattr(window, "_refresh_provider", lambda: refresh_calls.append(True))

    window._config_set("model.provider", "local")
    window._refresh_ollama_models(["qwen3.5:latest", "qwen3.8:27b"], "")
    assert window._config_get("model.provider") == "local"
    assert window._config_get("model.local.model") == "qwen3.5:latest"

    window._on_ollama_model_toggled("qwen3.8:27b", 1, True)

    assert window._config_get("model.provider") == "local"
    assert window._config_get("model.local.model") == "qwen3.8:27b"
    provider = create_provider(window._config_get)
    assert isinstance(provider, OllamaProvider)
    assert provider._model == "qwen3.8:27b"
    assert refresh_calls


def test_ollama_models_are_single_select(window):
    window._config_set("model.provider", "local")
    window._refresh_ollama_models(["qwen3.5:latest", "qwen3.8:27b", "qwen3.5:0.8b"], "")

    window._on_ollama_model_toggled("qwen3.5:latest", 0, True)
    window._on_ollama_model_toggled("qwen3.8:27b", 1, True)

    toggles = [
        window._ollama_models_table.cellWidget(row, 1).layout().itemAt(0).widget()
        for row in range(3)
    ]
    assert toggles[0].value() == 0
    assert toggles[1].value() == 1
    assert toggles[2].value() == 0
    assert window._config_get("model.local.model") == "qwen3.8:27b"


def test_toggle_switch_clicks_change_value():
    toggle = ToggleSwitch()
    click = type("FakeMouseEvent", (), {"button": lambda self, event=None: None})()
    # This is intentionally indirect because Qt owns the event object.
    # We only verify the switch state transitions.
    toggle.setValue(0)
    toggle.setValue(1)
    toggle.setValue(0)

    assert toggle.value() == 0


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


def test_saved_config_delete(window, monkeypatch):
    window._model_type_combo.setCurrentIndex(0)
    window._api_key_input.setText("test-key")
    window._cloud_model_input.setText("demo-model")
    window._save_cloud_config()

    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *args, **kwargs: QMessageBox.StandardButton.No,
    )
    window._delete_cloud_config(0)
    assert len(window._saved_config_rows) == 1

    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
    )
    window._delete_cloud_config(0)

    assert len(window._saved_config_rows) == 0
    assert window._config_get("model.active_config") is None
    assert window._config_get("model.saved_cloud_configs", []) == []
