"""In-process batch grading service (eng review A2).

Screening ~1000 plans can't live in the browser (a closed tab loses the run) or
starve the interactive endpoints. This service persists the job and every item's
state, so a crash or redeploy resumes: re-running a job only processes items that
are not yet done. The actual grading is injected as `work_fn(key) -> grade_id`,
so this module is pure orchestration + persistence — testable without the LLM,
and callable from an asyncio worker pool wrapper in production.

Item lifecycle:  pending ──work_fn ok──▶ done
                         └─work_fn raises, attempts>=max──▶ error
A crash between items leaves the rest `pending`; the next process_pending()
call picks them up (done items are skipped — that is the resume guarantee).
"""
from __future__ import annotations

from typing import Callable, List, Optional

from sqlalchemy import select

from backend.src.persistence import BatchJob, JobItem


def create_job(session, keys: List[str], name: str = "") -> BatchJob:
    job = BatchJob(name=name, status="pending")
    for key in keys:
        job.items.append(JobItem(key=key, status="pending"))
    session.add(job)
    session.commit()
    return job


def get_job(session, job_id: int) -> Optional[BatchJob]:
    return session.get(BatchJob, job_id)


def job_items(session, job_id: int) -> List[JobItem]:
    stmt = select(JobItem).where(JobItem.job_id == job_id).order_by(JobItem.id)
    return list(session.execute(stmt).scalars())


def job_progress(session, job_id: int) -> dict:
    counts = {"total": 0, "pending": 0, "done": 0, "error": 0}
    for it in job_items(session, job_id):
        counts["total"] += 1
        counts[it.status] = counts.get(it.status, 0) + 1
    return counts


def _finalize_status(session, job_id: int) -> str:
    prog = job_progress(session, job_id)
    if prog["error"] and prog["pending"] == 0:
        status = "error"           # finished, but some items failed terminally
    elif prog["pending"] == 0:
        status = "done"
    else:
        status = "running"         # unfinished (e.g. interrupted) — resumable
    job = get_job(session, job_id)
    job.status = status
    session.commit()
    return status


def process_pending(
    session,
    job_id: int,
    work_fn: Callable[[str], int],
    max_attempts: int = 1,
) -> BatchJob:
    """Process every not-yet-done item through work_fn. Commits after each item
    so progress survives a crash. work_fn returns a grade id on success; if it
    raises and the item has used all attempts it is marked "error", otherwise it
    is left pending for a later resume. A BaseException that is not an Exception
    (e.g. KeyboardInterrupt) propagates — a true interruption, not a per-item
    failure — leaving remaining items pending."""
    job = get_job(session, job_id)
    job.status = "running"
    session.commit()

    for item in job_items(session, job_id):
        if item.status == "done":
            continue  # resume: never re-run completed work
        item.attempts += 1
        try:
            grade_id = work_fn(item.key)
        except Exception as e:  # per-item failure (not a crash)
            if item.attempts >= max_attempts:
                item.status, item.error = "error", str(e)
            # else: leave pending for a later resume attempt
            session.commit()
            continue
        item.status, item.grade_id, item.error = "done", grade_id, None
        session.commit()

    _finalize_status(session, job_id)
    return get_job(session, job_id)
