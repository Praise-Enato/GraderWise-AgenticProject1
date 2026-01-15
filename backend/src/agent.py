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
# Load environment variables
load_dotenv()

# --- LOGGING SETUP ---
import logging
import datetime

# Create logs directory if it doesn't exist (handled by shell command previously, but good to be safe)
os.makedirs("backend/logs", exist_ok=True)

# Configure Logger
logging.basicConfig(
    filename='backend/logs/grading_debug.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    force=True # Ensure we overwrite any existing basicConfig
)
logger = logging.getLogger(__name__)

def log_agent_action(node_name: str, message: str, details: Any = None):
    """Helper to log actions to both file and print to terminal"""
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    # Terminal
    print(f"[{timestamp}] {node_name}: {message}")
    # File
    logger.info(f"{node_name}: {message}")
    if details:
        logger.info(f"DETAILS:\n{json.dumps(details, indent=2, default=str)}")

# --- 1. SETUP DEEPSEEK-V3 LLM ---
api_key = os.getenv("DEEPSEEK_API_KEY")
if not api_key:
    # Fallback or strict warning ensures we don't fail silently
    print("WARNING: DEEPSEEK_API_KEY not found in environment.")
else:
    print(f"INFO: DEEPSEEK_API_KEY loaded. Length: {len(api_key)}")

llm = ChatOpenAI(
    model="deepseek-chat",
    openai_api_key=api_key,
    openai_api_base="https://api.deepseek.com",
    temperature=0,
    max_retries=3,
    request_timeout=120
)

# --- 2. DEFINE AGENT STATE ---
class AgentState(TypedDict):
    submission_files: List[dict] # List of {filename, content}
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
    thinking_process: List[str] # Log of agent's thoughts


# --- 3. NODE IMPLEMENTATIONS ---

def retrieve(state: AgentState) -> dict:
    """
    Node 0: Retrieve context using RAG.
    """
    print("---RETRIEVING CONTEXT---")
    
    # Check for skip_rag flag
    if state.get("skip_rag", False):
        print("---SKIPPING RAG (Requested)---")
        return {
            "context": [], 
            "revision_number": state.get("revision_number", 0), 
            "grader_feedback": state.get("grader_feedback", ""),
            "is_valid": state.get("is_valid", False),
            "thinking_process": ["Skipping RAG."]
        }

    rubric = state.get("rubric", [])
    
    # --- OPTION 1: SMART QUERY (FIXES ATTENTION SPAN) ---
    # We query using the RUBRIC (The Question) instead of the SUBMISSION (The Answer).
    # This ensures we always retrieve the correct lecture notes for the topic.
    
    rubric_topics = [item.criteria for item in rubric]
    rubric_details = [item.description for item in rubric]
    
    # Construct a targeted query
    # Example: "Context for Photosynthesis, Cellular Respiration. Define process..."
    query = f"Academic context and definitions for: {', '.join(rubric_topics)}. {' '.join(rubric_details)}"
    
    # Truncate query safely to ~400 words (2000 chars) to respect embedding limits
    # This is safe because Rubrics are rarely longer than 2000 chars.
    query = query[:2000] 

    try:
        context = rag.retrieve_context(query)
    except Exception as e:
        print(f"RAG Error: {e}")
        context = []

    return {
        "context": context,
        "revision_number": state.get("revision_number", 0),
        "grader_feedback": state.get("grader_feedback", ""),
        "is_valid": state.get("is_valid", False),
        "thinking_process": ["Agent initializing...", f"Retrieving context for topics: {rubric_topics}"] + ([f"Found {len(context)} context chunks."] if context else ["No relevant context found."])
    }

