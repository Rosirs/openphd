"""Tests for composite tool data model."""
from phd_agent.core.composite import CompositeToolDefinition, build_system_prompt


def test_composite_def_roundtrip():
    d = CompositeToolDefinition(
        tool_id="my_tool", name="My Tool", description="does X",
        system_prompt="summarize papers",
        sub_tools=["arxiv_search", "writing_polisher"],
        owner_user_id="u1",
    )
    data = d.model_dump_json()
    d2 = CompositeToolDefinition.model_validate_json(data)
    assert d2.sub_tools == ["arxiv_search", "writing_polisher"]
    assert d2.system_prompt == "summarize papers"


def test_build_system_prompt_augments_user_input():
    prompt = build_system_prompt(
        name="MyTool", user_intent="summarize papers",
        sub_tools=["arxiv_search", "writing_polisher"],
        max_sub_iterations=5,
    )
    assert "summarize papers" in prompt
    assert "arxiv_search" in prompt
    assert "writing_polisher" in prompt
    assert "5" in prompt
