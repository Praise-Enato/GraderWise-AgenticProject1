import os
import re
import glob
import json as _json
import tempfile
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Depends, Response
from fastapi.responses import FileResponse
from sqlalchemy import select
from sse_starlette.sse import EventSourceResponse
from backend.src.stream_events import stage_event
from backend.src import persistence as _persist
from backend.src import grade_record as _gr
from backend.src import aggregate as _agg
from backend.src import fairness as _fair
from backend.src import batch as _batch
from backend.src.llm import get_model_config
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
from backend.src.models import RubricItem, GradeResult, IngestResponse, ChatRequest, ChatResponse
from backend.src import rag
from backend.src import agent
from backend.src import rubric_parser
from backend.src import rubric_csv
from backend.src import vision_grade
from backend.src import calibration
from backend.src import general_rubric
from backend.src.business_name import extract as extract_business_name
from backend.src.input_adapter import ADAPTER_SUFFIXES, get_adapter
from backend.src.grading import to_grade_result
from backend.src.eligibility import screen_eligibility, EligibilityResult
from backend.src.report import build_report_pdf
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from fastapi.concurrency import run_in_threadpool

# Disable ChromaDB/PostHog Telemetry
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_SERVER_NO_INTERACTIVE_MODE"] = "True"
os.environ["OTEL_PYTHON_DISABLED"] = "True"

app = FastAPI(title="GradeWise API")

# --- CORS CONFIGURATION ---
# Overridable via ALLOWED_ORIGINS (comma-separated). Default stays "*" so
# existing deployments don't break, but a judge-facing deployment SHOULD lock
# this down by setting ALLOWED_ORIGINS to its known frontends (eng review).
_origins_env = os.getenv("ALLOWED_ORIGINS", "").strip()
ALLOWED_ORIGINS = [o.strip() for o in _origins_env.split(",") if o.strip()] or ["*"]
if ALLOWED_ORIGINS == ["*"]:
    print("WARNING: CORS allow_origins is '*' (open to any site). "
          "Set ALLOWED_ORIGINS before judge-facing use.")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ------------------------------------


@app.get("/health")
def health():
    """Liveness/readiness probe for the Docker/compose stack."""
    return {"status": "ok"}


# --- Backend-owned persistence (A3): the engine + a per-request session ------ #
_DB_ENGINE = _persist.make_engine()
_persist.init_db(_DB_ENGINE)
_SessionLocal = _persist.make_session_factory(_DB_ENGINE)


def get_session():
    """FastAPI dependency yielding a DB session (overridable in tests)."""
    session = _SessionLocal()
    try:
        yield session
    finally:
        session.close()


def _submission_text(request: "GradeRequest") -> str:
    if request.submission_text:
        return request.submission_text
    return "\n".join(f.content for f in (request.submission_files or []))


def _rubric_dicts(request: "GradeRequest") -> list:
    return [r.model_dump() if hasattr(r, "model_dump") else r for r in request.rubric]


def _grade_of_record_dict(request: "GradeRequest", result: GradeResult) -> dict:
    """Pin the canonical grade for dispute defense (X4). Temperatures reflect the
    ensemble settings; the input hash is derived from the exact rubric + text."""
    n = request.ensemble_n or 1
    temps = [request.ensemble_temperature or 0.4] * n if n > 1 else [0.0]
    rec = _gr.record_for(
        _rubric_dicts(request), _submission_text(request),
        model=get_model_config("grade").model, temperatures=temps,
        assessments=result.assessments, total=result.score, ai_flag=result.ai_content_flag,
    )
    return rec.to_dict()


# The client sends "team" when the judge typed no name (it has no way to know the
# business until the plan has been read).
_TEAM_PLACEHOLDER = "team"


def _record_team(student_id: str, result: GradeResult, filename: str) -> str:
    """What to file a run under in History. The judge's typed name wins; otherwise
    the name read out of the plan; only then the file name. Resolved server-side
    because the server is what actually read the document."""
    typed = (student_id or "").strip()
    if typed and typed.lower() != _TEAM_PLACEHOLDER:
        return typed
    return (result.business_name or "").strip() or filename


