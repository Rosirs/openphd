"""Onboarding endpoints: status, save, test, skip."""
from __future__ import annotations
import time
from fastapi import APIRouter, HTTPException
from phd_agent.core.profile import UserProfile
from phd_agent.core.providers import PROVIDER_PRESETS
from phd_agent.api.deps import get_repo, invalidate_profile_cache
from phd_agent.llm.openai_compat import OpenAICompatClient

router = APIRouter()


@router.get("/onboard/status")
async def get_status() -> dict:
    repo = get_repo()
    profile = await repo.load_profile()
    if profile is None:
        return {
            "configured": False,
            "onboarded": False,
            "profile": None,
            "providers": [
                {"key": k, "label": v["label"], "supported": v["supported"]}
                for k, v in PROVIDER_PRESETS.items()
            ],
        }
    return {
        "configured": bool(profile.api_key),
        "onboarded": profile.onboarded,
        "profile": {
            "llm_provider": profile.llm_provider,
            "base_url": profile.base_url,
            "model_name": profile.model_name,
            "api_key_masked": profile.masked_key(),
            "onboarded": profile.onboarded,
        },
        "providers": [
            {"key": k, "label": v["label"], "supported": v["supported"]}
            for k, v in PROVIDER_PRESETS.items()
        ],
    }


@router.post("/onboard/save")
async def save_profile(body: dict) -> dict:
    provider = body.get("llm_provider", "openai")
    if provider not in PROVIDER_PRESETS:
        raise HTTPException(400, f"unknown provider: {provider}")
    if not PROVIDER_PRESETS[provider]["supported"]:
        raise HTTPException(400, f"provider not supported yet: {provider}")

    repo = get_repo()
    existing = await repo.load_profile()
    preset = PROVIDER_PRESETS[provider]
    profile = UserProfile(
        llm_provider=provider,
        base_url=body.get("base_url") or preset["base_url"],
        api_key=body.get("api_key", ""),
        model_name=body.get("model_name") or preset["default_model"],
        onboarded=True,
        onboarded_at=existing.onboarded_at if existing else None,
    )
    await repo.save_profile(profile)
    invalidate_profile_cache()
    return {
        "profile": {
            "llm_provider": profile.llm_provider,
            "base_url": profile.base_url,
            "model_name": profile.model_name,
            "api_key_masked": profile.masked_key(),
        },
        "message": "saved",
    }


@router.post("/onboard/test")
async def test_connection(body: dict) -> dict:
    """Send a tiny ping to validate the API key. 5s timeout."""
    provider = body.get("llm_provider", "openai")
    if provider not in PROVIDER_PRESETS or not PROVIDER_PRESETS[provider]["supported"]:
        raise HTTPException(400, f"provider not testable: {provider}")

    preset = PROVIDER_PRESETS[provider]
    base_url = body.get("base_url") or preset["base_url"]
    api_key = body.get("api_key", "")
    model_name = body.get("model_name") or preset["default_model"]

    if not api_key:
        raise HTTPException(400, "api_key required")

    client = OpenAICompatClient(base_url=base_url, api_key=api_key, timeout=5.0)
    started = time.perf_counter()
    try:
        r = await client.chat(
            messages=[{"role": "user", "content": "ping"}],
            tools=None, budget=10, model=model_name,
        )
        latency_ms = int((time.perf_counter() - started) * 1000)
        return {"ok": True, "message": "connected", "latency_ms": latency_ms,
                "model": r.model}
    except Exception as e:
        latency_ms = int((time.perf_counter() - started) * 1000)
        return {"ok": False, "message": str(e), "latency_ms": latency_ms}


@router.post("/onboard/skip")
async def skip_onboard() -> dict:
    """User chose to skip; mark onboarded=True. Keeps existing api_key if any."""
    repo = get_repo()
    existing = await repo.load_profile()
    if existing:
        existing.onboarded = True
        await repo.save_profile(existing)
    else:
        await repo.save_profile(UserProfile(
            llm_provider="openai", base_url="", api_key="", model_name="",
            onboarded=True,
        ))
    invalidate_profile_cache()
    return {"ok": True}