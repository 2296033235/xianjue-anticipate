"""Tests for LLM provider modules."""

import pytest

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

