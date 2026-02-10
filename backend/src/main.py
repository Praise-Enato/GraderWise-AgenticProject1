import os
import json
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
from backend.src.models import RubricItem, GradeResult, IngestResponse, ChatRequest, ChatResponse, BusinessPlanGradeRequest, SubmissionFile
from backend.src import rag
from backend.src import agent
from backend.src import rubric_parser
from backend.src.pptx_processor import PPTXProcessor
from backend.src import business_rubric_templates
from backend.src.business_rag import BusinessRAG
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from fastapi.concurrency import run_in_threadpool

# Disable ChromaDB/PostHog Telemetry
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_SERVER_NO_INTERACTIVE_MODE"] = "True"
os.environ["OTEL_PYTHON_DISABLED"] = "True"

app = FastAPI(title="GradeWise API")

# --- CORS CONFIGURATION (THE FIX) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # <--- CHANGED FROM "localhost:3000" TO "*"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ------------------------------------

# --- AUTO-INGEST BUSINESS CONTEXT STARTER PACK ON STARTUP ---
@app.on_event("startup")
async def startup_event():
    """Auto-ingest business context starter pack on first run."""
    try:
        BusinessRAG.auto_ingest_starter_pack()
    except Exception as e:
        print(f"Warning: Business context auto-ingest failed: {e}")


class SubmissionFile(BaseModel):
    filename: str
    content: str = Field(..., description="The text content of the file")

class GradeRequest(BaseModel):
    submission_files: Optional[List[SubmissionFile]] = Field(None, description="List of files to grade")
    rubric: List[RubricItem]
    student_id: str
    submission_text: Optional[str] = None 

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

