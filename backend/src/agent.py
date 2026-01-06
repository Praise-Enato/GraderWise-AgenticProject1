from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv()

from typing import List, TypedDict, Any
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from backend.src.models import RubricItem, GradeResult
from backend.src import rag

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
    score: float = Field(..., description="The score awarded (0-10)")
    critique_points: List[str] = Field(..., description="List of specific weaknesses found in the submission. Be specific.")
    citations: List[str] = Field(default_factory=list, description="Relevant citations from context or submission.")

# Initialize LLM
llm = ChatGroq(model_name="llama-3.1-8b-instant") # Switched to 3.1-8b-instant

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
    Node 1: The Grader - Holistic Evaluator (Calibrated)
    """
    print("---GRADING SUBMISSION (NODE 1)---")
    submission_text = state["submission_text"]
    rubric = state["rubric"]
    context = state["context"]
    
    # Format rubric
    rubric_str = "\n".join([f"- {item.criteria} (Max Points: {item.max_points}): {item.description}" for item in rubric])
    
    # Truncate context to safe limit (prevent 500 Errors / Rate Limits)
    context_str = "\n\n".join(context)[:1500] 
    
    # Truncate submission if absurdly long
    if len(submission_text) > 8000:
        submission_text = submission_text[:8000] + "... [TRUNCATED]"

    # --- THE SECRET SAUCE: FEW-SHOT EXAMPLES ---
    # We teach the AI what humans consider a "6" and an "8"
    reference_anchors = """
    EXAMPLE 1 (Human Score: 6/10):
    "Dear local newspaper, I think effects computers have on people are great learning skills/affects because they give us time to chat with friends/new people... (Essay about chatting and safety)... Thank you for listening."
    REASONING: Argument is clear, but structure is loose. Many typos ("troble", "buisness"). Tone is conversational. THIS IS A PASSING SCORE (6).

    EXAMPLE 2 (Human Score: 8/10):
    "Dear @CAPS1 @CAPS2, I believe that using computers will benefit us in many ways like talking and becoming friends... Using computers can help us find coordibates... (Essay about maps and jobs)..."
    REASONING: Strong arguments (Jobs, Maps, Social). Clear structure. Despite spelling errors ("coordibates", "mysace"), the LOGIC is strong. THIS IS A HIGH SCORE (8).
    """
    
    system_prompt = """You are a Holistic Essay Grader. You are grading real student essays (likely middle/high school).
    
    CRITICAL CALIBRATION RULES:
    1. **IGNORE SPELLING/GRAMMAR:** Do NOT deduct points for typos ("troble", "coordibates") or informal tone unless it makes the text unreadable.
    2. **FOCUS ON ARGUMENT:** If the student makes valid points supported by reasons, they deserve a high score (6-9), even if the writing style is messy.
    3. **USE THE ANCHORS:** Compare the submission to the REFERENCE ANCHORS below. If it is similar in quality to Example 2, give it an 8.
    
    SCORING SCALE:
    - 0-2: Off-topic or incoherent.
    - 3-5: Weak argument, very short, or very confusing.
    - 6-7: (Proficient) Clear argument, understandable, decent length. (See Example 1).
    - 8-10: (Strong) Multiple distinct arguments, good examples, persuasive. (See Example 2).
    
    Output strictly in JSON format with "score" (float), "critique_points" (list), and "citations" (list).
    """
    
    human_prompt = """
    REFERENCE ANCHORS:
    {reference_anchors}
    
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
    start_chain = prompt | json_llm
    
    try:
        result = start_chain.invoke({
            "rubric_str": rubric_str,
            "context_str": context_str,
            "submission_text": submission_text,
            "reference_anchors": reference_anchors
        })
        import json
        parsed = json.loads(result.content)
        
        # Robust Score Parsing
        score_raw = parsed.get("score", 0)
        if isinstance(score_raw, dict):
             score = float(score_raw.get("score", score_raw.get("value", 0)))
        else:
             score = float(score_raw)
             
        critique = parsed.get("critique_points", [])
        if isinstance(critique, str): critique = [critique]
        
        # Validate citations
        citations_raw = parsed.get("citations", [])
        citations = []
        for c in citations_raw:
            if isinstance(c, dict):
                citations.append(str(c)) # Convert dict to string representation
            else:
                citations.append(str(c))
        
    except Exception as e:
        print(f"JSON Parsing Error in Node 1: {e}")
        score = 0
        critique = ["Error parsing grader output."]
        citations = []
    
    return {"grade_data": {"score": score, "critique_points": critique, "citations": citations}}
def generate_feedback(state: AgentState) -> dict:
    """
    Node 2: The Mentor - Expert Writing Coach
    """
    print("---GENERATING FEEDBACK (NODE 2)---")
    submission_text = state["submission_text"]
    grade_data = state["grade_data"]
    score = grade_data["score"]
    critique_points = "\n".join(f"- {point}" for point in grade_data["critique_points"])
    
    system_prompt = """You are a helpful Mentor and Expert Writing Coach. 
    Your goal is to take the harsh critique from the Grader and turn it into actionable, supportive, but professional feedback for the student.
    
    Instructions:
    1. Do not simply list the errors. Explain *how* to fix them.
    2. FIND THE SPECIFIC SENTENCES in the student's text that correspond to the critique and quote them.
    3. Be specific. Instead of "Improve grammar", say "In the sentence '...', you used..."
    4. Maintain a supportive tone, even if the score is low.
    5. Do not argue with the score. Accept it as fact.
    """
    
    human_prompt = """
    STUDENT SUBMISSION:
    {submission_text}
    
    GRADER SCORE: {score}/10
    
    GRADER CRITIQUE:
    {critique_points}
    
    Generate the student-facing feedback response now.
    """
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", human_prompt)
    ])
    
    chain = prompt | llm
    feedback_response = chain.invoke({
        "submission_text": submission_text,
        "score": score,
        "critique_points": critique_points
    })
    final_feedback = feedback_response.content
    
    # Construct final GradeResult
    final_result = GradeResult(
        score=score,
        feedback=final_feedback,
        citations=grade_data.get("citations", [])
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
