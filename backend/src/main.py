from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from backend.src.models import RubricItem, GradeResult, IngestResponse
from backend.src import rag
from backend.src import agent

app = FastAPI(title="GradeWise API")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GradeRequest(BaseModel):
    submission_text: str
    rubric: List[RubricItem]
    student_id: str

@app.post("/ingest", response_model=IngestResponse)
async def ingest(files: List[UploadFile] = File(...)):
    """
    Ingests PDF course materials.
    """
    try:
        count = rag.ingest_course_material(files)
        return IngestResponse(status="success", files_processed=count)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/grade", response_model=GradeResult)
async def grade_submission(request: GradeRequest):
    """
    Grades a student submission using the agentic workflow.
    """
    try:
        inputs = {
            "submission_text": request.submission_text,
            "rubric": request.rubric,
            "context": [], # Initial empty context, will be populated by retrieve node
            "grade_result": None # Initial placeholder
        }
        
        result = agent.app.invoke(inputs)
        
        return result["grade_result"]
    except Exception as e:
        # Log error in real app
        print(f"Error grading submission: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "Welcome to GradeWise API"}
