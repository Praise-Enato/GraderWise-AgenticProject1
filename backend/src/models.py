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
    course_guide: Optional[str] = Field(None, description="Detailed comprehensive course guide text for this criteria")

class GradeResult(BaseModel):
    score: float = Field(..., description="The score awarded")
    feedback: str = Field(..., description="Feedback explaining the score")
    citations: List[str] = Field(default_factory=list, description="Relevant citations from the submission or course material")
    thinking_process: List[str] = Field(default_factory=list, description="Step-by-step logs of the agent's reasoning")
    confidence_score: float = Field(default=1.0, description="Confidence score of the final grade (0.0 to 1.0)")

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
    rubric: str = ""  # New field for explicit rubric context
    context_files: List[str] = []

class ChatResponse(BaseModel):
    response: str
    sources: List[str] = []

# Business Plan Grading Models

class PPTXFile(BaseModel):
    """Model for PPTX file metadata after extraction"""
    filename: str = Field(..., description="Name of the PPTX file")
    markdown_content: str = Field(..., description="Markdown representation of the presentation")
    slide_count: int = Field(..., description="Number of slides in the presentation")
    has_tables: bool = Field(default=False, description="Whether the presentation contains tables")
    has_images: bool = Field(default=False, description="Whether the presentation contains images")
    text_length: int = Field(..., description="Total character count of extracted text")

class SubmissionFile(BaseModel):
    """Model for a submission file (used in grading requests)"""
    filename: str = Field(..., description="Name of the file")
    content: str = Field(..., description="The text content of the file")

class BusinessPlanGradeRequest(BaseModel):
    """Request model for business plan grading"""
    pptx_files: Optional[List[dict]] = Field(None, description="List of PPTX files (as dicts with filename and content)")
    document_files: Optional[List[SubmissionFile]] = Field(None, description="List of document files (PDF/DOCX converted to text)")
    rubric: List[RubricItem] = Field(..., description="Business plan rubric criteria")
    student_id: str = Field(..., description="Unique identifier for the student/team")
    business_context_type: str = Field(default="startup", description="Type of business plan: startup, enterprise, or nonprofit")
    grading_type: str = Field(default="business_plan", description="Grading type identifier")

# --- Agent State Definition (Shared) ---
from typing import TypedDict, List, Any

class AgentState(TypedDict, total=False):
    # Required fields
    submission_files: List[dict] # List of {filename, content}
    rubric: List[RubricItem]
    # Optional fields (total=False makes all fields optional by default)
    context: List[str]
    grade_data: dict
    final_feedback: str
    grade_result: GradeResult
    # Control Fields for Self-Correction Loop
    revision_number: int       # Tracks retry attempts (default: 0)
    grader_feedback: str       # Rejection reason from the Judge (default: "")
    is_valid: bool             # Flag for conditional edge (default: False)
    skip_rag: bool             # Optional flag to skip RAG (default: False)
    thinking_process: List[str] # Log of agent's thoughts
    # Business Plan Grading Fields (NEW)
    grading_type: str          # "academic" or "business_plan"
    pptx_content: List[dict]   # Processed PPTX slides
    business_context_type: str # "startup", "enterprise", or "nonprofit"
    grading_examples: List[str] # RAG-retrieved grading examples from training data
