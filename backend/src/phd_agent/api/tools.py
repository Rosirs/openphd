"""Tool catalog endpoints."""
from __future__ import annotations
from fastapi import APIRouter, HTTPException, Query
from phd_agent.api.deps import get_runtime

router = APIRouter()


@router.get("/tools/catalog")
async def list_tools(user_id: str = Query(...)):
    runtime = get_runtime()
    await runtime.registry.load_user_composites(user_id)
    tools = await runtime.registry.list_my_tools(user_id)
    return {"tools": tools}


@router.get("/tools/{tool_id}")
async def get_tool(tool_id: str, user_id: str = Query(...)):
    runtime = get_runtime()
    await runtime.registry.load_user_composites(user_id)
    tools = await runtime.registry.list_my_tools(user_id)
    for t in tools:
        if t.get("name") == tool_id:
            return t
    raise HTTPException(404, "tool not found")
