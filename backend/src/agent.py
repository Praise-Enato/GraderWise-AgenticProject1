from dotenv import load_dotenv
import os
import json
from typing import List, TypedDict, Dict, Annotated, Any
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from backend.src.models import RubricItem, GradeResult
from backend.src import rag

# Load environment variables
load_dotenv()

# --- 1. SETUP DEEPSEEK-V3 LLM ---
api_key = os.getenv("DEEPSEEK_API_KEY")
if not api_key:
    # Fallback or strict warning ensures we don't fail silently
    print("WARNING: DEEPSEEK_API_KEY not found in environment.")

llm = ChatOpenAI(
    model="deepseek-chat",
    openai_api_key=api_key,
    openai_api_base="https://api.deepseek.com",
    temperature=0
)

# --- 2. DEFINE AGENT STATE ---
class AgentState(TypedDict):
    submission_text: str
    rubric: List[RubricItem]
    context: List[str]
    grade_data: dict
    final_feedback: str
    grade_result: GradeResult
    # Control Fields for Self-Correction Loop
    revision_number: int       # Tracks retry attempts (default: 0)
    grader_feedback: str       # Rejection reason from the Judge (default: "")
    is_valid: bool             # Flag for conditional edge (default: False)
    skip_rag: bool             # Optional flag to skip RAG (default: False)


# --- 3. NODE IMPLEMENTATIONS ---

def retrieve(state: AgentState) -> dict:
    """
    Node 0: Retrieve context using RAG.
    """
    print("---RETRIEVING CONTEXT---")
    submission_text = state["submission_text"]
    # Initialize defaults if not present
    revision_number = state.get("revision_number", 0)
    grader_feedback = state.get("grader_feedback", "")
    is_valid = state.get("is_valid", False)
    
    # Check for skip_rag flag
    if state.get("skip_rag", False):
        print("---SKIPPING RAG (Requested)---")
        context = []
    else:
        try:
            context = rag.retrieve_context(submission_text)
        except Exception as e:
            print(f"RAG Error: {e}")
            context = []

    return {
        "context": context,
        "revision_number": revision_number,
        "grader_feedback": grader_feedback,
        "is_valid": is_valid
    }

