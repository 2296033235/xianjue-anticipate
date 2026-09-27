from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

import pytest
import threading

from PySide6.QtWidgets import QApplication

from src.xianjue.app import XianJueApp
from src.xianjue.providers.base import TranslationResult


class ImmediateCaller:
    def call(self, fn) -> None:
        fn()


class FakePipeline:
    def __init__(self, provider=None) -> None:
        self._provider = provider

    @property
    def provider(self):
        return self._provider

    @provider.setter
    def provider(self, value):
        self._provider = value


class FakeDatabase:
    def __init__(self) -> None:
        self.history = []

    def add_history(self, source, target, source_lang, target_lang, engine):
        self.history.append((source, target, source_lang, target_lang, engine))


class FakeMainWindow:
    def __init__(self) -> None:
        self.results = []
        self.errors = []
        self.result_event = threading.Event()
        self.error_event = threading.Event()

    def show_manual_result(self, result, source_text):
        self.results.append((result, source_text))
        self.result_event.set()

    def show_manual_error(self, error):
        self.errors.append(error)
        self.error_event.set()


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture()
def fake_app():
    app = SimpleNamespace(
        provider=None,
        config_get=lambda key, default=None: default,
        db=FakeDatabase(),
        _caller=ImmediateCaller(),
        main_window=FakeMainWindow(),
        pipeline=FakePipeline(),
    )
    return app


def test_refresh_provider_updates_pipeline_provider(fake_app, monkeypatch):
    provider = object()
    monkeypatch.setattr("src.xianjue.app.create_provider", lambda config_get: provider)

    XianJueApp._refresh_provider(fake_app)

    assert fake_app.provider is provider
    assert fake_app.pipeline._provider is provider


def test_manual_translation_uses_provider_and_shows_result(fake_app, monkeypatch):
    provider = Mock()
    provider.translate.return_value = TranslationResult(
        translation="你好",
        engine="Custom (demo-model)",
        structured=True,
    )
    monkeypatch.setattr("src.xianjue.app.create_provider", lambda config_get: provider)

    XianJueApp._on_manual_translate(fake_app, "hello", "en", "zh")

    assert fake_app.main_window.result_event.wait(2)
    provider.translate.assert_called_once()
    assert fake_app.main_window.results[0][0].translation == "你好"
    assert fake_app.main_window.results[0][1] == "hello"
    assert fake_app.db.history[0] == (
        "hello",
        "你好",
        "en",
        "zh",
        "Custom (demo-model)",
    )


def test_manual_translation_shows_error_when_provider_fails(fake_app, monkeypatch):
    provider = Mock()
    provider.translate.side_effect = RuntimeError("bad request")
    monkeypatch.setattr("src.xianjue.app.create_provider", lambda config_get: provider)

    XianJueApp._on_manual_translate(fake_app, "hello", "en", "zh")

    assert fake_app.main_window.error_event.wait(2)
    assert fake_app.main_window.errors[0] == "bad request"
    assert fake_app.db.history == []
