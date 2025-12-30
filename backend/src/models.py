from pydantic import BaseModel, Field
from typing import List, Optional

class RubricItem(BaseModel):
    criteria: str = Field(..., description="The criteria for evaluating the submission")
    max_points: int = Field(..., description="Maximum points available for this criteria")
    description: str = Field(..., description="Detailed description of the criteria")

class GradeResult(BaseModel):
    score: float = Field(..., description="The score awarded")
    feedback: str = Field(..., description="Feedback explaining the score")
    citations: List[str] = Field(default_factory=list, description="Relevant citations from the submission or course material")

class StudentSubmission(BaseModel):
    text: str = Field(..., description="The student's submission text")
    student_id: str = Field(..., description="Unique identifier for the student")

class IngestResponse(BaseModel):
    status: str = Field(..., description="Status of the ingestion process")
    files_processed: int = Field(..., description="Number of files successfully processed")