def grade_submission(state: AgentState) -> dict:
    """
    Node 1: The Grader (Universal Evaluator)
    Analyzes subject, adopts persona, grades strictly.
    Handles Retries if Judge rejected previous output.
    """
    print(f"---GRADING SUBMISSION (Attempt {state.get('revision_number', 0) + 1})---")
    submission_text = state["submission_text"]
    rubric = state["rubric"]
    context = state["context"]
    grader_feedback = state.get("grader_feedback", "")
    
    # Format rubric
    rubric_str = "\n".join([f"- {item.criteria} (Max Points: {item.max_points}): {item.description}" for item in rubric])
    
    # Truncate context and submission to safe limits
    context_str = "\n\n".join(context)[:3000]
    if len(submission_text) > 15000:
        submission_text_safe = submission_text[:15000] + "... [TRUNCATED]"
    else:
        submission_text_safe = submission_text

    total_points = sum(item.max_points for item in rubric)

    # Base System Prompt
    # Note: We use double curly braces {{ }} for literal braces in LangChain templates
    system_prompt_text = f"""You are a Universal Academic Grader. Your task is to grade the STUDENT SUBMISSION based STRICTLY on the provided RUBRIC and CONTEXT.

    1. **ANALYZE SUBJECT**: Determine the subject (Math, CS, History, etc.).
    2. **ADOPT PERSONA**: Adopt the persona of a fair but rigorous grader.

    3. **GRADING & SCORING RULES**:
       - **DO NOT OVER-PENALIZE GRAMMAR**: Unless the Rubric explicitly mentions "Grammar" or "Spelling" as a major criteria, do not deduct more than 10-15% of the score for typos or informal tone. Focus on the CONTENT and ARGUMENT.
       - **STEM (Math/Science/Code)**: 
         - **CHECK THE ANSWER**: If the logic/answer is correct, award high marks even if the explanation is messy.
         - "Polite but wrong" is a FAIL.
       - **HUMANITIES**: 
         - Look for the *presence* of ideas, not just perfect execution. 
         - If the student makes a good point but uses slang, they should still get a passing score.

    4. **SCORING CALCULATION**:
       - **TOTAL POINTS AVAILABLE: {total_points}**
       - Score each rubric item based on the evidence found.
       - **Bias towards the average**: Real students rarely get 0.0 or Perfect scores. Use the full range (3, 4, 6, 8).
       
    Output strictly in **JSON**:
    {{{{
        "score": <float>,
        "critique_points": ["<specific point 1>", "<specific point 2>"],
        "rubric_performance": {{{{
            "<Criteria Name>": "<Specific comment>"
        }}}}
    }}}}
    """

    # User Prompt Template
    user_prompt_text = """
    RUBRIC:
    {rubric_str}
    
    CONTEXT:
    {context_str}
    
    STUDENT SUBMISSION:
    {submission_text}
    """

    # Retry Logic: Prepend Feedback if it exists
    if grader_feedback:
        user_prompt_text = f"⚠️ PREVIOUS GRADE REJECTED. JUDGE SAID: {{grader_feedback}}. FIX THIS ERROR.\n\n" + user_prompt_text

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt_text),
        ("user", user_prompt_text)
    ])

    # Bind to JSON object mode
    json_llm = llm.bind(response_format={"type": "json_object"})
    chain = prompt | json_llm

    try:
        # Pass variables to invoke
        result = chain.invoke({
            "total_points": total_points,
            "rubric_str": rubric_str,
            "context_str": context_str,
            "submission_text": submission_text_safe,
            "grader_feedback": grader_feedback
        })
        parsed = json.loads(result.content)
        
        # Robust Parsing
        grade_data = {
            "score": float(parsed.get("score", 0.0)),
            "critique_points": parsed.get("critique_points", []),
            "rubric_performance": parsed.get("rubric_performance", {})
        }

    except Exception as e:
        print(f"JSON Parsing Error in Grader: {e}")
        # Return default failure state for the Judge to catch
        grade_data = {
            "score": 0.0,
            "critique_points": ["Error parsing specific grader output."],
            "rubric_performance": {}
        }

    return {"grade_data": grade_data}


def validate_grade(state: AgentState) -> dict:
    """
    Node 2: The Judge (Quality Assurance Auditor)
    Reviews the grade_data for consistency and validity.
    """
    print("---VALIDATING GRADE (NODE 2)---")
    grade_data = state["grade_data"]
    rubric = state["rubric"]
    total_points = sum(item.max_points for item in rubric)
    
    score = grade_data.get("score", 0.0)
    critique_points = grade_data.get("critique_points", [])
    
    valid = True
    reason = ""

    # Criteria 1: System/Parse Error
    if score == 0.0 and "Error parsing" in str(critique_points):
        valid = False
        reason = "JSON Parsing failed in previous attempt."

    # Criteria 2: Score < Max but Critique says "Perfect" (Inconsistency)
    # We define "Perfect" loosely as having no negative critique or explicitly saying 'perfect'
    critique_text = " ".join(critique_points).lower()
    if score < total_points and ("perfect" in critique_text or "no errors" in critique_text or not critique_points):
        # Unless the score is very high (e.g. 95%), this is suspicious. 
        # But sticking to the user prompt's logic:
        # "Fail: Score is < 10 but Critique says 'Perfect' or 'No errors'." (Assuming 10 is max, here generalized to total_points)
        if score < total_points:
             # Double check if it's really claiming perfection
             if "no errors" in critique_text or "perfect" in critique_text or len(critique_points) == 0:
                 valid = False
                 reason = f"Score is {score}/{total_points} (imperfect) but critique claims no errors."

    # Criteria 3: Score is Max but Critique lists specific errors
    if score == total_points and len(critique_points) > 0:
        # Filter out empty strings or positive praise disguised as critique
        # Heuristic: If critique has words like "missing", "incorrect", "fail", "wrong"
        negative_keywords = ["missing", "incorrect", "fail", "wrong", "error", "should have", "needs"]
        has_negative = any(keyword in critique_text for keyword in negative_keywords)
        if has_negative:
            valid = False
            reason = f"Score is {score}/{total_points} (perfect) but critique lists specific errors."
            
    # Criteria 4: Score checks against Total Points
    if score > total_points:
        valid = False
        reason = f"Score {score} exceeds total possible points {total_points}."

    # Update State
    current_revision = state.get("revision_number", 0)
    
    if not valid:
        print(f"❌ Grade Rejected: {reason}")
        return {
            "is_valid": False,
            "grader_feedback": reason,
            "revision_number": current_revision + 1
        }
    else:
        print("✅ Grade Validated.")
        return {
            "is_valid": True,
            "grader_feedback": "",
            "revision_number": current_revision # No increment validation passed
        }


