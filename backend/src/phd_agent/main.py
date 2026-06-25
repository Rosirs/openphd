"""FastAPI app entry point (stub; populated by Task 13)."""
from fastapi import FastAPI

def create_app() -> FastAPI:
    app = FastAPI(title="PhD-Agent", version="0.1.0")

    @app.get("/health")
    def health() -> dict:
        return {"ok": True}

    return app

app = create_app()
