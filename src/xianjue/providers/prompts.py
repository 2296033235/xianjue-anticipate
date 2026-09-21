"""Shared prompt templates for translation."""

TRANSLATION_QUICK_PROMPT = """\
Translate the following text to {target_lang}. Output ONLY the translation, no explanations, no extra text.

Text: {text}
"""

TRANSLATION_PROMPT = """\
You are a professional translator. Translate the following text to {target_lang}.

Rules:
1. Provide a natural, accurate translation.
2. Identify up to 5 key technical terms with brief Chinese explanations.
3. Break the text into sentence pairs (source sentence, translated sentence).
4. Provide a word-level mapping for content words only (nouns, verbs, adjectives).
5. Output ONLY valid JSON in exactly this format, no other text:
{{
  "translation": "<full translation>",
  "terms": [
    {{"original": "<term>", "translation": "<term in Chinese>", "explanation": "<brief explanation>"}}
  ],
  "sentence_pairs": [
    {{"source": "<source sentence>", "target": "<translated sentence>"}}
  ],
  "word_map": [
    {{"source_word": "<word>", "target_word": "<translated word>"}}
  ]
}}

Text to translate:
{text}
"""

CHAT_PROMPT = """\
You are a helpful assistant. Respond in {target_lang}.

User: {message}
"""
