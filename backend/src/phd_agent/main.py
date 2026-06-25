"""FastAPI app factory: wires registry, orchestrator, bus, and routers."""
from __future__ import annotations
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from phd_agent.core.events import EventBus
from phd_agent.core.registry import AgentRegistry
from phd_agent.llm.base import BaseLLMClient, LLMResponse
from phd_agent.orchestrator import PipelineOrchestrator

class _StubLLM(BaseLLMClient):
    """Skeleton-phase LLM that returns empty responses (real impl in Phase 2)."""
    async def chat(self, messages, *, budget):
        return LLMResponse(content="", tokens_used=0, model="stub")
    def count_tokens(self, text):
        return len(text) // 4

def create_app() -> FastAPI:
    app = FastAPI(title="PhD-Agent", version="0.1.0")

    plugins_dir = Path(__file__).parent / "plugins"
    registry = AgentRegistry(plugins_dir)
    bus = EventBus()
    llm = _StubLLM()
    orchestrator = PipelineOrchestrator(registry=registry, llm=llm, bus=bus)

    app.state.registry = registry
    app.state.bus = bus
    app.state.llm = llm
    app.state.orchestrator = orchestrator

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from phd_agent.api.agents import router as agents_router
    from phd_agent.api.pipelines import router as pipelines_router
    app.include_router(agents_router, prefix="/api")    # /api/agents/catalog
    app.include_router(pipelines_router, prefix="/api")  # /api/pipelines/*

    @app.get("/health")
    def health() -> dict:
        return {"ok": True}

    return app

app = create_app()
