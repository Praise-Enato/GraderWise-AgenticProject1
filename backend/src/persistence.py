"""Backend-owned persistence for GradeWise (eng review A3 / P3).

The grades are produced in this Python backend, so the backend owns the store
(the unused frontend Prisma is dropped). SQLite with WAL mode to start —
adequate for a single-box competition run and safe under the in-process worker
pool (P3) — with a Postgres path later via DATABASE_URL. This module is the
schema + a small repository the API and the batch service call; it holds the
durable judge workflow: submissions, grades, per-criterion scores, judge
overrides, and an audit trail (who changed what, when).

SQLAlchemy 2.0 style. Pure-ish: no network, no LLM; unit-tested against a
temp-file SQLite DB.
"""
from __future__ import annotations

import datetime as _dt
import os
from typing import List, Optional

from sqlalchemy import (
    JSON, DateTime, Float, ForeignKey, Integer, String, Text, Boolean,
    create_engine, event, select,
)
from sqlalchemy.orm import (
    DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker,
)

DEFAULT_DB_URL = "sqlite:///./backend/data/gradewise.db"


def _utcnow() -> _dt.datetime:
    return _dt.datetime.now(_dt.timezone.utc)


class Base(DeclarativeBase):
    pass


# --- Schema ----------------------------------------------------------------- #
class Submission(Base):
    __tablename__ = "submissions"
    id: Mapped[int] = mapped_column(primary_key=True)
    team: Mapped[str] = mapped_column(String(256))
    filename: Mapped[str] = mapped_column(String(512))
    content: Mapped[str] = mapped_column(Text, default="")
    group: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)  # fairness attr (language/region)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    created_at: Mapped[_dt.datetime] = mapped_column(DateTime, default=_utcnow)
    grades: Mapped[List["Grade"]] = relationship(back_populates="submission", cascade="all, delete-orphan")


class Grade(Base):
    __tablename__ = "grades"
    id: Mapped[int] = mapped_column(primary_key=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("submissions.id"))
    score: Mapped[float] = mapped_column(Float)
    total_points: Mapped[float] = mapped_column(Float, default=0.0)
    feedback: Mapped[str] = mapped_column(Text, default="")
    confidence_score: Mapped[float] = mapped_column(Float, default=1.0)
    graded_ok: Mapped[bool] = mapped_column(Boolean, default=True)
    eligibility_status: Mapped[str] = mapped_column(String(32), default="eligible")
    ai_content_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    is_override: Mapped[bool] = mapped_column(Boolean, default=False)
    actor: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)  # judge id for overrides
    grade_of_record: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # pinned provenance (X4)
    created_at: Mapped[_dt.datetime] = mapped_column(DateTime, default=_utcnow)
    submission: Mapped["Submission"] = relationship(back_populates="grades")
    assessments: Mapped[List["CriterionScore"]] = relationship(
        back_populates="grade", cascade="all, delete-orphan")


class CriterionScore(Base):
    __tablename__ = "criterion_scores"
    id: Mapped[int] = mapped_column(primary_key=True)
    grade_id: Mapped[int] = mapped_column(ForeignKey("grades.id"))
    criteria_index: Mapped[int] = mapped_column(Integer, default=0)
    criteria_name: Mapped[str] = mapped_column(String(512))
    awarded_points: Mapped[float] = mapped_column(Float, default=0.0)
    max_points: Mapped[float] = mapped_column(Float, default=0.0)
    reason: Mapped[str] = mapped_column(Text, default="")
    evidence: Mapped[str] = mapped_column(Text, default="")
    grade: Mapped["Grade"] = relationship(back_populates="assessments")


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    submission_id: Mapped[Optional[int]] = mapped_column(ForeignKey("submissions.id"), nullable=True)
    grade_id: Mapped[Optional[int]] = mapped_column(ForeignKey("grades.id"), nullable=True)
    actor: Mapped[str] = mapped_column(String(128))
    action: Mapped[str] = mapped_column(String(64))
    detail: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[_dt.datetime] = mapped_column(DateTime, default=_utcnow)


class BatchJob(Base):
    """A batch grading run. Per-item state lives in JobItem so a crash/redeploy
    can resume (eng review A2)."""
    __tablename__ = "batch_jobs"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(256), default="")
    status: Mapped[str] = mapped_column(String(32), default="pending")  # pending|running|done|error
    created_at: Mapped[_dt.datetime] = mapped_column(DateTime, default=_utcnow)
    items: Mapped[List["JobItem"]] = relationship(back_populates="job", cascade="all, delete-orphan")


class JobItem(Base):
    __tablename__ = "job_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("batch_jobs.id"))
    key: Mapped[str] = mapped_column(String(512))                       # identifies the work (filename / hash)
    status: Mapped[str] = mapped_column(String(32), default="pending")  # pending|done|error
    grade_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    job: Mapped["BatchJob"] = relationship(back_populates="items")


