from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv()

from typing import List, TypedDict, Any
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from backend.src.models import RubricItem, GradeResult
from backend.src import rag

# Define Agent State
class AgentState(TypedDict):
    submission_text: str
    rubric: List[RubricItem]
    context: List[str]
    grade_result: GradeResult

# Initialize LLM
llm = ChatGroq(model_name="llama-3.3-70b-versatile") # Using 70b or 8b based on availability, 70b is safer for complex tasks.
# Note: Prompt said "Llama 3 (via Groq API)".

def retrieve(state: AgentState) -> dict:
    """
    Node to retrieve context using RAG.
    """
    print("---RETRIEVING CONTEXT---")
    submission_text = state["submission_text"]
    context = rag.retrieve_context(submission_text)
    return {"context": context}

def grade(state: AgentState) -> dict:
    """
    Node to grade the submission using Llama 3.
    """
    print("---GRADING SUBMISSION---")
    submission_text = state["submission_text"]
    rubric = state["rubric"]
    context = state["context"]
    
    # Format rubric for prompt
    rubric_str = "\n".join([f"- {item.criteria} (Max Points: {item.max_points}): {item.description}" for item in rubric])
    
    # Format context for prompt
    context_str = "\n\n".join(context)
    
    system_prompt = """You are a strict, critical academic grader. Do not inflate grades. Your task is to evaluate a student submission based strictly on the provided rubric and course materials.
    
    Instructions:
    1. Analyze the Student Submission against the Rubric Criteria.
    2. CRITICAL: Length does NOT equal quality. Do not reward rambling or repetitive essays.
    3. Fluff Detection: If the student repeats the same point multiple times to fill space, deduct points heavily.
    4. Focus STRICTLY on the argument quality and organization. A long essay with weak arguments must receive a low score (0-3).
    5. Strictly follow the rubric instructions.
    6. If an essay is short, repetitive, or off-topic, you MUST assign a low score (0-4).
    7. Use the full scoring range (0-10). Do not default to 7 or 8 for mediocre work.
    8. Use the provided Context (Course Materials) to verify factual accuracy and direct references.
    9. Be objective and fair. Deduct points for missing elements defined in the rubric.
    10. Provide constructive feedback explaining the score.
    11. Cite specific parts of the submission or context where applicable.
    
    Return the result in the specified structured format.
    """
    
    human_prompt = f"""
    RUBRIC:
    {rubric_str}
    
    COURSE MATERIAL CONTEXT:
    {context_str}
    
    STUDENT SUBMISSION:
    {submission_text}
    """
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", human_prompt)
    ])
    
    # structured_llm = llm.with_structured_output(GradeResult)
    # Using JSON mode or structured output if available in langchain_groq wrapper properly.
    # Assuming .with_structured_output works as standard in newer langchain versions with pydantic models.
    grader = prompt | llm.with_structured_output(GradeResult)
    
    result = grader.invoke({})
    
    return {"grade_result": result}

# Build the Graph
workflow = StateGraph(AgentState)

workflow.add_node("retrieve", retrieve)
workflow.add_node("grade", grade)

workflow.set_entry_point("retrieve")
workflow.add_edge("retrieve", "grade")
workflow.add_edge("grade", END)

app = workflow.compile()
