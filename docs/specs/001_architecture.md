# Architecture Specification

## Pydantic Models

```python
from pydantic import BaseModel, Field
from typing import List, Optional

class RubricItem(BaseModel):
    criteria: str = Field(..., description="The criteria for evaluating the submission")
    max_points: int = Field(..., description="Maximum points available for this criteria")

class GradeResult(BaseModel):
    score: int = Field(..., description="The score awarded")
    feedback: str = Field(..., description="Feedback explaining the score")
    citations: List[str] = Field(default_factory=list, description="Relevant citations from the submission or course material")

class IngestRequest(BaseModel):
    submission_text: str = Field(..., description="The student's submission text")
    rubric_id: str = Field(..., description="ID of the rubric to use for grading")
    student_id: Optional[str] = Field(None, description="Optional student identifier")
```

## Agent Workflow

The grading agent generally follows these 4 steps:

1.  **Receive Text**: The system accepts an `IngestRequest` containing the student submission and rubric identifier.
2.  **Retrieve Context (RAG)**: Using the submission content and rubric criteria, relevant course materials are retrieved from the vector store (ChromaDB) to provide context for grading.
3.  **Check Rubric**: The agent iterates through each `RubricItem` associated with the provided `rubric_id`.
4.  **Generate Score**: For each rubric item, the Llama 3 model (via Groq) evaluates the submission against the criteria and retrieved context to generate a `GradeResult` (score, feedback, citations).
