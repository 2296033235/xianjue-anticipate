"""Tests for LLM provider modules."""

import pytest

from src.xianjue.providers.custom_cloud_provider import CustomCloudProvider
from src.xianjue.providers.deepseek_provider import _parse_structured
from src.xianjue.providers.ollama_provider import OllamaProvider


class TestParseStructured:
    def test_direct_json(self):
        raw = '{"translation": "hello"}'
        result = _parse_structured(raw)
        assert result["translation"] == "hello"

    def test_json_in_prose(self):
        raw = 'Here is the result:\n{"translation": "hello"}\nDone.'
        result = _parse_structured(raw)
        assert result["translation"] == "hello"

    def test_json_in_code_block(self):
        raw = '```json\n{"translation": "hello"}\n```'
        result = _parse_structured(raw)
        assert result["translation"] == "hello"

    def test_invalid_returns_empty(self):
        assert _parse_structured("not json at all") == {}


class TestOllamaConnection:
    def test_connection(self):
        provider = OllamaProvider()
        # This test requires Ollama to be running locally.
        # Skip if not available.
        try:
            assert provider.test_connection()
        except Exception:
            pytest.skip("Ollama not running")

    def test_list_models_detailed_reports_models(self, monkeypatch):
        provider = OllamaProvider(host="http://localhost:11434")

        class FakeResponse:
            status_code = 200

            def json(self):
                return {"models": [{"name": "qwen3.5:latest"}]}

        monkeypatch.setattr("httpx.get", lambda *args, **kwargs: FakeResponse())

        models, error, latency_ms = provider.list_models_detailed()

        assert models == ["qwen3.5:latest"]
        assert error == ""
        assert latency_ms >= 0

    def test_list_models_detailed_reports_error(self, monkeypatch):
        provider = OllamaProvider(host="http://localhost:11434")

        class FakeResponse:
            status_code = 500

            def json(self):
                return {"error": "Ollama request failed"}

        monkeypatch.setattr("httpx.get", lambda *args, **kwargs: FakeResponse())

        models, error, latency_ms = provider.list_models_detailed()

        assert models == []
        assert error == "Ollama request failed"
        assert latency_ms >= 0


class TestCustomCloudProvider:
    def test_connection_detailed_reports_success_and_latency(self, monkeypatch):
        provider = CustomCloudProvider(
            api_key="test-key",
            model="demo-model",
            base_url="https://example.com/v1",
            api_format="chat_completions",
        )
        monkeypatch.setattr(provider, "_request", lambda *args, **kwargs: "pong")

        ok, error, latency_ms = provider.test_connection_detailed()

        assert ok is True
        assert error == ""
        assert latency_ms >= 0

    def test_connection_detailed_reports_error(self, monkeypatch):
        provider = CustomCloudProvider(
            api_key="test-key",
            model="demo-model",
            base_url="https://example.com/v1",
            api_format="chat_completions",
        )

        def fail(*args, **kwargs):
            raise RuntimeError("bad request")

        monkeypatch.setattr(provider, "_request", fail)

        ok, error, latency_ms = provider.test_connection_detailed()

        assert ok is False
        assert error == "bad request"
        assert latency_ms >= 0

    def test_connection_detailed_shows_http_error_code(self, monkeypatch):
        provider = CustomCloudProvider(
            api_key="test-key",
            model="demo-model",
            base_url="https://api.example.com/anthropic",
            api_format="anthropic_messages",
        )

        class FakeResponse:
            status_code = 401
            text = ""

            def json(self):
                return {
                    "error": {
                        "type": "invalid_request_error",
                        "message": "invalid api key",
                    }
                }

        monkeypatch.setattr("httpx.post", lambda *args, **kwargs: FakeResponse())

        ok, error, latency_ms = provider.test_connection_detailed()

        assert ok is False
        assert error == "HTTP 401"
        assert latency_ms >= 0

    def test_connection_detailed_shows_empty_response_code(self, monkeypatch):
        provider = CustomCloudProvider(
            api_key="test-key",
            model="demo-model",
            base_url="https://api.example.com/anthropic",
            api_format="anthropic_messages",
        )

        class FakeResponse:
            status_code = 200

            def json(self):
                return {"content": []}

        monkeypatch.setattr("httpx.post", lambda *args, **kwargs: FakeResponse())

        ok, error, latency_ms = provider.test_connection_detailed()

        assert ok is False
        assert error == "HTTP 200"
        assert latency_ms >= 0

    def test_translate_parses_structured_response(self, monkeypatch):
        provider = CustomCloudProvider(
            api_key="test-key",
            model="demo-model",
            base_url="https://example.com/v1",
            api_format="responses",
        )
        captured = []

        def fake_request(prompt, system, max_tokens, timeout=30.0):
            captured.append((prompt, system, max_tokens, timeout))
            return '{"translation": "你好", "terms": [{"original": "hello", "translation": "你好", "explanation": "问候"}]}'

        monkeypatch.setattr(provider, "_request", fake_request)

        result = provider.translate("hello", source_lang="en", target_lang="zh", detailed=True)

        assert result.translation == "你好"
        assert result.structured is True
        assert result.terms[0]["original"] == "hello"
        assert "hello" in captured[0][0]
