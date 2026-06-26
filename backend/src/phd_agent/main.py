"""FastAPI app factory: wires registry, runtime, bus, and routers."""
from __future__ import annotations
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from phd_agent.api.chat import router as chat_router
from phd_agent.api.tools import router as tools_router
from phd_agent.api.canvas import router as canvas_router
from phd_agent.api.onboard import router as onboard_router


def create_app() -> FastAPI:
    app = FastAPI(title="PhD-Agent", version="0.2.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    async def startup():
        from phd_agent.api.deps import get_runtime
        get_runtime()  # warm up

    app.include_router(chat_router)
    app.include_router(tools_router)
    app.include_router(canvas_router)
    app.include_router(onboard_router)

    @app.get("/health")
    def health() -> dict:
        return {"ok": True}

    return app


app = create_app()
