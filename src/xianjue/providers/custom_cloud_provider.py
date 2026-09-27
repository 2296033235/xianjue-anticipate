"""Cloud translation through configurable LLM API formats."""

from __future__ import annotations

import time

import httpx
from openai import OpenAI

from .base import LLMProvider, TranslationResult
from .deepseek_provider import _LANG_NAMES, _parse_structured
from .prompts import TRANSLATION_PROMPT, TRANSLATION_QUICK_PROMPT


class CustomCloudProvider(LLMProvider):
    """Run one of the three cloud request formats supported by the settings UI."""

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str,
        api_format: str = "chat_completions",
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._api_format = api_format

    @property
    def name(self) -> str:
        return f"Custom ({self._model})"

    @property
    def api_format(self) -> str:
        return self._api_format

    def _sdk_base_url(self) -> str:
        base = self._base_url.rstrip("/")
        return base if base.endswith("/v1") else f"{base}/v1"

    def _anthropic_endpoint(self) -> str:
        base = self._base_url.rstrip("/")
        return f"{base}/messages" if base.endswith("/v1") else f"{base}/v1/messages"

    def _chat_completions(
        self,
        messages: list[dict],
        max_tokens: int,
        timeout: float = 30.0,
    ) -> str:
        client = OpenAI(api_key=self._api_key, base_url=self._sdk_base_url())
        response = client.chat.completions.create(
            model=self._model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.3,
            timeout=timeout,
        )
        return response.choices[0].message.content or ""

    def _responses(
        self,
        messages: list[dict],
        max_tokens: int,
        timeout: float = 30.0,
    ) -> str:
        client = OpenAI(api_key=self._api_key, base_url=self._sdk_base_url())
        response = client.responses.create(
            model=self._model,
            input=messages,
            max_output_tokens=max_tokens,
            timeout=timeout,
        )
        if getattr(response, "output_text", None):
            return response.output_text

        parts: list[str] = []
        for item in getattr(response, "output", []):
            content = (
                item.get("content", [])
                if isinstance(item, dict)
                else getattr(item, "content", [])
            )
            for part in content:
                text = (
                    part.get("text", "")
                    if isinstance(part, dict)
                    else getattr(part, "text", "")
                )
                if text:
                    parts.append(text)
        return "".join(parts)

    def _anthropic_messages(
        self,
        messages: list[dict],
        max_tokens: int,
        system: str | None = None,
        timeout: float = 30.0,
    ) -> str:
        payload: dict = {
            "model": self._model,
            "max_tokens": max_tokens,
            "messages": messages,
        }
        if system:
            payload["system"] = system

        response = httpx.post(
            self._anthropic_endpoint(),
            headers={
                "x-api-key": self._api_key,
                "anthropic-version": "2023-06-01",
            },
            json=payload,
            timeout=timeout,
        )
        status_code = response.status_code
        if status_code >= 400:
            data = response.json()
            code, message = self._error_fields(data)
            raise ValueError(
                self._format_api_error(
                    status_code,
                    code,
                    message,
                    response.text or "API error",
                )
            )

        data = response.json()
        content = data.get("content", [])
        raw = "".join(
            part.get("text", "")
            for part in content
            if isinstance(part, dict) and part.get("type") == "text"
        )
        if raw:
            return raw

        code, message = self._error_fields(data)
        raise ValueError(
            self._format_api_error(status_code, code, message, "Empty response")
        )

    @staticmethod
    def _error_fields(data: object) -> tuple[str, str]:
        if not isinstance(data, dict):
            return "", ""
        error = data.get("error")
        if not isinstance(error, dict):
            if error:
                return str(error), ""
            return "", ""
        code = str(error.get("code") or error.get("type") or "")
        message = str(error.get("message") or "")
        return code, message

    @staticmethod
    def _format_api_error(
        status_code: int,
        code: str,
        message: str,
        fallback: str,
    ) -> str:
        parts = [f"HTTP {status_code}"]
        if code:
            parts.append(code)
        if message:
            parts.append(message)
        if not code and not message:
            parts.append(fallback)
        return " · ".join(parts)

    def _request(
        self,
        prompt: str,
        system: str | None,
        max_tokens: int,
        timeout: float = 30.0,
    ) -> str:
        if self._api_format == "anthropic_messages":
            messages = [{"role": "user", "content": prompt}]
            return self._anthropic_messages(
                messages,
                max_tokens,
                system=system,
                timeout=timeout,
            )

        messages = (
            [{"role": "system", "content": system}, {"role": "user", "content": prompt}]
            if system
            else [{"role": "user", "content": prompt}]
        )
        if self._api_format == "responses":
            return self._responses(messages, max_tokens, timeout=timeout)
        return self._chat_completions(messages, max_tokens, timeout=timeout)

    def test_connection(self) -> bool:
        ok, _, _ = self.test_connection_detailed()
        return ok

    def test_connection_detailed(self) -> tuple[bool, str, float]:
        start = time.monotonic()
        try:
            raw = self._request("ping", None, 5, timeout=3.0).strip()
            latency_ms = int((time.monotonic() - start) * 1000)
            return bool(raw), "" if raw else "Empty response", latency_ms
        except Exception as exc:
            latency_ms = int((time.monotonic() - start) * 1000)
            return False, self._format_exception_error(exc), latency_ms

    def translate(
        self,
        text: str,
        source_lang: str = "auto",
        target_lang: str = "zh",
        timeout: float = 15.0,
        detailed: bool = False,
    ) -> TranslationResult:
        start = time.monotonic()
        target_name = _LANG_NAMES.get(target_lang, target_lang)

        if not detailed:
            prompt = TRANSLATION_QUICK_PROMPT.format(target_lang=target_name, text=text)
            raw = self._request(prompt, None, 1024, timeout=timeout).strip()
            return TranslationResult(
                translation=raw,
                engine=self.name,
                latency=time.monotonic() - start,
            )

        prompt = TRANSLATION_PROMPT.format(target_lang=target_name, text=text)
        raw = self._request(
            prompt,
            "You are a translator. Output only JSON.",
            2048,
            timeout=timeout,
        )
        parsed = _parse_structured(raw)
        if parsed and "translation" in parsed:
            return TranslationResult(
                translation=parsed.get("translation", raw),
                terms=parsed.get("terms", []),
                sentence_pairs=parsed.get("sentence_pairs", []),
                word_map=parsed.get("word_map", []),
                engine=self.name,
                latency=time.monotonic() - start,
                structured=True,
            )
        return TranslationResult(
            translation=raw.strip(),
            engine=self.name,
            latency=time.monotonic() - start,
        )

    @staticmethod
    def _format_exception_error(exc: Exception) -> str:
        status_code = getattr(exc, "status_code", None)
        if status_code is None:
            response = getattr(exc, "response", None)
            status_code = getattr(response, "status_code", None)

        detail = str(exc).strip() or "Unknown error"
        if status_code and f"HTTP {status_code}" not in detail:
            detail = f"HTTP {status_code} · {detail}"
        return detail
