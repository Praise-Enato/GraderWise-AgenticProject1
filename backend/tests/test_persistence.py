"""Tests for backend-owned persistence (A3: SQLAlchemy, SQLite WAL per P3).

Backbone for the durable judge workflow (saved leaderboards, triage queue,
overrides, audit trail) that Phase 2/3 build on. Tested against a temp-file
SQLite DB so WAL and foreign keys are exercised for real. No network.
"""
import pytest

from backend.src import persistence as P


@pytest.fixture()
def session(tmp_path):
    engine = P.make_engine(f"sqlite:///{tmp_path/'test.db'}")
    P.init_db(engine)
    Session = P.make_session_factory(engine)
    s = Session()
    try:
        yield s
    finally:
        s.close()


def test_init_enables_wal(tmp_path):
    engine = P.make_engine(f"sqlite:///{tmp_path/'wal.db'}")
    P.init_db(engine)
    with engine.connect() as conn:
        from sqlalchemy import text
        mode = conn.execute(text("PRAGMA journal_mode")).scalar()
    assert str(mode).lower() == "wal"


def test_add_submission_defaults_to_pending(session):
    sub = P.add_submission(session, team="Team A", filename="a.pdf", content="plan text")
    assert sub.id is not None
    assert sub.status == "pending"
    assert P.get_submission(session, sub.id).content == "plan text"


def test_save_grade_round_trips_assessments(session):
    sub = P.add_submission(session, team="Team A", filename="a.pdf", content="x")
    grade = P.save_grade(
        session, sub.id, score=6.0, total_points=8.0, feedback="ok",
        assessments=[
            {"criteria_index": 1, "criteria_name": "Market", "awarded_points": 6,
             "max_points": 8, "reason": "r", "evidence": "2.3 million farmers"},
        ],
        grade_of_record={"model": "deepseek-chat", "input_hash": "abc"},
    )
    got = P.latest_grade(session, sub.id)
    assert got.score == pytest.approx(6.0)
    assert len(got.assessments) == 1
    assert got.assessments[0].evidence == "2.3 million farmers"
    assert got.grade_of_record["model"] == "deepseek-chat"


def test_leaderboard_orders_by_score_and_excludes_ineligible(session):
    a = P.add_submission(session, team="A", filename="a", content="x")
    b = P.add_submission(session, team="B", filename="b", content="x")
    c = P.add_submission(session, team="C", filename="c", content="x")
    P.save_grade(session, a.id, score=70.0, total_points=100.0)
    P.save_grade(session, b.id, score=90.0, total_points=100.0)
    P.save_grade(session, c.id, score=95.0, total_points=100.0,
                 eligibility_status="ineligible")  # excluded from ranking
    board = P.leaderboard(session)
    teams = [sub.team for sub, _ in board]
    assert teams == ["B", "A"]  # 90 then 70; C excluded


def test_latest_grade_reflects_override_and_audit_trail(session):
    sub = P.add_submission(session, team="A", filename="a", content="x")
    P.save_grade(session, sub.id, score=60.0, total_points=100.0)
    P.override_grade(session, sub.id, score=75.0, total_points=100.0,
                     actor="judge_jane", detail="raised financials after review")
    latest = P.latest_grade(session, sub.id)
    assert latest.score == pytest.approx(75.0)
    assert latest.is_override is True
    events = P.audit_for_submission(session, sub.id)
    assert any(e.action == "override" and e.actor == "judge_jane" for e in events)
