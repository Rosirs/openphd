import json
import pytest
from fastapi.testclient import TestClient
from phd_agent.main import create_app

@pytest.fixture
def client():
    return TestClient(create_app())

def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"ok": True}

def test_agents_catalog_returns_real_plugins(client):
    r = client.get("/api/agents/catalog")
    assert r.status_code == 200
    body = r.json()
    ids = {a["agent_id"] for a in body["agents"]}
    assert "mock_echo" in ids
    assert "mock_logger" in ids

def test_validate_happy_path(client):
    r = client.post("/api/pipelines/validate", json={
        "active_pipeline": ["mock_echo", "mock_logger"],
        "user_id": "u1",
        "dynamic_storage": {"echo_input": "hi"},
    })
    assert r.status_code == 200
    assert r.json()["valid"] is True

def test_validate_invalid_pipeline_returns_200_with_valid_false(client):
    r = client.post("/api/pipelines/validate", json={
        "active_pipeline": ["mock_logger"],
        "user_id": "u1",
        "dynamic_storage": {},
    })
    assert r.status_code == 200  # we return 200 with valid:false, not 422
    body = r.json()
    assert body["valid"] is False
    assert body["failed_at"] == 0

def test_run_returns_run_id(client):
    r = client.post("/api/pipelines/run", json={
        "user_id": "u1",
        "active_pipeline": ["mock_echo", "mock_logger"],
        "dynamic_storage": {"echo_input": "hello"},
    })
    assert r.status_code == 200
    assert "run_id" in r.json()
