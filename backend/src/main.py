import os

# Disable ChromaDB/PostHog Telemetry
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_SERVER_NO_INTERACTIVE_MODE"] = "True"
os.environ["OTEL_PYTHON_DISABLED"] = "True"

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from backend.src.models import RubricItem, GradeResult, IngestResponse, ChatRequest, ChatResponse
from backend.src import rag
from backend.src import agent
from backend.src import rubric_parser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

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
        count = rag.ingest_documents(files)
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
    Extracts text from a single file (PDF, DOCX, TXT, CSV, XLSX) for student submission.
    """
    try:
        text = rag.extract_text_from_file(file)
        return {"text": text}
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

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    RAG-powered chat for discussing feedback.
    """
    try:
        # 1. Retrieve RAG Context if relevant
        # Only query RAG if the question warrants it (optimization)
        context = rag.retrieve_context(request.question)
        
        # 2. Setup Prompt using Agent's LLM
        system_prompt = """You are an intelligent Academic Tutor and Feedback Coach.
        Your goal is to help the student understand their feedback and improve their work.
        
        RULES:
        - Explain regarding the SPECIFIC feedback provided.
        - Use the Course Context to backup your explanations.
        - Do NOT give the direct answer if it's a specific problem (Socratic method).
        - If the user asks for general help, verify it aligns with the course context.
        - Be encouraging but professional.
        """
        
        user_prompt = f"""
        STUDENT QUESTION: {request.question}
        
        COURSE CONTEXT (RAG):
        {chr(10).join(context)}
        
        GRADING RUBRIC:
        {request.rubric}
        
        SUBMISSION EXCERPT:
        {request.submission_text[:2000]}...
        
        GRADER FEEDBACK:
        {request.feedback}
        """
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", user_prompt)
        ])
        
        # Reuse the LLM from agent module
        chain = prompt | agent.llm | StrOutputParser()
        
        response = chain.invoke({})
        
        return ChatResponse(
            response=response,
            sources=context
        )
        
    except Exception as e:
        print(f"Error in chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "Welcome to GradeWise API"}
