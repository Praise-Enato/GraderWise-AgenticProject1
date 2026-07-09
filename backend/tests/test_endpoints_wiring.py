"""End-to-end tests for the newly-wired endpoints (no LLM).

- /leaderboard exercises persistence.leaderboard + aggregate.cutoff_tie_zone
  (tie-band, OV#2) + fairness (OV#13) against persisted grades.
- /grade/batch exercises the batch service through the API, with the per-item
  grader substituted so no model call is made.
"""
import pytest
from fastapi.testclient import TestClient

import backend.src.main as main
from backend.src.main import app, get_session
from backend.src import persistence as P


@pytest.fixture()
def client(tmp_path):
    engine = P.make_engine(f"sqlite:///{tmp_path/'api.db'}")
    P.init_db(engine)
    Factory = P.make_session_factory(engine)

    def _override():
        s = Factory()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_session] = _override
    yield TestClient(app), Factory
    app.dependency_overrides.clear()


def test_leaderboard_ranks_with_tie_zone_and_fairness(client):
    tc, Factory = client
    s = Factory()
    a = P.add_submission(s, team="A", filename="a", content="x", group="en")
    b = P.add_submission(s, team="B", filename="b", content="x", group="fr")
    c = P.add_submission(s, team="C", filename="c", content="x", group="fr")
    P.save_grade(s, a.id, score=90.0, total_points=100.0)
    P.save_grade(s, b.id, score=71.0, total_points=100.0)
    P.save_grade(s, c.id, score=70.5, total_points=100.0)
    s.close()

    r = tc.get("/leaderboard?shortlist=2&band=1.0")
    assert r.status_code == 200
    data = r.json()
    assert [row["team"] for row in data["ranking"]] == ["A", "B", "C"]     # ranked desc
    # cutoff is rank 2 (score 71); C (70.5) is within 1.0 -> contested tie zone
    assert set(data["tie_zone_at_cutoff"]) == {str(b.id), str(c.id)}
    assert "flag_rate_by_group" in data["fairness"]


def test_grade_batch_runs_the_job_through_the_api(client, monkeypatch):
    tc, Factory = client

    # Substitute the per-item grader so no LLM is called; save a stub grade.
    def fake_item(session, submission_id, rubric, options):
        g = P.save_grade(session, submission_id, score=50.0, total_points=100.0)
        return g.id

    monkeypatch.setattr(main, "_batch_grade_item", fake_item)

    r = tc.post("/grade/batch", json={
        "submissions": [{"filename": "a.txt", "content": "plan a"},
                        {"filename": "b.txt", "content": "plan b"}],
        "rubric": [{"criteria": "C", "max_points": 5, "description": "d"}],
    })
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 2 and body["done"] == 2

    status = tc.get(f"/grade/batch/{body['job_id']}").json()
    assert status["status"] == "done"


def test_grade_batch_requires_submissions(client):
    tc, _ = client
    r = tc.post("/grade/batch", json={"submissions": [], "rubric": []})
    assert r.status_code == 422


def test_batch_status_unknown_job_404(client):
    tc, _ = client
    assert tc.get("/grade/batch/999999").status_code == 404
