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
