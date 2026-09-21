"""Determine whether a copied text is worth translating.

This is the first (and cheapest) layer of the intent pipeline. It uses
zero-cost local rules to reject content that should never reach the LLM.
"""

from __future__ import annotations

import re

# --- rejection rules ---------------------------------------------------------

_URL_RE = re.compile(
    r"(https?://|www\.)\S+", re.IGNORECASE
)
_IPV4_RE = re.compile(r"\b\d{1,3}(\.\d{1,3}){3}\b")
_NUMERIC_RE = re.compile(r"^\s*\d+([\s,.:;\-]\s*\d+)*\s*$")
_HEX_HASH_RE = re.compile(r"\b[0-9a-fA-F]{32,}\b")
_BASE64_RE = re.compile(r"\b[A-Za-z0-9+/=]{40,}\b")
_FILE_PATH_RE = re.compile(r"^[A-Za-z]:\\[\w\s.\-\\]+$")
_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")

_CODE_INDICATORS = (
    "{", "}", "=>", "->", "::", "#!", "<html", "</",
    "function ", "def ", "class ", "import ", "from ",
    "const ", "var ", "let ", "return ", "if (", "for (",
)

# Common programming-language keywords (for word-level code check).
_CODE_KEYWORDS = {
    "def", "class", "import", "from", "return", "lambda", "if", "elif",
    "else", "for", "while", "try", "except", "raise", "with", "yield",
    "async", "await", "function", "const", "let", "var", "new", "typeof",
    "interface", "type", "enum", "public", "private", "protected", "void",
}


def is_url(text: str) -> bool:
    """True if the text is essentially a URL or set of URLs."""
    stripped = text.strip()
    if not stripped:
        return False
    # If the entire text is a single URL, definitely skip.
    if _URL_RE.fullmatch(stripped):
        return True
    return False


def is_numeric(text: str) -> bool:
    """True for pure numbers, phone numbers, dates, and similar."""
    stripped = text.strip()
    if not stripped:
        return False
    if _NUMERIC_RE.fullmatch(stripped):
        return True
    if _IPV4_RE.fullmatch(stripped):
        return True
    return False


def is_code_like(text: str) -> bool:
    """Heuristic: does the text look like source code rather than prose?"""
    stripped = text.strip()
    if not stripped:
        return False

    lines = stripped.splitlines()
    if len(lines) == 0:
        return False

    # Single-line check: does it contain code indicators?
    if len(lines) <= 2:
        low = stripped.lower()
        for ind in _CODE_INDICATORS:
            if ind in low:
                return True
        # Check for heavy symbol density (common in code).
        symbol_count = sum(1 for c in stripped if c in "{}[]()<>|&=;+-*/")
        if symbol_count > len(stripped) * 0.3:
            return True
        # Single word that is a code keyword.
        words = stripped.split()
        if len(words) == 1 and words[0].lower() in _CODE_KEYWORDS:
            return True
        return False

    # Multi-line: check for code structure signals.
    code_lines = 0
    for line in lines:
        ls = line.strip()
        if not ls:
            continue
        low = ls.lower()
        if any(ind in low for ind in _CODE_INDICATORS):
            code_lines += 1
            continue
        # Lines starting with tab/spaces + code patterns.
        if re.match(r"^(import |from |def |class |const |var |let |return )", low):
            code_lines += 1
            continue
        # Heavy punctuation density typical of code.
        symbol_count = sum(1 for c in ls if c in "{}()[]=;|&<>+-*/")
        if len(ls) > 5 and symbol_count / len(ls) > 0.35:
            code_lines += 1

    total = sum(1 for l in lines if l.strip())
    return total > 0 and code_lines / total > 0.5


def is_file_path(text: str) -> bool:
    """True if the text looks like a Windows file path."""
    stripped = text.strip()
    if not stripped:
        return False
    return bool(_FILE_PATH_RE.match(stripped))


def is_binary_noise(text: str) -> bool:
    """True for hashes, base64 blobs, and other non-human-readable strings."""
    stripped = text.strip()
    if not stripped:
        return False
    if _HEX_HASH_RE.fullmatch(stripped):
        return True
    if _BASE64_RE.fullmatch(stripped):
        return True
    return False


def should_skip(text: str) -> bool:
    """Main entry: return True if the text should NOT be sent for translation."""
    return (
        is_url(text)
        or is_numeric(text)
        or is_code_like(text)
        or is_file_path(text)
        or is_binary_noise(text)
    )