def _persist_grade(session, request: "GradeRequest", result: GradeResult):
    """Record the submission + grade + per-criterion breakdown in the backend
    store (A3). Best-effort: a persistence failure never fails the grade."""
    filename = request.submission_files[0].filename if request.submission_files else "submission.txt"
    sub = _persist.add_submission(session, team=_record_team(request.student_id, result, filename),
                                  filename=filename, content=_submission_text(request), status="graded")
    _persist.save_grade(
        session, sub.id, score=result.score,
        total_points=sum(a.max_points for a in result.assessments),
        feedback=result.feedback, assessments=[a.model_dump() for a in result.assessments],
        confidence_score=result.confidence_score, graded_ok=result.graded_ok,
        eligibility_status=result.eligibility_status, ai_content_flag=result.ai_content_flag,
        grade_of_record=result.grade_of_record,
    )
    return sub


# --- Stored plan files (kept so past runs can be re-opened) ------------------ #
# Files are named "<submission_id>__<sanitized-original-name>" so the DB needs no
# extra column. Lives under the bind-mounted ./backend/data, so it persists across
# container rebuilds on the server.
UPLOADS_DIR = "./backend/data/uploads"


def _store_plan_file(submission_id: int, filename: str, data: bytes) -> None:
    """Persist the raw uploaded plan file. Best-effort — never fails the grade."""
    try:
        os.makedirs(UPLOADS_DIR, exist_ok=True)
        safe = re.sub(r"[^A-Za-z0-9._-]", "_", filename or "plan")
        with open(os.path.join(UPLOADS_DIR, f"{submission_id}__{safe}"), "wb") as fh:
            fh.write(data)
    except Exception as e:  # pragma: no cover - disk/env dependent
        print(f"WARN: could not store plan file for submission {submission_id}: {e}")


def _find_plan_file(submission_id: int) -> Optional[str]:
    """Return the stored file path for a submission, or None."""
    matches = sorted(glob.glob(os.path.join(UPLOADS_DIR, f"{submission_id}__*")))
    return matches[0] if matches else None


def _persist_vision_grade(session, student_id: str, filename: str, text: str,
                          result: GradeResult, data: bytes):
    """Persist a vision grade + keep the original plan file (A3, extended to the
    vision path). Best-effort: a persistence failure never fails the grade."""
    try:
        sub = _persist.add_submission(session, team=_record_team(student_id, result, filename),
                                      filename=filename, content=text or "", status="graded")
        _persist.save_grade(
            session, sub.id, score=result.score,
            total_points=sum(a.max_points for a in result.assessments),
            feedback=result.feedback, assessments=[a.model_dump() for a in result.assessments],
            confidence_score=result.confidence_score, graded_ok=result.graded_ok,
            eligibility_status=result.eligibility_status, ai_content_flag=result.ai_content_flag,
        )
        _store_plan_file(sub.id, filename, data)
    except Exception as pe:  # pragma: no cover - persistence must never fail a grade
        print(f"WARN: could not persist vision grade: {pe}")

class SubmissionFile(BaseModel):
    filename: str
    content: str = Field(..., description="The text content of the file")

class GradeRequest(BaseModel):
    submission_files: Optional[List[SubmissionFile]] = Field(None, description="List of files to grade")
    rubric: List[RubricItem]
    student_id: str
    submission_text: Optional[str] = None
    guideline: Optional[str] = Field(None, description="Judges' guideline document, injected as fixed context")
    skip_rag: Optional[bool] = Field(None, description="Skip RAG retrieval (default True for business plans)")
    max_retries: Optional[int] = Field(None, description="Max Judge retries (capped for batch, full for live)")
    use_calibration: Optional[bool] = Field(None, description="Apply few-shot calibration (BYUMS-specific). Set False for the general rubric.")
    use_grounding: Optional[bool] = Field(None, description="Ground the grader in the static reference corpus (financial/market/quality guides). No-op if the corpus is not ingested.")
    use_evidence: Optional[bool] = Field(None, description="Ask the grader for a verbatim evidence quote per criterion; the Judge rejects quotes not found in the submission. Opt-in (default off).")
    ensemble_n: Optional[int] = Field(None, description="Grade N times and aggregate per criterion by median; reports grader disagreement. Default 1 (single pass).")
    ensemble_temperature: Optional[float] = Field(None, description="Fixed sampling temperature for ensemble runs (default 0.4). Ignored when ensemble_n <= 1.")


