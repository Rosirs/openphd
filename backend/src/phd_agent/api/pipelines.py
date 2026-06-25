"""POST /pipelines/validate, /pipelines/run, GET /pipelines/{id}/events."""
from __future__ import annotations
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
from phd_agent.api.schemas import (
    RunRequest, RunResponse,
    ValidateRequest, ValidateResponse, StepValidationOut,
)

router = APIRouter()

@router.post("/pipelines/validate", response_model=ValidateResponse)
def validate(req: ValidateRequest, request: Request) -> ValidateResponse:
    from phd_agent.core.validator import validate_pipeline
    reg = request.app.state.registry
    bootstrap = (
        {f"dynamic_storage.{k}" for k in req.dynamic_storage.keys()}
        | {"user_id", "user_background"}
    )
    result = validate_pipeline(req.active_pipeline, reg, bootstrap_fields=bootstrap)
    return ValidateResponse(
        valid=result.valid,
        failed_at=result.failed_at,
        steps=[
            StepValidationOut(
                step=s.step,
                agent_id=s.agent_id,
                required=sorted(s.required),
                provided_at_step=sorted(s.provided_at_step),
                missing=sorted(s.missing),
                ok=s.ok,
            )
            for s in result.steps
        ],
    )

@router.post("/pipelines/run", response_model=RunResponse)
async def run(req: RunRequest, request: Request) -> RunResponse:
    orch = request.app.state.orchestrator
    try:
        run_id = await orch.run(
            user_id=req.user_id,
            active_pipeline=req.active_pipeline,
            initial_dynamic_storage=req.dynamic_storage,
            user_background=req.user_background,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    final = await orch.repo.load(req.user_id)
    return RunResponse(run_id=run_id, status=final.status)

@router.get("/pipelines/{run_id}/events")
async def events(run_id: str, request: Request) -> StreamingResponse:
    bus = request.app.state.bus

    async def gen():
        async for event in bus.subscribe(run_id):
            yield {
                "event": "step",
                "id": str(event.step),
                "data": (
                    f'{{"step":{event.step},"agent_id":"{event.agent_id}",'
                    f'"status":"{event.status}","duration_ms":{event.duration_ms},'
                    f'"error":{json_str(event.error)}}}'
                ),
            }
            if event.status == "end":
                break

    return EventSourceResponse(gen())

def json_str(s) -> str:
    import json
    return json.dumps(s)
