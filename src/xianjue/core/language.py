"""Language detection using lingua-py with graceful fallback."""

from __future__ import annotations

_LANG_MAP = {
    "CHINESE": "zh",
    "ENGLISH": "en",
    "JAPANESE": "ja",
    "KOREAN": "ko",
    "FRENCH": "fr",
    "GERMAN": "de",
    "SPANISH": "es",
    "RUSSIAN": "ru",
}

# CJK character ranges for a cheap pre-check (faster than full lingua).
_CJK_RE = __import__("re").compile(r"[\u4e00-\u9fff]")
_HIRAGANA_RE = __import__("re").compile(r"[\u3040-\u309f\u30a0-\u30ff]")
_HANGUL_RE = __import__("re").compile(r"[\uac00-\ud7af]")
_CYRILLIC_RE = __import__("re").compile(r"[\u0400-\u04ff]")
_LATIN_RE = __import__("re").compile(r"[a-zA-Z]")


def detect_language(text: str) -> str:
    """Return a short language code ('zh', 'en', ...) or 'unknown'."""
    if not text or not text.strip():
        return "unknown"

    # Cheap CJK check first (handles most use cases without loading lingua).
    cjk_count = len(_CJK_RE.findall(text))
    hiragana_count = len(_HIRAGANA_RE.findall(text))
    hangul_count = len(_HANGUL_RE.findall(text))
    cyrillic_count = len(_CYRILLIC_RE.findall(text))
    latin_count = len(_LATIN_RE.findall(text))

    if hangul_count > latin_count * 0.3:
        return "ko"
    if hiragana_count > latin_count * 0.3:
        return "ja"
    if cjk_count > latin_count * 0.3:
        return "zh"
    if cyrillic_count > latin_count * 0.3:
        return "ru"

    # For Latin-script text, try lingua for precision (fr, de, es, etc.).
    if latin_count > 10:
        try:
            from lingua import Language, LanguageDetectorBuilder
            detector = LanguageDetectorBuilder.from_all_languages().build()
            detected = detector.detect_language_of(text)
            if detected:
                name = str(detected).split(".")[-1]  # e.g. "Language.ENGLISH"
                code = _LANG_MAP.get(name.upper(), None)
                if code:
                    return code
        except Exception:
            pass

    # Default: assume English for Latin text.
    if latin_count > 0:
        return "en"

    return "unknown"

