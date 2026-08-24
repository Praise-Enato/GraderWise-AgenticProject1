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


# --------------------- History record name (_record_team) -------------------- #
# What a run is filed under in History: the judge's typed name, else the name read
# out of the plan, else the file name. The client cannot know the middle one (it
# has not read the document), which is why the server resolves it.

def _res(business_name=""):
    from backend.src.models import GradeResult
    return GradeResult(score=1.0, feedback="", business_name=business_name)


def test_record_team_prefers_the_typed_name():
    assert main._record_team("Acme Ventures", _res("Read From Plan"), "plan.pdf") == "Acme Ventures"


def test_record_team_uses_the_extracted_name_when_none_typed():
    # "team" is the placeholder the client sends when the judge typed nothing.
    assert main._record_team("team", _res("Read From Plan"), "plan.pdf") == "Read From Plan"
    assert main._record_team("", _res("Read From Plan"), "plan.pdf") == "Read From Plan"


def test_record_team_falls_back_to_the_filename():
    assert main._record_team("team", _res(""), "campus glow salon.docx") == "campus glow salon.docx"


# ------------------ History: download the PDF report of a past run ----------- #
# History offered only the original plan file, so a judge could re-read a
# submission but not re-obtain the report that was produced from it. The report
# builder is stateless, so the stored grade is rehydrated and re-rendered.

def _seed_graded(session, team="Jideofor Enterprise", filename="plan.pdf", total=80.0):
    sub = P.add_submission(session, team=team, filename=filename, content="plan text",
                           status="graded")
    P.save_grade(session, sub.id, score=37.5, total_points=total,
                 feedback="Tighten the financials.", confidence_score=0.9,
                 assessments=[
                     {"criteria_index": 1, "criteria_name": "Problem - Clarity",
                      "awarded_points": 3.0, "max_points": 5.0, "reason": "partly evidenced"},
                     {"criteria_index": 2, "criteria_name": "Financials - Detailed Breakdown",
                      "awarded_points": 0.0, "max_points": 10.0, "reason": "no projections"},
                 ])
    return sub.id


def test_history_report_download(client):
    tc, Factory = client
    s = Factory()
    sid = _seed_graded(s)
    s.close()

    r = tc.get(f"/grade-history/{sid}/report")
    assert r.status_code == 200, r.text
    assert r.headers["content-type"] == "application/pdf"
    assert r.content.startswith(b"%PDF")
    # Headed by the business name, and named after it on disk.
    assert b"/Title (Jideofor Enterprise - Business Plan Evaluation)" in r.content
    assert "Jideofor-Enterprise-report.pdf" in r.headers["content-disposition"]


def test_history_report_falls_back_to_the_filename_when_unnamed(client):
    tc, Factory = client
    s = Factory()
    sid = _seed_graded(s, team="", filename="campus glow salon.docx")
    s.close()
    r = tc.get(f"/grade-history/{sid}/report")
    assert r.status_code == 200
    assert b"/Title (campus glow salon - Business Plan Evaluation)" in r.content


def test_history_report_does_not_depend_on_the_stored_plan_file(client):
    # The report is rebuilt from the grade alone, so it is available whether or not
    # the upload was kept (text-mode runs keep no file). Deliberately does NOT
    # assert has_file: _find_plan_file globs a shared directory, so that flag
    # depends on files other tests left behind, not on this submission.
    tc, Factory = client
    s = Factory()
    sid = _seed_graded(s)          # no plan file written for this submission
    s.close()
    r = tc.get(f"/grade-history/{sid}/report")
    assert r.status_code == 200
    assert r.content.startswith(b"%PDF")


def test_history_report_404s_for_unknown_submission(client):
    tc, _ = client
    assert tc.get("/grade-history/99999/report").status_code == 404


def test_rubric_label_inference():
    assert main._rubric_label_for(80.0) == "BYUMS Competition (80)"
    assert main._rubric_label_for(100.0) == "General Business (100)"
    assert main._rubric_label_for(55.0) == "55 pts"
    assert main._rubric_label_for(0) == ""      # omitted rather than guessed
