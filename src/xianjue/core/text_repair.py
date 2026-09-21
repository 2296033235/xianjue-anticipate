"""Repair text extracted from PDFs and other sources before translation.

PDF text extraction commonly produces:
  - hyphenated line breaks: "fine-\ntuned" -> "fine-tuned"
  - missing spaces at line breaks: "on alarge dataset"
  - excessive internal newlines within sentences
  - ligature characters: U+FB00..U+FB04

This module normalises those artefacts so the LLM receives clean input.
"""

from __future__ import annotations

import re
import unicodedata

_LIGATURE_MAP = {
    "\uFB00": "ff", "\uFB01": "fi", "\uFB02": "fl",
    "\uFB03": "ffi", "\uFB04": "ffl",
}

# Hyphen at end of line followed by newline: merge the two halves,
# keeping the hyphen (safe for compound words like "fine-tuned").
_DEHYPHENATE = re.compile(r"(\w)-\n(\w)")

# Newline between two Latin word characters without punctuation on either
# side: assume a missing space (PDF line break inside a sentence).
_JOIN_WORDS = re.compile(r"(\w)\n(\w)")

# Multiple spaces / tabs -> single space.
_COLLAPSE_WS = re.compile(r"[ \t]+")

# Blank lines between paragraphs -> single newline (keep paragraph breaks).
_PARA_BREAK = re.compile(r"\n\s*\n")


def repair(text: str) -> str:
    """Normalise common PDF copy artefacts while preserving paragraph structure."""
    if not text:
        return text

    # Unicode NFKC normalisation handles most ligatures and compatibility chars.
    text = unicodedata.normalize("NFKC", text)
    for src, dst in _LIGATURE_MAP.items():
        text = text.replace(src, dst)

    # "fine-\ntuned" -> "fine-tuned" (keep the hyphen)
    text = _DEHYPHENATE.sub(r"\1-\2", text)

    # "fine-\n\ntuned" (blank line inside a hyphenated word, rare but happens)
    text = re.sub(r"(\w)-\n\s*\n(\w)", r"\1-\2", text)

    # "on alarge dataset" -> "on a large dataset"
    text = _JOIN_WORDS.sub(r"\1 \2", text)

    # Collapse runs of spaces/tabs.
    text = _COLLAPSE_WS.sub(" ", text)

    # Collapse multiple blank lines into a single paragraph break.
    text = _PARA_BREAK.sub("\n\n", text)

    return text.strip()
