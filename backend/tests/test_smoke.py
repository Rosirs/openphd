"""Smoke tests to verify package imports."""
def test_package_imports():
    import phd_agent
    assert phd_agent.__version__ == "0.1.0"

def test_health_endpoint():
    from fastapi.testclient import TestClient
    from phd_agent.main import app
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}
