import os
import json as _json
import tempfile
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from sse_starlette.sse import EventSourceResponse
from backend.src.stream_events import stage_event
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
from backend.src.input_adapter import get_adapter
from backend.src.grading import to_grade_result
from backend.src.eligibility import screen_eligibility, EligibilityResult
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
async def grade_submission(request: GradeRequest):
    """
    Grades a student submission using the agentic workflow.
    """
    # Validate before the try so the 422 is not swallowed and re-raised as a 500.
    if not request.submission_files and not request.submission_text:
        raise HTTPException(status_code=422, detail="Provide submission_files or submission_text.")
    try:
        inputs = _build_grade_inputs(request)
        result = await run_in_threadpool(agent.app.invoke, inputs)
        return result["grade_result"]
    except Exception as e:
        print(f"Error grading submission: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
            yield {"event": "error", "data": _json.dumps({"stage": "error", "message": str(e)})}

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
    if suffix not in (".pdf", ".pptx"):
        raise HTTPException(status_code=422, detail="Vision grading requires a PDF or PPTX file.")

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
        if not image_uris:
            detail = ("Could not render slide images from the PDF (is pypdfium2 installed?)."
                      if suffix == ".pdf" else
                      "No embedded images found in the .pptx — grade this deck via the text "
                      "path (/grade) instead, which reads its slide text and tables.")
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
        )

        thinking = [
            f"Rendered {len(image_uris)} slide image(s) and graded with the vision model.",
            f"Eligibility: {elig.status}",
        ]
        # The eligibility screen runs on extracted text; warn when a deck is image-only.
        if len((normalized.text or "").strip()) < 200:
            thinking.append("Note: little extractable text — the eligibility/DQ screen is limited for image-only decks.")
        dq_reasons = list(elig.reasons) + [f"(advisory) {n}" for n in elig.advisory_notes]

        return to_grade_result(
            grade_data,
            feedback=grade_data.general_feedback or "See the per-criterion notes above.",
            thinking_process=thinking,
            confidence_score=0.9,
            eligibility_status=elig.status,
            dq_reasons=dq_reasons,
            ai_content_flag=elig.ai_content_flag,
        )
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