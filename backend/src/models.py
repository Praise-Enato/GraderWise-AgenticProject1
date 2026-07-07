from pydantic import BaseModel, Field
from typing import List, Optional


class RubricItem(BaseModel):
    criteria: str = Field(..., description="The criteria for evaluating the submission")
    max_points: float = Field(..., description="Maximum points available for this criteria")
    description: str = Field(..., description="Detailed description of the criteria for full points")
    developing_points: Optional[float] = Field(None, description="Points for partial or developing mastery")
    developing_description: Optional[str] = Field(None, description="Description for partial or developing mastery")
    zero_points: Optional[float] = Field(0.0, description="Points for zero mastery (usually 0)")
    zero_description: Optional[str] = Field(None, description="Description for zero mastery or missing criteria")


class CriterionAssessment(BaseModel):
    """Per-criterion grading result.

    This survives all the way to the API response so per-criterion agreement,
    the leaderboard breakdown, and disagreement flags can be computed. Previously
    the per-criterion data was computed in the agent and dropped before the
    response (see eng review: GradeResult only carried a flat total).
    """
    criteria_index: int = Field(..., description="1-based index of the rubric criterion")
    criteria_name: str = Field(..., description="Name of the criterion assessed")
    awarded_points: float = Field(..., description="Points awarded for this criterion")
    max_points: float = Field(..., description="Maximum points possible for this criterion")
    reason: str = Field("", description="Justification citing the rubric line or measured quantity")


# Eligibility status constants. A plan is screened for competition disqualifiers
# BEFORE it is ranked, so an ineligible plan is flagged rather than silently
# buried in the ranking with a low score.
ELIGIBILITY_ELIGIBLE = "eligible"
ELIGIBILITY_INELIGIBLE = "ineligible"
ELIGIBILITY_NEEDS_REVIEW = "needs_review"
ELIGIBILITY_STATUSES = (ELIGIBILITY_ELIGIBLE, ELIGIBILITY_INELIGIBLE, ELIGIBILITY_NEEDS_REVIEW)


class GradeResult(BaseModel):
    score: float = Field(..., description="Total score awarded (sum of per-criterion awards)")
    feedback: str = Field(..., description="Participant-facing feedback")
    citations: List[str] = Field(default_factory=list, description="Relevant citations")
    thinking_process: List[str] = Field(default_factory=list, description="Step-by-step reasoning logs")
    confidence_score: float = Field(
        default=1.0,
        description="NOTE: derived from retry count, NOT calibrated to correctness. "
                    "Do not present to users as a real confidence value.",
    )

    # --- Per-criterion breakdown (enables per-criterion agreement + leaderboard) ---
    assessments: List[CriterionAssessment] = Field(default_factory=list)

    # --- Grading status: a parse failure must be distinguishable from a real zero ---
    graded_ok: bool = Field(
        default=True,
        description="False if grading failed (e.g. unparseable model output). A failed grade "
                    "must be flagged for human review, never ranked as a genuine 0.",
    )
    error: Optional[str] = Field(default=None, description="Error detail when graded_ok is False")

    # --- Eligibility / disqualifier screen (competition gating logic) ---
    eligibility_status: str = Field(
        default=ELIGIBILITY_ELIGIBLE, description="eligible | ineligible | needs_review"
    )
    dq_reasons: List[str] = Field(
        default_factory=list, description="Reasons a plan was flagged ineligible / needs review"
    )
    ai_content_flag: bool = Field(
        default=False,
        description="True if the submission is suspected AI-generated content "
                    "(the competition asks judges to flag this).",
    )


class StudentSubmission(BaseModel):
    text: str = Field(..., description="The student's submission text")
    student_id: str = Field(..., description="Unique identifier for the student")


class IngestResponse(BaseModel):
    status: str = Field(..., description="Status of the ingestion process")
    files_processed: int = Field(..., description="Number of files successfully processed")


class ChatRequest(BaseModel):
    question: str
    feedback: str
    submission_text: str = ""
    rubric: str = ""
    context_files: List[str] = []


class ChatResponse(BaseModel):
    response: str
    sources: List[str] = []
