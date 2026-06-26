from phd_agent.core.providers import PROVIDER_PRESETS


def test_openai_supported():
    p = PROVIDER_PRESETS["openai"]
    assert p["supported"] is True
    assert "openai.com" in p["base_url"]
    assert p["default_model"]


def test_anthropic_listed_but_disabled():
    p = PROVIDER_PRESETS["anthropic"]
    assert p["supported"] is False
    assert "disabled_reason" in p


def test_deepseek_and_moonshot_supported():
    for k in ["deepseek", "moonshot"]:
        assert PROVIDER_PRESETS[k]["supported"] is True


def test_custom_supported_with_empty_defaults():
    p = PROVIDER_PRESETS["custom"]
    assert p["supported"] is True
    assert p["base_url"] == ""
    assert p["default_model"] == ""


def test_all_presets_have_required_keys():
    required = {"label", "base_url", "default_model", "supported"}
    for k, v in PROVIDER_PRESETS.items():
        assert required.issubset(v.keys()), f"missing keys in {k}"


def test_minimax_supported():
    p = PROVIDER_PRESETS["MiniMax"]
    assert p["supported"] is True
    assert p["base_url"] == "https://api.MiniMax.chat/v1"
    assert p["default_model"] == "MiniMax-M3"