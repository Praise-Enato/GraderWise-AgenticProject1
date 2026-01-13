import os

# Disable ChromaDB/PostHog Telemetry
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_SERVER_NO_INTERACTIVE_MODE"] = "True"
os.environ["OTEL_PYTHON_DISABLED"] = "True"

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from backend.src.models import RubricItem, GradeResult, IngestResponse
from backend.src import rag
from backend.src import agent
from backend.src import rubric_parser

app = FastAPI(title="GradeWise API")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from typing import List, Optional, Dict, Any

class GradeRequest(BaseModel):
    submission_text: str
    rubric: Optional[List[RubricItem]] = None
    course_name: Optional[str] = None
    student_id: str
    messages: List[Dict[str, Any]] = []
    grade_data: Optional[Dict[str, Any]] = None

@app.post("/ingest", response_model=IngestResponse)
async def ingest(files: List[UploadFile] = File(...)):
    """
    Ingests PDF course materials.
    """
    try:
        count = rag.ingest_documents(files)
        return IngestResponse(status="success", files_processed=count)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/parse-rubric", response_model=List[RubricItem])
async def parse_rubric_endpoint(files: List[UploadFile] = File(...)):
    """
    Parses uploaded rubric files (PDF, DOCX, TXT, CSV, XLSX) into structured RubricItems.
    Also saves them to 'backend/data/rubrics' for the Student Portal to access.
    """
    try:
        # Save files to disk first
        save_dir = "./backend/data/rubrics"
        os.makedirs(save_dir, exist_ok=True)
        
        for file in files:
            # Reset cursor (just in case, though usually at 0)
            file.file.seek(0)
            
            save_path = os.path.join(save_dir, file.filename)
            with open(save_path, "wb") as buffer:
                import shutil
                shutil.copyfileobj(file.file, buffer)
            
            # Reset cursor for parsing
            file.file.seek(0)

        # Parse Logic
        rubric_items = rubric_parser.parse_rubric(files)
        return rubric_items
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/extract-text")
async def extract_text_endpoint(file: UploadFile = File(...)):
    """
    Extracts text from a single file (PDF, DOCX, TXT, CSV, XLSX) for student submission.
    """
    try:
        text = rag.extract_text_from_file(file)
        return {"text": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/grade")
async def grade_submission(request: GradeRequest):
    """
    Grades a student submission using the agentic workflow.
    Returns the FULL graph state (messages, grade_data, etc.).
    """
    try:
        rubric_to_use = request.rubric
        
        # DYNAMIC RUBRIC LOADING
        if not rubric_to_use:
            if not request.course_name:
                # If both are missing, we can't grade (unless it's just a Q&A follow up?)
                # But Q&A needs grade_data history. If this is a fresh submission, we need a rubric.
                if not request.grade_data:
                     raise HTTPException(status_code=400, detail="Either 'rubric' or 'course_name' must be provided for a new submission.")
                else:
                    rubric_to_use = [] # Q&A mode, rubric might not be strictly needed if grade_data exists
            else:
                 # Search for rubric file in backend/data/rubrics
                 rubric_dir = "./backend/data/rubrics"
                 found_file = None
                 normalized_course = request.course_name.lower().replace(" ", "")
                 
                 if os.path.exists(rubric_dir):
                     for fname in os.listdir(rubric_dir):
                         if normalized_course in fname.lower().replace(" ", ""):
                             found_file = os.path.join(rubric_dir, fname)
                             break
                 
                 if found_file:
                     print(f"Found Rubric File: {found_file}")
                     raw_text = rag.extract_text_from_path(found_file, os.path.basename(found_file))
                     rubric_to_use = rubric_parser.parse_rubric_text(raw_text)
                 else:
                     raise HTTPException(status_code=404, detail=f"No course material and rubric available at this time for '{request.course_name}'.")

        inputs = {
            "submission_text": request.submission_text,
            "rubric": rubric_to_use if rubric_to_use else [],
            "context": [], # Initial empty context, will be populated by retrieve node
            "messages": request.messages,
            "grade_data": request.grade_data if request.grade_data else {},
            "grade_result": None # Initial placeholder
        }
        
        # Invoke the graph
        result = agent.app.invoke(inputs)
        
        # Return the full state so frontend can sync messages and grade_data
        return result
        
    except HTTPException as he:
        raise he
    except Exception as e:
        # Log error in real app
        print(f"Error grading submission: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "Welcome to GradeWise API"}
