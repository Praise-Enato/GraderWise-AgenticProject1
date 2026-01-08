from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv()

from typing import List, TypedDict, Any, Dict
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from backend.src.models import RubricItem, GradeResult
from backend.src import rag
import json

# Define Agent State
class AgentState(TypedDict):
    submission_text: str
    rubric: List[RubricItem]
    context: List[str]
    grade_data: dict
    final_feedback: str
    grade_result: GradeResult

# Internal model for the grader node
class InternalGrade(BaseModel):
    score: float = Field(..., description="The score awarded (based on the total points available in the rubric)")
    critique_points: List[str] = Field(..., description="List of specific weaknesses found in the submission.")
    rubric_performance: Dict[str, str] = Field(..., description="Dictionary mapping rubric criteria to specific performance feedback.")

# Initialize LLM
llm = ChatGroq(model_name="llama-3.3-70b-versatile")

def retrieve(state: AgentState) -> dict:
    """
    Node to retrieve context using RAG.
    """
    print("---RETRIEVING CONTEXT---")
    submission_text = state["submission_text"]
    context = rag.retrieve_context(submission_text)
    return {"context": context}

def grade_submission(state: AgentState) -> dict:
    """
    Node 1: The Universal Evaluator
    Analytic grader that adapts to the subject (STEM vs Humanities).
    """
    print("---GRADING SUBMISSION (NODE 1)---")
    submission_text = state["submission_text"]
    rubric = state["rubric"]
    context = state["context"]
    
    # Format rubric
    rubric_str = "\n".join([f"- {item.criteria} (Max Points: {item.max_points}): {item.description}" for item in rubric])
    
    # Truncate context to safe limit
    context_str = "\n\n".join(context)[:3000]
    
    # Truncate submission if absurdly long
    if len(submission_text) > 15000:
        submission_text = submission_text[:15000] + "... [TRUNCATED]"

    system_prompt = """You are a Universal Academic Grader. Your task is to grade the STUDENT SUBMISSION based STRICTLY on the provided RUBRIC and CONTEXT.

    1. **ANALYZE SUBJECT**: First, determine the subject matter (e.g., Computer Science, Math, History, Literature) based on the Rubric and Context.
    2. **ADOPT PERSONA**: Adopt the persona of a strict, expert professor in that field.

    3. **SUBJECT-SPECIFIC GRADING LOGIC**:
       - **IF STEM (Math, Science, Coding)**: 
         - **CHECK THE ANSWER FIRST**: Solve the problem yourself. If the student's final answer is wrong, award partial credit only for correct steps.
         - Prioritize objective accuracy. "Close" is not enough in Math.
         - Code must be syntactically correct.
         - A polite but wrong answer is a FAIL.
       - **IF HUMANITIES (History, English, Philosophy)**:
         - Prioritize argument structure, evidence usage, thesis clarity, and persuasion.
         - Fact-checking is still required, but nuance is valued.

    4. **SCORING**:
       - Score strictly based on the **Max Points** defined in the Rubric.
       - If the rubric items sum to 100, your score should be out of 100.
       - If the rubric items sum to 10, your score should be out of 10.
       - Deduct points for factual errors, hallucinations, or unmet criteria.
       
    Output strictly in JSON format matching the following structure:
    {{
        "score": <float>,
        "critique_points": ["<specific point 1>", "<specific point 2>"],
        "rubric_performance": {{
            "<Criteria Name>": "<Specific comment on how this criteria was met or missed>"
        }}
    }}
    """
    
    human_prompt = """
    RUBRIC:
    {rubric_str}
    
    CONTEXT:
    {context_str}
    
    STUDENT SUBMISSION:
    {submission_text}
    """
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", human_prompt)
    ])
    
    # Bind JSON mode
    json_llm = llm.bind(response_format={"type": "json_object"})
    chain = prompt | json_llm
    
    try:
        result = chain.invoke({
            "rubric_str": rubric_str,
            "context_str": context_str,
            "submission_text": submission_text
        })
        parsed = json.loads(result.content)
        
        # Robust Parsing
        grade_data = {
            "score": float(parsed.get("score", 0)),
            "critique_points": parsed.get("critique_points", []),
            "rubric_performance": parsed.get("rubric_performance", {})
        }
        
    except Exception as e:
        print(f"JSON Parsing Error in Node 1: {e}")
        grade_data = {
            "score": 0.0,
            "critique_points": ["Error parsing grader output."],
            "rubric_performance": {}
        }
    
    return {"grade_data": grade_data}

