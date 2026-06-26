"""LLM provider presets. Anthropic is listed but disabled in v1."""

PROVIDER_PRESETS: dict[str, dict] = {
    "openai": {
        "label": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o-mini",
        "supported": True,
    },
    "deepseek": {
        "label": "DeepSeek",
        "base_url": "https://api.deepseek.com/v1",
        "default_model": "deepseek-chat",
        "supported": True,
    },
    "moonshot": {
        "label": "Moonshot (Kimi)",
        "base_url": "https://api.moonshot.cn/v1",
        "default_model": "moonshot-v1-8k",
        "supported": True,
    },
    "MiniMax": {
        "label": "MiniMax",
        "base_url": "https://api.MiniMax.chat/v1",
        "default_model": "MiniMax-M3",
        "supported": True,
    },
    "custom": {
        "label": "Custom (OpenAI-compatible)",
        "base_url": "",
        "default_model": "",
        "supported": True,
    },
    "anthropic": {
        "label": "Anthropic Claude",
        "base_url": "https://api.anthropic.com",
        "default_model": "claude-3-5-sonnet-20241022",
        "supported": False,
        "disabled_reason": "Anthropic uses a non-OpenAI API; will be supported in a later phase.",
    },
}