def generate_feedback(state: AgentState) -> dict:
    """
    Node 3: The Mentor (Socratic Tutor)
    Provides feedback without giving the answer.
    """
    print("---GENERATING FEEDBACK (NODE 3)---")
    submission_text = state["submission_text"]
    grade_data = state["grade_data"]
    score = grade_data["score"]
    
    rubric_performance_str = json.dumps(grade_data.get("rubric_performance", {}), indent=2)
    critique_points_str = "\n".join(f"- {p}" for p in grade_data.get("critique_points", []))
    
    rubric = state["rubric"]
    total_points = sum(item.max_points for item in rubric)
    
    system_prompt = """You are a supportive Academic Mentor and Socratic Tutor.
    
    Your goal is to guide the student to improve their work based on the Grader's feedback, WITHOUT doing the work for them.

    **CRITICAL RULE (NO EXPO):**
    - You are forbidden from stating the correct answer.
    - Do NOT say "The correct answer is X".
    - Do NOT perform the calculation for them.
    - Do NOT show the corrected code.
    - If they calculated wrong, ask: "Check your division step. What is 10 / 2?" (Allowed)
    - UNACCEPTABLE: "You got 4, but it should be 5."
    - ACCEPTABLE: "You got 4. Let's verify that. Is 2 * 4 + 5 equal to 15?"
    
    **INSTRUCTIONS:**
    1. **Concept Explanation**: Explain the underlying concept they missed.
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
    
    user_prompt = """
    STUDENT SUBMISSION:
    {submission_text}
    
    GRADER SCORE: {score}/{total_points}
    
    GRADER CRITIQUE:
    {critique_points_str}
    
    RUBRIC PERFORMANCE:
    {rubric_performance_str}
    
    Generate the student-facing Socratic feedback now.
    """
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", user_prompt)
    ])
    
    chain = prompt | llm
    
    feedback_response = chain.invoke({
        "submission_text": submission_text,
        "score": score,
        "total_points": total_points,
        "critique_points_str": critique_points_str,
        "rubric_performance_str": rubric_performance_str
    })
    final_feedback = feedback_response.content
    
    # Construct final GradeResult
    final_result = GradeResult(
        score=score,
        feedback=final_feedback,
        citations=[]
    )
    
    return {"final_feedback": final_feedback, "grade_result": final_result}


# --- 4. CONDITIONAL EDGES ---

def check_validation(state: AgentState):
    """
    Determines next step based on validation result and retry count.
    """
    is_valid = state.get("is_valid", False)
    revision_number = state.get("revision_number", 0)
    MAX_RETRIES = 3

    if is_valid:
        return "generate_feedback"
    elif revision_number < MAX_RETRIES:
        return "grade_submission"
    else:
        # Stop loop, accept best effort (or last effort)
        print("⚠️ Max retries reached. Proceeding with current grade.")
        return "generate_feedback"


# --- 5. BUILD GRAPH ---
workflow = StateGraph(AgentState)

workflow.add_node("retrieve", retrieve)
workflow.add_node("grade_submission", grade_submission)
workflow.add_node("validate_grade", validate_grade)
workflow.add_node("generate_feedback", generate_feedback)

workflow.set_entry_point("retrieve")

workflow.add_edge("retrieve", "grade_submission")
workflow.add_edge("grade_submission", "validate_grade")

workflow.add_conditional_edges(
    "validate_grade",
    check_validation,
    {
        "grade_submission": "grade_submission",
        "generate_feedback": "generate_feedback"
    }
)

workflow.add_edge("generate_feedback", END)

app = workflow.compile()
