"""Chat session + messages endpoints (SSE streaming)."""
from __future__ import annotations
import json
import os
import uuid
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from phd_agent.core.json_repo import JsonFileRepository
from phd_agent.core.chat import ChatSession

router = APIRouter()
_REPO = JsonFileRepository(base_dir=os.environ.get("DATA_DIR", "data"))


@router.post("/chat/conversations")
async def create_conversation(body: dict):
    user_id = body.get("user_id")
    if not user_id:
        raise HTTPException(400, "user_id required")
    conv_id = str(uuid.uuid4())
    session = ChatSession(
        user_id=user_id, conversation_id=conv_id,
        title=body.get("title", "New chat"),
    )
    await _REPO.save_conversation(session)
    return {"conversation_id": conv_id, "session": session.model_dump(mode="json")}


@router.get("/chat/conversations")
async def list_conversations(user_id: str = Query(...)):
    convs = await _REPO.list_conversations(user_id)
    return {"conversations": [c.model_dump(mode="json") for c in convs]}


@router.get("/chat/conversations/{conv_id}")
async def get_conversation(conv_id: str, user_id: str = Query(...)):
    s = await _REPO.load_conversation(user_id, conv_id)
    if not s:
        raise HTTPException(404, "conversation not found")
    return s.model_dump(mode="json")


@router.delete("/chat/conversations/{conv_id}")
async def delete_conversation(conv_id: str, user_id: str = Query(...)):
    await _REPO.delete_conversation(user_id, conv_id)
    return {"ok": True}


@router.post("/chat/conversations/{conv_id}/messages")
async def post_message(conv_id: str, body: dict, user_id: str = Query(...)):
    from phd_agent.api.deps import get_runtime
    runtime = get_runtime()
    session = await _REPO.load_conversation(user_id, conv_id)
    if not session:
        raise HTTPException(404, "conversation not found")
    content = body.get("content", "")

    async def event_gen():
        async for ev in runtime.run_turn(session, content):
            yield f"event: {ev['type']}\ndata: {json.dumps(ev, default=str)}\n\n"

    return StreamingResponse(event_gen(), media_type="text/event-stream")
