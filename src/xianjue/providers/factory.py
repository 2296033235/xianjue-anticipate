"""Create the appropriate provider from config."""

from __future__ import annotations

from .base import LLMProvider


def create_provider(config_get) -> LLMProvider:
    """Build an LLMProvider based on the current config.

    config_get: callable for dot-path access (e.g. 'model.cloud.api_key').
    """
    provider_type = config_get("model.provider", "cloud")

    if provider_type == "custom":
        from .custom_cloud_provider import CustomCloudProvider
        configs = config_get("model.saved_cloud_configs", [])
        active = config_get("model.active_config", 0)
        active_config = configs[active] if isinstance(active, int) and 0 <= active < len(configs) else {}
        api_key = active_config.get("api_key", config_get("model.cloud.api_key", ""))
        model = active_config.get("model", config_get("model.cloud.model", "deepseek-chat"))
        base_url = active_config.get("base_url", config_get("model.cloud.base_url", "https://api.deepseek.com"))
        api_format = active_config.get("api_format", "chat_completions")
        return CustomCloudProvider(
            api_key=api_key,
            model=model,
            base_url=base_url,
            api_format=api_format,
        )

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