class ReportRequest(BaseModel):
    """A graded result to render as a PDF. `result` is the GradeResult the client
    already received from /grade (round-trips cleanly). Generic across rubrics."""
    result: GradeResult
    team_name: Optional[str] = ""
    rubric_label: Optional[str] = ""


def _report_filename(team_name: str) -> str:
    base = re.sub(r"[^A-Za-z0-9._-]+", "-", (team_name or "business-plan").strip()).strip("-")
    return f"{base or 'business-plan'}-report.pdf"


@app.post("/ingest", response_model=IngestResponse)
async def ingest(files: List[UploadFile] = File(...)):
    """
    Ingests PDF course materials.
    """
    try:
        count = await run_in_threadpool(rag.ingest_documents, files)
        return IngestResponse(status="success", files_processed=count)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/parse-rubric", response_model=List[RubricItem])
async def parse_rubric_endpoint(files: List[UploadFile] = File(...)):
    """
    Parses uploaded rubric files (PDF, DOCX, TXT, CSV, XLSX) into structured RubricItems.
    """
    try:
        rubric_items = rubric_parser.parse_rubric(files)
        return rubric_items
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/extract-text")
async def extract_text_endpoint(file: UploadFile = File(...)):
    """
    Extracts text from a single file.
    """
    try:
        text = rag.extract_text_from_file(file)
        return {"text": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/extract-files-content")
async def extract_files_content_endpoint(files: List[UploadFile] = File(...)):
    """
    Extracts text from multiple files and returns a list of {filename, content}.
    """
    results = []
    for file in files:
        try:
            text = await run_in_threadpool(rag.extract_text_from_file, file)
            results.append({"filename": file.filename, "content": text})
        except Exception as e:
            results.append({"filename": file.filename, "content": f"Error extracting text: {str(e)}"})
    return results

def _build_grade_inputs(request: "GradeRequest") -> dict:
    """Assemble the LangGraph inputs from a GradeRequest. Shared by /grade and
    the streaming endpoint so both honor the same optional flags."""
    if request.submission_text and not request.submission_files:
        files_input = [{"filename": "submission_text.txt", "content": request.submission_text}]
    else:
        files_input = [f.model_dump() for f in request.submission_files]
    inputs = {
        "submission_files": files_input,
        "rubric": request.rubric,
        "guideline": request.guideline or "",
        "context": [],
        "revision_number": 0,
    }
    # Only override agent defaults when the caller was explicit.
    for attr in ("skip_rag", "max_retries", "use_calibration", "use_grounding",
                 "use_evidence", "ensemble_n", "ensemble_temperature"):
        val = getattr(request, attr, None)
        if val is not None:
            inputs[attr] = val
    return inputs


@app.post("/grade", response_model=GradeResult)
async def grade_submission(request: GradeRequest, session=Depends(get_session)):
    """
    Grades a student submission using the agentic workflow, pins a grade-of-record
    for dispute defense, and persists the result in the backend store.
    """
    # Validate before the try so the 422 is not swallowed and re-raised as a 500.
    if not request.submission_files and not request.submission_text:
        raise HTTPException(status_code=422, detail="Provide submission_files or submission_text.")
    try:
        inputs = _build_grade_inputs(request)
        invoked = await run_in_threadpool(agent.app.invoke, inputs)
        result: GradeResult = invoked["grade_result"]
        result.grade_of_record = _grade_of_record_dict(request, result)
        try:
            await run_in_threadpool(_persist_grade, session, request, result)
        except Exception as pe:  # persistence must never fail a grade
            print(f"WARN: could not persist grade: {pe}")
        return result
    except Exception as e:
        print(f"Error grading submission: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/grade/report")
def grade_report(req: ReportRequest):
    """Render a graded result to a downloadable PDF. Stateless — the client posts
    back the GradeResult it received. Generic across rubrics."""
    # The client normally sends the name it is displaying; fall back to the name
    # read out of the plan so a report is attributable even if it doesn't.
    team = (req.team_name or "").strip() or (req.result.business_name or "").strip()
    try:
        pdf = build_report_pdf(req.result, team_name=team, rubric_label=req.rubric_label or "")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not build the PDF report: {e}")
    filename = _report_filename(team)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# --- Judge leaderboard: ranking + tie-band (OV#2) + fairness (OV#13) -------- #
@app.get("/leaderboard")
def leaderboard(shortlist: int = 10, band: float = 1.0, session=Depends(get_session)):
    """Rank persisted, eligible grades; flag the statistical tie zone at the
    shortlist cutoff; summarize fairness across submission groups."""
    rows = _persist.leaderboard(session)  # [(submission, grade)] desc by score
    scored = [(str(sub.id), grade.score) for sub, grade in rows]
    tie = _agg.cutoff_tie_zone(scored, k=shortlist, band=band)
    records = [
        _fair.GroupRecord(
            group=(sub.group or "unspecified"), score=grade.score,
            flagged=(grade.eligibility_status != "eligible"), ai_flag=grade.ai_content_flag,
        )
        for sub, grade in rows
    ]
    flag_rates = _fair.flag_rate_by_group(records)
    return {
        "ranking": [
            {"rank": i + 1, "submission_id": sub.id, "team": sub.team,
             "score": grade.score, "in_tie_zone": str(sub.id) in tie}
            for i, (sub, grade) in enumerate(rows)
        ],
        "tie_zone_at_cutoff": tie,
        "fairness": {
            "flag_rate_by_group": flag_rates,
            "disparate_impact_ratio": _fair.disparate_impact_ratio(flag_rates),
            "mean_score_by_group": _fair.mean_score_by_group(records),
        },
    }


# --- Batch grading (A2): persist each submission, then run the resumable job - #
class BatchRequest(BaseModel):
    submissions: List[SubmissionFile]
    rubric: List[RubricItem]
    guideline: Optional[str] = None
    use_calibration: Optional[bool] = None
    use_evidence: Optional[bool] = None
    ensemble_n: Optional[int] = None
    ensemble_temperature: Optional[float] = None
    max_retries: Optional[int] = None


def _batch_grade_item(session, submission_id: int, rubric, options: dict) -> int:
    """Grade one persisted submission and save its grade; returns the grade id.
    Module-level so tests can substitute it without invoking the LLM."""
    sub = _persist.get_submission(session, submission_id)
    req = GradeRequest(
        submission_files=[SubmissionFile(filename=sub.filename, content=sub.content)],
        rubric=rubric, student_id=sub.team, **options,
    )
    result: GradeResult = agent.app.invoke(_build_grade_inputs(req))["grade_result"]
    result.grade_of_record = _grade_of_record_dict(req, result)
    grade = _persist.save_grade(
        session, submission_id, score=result.score,
        total_points=sum(a.max_points for a in result.assessments),
        feedback=result.feedback, assessments=[a.model_dump() for a in result.assessments],
        confidence_score=result.confidence_score, graded_ok=result.graded_ok,
        eligibility_status=result.eligibility_status, ai_content_flag=result.ai_content_flag,
        grade_of_record=result.grade_of_record,
    )
    return grade.id


@app.post("/grade/batch")
def grade_batch(request: BatchRequest, session=Depends(get_session)):
    """Persist every submission, create a resumable job, and grade them. Note:
    for a very large field this should move to a background worker; it runs in
    the request here for a single-box deployment."""
    if not request.submissions:
        raise HTTPException(status_code=422, detail="Provide at least one submission.")
    subs = [
        _persist.add_submission(session, team="batch", filename=s.filename, content=s.content, status="pending")
        for s in request.submissions
    ]
    job = _batch.create_job(session, keys=[str(s.id) for s in subs], name="grade-batch")
    options = {k: v for k, v in {
        "guideline": request.guideline, "use_calibration": request.use_calibration,
        "use_evidence": request.use_evidence, "ensemble_n": request.ensemble_n,
        "ensemble_temperature": request.ensemble_temperature, "max_retries": request.max_retries,
    }.items() if v is not None}
    _batch.process_pending(session, job.id,
                           lambda key: _batch_grade_item(session, int(key), request.rubric, options))
    return {"job_id": job.id, **_batch.job_progress(session, job.id)}


@app.get("/grade/batch/{job_id}")
def grade_batch_status(job_id: int, session=Depends(get_session)):
    job = _batch.get_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Unknown batch job id.")
    return {"job_id": job_id, "status": job.status, **_batch.job_progress(session, job_id)}


# --- Live Grading Theater stream (Phase 3, eng review A1) ------------------- #
# EventSource can't POST, and the payload (rubric + submission) is too big for a
# query string, so we use the job-id pattern: POST the request to get an id,
# then open an EventSource GET on that id. The stream is driven by the REAL
# pipeline via LangGraph astream -> stage_event, so the theater animates actual
# progress. Requests are held in-process (single-box deployment); a restart
# drops in-flight stream requests, which is acceptable for a live single grade.
_STREAM_REQUESTS: dict = {}


@app.post("/grade/stream/start")
async def grade_stream_start(request: GradeRequest):
    """Register a grade request for streaming; returns a job_id to open with an
    EventSource GET at /grade/stream/{job_id}."""
    if not request.submission_files and not request.submission_text:
        raise HTTPException(status_code=422, detail="Provide submission_files or submission_text.")
    job_id = uuid.uuid4().hex
    _STREAM_REQUESTS[job_id] = request
    return {"job_id": job_id}


@app.get("/grade/stream/{job_id}")
async def grade_stream(job_id: str):
    """Stream the grading pipeline as SSE stage events (screening -> reading ->
    judging -> coaching -> done), then a terminal done/error event."""
    request = _STREAM_REQUESTS.pop(job_id, None)
    if request is None:
        raise HTTPException(status_code=404, detail="Unknown or expired stream job id.")
    inputs = _build_grade_inputs(request)

    async def event_gen():
        final = None
        try:
            async for update in agent.app.astream(inputs, stream_mode="updates"):
                for node_name, delta in update.items():
                    if node_name == "generate_feedback" and isinstance(delta, dict):
                        gr = delta.get("grade_result")
                        if gr is not None:
                            final = gr.model_dump() if hasattr(gr, "model_dump") else gr
                    ev = stage_event(node_name, delta if isinstance(delta, dict) else {})
                    if ev is not None:
                        yield {"event": "stage", "data": _json.dumps(ev)}
            yield {"event": "done", "data": _json.dumps({"stage": "done", "grade_result": final})}
        except Exception as e:  # a mid-stream failure must be a visible event, not a silent hang
            # Named "grade_error" (not "error") so it doesn't collide with the browser
            # EventSource's built-in connection-error event, which carries no data.
            yield {"event": "grade_error", "data": _json.dumps({"stage": "error", "message": str(e)})}

    # X-Accel-Buffering: no prevents nginx from buffering the stream (eng review:
    # the deployed stack sits behind nginx and would otherwise hang the theater).
    return EventSourceResponse(event_gen(), headers={"X-Accel-Buffering": "no"})

# Path (relative to the repo-root CWD the backend runs from) to the competition
# rubric CSV and the judges' guideline. Overridable via env for other deployments.
BPC_RUBRIC_CSV = os.getenv("BPC_RUBRIC_CSV", "BYUMS RUBRIC - Sheet1.csv")
BPC_GUIDELINE_MD = os.getenv("BPC_GUIDELINE_MD", "Judging_Instructions_BYUMS_Africa_BPC_2026.md")


@app.post("/grade-vision", response_model=GradeResult)
async def grade_vision(
    files: List[UploadFile] = File(...),
    rubric: str = Form(...),          # JSON string: list of rubric items
    guideline: str = Form(""),
    student_id: str = Form("team"),
    use_calibration: str = Form("true"),   # "false" for the general rubric
    session=Depends(get_session),
):
    """Vision grading (Phase 1b): render the uploaded plan PDF to slide images and
    grade them with a multimodal model, so image-based content (financial tables,
    licenses, bank statements) is actually seen — not inferred from headings."""
    try:
        rubric_items = [RubricItem(**r) for r in _json.loads(rubric)]
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Invalid rubric JSON: {e}")
    if not files:
        raise HTTPException(status_code=422, detail="Upload at least one PDF.")

    f = files[0]  # MVP: one plan per call
    suffix = os.path.splitext(f.filename or "plan.pdf")[1].lower()
    if suffix not in ADAPTER_SUFFIXES:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported plan file '{suffix or '(no extension)'}'. "
                   f"Supported: {', '.join(ADAPTER_SUFFIXES)}.",
        )

    MAX_UPLOAD_BYTES = 25 * 1024 * 1024  # keep in sync with nginx client_max_body_size
    if getattr(f, "size", None) and f.size > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File too large (max 25 MB).")
    data = await f.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File too large (max 25 MB).")

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp_path = tmp.name
    try:
        tmp.write(data)
        tmp.close()

        # Render + text-extract are CPU-bound; run off the event loop.
        normalized = await run_in_threadpool(get_adapter(tmp_path).load, tmp_path)
        image_uris = vision_grade.pngs_to_datauris(normalized.page_images)
        has_text = bool((normalized.text or "").strip())
        # Images are evidence, not a precondition. A .docx without pictures and a
        # .txt/.md have nothing to render, and refusing them here would mean a mixed
        # batch (some PDFs, some DOCX) could not be screened in one pass. Fail only
        # when the file yielded NOTHING to grade.
        if not image_uris and not has_text:
            detail = ("Could not render slide images from the PDF and extracted no text "
                      "(is pypdfium2 installed? is the PDF a scan?)."
                      if suffix == ".pdf" else
                      f"Extracted neither text nor images from this {suffix} file — "
                      "nothing to grade. Check the file opens correctly.")
            raise HTTPException(status_code=422, detail=detail)

        # Competition mode (use_calibration) gates BOTH the few-shot calibration and
        # the BYUMS-specific eligibility/DQ screen. The general rubric uses neither.
        competition_mode = use_calibration.lower() != "false"
        if competition_mode:
            elig = screen_eligibility(normalized.text)
            calib = calibration.build_calibration_block(
                agent._load_fewshot_examples(), exclude_filenames={f.filename or ""}
            )
        else:
            elig = EligibilityResult(status="eligible", reasons=[], advisory_notes=[], ai_content_flag=False)
            calib = ""
        rubric_str = agent._format_rubric(rubric_items)

        grade_data = await run_in_threadpool(
            vision_grade.grade_with_vision,
            agent.grader_system(competition=competition_mode), rubric_items, rubric_str,
            guideline or "None provided.", calib, image_uris,
            submission_text=normalized.text,
        )

        # Business name from the deck's own extracted slide text, not the file name.
        detected = extract_business_name(normalized.text)

        if image_uris:
            read_as = f"Rendered {len(image_uris)} image(s) from the plan"
            read_as += (" plus its extracted text; graded with the vision model."
                        if has_text else "; graded with the vision model.")
        else:
            read_as = ("No images in this document (nothing to render) — graded from its "
                       "extracted text with the vision model.")
        thinking = [read_as, f"Eligibility: {elig.status}"]
        if detected:
            thinking.append(f'Business name read from the plan: "{detected.name}" ({detected.source}).')
        # The eligibility screen runs on extracted text; warn when a deck is image-only.
        if image_uris and len((normalized.text or "").strip()) < 200:
            thinking.append("Note: little extractable text — the eligibility/DQ screen is limited for image-only decks.")
        dq_reasons = list(elig.reasons) + [f"(advisory) {n}" for n in elig.advisory_notes]

        result = to_grade_result(
            grade_data,
            feedback=grade_data.general_feedback or "See the per-criterion notes above.",
            thinking_process=thinking,
            confidence_score=0.9,
            eligibility_status=elig.status,
            dq_reasons=dq_reasons,
            ai_content_flag=elig.ai_content_flag,
            business_name=detected.name,
        )
        # Persist the run + keep the original plan file (best-effort, off the loop).
        await run_in_threadpool(_persist_vision_grade, session, student_id,
                                f.filename or "plan", normalized.text, result, data)
        return result
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in vision grading: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            tmp.close()
        except Exception:
            pass
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.get("/grade-history")
def grade_history(limit: int = 100, session=Depends(get_session)):
    """Recent graded plans (most recent first), each with its latest grade. Powers
    the Business -> History view. Includes text and vision runs."""
    subs = session.execute(
        select(_persist.Submission).order_by(_persist.Submission.created_at.desc()).limit(limit)
    ).scalars().all()
    out = []
    for sub in subs:
        g = _persist.latest_grade(session, sub.id)
        if not g:
            continue
        out.append({
            "submission_id": sub.id,
            "filename": sub.filename,
            "team": sub.team,
            "score": g.score,
            "total_points": g.total_points,
            "eligibility_status": g.eligibility_status,
            "graded_ok": g.graded_ok,
            "created_at": sub.created_at.isoformat(),
            "has_file": _find_plan_file(sub.id) is not None,
        })
    return out


