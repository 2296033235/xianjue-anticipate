"""Unit tests for core modules (text repair, intent filter, language detection)."""

import pytest
import threading

from src.xianjue.providers.base import TranslationResult
from src.xianjue.core.text_repair import repair
from src.xianjue.core.intent_filter import (
    is_url, is_numeric, is_code_like, is_file_path, is_binary_noise, should_skip,
)
from src.xianjue.core.language import detect_language
from src.xianjue.core.pipeline import TranslationPipeline


class TestTextRepair:
    def test_dehyphenate_keeps_hyphen(self):
        assert repair("fine-\ntuned") == "fine-tuned"

    def test_dehyphenate_multiline(self):
        assert repair("fine-\n\ntuned") == "fine-tuned"

    def test_join_line_break_words(self):
        assert repair("on\na large") == "on a large"

    def test_ligature_fi(self):
        assert repair("\ufb01ne") == "fine"

    def test_ligature_ffl(self):
        assert repair("ba\ufb04e") == "baffle"

    def test_full_pdf_sentence(self):
        result = repair("The model was fine-\ntuned on\na large dataset with \ufb01ne-grained\nfeatures.")
        assert result == "The model was fine-tuned on a large dataset with fine-grained features."

    def test_paragraph_preserved(self):
        text = "First paragraph.\n\nSecond paragraph."
        assert repair(text) == "First paragraph.\n\nSecond paragraph."

    def test_empty(self):
        assert repair("") == ""


class TestIntentFilter:
    def test_url_rejected(self):
        assert is_url("https://example.com/path?q=1")
        assert is_url("http://www.example.org")

    def test_url_with_text_not_rejected(self):
        assert not is_url("The https:// protocol is widely used")

    def test_numeric_rejected(self):
        assert is_numeric("123-456-7890")
        assert is_numeric("192.168.1.1")
        assert is_numeric("12345678")

    def test_numeric_with_text_not_rejected(self):
        assert not is_numeric("The answer is 42")

    def test_code_rejected(self):
        assert is_code_like("def hello():")
        assert is_code_like("const x = {a: 1};")
        assert is_code_like("import numpy as np")

    def test_prose_not_code(self):
        assert not is_code_like("The weather is nice today")

    def test_file_path(self):
        assert is_file_path("C:\\Users\\test\\document.pdf")
        assert not is_file_path("This is a regular sentence.")

    def test_binary_noise(self):
        assert is_binary_noise("a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6")

    def test_should_skip_aggregate(self):
        assert should_skip("https://github.com/user/repo")
        assert should_skip("12345678")
        assert should_skip("def main(): return 42")
        assert should_skip("C:\\Users\\test\\file.txt")
        assert not should_skip("This is a normal English sentence to translate.")


class TestLanguageDetection:
    def test_english(self):
        assert detect_language("Hello, this is English text.") == "en"

    def test_chinese(self):
        assert detect_language("这是一段中文文本") == "zh"

    def test_unknown(self):
        assert detect_language("") == "unknown"
        assert detect_language("   ") == "unknown"


class TestPipelineProviderSwitching:
    def test_provider_property_updates_active_provider(self):
        old_provider = object()
        new_provider = object()
        pipeline = TranslationPipeline(
            config_get=lambda key, default=None: default,
            provider=old_provider,
            on_result=lambda *args, **kwargs: None,
        )

        pipeline.provider = new_provider

        assert pipeline._provider is new_provider

    def test_manual_translation_uses_active_provider(self):
        class FakeProvider:
            def translate(
                self,
                text: str,
                source_lang: str = "auto",
                target_lang: str = "zh",
                detailed: bool = False,
            ) -> TranslationResult:
                return TranslationResult(
                    translation="你好",
                    engine=f"Fake ({text})",
                    structured=detailed,
                )

        provider = FakeProvider()
        pipeline = TranslationPipeline(
            config_get=lambda key, default=None: default,
            provider=provider,
            on_result=lambda *args, **kwargs: None,
        )
        done = threading.Event()
        captured = {}

        def on_result(result, source_text):
            captured["result"] = result
            captured["source_text"] = source_text
            done.set()

        pipeline.translate_manual("hello", source_lang="en", target_lang="zh", callback=on_result)

        assert done.wait(2)
        assert captured["result"].translation == "你好"
        assert captured["source_text"] == "hello"
