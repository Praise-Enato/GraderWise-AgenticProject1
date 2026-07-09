"""Health endpoint + CORS config, exercised via the FastAPI TestClient.

/health is needed by the Docker/compose stack for readiness checks. CORS is
made overridable (ALLOWED_ORIGINS env) so a deployment can lock it down; the
default stays permissive so existing deployments don't break.
"""
from fastapi.testclient import TestClient

from backend.src.main import app

client = TestClient(app)


def test_health_returns_ok():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