# --- Engine / session ------------------------------------------------------- #
def make_engine(url: Optional[str] = None):
    """Create an engine. SQLite gets WAL (concurrent readers under the worker
    pool) and enforced foreign keys via a connect-time pragma hook."""
    url = url or os.getenv("DATABASE_URL", DEFAULT_DB_URL)
    if url.startswith("sqlite:///") and not url.startswith("sqlite:///:"):
        # Ensure the parent directory exists so a first run can create the file.
        db_path = url[len("sqlite:///"):]
        parent = os.path.dirname(db_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    engine = create_engine(url, connect_args=connect_args, future=True)
    if url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def _sqlite_pragmas(dbapi_conn, _record):  # pragma: no cover - trivial
            cur = dbapi_conn.cursor()
            cur.execute("PRAGMA journal_mode=WAL")
            cur.execute("PRAGMA foreign_keys=ON")
            cur.close()
    return engine


def make_session_factory(engine):
    return sessionmaker(bind=engine, future=True, expire_on_commit=False)


def init_db(engine) -> None:
    Base.metadata.create_all(engine)


# --- Repository ------------------------------------------------------------- #
def add_submission(session, team: str, filename: str, content: str = "",
                   group: Optional[str] = None, status: str = "pending") -> Submission:
    sub = Submission(team=team, filename=filename, content=content, group=group, status=status)
    session.add(sub)
    session.commit()
    return sub


def get_submission(session, submission_id: int) -> Optional[Submission]:
    return session.get(Submission, submission_id)


def save_grade(session, submission_id: int, *, score: float, total_points: float = 0.0,
               feedback: str = "", assessments: Optional[List[dict]] = None,
               confidence_score: float = 1.0, graded_ok: bool = True,
               eligibility_status: str = "eligible", ai_content_flag: bool = False,
               grade_of_record: Optional[dict] = None, is_override: bool = False,
               actor: Optional[str] = None) -> Grade:
    grade = Grade(
        submission_id=submission_id, score=score, total_points=total_points,
        feedback=feedback, confidence_score=confidence_score, graded_ok=graded_ok,
        eligibility_status=eligibility_status, ai_content_flag=ai_content_flag,
        grade_of_record=grade_of_record, is_override=is_override, actor=actor,
    )
    for a in (assessments or []):
        grade.assessments.append(CriterionScore(
            criteria_index=int(a.get("criteria_index", 0)),
            criteria_name=str(a.get("criteria_name", "")),
            awarded_points=float(a.get("awarded_points", 0.0)),
            max_points=float(a.get("max_points", 0.0)),
            reason=str(a.get("reason", "")),
            evidence=str(a.get("evidence", "")),
        ))
    session.add(grade)
    session.commit()
    return grade


def _grades_desc(session, submission_id: int, eligible_only: bool = False) -> List[Grade]:
    stmt = select(Grade).where(Grade.submission_id == submission_id)
    if eligible_only:
        stmt = stmt.where(Grade.graded_ok.is_(True), Grade.eligibility_status == "eligible")
    stmt = stmt.order_by(Grade.id.desc())
    return list(session.execute(stmt).scalars())


def latest_grade(session, submission_id: int) -> Optional[Grade]:
    grades = _grades_desc(session, submission_id)
    return grades[0] if grades else None


def leaderboard(session):
    """(submission, latest eligible+graded_ok grade) rows, ranked by score desc.
    Submissions with no rankable grade are omitted (flagged/ineligible go to a
    separate triage view, never buried in the ranking)."""
    rows = []
    for sub in session.execute(select(Submission)).scalars():
        eligible = _grades_desc(session, sub.id, eligible_only=True)
        if eligible:
            rows.append((sub, eligible[0]))
    rows.sort(key=lambda t: t[1].score, reverse=True)
    return rows


def record_audit(session, actor: str, action: str, detail: str = "",
                 submission_id: Optional[int] = None, grade_id: Optional[int] = None) -> AuditEvent:
    ev = AuditEvent(actor=actor, action=action, detail=detail,
                    submission_id=submission_id, grade_id=grade_id)
    session.add(ev)
    session.commit()
    return ev


def override_grade(session, submission_id: int, *, score: float, total_points: float = 0.0,
                   actor: str, detail: str = "", **grade_kwargs) -> Grade:
    """Record a judge override as a NEW grade (is_override=True) plus an audit
    event — the prior grade is kept for the trail, never mutated."""
    grade = save_grade(session, submission_id, score=score, total_points=total_points,
                       is_override=True, actor=actor, **grade_kwargs)
    record_audit(session, actor=actor, action="override", detail=detail,
                 submission_id=submission_id, grade_id=grade.id)
    return grade


def audit_for_submission(session, submission_id: int) -> List[AuditEvent]:
    stmt = select(AuditEvent).where(AuditEvent.submission_id == submission_id).order_by(AuditEvent.id)
    return list(session.execute(stmt).scalars())
