"""Tests for the in-process batch grading service (eng review A2).

A ~1000-plan run must survive a crash/redeploy: job + per-item state is
persisted, and re-running a job only processes the unfinished items (resume).
The grading work is injected as a callable so this is testable without the LLM.
"""
import pytest

from backend.src import persistence as P
from backend.src import batch as B


@pytest.fixture()
def session(tmp_path):
    engine = P.make_engine(f"sqlite:///{tmp_path/'jobs.db'}")
    P.init_db(engine)
    Session = P.make_session_factory(engine)
    s = Session()
    try:
        yield s
    finally:
        s.close()


def test_create_job_is_pending_with_items(session):
    job = B.create_job(session, keys=["a", "b", "c"], name="run1")
    assert job.status == "pending"
    prog = B.job_progress(session, job.id)
    assert prog["total"] == 3 and prog["done"] == 0 and prog["pending"] == 3


def test_process_pending_happy_path_marks_job_done(session):
    job = B.create_job(session, keys=["a", "b"])
    calls = []
    B.process_pending(session, job.id, lambda key: calls.append(key) or 1)
    prog = B.job_progress(session, job.id)
    assert prog["done"] == 2 and prog["pending"] == 0
    assert B.get_job(session, job.id).status == "done"
    assert sorted(calls) == ["a", "b"]


def test_failing_item_is_marked_error_and_job_finishes_with_error(session):
    job = B.create_job(session, keys=["ok", "bad"])

    def work(key):
        if key == "bad":
            raise ValueError("boom")
        return 1

    B.process_pending(session, job.id, work, max_attempts=1)
    prog = B.job_progress(session, job.id)
    assert prog["done"] == 1 and prog["error"] == 1
    assert B.get_job(session, job.id).status == "error"


def test_resume_only_processes_unfinished_items(session):
    job = B.create_job(session, keys=["a", "b", "c"])

    def crash_after_a(key):
        if key == "a":
            return 1
        raise KeyboardInterrupt  # simulate a crash mid-run (not a per-item error)

    with pytest.raises(KeyboardInterrupt):
        B.process_pending(session, job.id, crash_after_a)
    assert B.job_progress(session, job.id)["done"] == 1  # 'a' persisted before the crash

    called = []
    B.process_pending(session, job.id, lambda key: called.append(key) or 2)
    assert sorted(called) == ["b", "c"]              # resumed; 'a' not re-graded
    assert B.get_job(session, job.id).status == "done"


def test_item_records_returned_grade_id(session):
    job = B.create_job(session, keys=["a"])
    B.process_pending(session, job.id, lambda key: 4242)
    item = B.job_items(session, job.id)[0]
    assert item.status == "done"
    assert item.grade_id == 4242