def grade_submission(state: AgentState) -> dict:
    """
    Node 1: The Grader (Universal Evaluator)
    """
    print(f"---GRADING SUBMISSION (Attempt {state.get('revision_number', 0) + 1})---")
    submission_files = state["submission_files"]
    rubric = state["rubric"]
    context = state["context"]
    grader_feedback = state.get("grader_feedback", "")
    
    # --- 1. UNIVERSAL RUBRIC DISPLAY ---
    # We display the raw text so it works for ANY subject (Math, History, CS)
    rubric_parts = []
    for i, item in enumerate(rubric):
        part = f"### CRITERIA {i+1}: {item.criteria} (Max: {item.max_points} pts)"
        part += f"\n   - [FULL MARKS]: {item.description}"
        if item.developing_description:
             part += f"\n   - [PARTIAL/DEVELOPING]: {item.developing_description}"
        if item.zero_description:
             part += f"\n   - [ZERO/MISSING]: {item.zero_description}"
        rubric_parts.append(part)
    rubric_str = "\n\n".join(rubric_parts)
    
    # --- 2. PREPARE SUBMISSION ---
    context_str = "\n\n".join(context)[:3000]
    
    formatted_submission = ""
    for file in submission_files:
        content = file['content']
        if len(content) > 20000: 
            content = content[:20000] + "... [TRUNCATED]"
        formatted_submission += f"\n--- FILE: {file['filename']} ---\n{content}\n"
    
    # --- 3. THE UNIVERSAL SYSTEM PROMPT ---
    system_prompt_text = f"""You are an Expert Academic Grader (Universal).
    
    **YOUR TASK**:
    Evaluate the STUDENT SUBMISSION against the RUBRIC strictly and fairly.
    
    **UNIVERSAL GRADING RULES**:
    1. **The Rubric is Law**: Grade ONLY based on the criteria listed.
    
    2. **"Content Over Filename" Rule**: 
       - If the rubric asks for a specific file (e.g., 'report.txt'), **DO NOT** give a zero just because the filename is wrong.
       - **SEARCH** the submission content. If you find the *content* (e.g., a "Table of Work") inside *any* file or the main text, **GRADE IT**.
       - Only award 0 if the *content* is genuinely missing.
    
    3. **Partial Points (Numeric vs. Subjective)**: 
       - **Numeric Rubric**: If the rubric lists specific numbers (e.g., "(41.5) pts"), you **MUST** snap to those exact numbers.
       - **Subjective Rubric**: If the rubric is vague (e.g., "Good Analysis"), use your judgment on a 0-100% scale of the max points. 
         - *Example:* "Good Analysis (10 pts)". Student is decent but not great -> Award 7.5 or 8.0.
    
    4. **Fact Checking**:
       - Use the `COURSE CONTEXT` to verify claims.
       - If a student makes a claim that contradicts the Context, deduct points for "Accuracy" (if applicable).
    
    **OUTPUT FORMAT**:
    You must output a JSON list of assessments for EACH criteria.
    {{{{
        "assessments": [
            {{{{
                "criteria_index": 1,
                "criteria_name": "Name of criteria",
                "awarded_points": <float>,
                "reason": "Brief explanation referencing the submission content."
            }}}},
            ... one for every rubric item
        ],
        "general_feedback": "A summary of the overall performance."
    }}}}
    """

    user_prompt_text = """
    RUBRIC:
    {rubric_str}
    
    COURSE CONTEXT (Use for fact-checking only):
    {context_str}
    
    STUDENT SUBMISSION:
    {submission_text}
    """

    if grader_feedback:
        user_prompt_text = f"⚠️ PREVIOUS GRADE REJECTED. JUDGE SAID: {{grader_feedback}}. FIX THIS ERROR.\n\n" + user_prompt_text

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt_text),
        ("user", user_prompt_text)
    ])

    json_llm = llm.bind(response_format={"type": "json_object"})
    chain = prompt | json_llm

    try:
        result = chain.invoke({
            "rubric_str": rubric_str,
            "context_str": context_str,
            "submission_text": formatted_submission,
            "grader_feedback": grader_feedback
        })
        
        parsed = json.loads(result.content)
        assessments = parsed.get("assessments", [])
        
        # --- 4. PYTHON CALCULATION (Universal) ---
        total_score = 0.0
        critique_points = []
        rubric_performance = {}
        
        for item in assessments:
            # We let Python do the math to avoid AI hallucinations
            points = float(item.get("awarded_points", 0.0))
            reason = item.get("reason", "")
            name = item.get("criteria_name", "Unknown")
            
            total_score += points
            
            # Format feedback
            rubric_performance[name] = f"{points} pts - {reason}"
            
            # Identify critiques (Universal Logic: if points < max, it's a critique)
            # We can't know max per item easily here without parsing, so we assume if points == 0 it's a major critique
            if points == 0.0:
                critique_points.append(f"❌ {name}: {reason}")
            elif points < 5.0: # Heuristic for partial
                critique_points.append(f"⚠️ {name}: {reason}")
        
        grade_data = {
            "score": total_score,
            "critique_points": critique_points,
            "rubric_performance": rubric_performance
        }
        
        # LOGGING
        log_agent_action("GRADER", f"Calculated Score: {total_score}", grade_data)
        



    except Exception as e:
        log_agent_action("GRADER", f"ERROR: {str(e)}")
        print(f"JSON Parsing Error in Grader: {e}")
        grade_data = {
            "score": 0.0,
            "critique_points": ["Error parsing specific grader output."],
            "rubric_performance": {}
        }

    return {
        "grade_data": grade_data,
        "thinking_process": state.get("thinking_process", []) + [f"Graded {len(submission_files)} files universal style."]
    }

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
        log_agent_action("JUDGE", f"❌ Grade Rejected: {reason}", {"score": score, "critique": critique_points})
        return {
            "is_valid": False,
            "grader_feedback": reason,
            "revision_number": current_revision + 1,
            "thinking_process": state.get("thinking_process", []) + [f"Judge: Grade Rejected. {reason}", "Looping back to Grader..."]
        }
    else:
        print("✅ Grade Validated.")
        log_agent_action("JUDGE", "✅ Grade Validated")
        return {
            "is_valid": True,
            "grader_feedback": "",
            "revision_number": current_revision, # No increment validation passed
            "thinking_process": state.get("thinking_process", []) + ["Judge: Grade Validated. QA Passed.", "Moving to final feedback generation..."]
        }


