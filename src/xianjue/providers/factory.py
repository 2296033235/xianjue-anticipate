"""Create the appropriate provider from config."""

from __future__ import annotations

from .base import LLMProvider


def create_provider(config_get) -> LLMProvider:
    """Build an LLMProvider based on the current config.

    config_get: callable for dot-path access (e.g. 'model.cloud.api_key').
    """
    provider_type = config_get("model.provider", "cloud")

    if provider_type == "cloud":
        from .deepseek_provider import DeepSeekProvider
        api_key = config_get("model.cloud.api_key", "")
        model = config_get("model.cloud.model", "deepseek-chat")
        return DeepSeekProvider(api_key=api_key, model=model)

    # local
    from .ollama_provider import OllamaProvider
    host = config_get("model.local.host", "http://localhost:11434")
    model = config_get("model.local.model", "qwen3.5:9b")
    return OllamaProvider(host=host, model=model)

