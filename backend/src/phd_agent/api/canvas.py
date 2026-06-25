"""Canvas endpoints: preview and save composite tools."""
from __future__ import annotations
import os
from fastapi import APIRouter, HTTPException, Query
from phd_agent.core.composite import CompositeToolDefinition, build_system_prompt
from phd_agent.core.composite_agent import MAX_SUB_ITERATIONS
from phd_agent.api.deps import get_repo

router = APIRouter()


@router.post("/canvas/preview-prompt")
async def preview_prompt(body: dict):
    return {
        "augmented_system_prompt": build_system_prompt(
            name=body.get("name", "Tool"),
            user_intent=body.get("system_prompt", ""),
            sub_tools=body.get("sub_tools", []),
            max_sub_iterations=MAX_SUB_ITERATIONS,
        )
    }


@router.post("/canvas/composite")
async def save_composite(body: dict, user_id: str = Query(...)):
    repo = get_repo()
    tool = CompositeToolDefinition(
        tool_id=body["tool_id"],
        name=body["name"],
        description=body.get("description", body["name"]),
        system_prompt=body["system_prompt"],
        sub_tools=body["sub_tools"],
        owner_user_id=user_id,
        is_public=body.get("is_public", False),
    )
    await repo.save_composite_tool(tool)
    return {"tool": tool.model_dump(mode="json")}


@router.delete("/canvas/composite/{tool_id}")
async def delete_composite(tool_id: str, user_id: str = Query(...)):
    repo = get_repo()
    await repo.delete_composite_tool(user_id, tool_id)
    return {"ok": True}


@router.get("/canvas/composites")
async def list_composites(user_id: str = Query(...)):
    repo = get_repo()
    tools = await repo.list_composite_tools(user_id)
    return {"composites": [t.model_dump(mode="json") for t in tools]}