def generate_feedback(state: AgentState) -> dict:
    """
    Node 3: The Mentor (Socratic Tutor)
    Provides feedback without giving the answer.
    """
    print("---GENERATING FEEDBACK (NODE 3)---")
    submission_files = state["submission_files"]
    
    # Reconstruct submission for the prompt (similar to Grader, but maybe less strict truncation if possible)
    submission_text_formatted = ""
    for file in submission_files:
        content = file['content']
        if len(content) > 15000: # Slightly tighter limit for feedback generation context
            content = content[:15000] + "... [TRUNCATED]"
        submission_text_formatted += f"\n--- FILE: {file['filename']} ---\n{content}\n"
        
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
    
    try:
        feedback_response = chain.invoke({
            "submission_text": submission_text_formatted,
            "score": score,
            "total_points": total_points,
            "critique_points_str": critique_points_str,
            "rubric_performance_str": rubric_performance_str
        })
        final_feedback = feedback_response.content
    except Exception as e:
        print(f"Error in Mentor (Node 3): {type(e).__name__}: {e}")
        final_feedback = "I apologize, but I am unable to generate feedback at this time due to a connection error with the AI service. Please review the grade details above."

    # Calculate confidence based on revision count
    # 0 retries = 0.95 (High)
    # 1 retry = 0.98 (Very High - Self-Correction worked)
    # 2 retries = 0.90 (Good)
    # 3+ retries = 0.75 (Uncertain)
    revisions = state.get("revision_number", 0)
    confidence = 0.95
    if revisions == 1:
        confidence = 0.99
    elif revisions == 2:
        confidence = 0.90
    elif revisions >= 3:
        confidence = 0.75

    final_logs = state.get("thinking_process", []) + ["Finalizing feedback in Socratic style...", f"Confidence Score: {int(confidence * 100)}%"]

    # Construct final GradeResult
    final_result = GradeResult(
        score=score,
        feedback=final_feedback,
        citations=[],
        thinking_process=final_logs,
        confidence_score=confidence
    )
    
    return {"final_feedback": final_feedback, "grade_result": final_result, "thinking_process": final_logs}


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