@app.get("/grade-history/{submission_id}")
def grade_history_detail(submission_id: int, session=Depends(get_session)):
    """Full breakdown for one past run (score, feedback, per-criterion scores)."""
    sub = _persist.get_submission(session, submission_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found.")
    g = _persist.latest_grade(session, submission_id)
    if not g:
        raise HTTPException(status_code=404, detail="No grade for this submission.")
    return {
        "submission_id": sub.id,
        "filename": sub.filename,
        "team": sub.team,
        "created_at": sub.created_at.isoformat(),
        "score": g.score,
        "total_points": g.total_points,
        "feedback": g.feedback,
        "confidence_score": g.confidence_score,
        "graded_ok": g.graded_ok,
        "eligibility_status": g.eligibility_status,
        "ai_content_flag": g.ai_content_flag,
        "assessments": [
            {"criteria_index": a.criteria_index, "criteria_name": a.criteria_name,
             "awarded_points": a.awarded_points, "max_points": a.max_points, "reason": a.reason}
            for a in g.assessments
        ],
        "has_file": _find_plan_file(sub.id) is not None,
    }


@app.get("/plan-file/{submission_id}")
def plan_file(submission_id: int):
    """Download the original uploaded plan file for a past run, if it was kept."""
    path = _find_plan_file(submission_id)
    if not path or not os.path.exists(path):
        raise HTTPException(status_code=404, detail="No stored file for this submission.")
    original = os.path.basename(path).split("__", 1)[-1]
    return FileResponse(path, filename=original)


@app.get("/bpc-rubric")
async def bpc_rubric():
    """Serve the BYUMS competition rubric, split into the plan (80 pts) and video
    (20 pts) components, plus the judges' guideline text for use as fixed grading
    context. Single source of truth is the rubric CSV."""
    if not os.path.exists(BPC_RUBRIC_CSV):
        raise HTTPException(status_code=404, detail=f"Rubric CSV not found at '{BPC_RUBRIC_CSV}' (run from repo root).")
    try:
        items = rubric_csv.parse_byums_rubric_csv(BPC_RUBRIC_CSV)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse rubric CSV: {e}")
    plan, video = rubric_csv.split_video_plan(items)

    guideline = ""
    if os.path.exists(BPC_GUIDELINE_MD):
        try:
            with open(BPC_GUIDELINE_MD, "r", encoding="utf-8") as fh:
                guideline = fh.read()
        except Exception:
            guideline = ""

    return {
        "plan": rubric_csv.rubric_to_dicts(plan),
        "video": rubric_csv.rubric_to_dicts(video),
        "full": rubric_csv.rubric_to_dicts(items),
        "plan_total": rubric_csv.total_points(plan),
        "video_total": rubric_csv.total_points(video),
        "full_total": rubric_csv.total_points(items),
        "guideline": guideline,
    }


@app.get("/bpc-fewshot-scores")
async def bpc_fewshot_scores():
    """Return the human-scored reference plans (for the AI-vs-human head-to-head).
    Per-criterion human scores only — no plan text."""
    examples = agent._load_fewshot_examples()
    return [
        {
            "filename": e.filename,
            "business_name": e.business_name,
            "human_total": e.human_total,
            "items": [
                {"criteria": it.criteria, "awarded": it.awarded, "max_points": it.max_points}
                for it in e.items
            ],
        }
        for e in examples
    ]


@app.get("/general-rubric")
async def general_rubric_endpoint():
    """A general-purpose business-plan rubric (100 pts), not competition-specific.
    Use with use_calibration=False (the BYUMS few-shot example doesn't apply)."""
    return {"rubric": general_rubric.to_dicts(), "total": general_rubric.total_points()}


@app.get("/")
async def root():
    return {"message": "Welcome to GradeWise API"}