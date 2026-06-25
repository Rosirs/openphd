"""GET /agents/catalog."""
from __future__ import annotations
from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter()

class CatalogResponse(BaseModel):
    agents: list[dict]

@router.get("/agents/catalog", response_model=CatalogResponse)
def get_catalog(request: Request) -> CatalogResponse:
    reg = request.app.state.registry
    return CatalogResponse(
        agents=[c.model_dump() for c in (reg.get_contract(a) for a in reg.list_agent_ids())]
    )
