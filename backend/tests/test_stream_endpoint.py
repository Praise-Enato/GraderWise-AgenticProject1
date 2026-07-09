"""SSE endpoint surface (Phase 3 A1: job-id + EventSource GET).

The streaming body needs a live LLM (astream over the graph), so these cover
the testable surface: the start handshake returns a job id, an unknown id 404s,
and an empty request 422s. The stage-event contract itself is unit-tested in
test_stream_events.py.
"""
from fastapi.testclient import TestClient

from backend.src.main import app

client = TestClient(app)

_RUBRIC = [{"criteria": "Market", "max_points": 5, "description": "market sizing"}]


def test_stream_start_returns_a_job_id():
    r = client.post("/grade/stream/start",
                    json={"submission_text": "a plan", "rubric": _RUBRIC, "student_id": "t"})
    assert r.status_code == 200
    assert isinstance(r.json().get("job_id"), str) and r.json()["job_id"]


def test_stream_start_requires_a_submission():
    r = client.post("/grade/stream/start",
                    json={"rubric": _RUBRIC, "student_id": "t"})
    assert r.status_code == 422


def test_stream_unknown_job_id_is_404():
    r = client.get("/grade/stream/does-not-exist")
    assert r.status_code == 404