def generate_feedback(state: AgentState) -> dict:
    """
    Node 2: The Socratic Mentor
    Provides help without giving the answer.
    """
    print("---GENERATING FEEDBACK (NODE 2)---")
    submission_text = state["submission_text"]
    grade_data = state["grade_data"]
    score = grade_data["score"]
    
    rubric_performance_str = json.dumps(grade_data.get("rubric_performance", {}), indent=2)
    critique_points_str = "\n".join(f"- {p}" for p in grade_data.get("critique_points", []))
    
    system_prompt = """You are a supportive Academic Mentor and Socratic Tutor.
    
    Your goal is to guide the student to improve their work based on the Grader's feedback, WITHOUT doing the work for them.

    **CRITICAL RULE (NO EXPO):**
    - You are forbidden from stating the correct answer.
    - Do NOT say "The correct answer is X".
    - Do NOT perform the calculation for them (e.g., do NOT say "10 divided by 2 is 5").
    - Do NOT show the corrected code.
    - If they calculated wrong, ask: "Check your division step. What is 10 / 2?" (Allowed)
    - UNACCEPTABLE: "You got 4, but it should be 5."
    - ACCEPTABLE: "You got 4. Let's verify that. Is 2 * 4 + 5 equal to 15?"
    
    **INSTRUCTIONS:**
    1. **Concept Explanation**: Explain the underlying concept they missed (e.g., "In recursions, you need a base case...").
    2. **Socratic Guidance**: Provide a HINT or a LEADING QUESTION to help them find the answer themselves.
    3. **Tone**: Encouraging, constructive, but firm on standards.

    **OUTPUT FORMAT**:
    You MUST output the final feedback in the following Markdown format:

    ✅ **Rubric Strengths**:
    [List specific criteria where they performed well based on grade_data]

    ⚠️ **Areas for Improvement**:
    [List specific criteria where they lost points]

    💡 **Guidance**:
    [Your Socratic hints, conceptual explanations, and leading questions. NO ANSWERS.]
    
    """
    
    human_prompt = """
    STUDENT SUBMISSION:
    {submission_text}
    
    GRADER SCORE: {score}/10
    
    GRADER CRITIQUE:
    {critique_points_str}
    
    RUBRIC PERFORMANCE:
    {rubric_performance_str}
    
    Generate the student-facing Socratic feedback now.
    """
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", human_prompt)
    ])
    
    chain = prompt | llm
    
    feedback_response = chain.invoke({
        "submission_text": submission_text,
        "score": score,
        "critique_points_str": critique_points_str,
        "rubric_performance_str": rubric_performance_str
    })
    
    final_feedback = feedback_response.content
    
    # Construct final GradeResult
    final_result = GradeResult(
        score=score,
        feedback=final_feedback,
        citations=[] # Citations currently not focused on in this iteration, can be added back if needed
    )
    
    return {"final_feedback": final_feedback, "grade_result": final_result}

# Build the Graph
workflow = StateGraph(AgentState)

workflow.add_node("retrieve", retrieve)
workflow.add_node("grade_submission", grade_submission)
workflow.add_node("generate_feedback", generate_feedback)

workflow.set_entry_point("retrieve")
workflow.add_edge("retrieve", "grade_submission")
workflow.add_edge("grade_submission", "generate_feedback")
workflow.add_edge("generate_feedback", END)

app = workflow.compile()