@app.post("/grade", response_model=GradeResult)
async def grade_submission(request: GradeRequest):
    """
    Grades a student submission using the agentic workflow.
    """
    try:
        if request.submission_text and not request.submission_files:
             files_input = [{"filename": "submission_text.txt", "content": request.submission_text}]
        else:
             files_input = [f.dict() for f in request.submission_files]

        inputs = {
            "submission_files": files_input,
            "rubric": request.rubric,
            "context": [], 
            "grade_result": None 
        }
        
        result = await run_in_threadpool(agent.app.invoke, inputs)
        return result["grade_result"]
    except Exception as e:
        print(f"Error grading submission: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# @app.post("/chat", response_model=ChatResponse)
# async def chat_endpoint(request: ChatRequest):
#     """
#     RAG-powered chat for discussing feedback.
#     """
#     try:
#         context = rag.retrieve_context(request.question)
        
#         system_prompt = """You are an intelligent Academic Tutor and Feedback Coach.
#         Your goal is to help the student understand their feedback and improve their work.
        
#         RULES:
#         - Explain regarding the SPECIFIC feedback provided.
#         - Use the Course Context to backup your explanations.
#         - Do NOT give the direct answer if it's a specific problem (Socratic method).
#         - If the user asks for general help, verify it aligns with the course context.
#         - Be encouraging but professional.
#         """
        
#         user_prompt = f"""
#         STUDENT QUESTION: {request.question}
        
#         COURSE CONTEXT (RAG):
#         {chr(10).join(context)}
        
#         GRADING RUBRIC:
#         {request.rubric}
        
#         SUBMISSION EXCERPT:
#         {request.submission_text[:2000]}...
        
#         GRADER FEEDBACK:
#         {request.feedback}
        
#         """
        
#         prompt = ChatPromptTemplate.from_messages([
#             ("system", system_prompt),
#             ("user", user_prompt)
#         ])
        
#         chain = prompt | agent.llm | StrOutputParser()
#         response = chain.invoke({})
        
#         return ChatResponse(
#             response=response,
#             sources=context
#         )
        
#     except Exception as e:
#         print(f"Error in chat: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

# --- BUSINESS PLAN GRADING ENDPOINTS ---

@app.post("/extract-pptx")
async def extract_pptx_endpoint(file: UploadFile = File(...)):
    """
    Extract markdown from PPTX file using Microsoft MarkItDown.
    Returns markdown content and metadata (slide count, tables, images).
    """
    # Validate file type
    if not file.filename.lower().endswith('.pptx'):
        raise HTTPException(status_code=400, detail="File must be a PPTX file")

    temp_path = None
    try:
        # Save temp file with unique name to avoid collisions
        import uuid
        unique_filename = f"{uuid.uuid4()}_{file.filename}"
        temp_path = f"./backend/data/temp_uploads/{unique_filename}"
        os.makedirs("./backend/data/temp_uploads", exist_ok=True)

        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Extract using MarkItDown
        processor = PPTXProcessor()
        result = processor.extract_to_markdown(temp_path)

        return result

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error extracting PPTX: {e}")
        raise HTTPException(status_code=500, detail=f"PPTX extraction failed: {str(e)}")
    finally:
        # Always cleanup temp file
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as e:
                print(f"Warning: Could not remove temp file {temp_path}: {e}")


@app.post("/ingest-business-context")
async def ingest_business_context_endpoint(
    files: List[UploadFile] = File(...),
    context_type: str = Form("startup")
):
    """
    Ingest business-specific context materials (benchmarks, guides, templates).

    Parameters:
    - files: PDF, DOCX, or TXT files containing business context
    - context_type: Category tag — "startup", "enterprise", "nonprofit", or "general"
    """
    try:
        count = await run_in_threadpool(BusinessRAG.ingest_business_context, files, context_type)
        return {"status": "success", "files_processed": count, "context_type": context_type}
    except Exception as e:
        print(f"Error ingesting business context: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/grade-business-plan", response_model=GradeResult)
async def grade_business_plan_endpoint(
    student_id: str = Form(...),
    business_context_type: str = Form("startup"),
    pptx_files: Optional[List[UploadFile]] = File(None),
    document_files: Optional[List[UploadFile]] = File(None),
    rubric_json: str = Form(...)  # JSON string of rubric
):
    """
    Grade business plan with PPTX + document submissions.

    Parameters:
    - student_id: Unique identifier for the student/team
    - business_context_type: "startup", "enterprise", or "nonprofit"
    - pptx_files: PPTX pitch deck files (optional)
    - document_files: PDF/DOCX business plan documents (optional)
    - rubric_json: JSON string of rubric criteria
    """
    temp_files = []  # Track temp files for cleanup
    try:
        # Parse rubric from JSON
        try:
            rubric_data = json.loads(rubric_json)
            rubric = [RubricItem(**item) for item in rubric_data]
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Invalid rubric JSON: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid rubric format: {str(e)}")

        # Process PPTX files using MarkItDown
        pptx_content = []
        if pptx_files:
            processor = PPTXProcessor()
            import uuid
            for pptx_file in pptx_files:
                # Validate file type
                if not pptx_file.filename.lower().endswith('.pptx'):
                    raise HTTPException(status_code=400, detail=f"File {pptx_file.filename} must be a PPTX file")

                # Save temp file with unique name
                unique_filename = f"{uuid.uuid4()}_{pptx_file.filename}"
                temp_path = f"./backend/data/temp_uploads/{unique_filename}"
                temp_files.append(temp_path)
                os.makedirs("./backend/data/temp_uploads", exist_ok=True)

                with open(temp_path, "wb") as f:
                    content = await pptx_file.read()
                    f.write(content)

                # Extract markdown
                result = processor.extract_to_markdown(temp_path)
                pptx_content.append({
                    "filename": pptx_file.filename,
                    "content": result["markdown_content"]
                })

        # Process document files (extract text)
        doc_content = []
        if document_files:
            for doc_file in document_files:
                try:
                    text = await run_in_threadpool(rag.extract_text_from_file, doc_file)
                    doc_content.append({
                        "filename": doc_file.filename,
                        "content": text
                    })
                except Exception as e:
                    print(f"Error extracting {doc_file.filename}: {e}")
                    doc_content.append({
                        "filename": doc_file.filename,
                        "content": f"Error extracting text: {str(e)}"
                    })

        # Combine PPTX + documents
        all_files = pptx_content + doc_content

        if not all_files:
            raise HTTPException(status_code=400, detail="No files provided for grading")

        # Invoke business workflow via router
        inputs = {
            "submission_files": all_files,
            "rubric": rubric,
            "grading_type": "business_plan",
            "business_context_type": business_context_type,
            "context": [],  # business_retrieve node populates this from Business RAG
            "grade_result": None,
            "student_id": student_id
        }

        result = await run_in_threadpool(agent.router_app.invoke, inputs)
        return result["grade_result"]

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        print(f"Error grading business plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup all temp files
        for temp_path in temp_files:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception as e:
                    print(f"Warning: Could not remove temp file {temp_path}: {e}")


@app.get("/business-rubric-template/{business_type}")
async def get_business_rubric_template(business_type: str):
    """
    Get rubric template for business plan type.

    Parameters:
    - business_type: "startup", "enterprise", or "nonprofit"

    Returns:
    - List of RubricItem objects as JSON
    """
    try:
        rubric = business_rubric_templates.get_rubric_template(business_type)
        return [item.dict() for item in rubric]
    except Exception as e:
        print(f"Error getting rubric template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- ROOT ENDPOINT ---

@app.get("/")
async def root():
    return {
        "message": "Welcome to GradeWise API",
        "endpoints": {
            "academic_grading": "/grade",
            "business_plan_grading": "/grade-business-plan",
            "pptx_extraction": "/extract-pptx",
            "business_rubric_template": "/business-rubric-template/{business_type}",
            "ingest_materials": "/ingest",
            "ingest_business_context": "/ingest-business-context",
            "parse_rubric": "/parse-rubric"
        }
    }