import os
import json
import concurrent.futures
from typing import Dict
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from backend.src.models import RubricItem, GradeResult, AgentState
from backend.src.business_rag import BusinessRAG
from backend.src.rag import get_embedding_function
import logging

logger = logging.getLogger(__name__)

api_key = os.getenv("DEEPSEEK_API_KEY")
llm = ChatOpenAI(
    model="deepseek-chat",
    openai_api_key=api_key,
    openai_api_base="https://api.deepseek.com",
    temperature=0,
    max_retries=3,
    request_timeout=120
)

# --- BUSINESS SUMMARY PRE-COMPUTE PROMPT ---
BUSINESS_SUMMARY_PROMPT = """You are a Senior Venture Capital Partner reviewing a startup pitch.
Read the following business plan submission and generate a concise holistic summary.
Focus on identifying the core problem, solution, revenue model, target market, and any major financial or traction claims. 
This summary will be used to contextualize granular grading later.

**BUSINESS PLAN SUBMISSION:**
{submission_text}

Return ONLY the summary paragraph."""

# --- SINGLE CRITERIA GRADING PROMPT ---
SINGLE_CRITERIA_PROMPT = """You are a Senior Venture Capital Partner and Business Plan Evaluator.

**YOUR TASK:**
Evaluate this business plan submission against ONE specific rubric criteria constraints.
You are evaluating a real-world startup pitch. While the rubric is your foundation, act as an empathetic investor. If the entrepreneur provides data or narrative that functionally satisfies the spirit of the criteria—even if the exact academic terminology is missing—award full or partial credit based on the quality of their business logic.

**HOLISTIC BUSINESS SUMMARY (For Context):**
{business_summary}

**RUBRIC CRITERIA TO EVALUATE:**
Criteria: {criteria_name}
Max Points: {max_points}
Full Credit Requirements: {description}
Partial Credit Requirements: {developing_description} (Awards {developing_points} pts)
Zero Credit Requirements: {zero_description}

**COURSE GUIDE SPECIFIC TO THIS CRITERIA:**
{course_guide}

**INSTRUCTIONS:**
1. Evaluate ONLY this specific criteria independently, using the overall business summary for holistic context.
2. Read the Course Guide to understand exactly what is expected.
3. Scan the ENTIRE business plan submission below to find evidence for this criteria.
4. Return ONLY JSON format.

**OUTPUT FORMAT:**
{
    "awarded_points": 5.0,
    "reason": "Clear explanation citing specific evidence from the submission."
}

---
**BUSINESS PLAN SUBMISSION:**
{submission_text}

---
**RAG CONTEXT (If relevant to this criteria):**
{context_text}
"""

FINAL_FEEDBACK_PROMPT = """You are a Senior Venture Capital Partner.
You have evaluated a business plan criteria by criteria.

**ASSESSMENTS SO FAR:**
{assessments_json}

**YOUR TASK:**
Based on the collected assessments above, provide the final summary and investment decision.
Be supportive but realistic.

**OUTPUT FORMAT:**
{
    "general_feedback": "Overall assessment highlighting major strengths and critical gaps...",
    "investment_decision": "Pass / Needs Work / Not Fundable",
    "key_risks": ["Risk 1", "Risk 2"],
    "funding_recommendation": "Pre-seed / Seed / Series A / Not Ready"
}
"""

def business_retrieve(state: Dict) -> dict:
    """
    Node 0: We skip global retrieval now and just pass through, 
    since retrieval is done per-criteria in the grading step.
    """
    print("---RETRIEVING BUSINESS CONTEXT (Skipping global, moving to per-criteria)---")
    return {"thinking_process": ["Skipping global RAG retrieval; moving RAG to per-criteria grading."]}

def evaluate_single_criteria(item: RubricItem, submission_text: str, business_context_type: str, grader_feedback: str, business_summary: str) -> dict:
    local_logger = logging.getLogger(__name__)
    
    # 1. Retrieve independent RAG chunks for just THIS criteria
    query = f"{item.criteria}. {item.description}"
    try:
        context_chunks = BusinessRAG.retrieve_business_context(
            query=query,
            context_type=business_context_type,
            k=3
        )
    except Exception as e:
        local_logger.error(f"RAG Error for {item.criteria}: {e}")
        context_chunks = []
        
    context_text = "\\n".join(context_chunks) if context_chunks else "No additional context."
    course_guide = item.course_guide if item.course_guide else "No specific course guide available."
    
    prompt_text = SINGLE_CRITERIA_PROMPT.replace(
        "{business_summary}", business_summary
    ).replace(
        "{criteria_name}", item.criteria
    ).replace(
        "{max_points}", str(item.max_points)
    ).replace(
        "{description}", str(item.description)
    ).replace(
        "{developing_description}", str(item.developing_description)
    ).replace(
        "{developing_points}", str(item.developing_points)
    ).replace(
        "{zero_description}", str(item.zero_description)
    ).replace(
        "{course_guide}", course_guide
    ).replace(
        "{submission_text}", submission_text
    ).replace(
        "{context_text}", context_text
    )

    if grader_feedback:
        prompt_text += f"\n\n**JUDGE FEEDBACK (Previous overall attempt rejected):**\n{grader_feedback}\n"
        
    json_llm = llm.bind(response_format={"type": "json_object"})
    messages = [
        SystemMessage(content=prompt_text),
        HumanMessage(content="Evaluate this business plan criteria and return ONLY JSON.")
    ]
    
    try:
        response = json_llm.invoke(messages)
        result = json.loads(response.content)
        return {
            "criteria_name": item.criteria,
            "max_points": item.max_points,
            "awarded_points": float(result.get("awarded_points", 0.0)),
            "reason": result.get("reason", "No reason provided")
        }
    except Exception as e:
        local_logger.error(f"Error evaluating {item.criteria}: {e}")
        return {
            "criteria_name": item.criteria,
            "max_points": item.max_points,
            "awarded_points": 0.0,
            "reason": f"Evaluation error: {e}"
        }

def grade_business_plan(state: Dict) -> dict:
    """
    Node 1: Grade business plan criteria by criteria using parallel LLM calls.
    Each criteria gets its own prompt, its own RAG context, and its own course guide.
    """
    print("---GRADING BUSINESS PLAN (CRITERIA BY CRITERIA)---")
    logger.info("Node: grade_business_plan - Starting per-criteria evaluation")

    submission_files = state.get("submission_files", [])
    rubric = state.get("rubric", [])
    business_context_type = state.get("business_context_type", "startup")
    grader_feedback = state.get("grader_feedback", "")

    submission_parts = []
    for file in submission_files:
        filename = file.get("filename", "unknown")
        content = file.get("content", "")
        submission_parts.append(f"### {filename}\n\n{content}")

    submission_text = "\n\n---\n\n".join(submission_parts)
    # Truncate if extreme
    max_chars = 15000 * len(submission_files)
    if len(submission_text) > max_chars:
        submission_text = submission_text[:max_chars] + "\n\n[... content truncated for length ...]"

    assessments = []
    
    # Warm up / pre-load the embedding function
    get_embedding_function()
    
    # --- TWO-PASS MEMORY INJECTION: Generate Holistic Summary ---
    logger.info("Generating holistic business summary for context...")
    summary_prompt_text = BUSINESS_SUMMARY_PROMPT.replace("{submission_text}", submission_text)
    summary_messages = [
        SystemMessage(content="You are a VC Partner."),
        HumanMessage(content=summary_prompt_text)
    ]
    try:
        summary_response = llm.invoke(summary_messages)
        business_summary = summary_response.content
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        business_summary = "Holistic summary unavailable."
    
    # Run criteria independently SEQUENTIALLY to avoid PyTorch multi-threading crashes
    for item in rubric:
        result = evaluate_single_criteria(item, submission_text, business_context_type, grader_feedback, business_summary)
        assessments.append(result)
            
    # Re-sort assessments to match rubric order
    order_map = {item.criteria: i for i, item in enumerate(rubric)}
    assessments.sort(key=lambda x: order_map.get(x["criteria_name"], 999))

    # --- FINAL SYNTHESIS CALL ---
    assessments_json = json.dumps(assessments, indent=2)
    synthesis_prompt = FINAL_FEEDBACK_PROMPT.replace("{assessments_json}", assessments_json)
    
    json_llm = llm.bind(response_format={"type": "json_object"})
    messages = [
        SystemMessage(content=synthesis_prompt),
        HumanMessage(content="Return final JSON feedback.")
    ]
    
    try:
        response = json_llm.invoke(messages)
        final_meta = json.loads(response.content)
    except Exception as e:
        logger.error(f"Synthesis error: {e}")
        final_meta = {
            "general_feedback": "Error generating final summary.",
            "investment_decision": "Error",
            "key_risks": [],
            "funding_recommendation": "Error"
        }

    total_score = sum(a.get("awarded_points", 0) for a in assessments)
    
    grade_data = {
        "assessments": assessments,
        "total_score": total_score,
        "general_feedback": final_meta.get("general_feedback", ""),
        "investment_decision": final_meta.get("investment_decision", ""),
        "key_risks": final_meta.get("key_risks", []),
        "funding_recommendation": final_meta.get("funding_recommendation", "")
    }

    return {
        "grade_data": grade_data,
        "thinking_process": [f"Evaluated {len(assessments)} criteria independently using parallel execution. Score: {total_score}"]
    }

def validate_business_grade(state: Dict) -> dict:
    print("---VALIDATING BUSINESS GRADE---")
    
    grade_data = state.get("grade_data", {})
    rubric = state.get("rubric", [])
    revision_number = state.get("revision_number", 0)

    max_score = sum(item.max_points for item in rubric)
    total_score = grade_data.get("total_score", 0.0)

    is_valid = True
    rejection_reason = ""

    if total_score == 0.0:
        is_valid = False
        rejection_reason = "Score is 0 - likely parsing error"
    elif total_score > max_score + 0.1:
        is_valid = False
        rejection_reason = f"Score {total_score} exceeds maximum possible {max_score}"
        
    assessments = grade_data.get("assessments", [])
    if len(assessments) < len(rubric):
        is_valid = False
        rejection_reason = f"Missing assessments: expected {len(rubric)}, got {len(assessments)}"

    if not is_valid:
        revision_number += 1
        logger.info(f"Validation FAILED: {rejection_reason}")

    return {
        "is_valid": is_valid,
        "grader_feedback": rejection_reason,
        "revision_number": revision_number,
        "thinking_process": [f"Validation: {'PASSED' if is_valid else 'FAILED - ' + rejection_reason}"]
    }

def generate_business_feedback(state: Dict) -> dict:
    print("---GENERATING BUSINESS FEEDBACK---")
    
    grade_data = state.get("grade_data", {})
    rubric = state.get("rubric", [])
    revision_number = state.get("revision_number", 0)

    confidence_map = {0: 0.99, 1: 0.90, 2: 0.80, 3: 0.75}
    confidence_score = confidence_map.get(revision_number, 0.75)

    total_score = grade_data.get("total_score", 0.0)
    max_score = sum(item.max_points for item in rubric) if rubric else 0
    assessments = grade_data.get("assessments", [])
    investment_decision = grade_data.get("investment_decision", "Needs Work")
    key_risks = grade_data.get("key_risks", [])
    funding_recommendation = grade_data.get("funding_recommendation", "Not specified")

    feedback_parts = []
    score_pct = (total_score / max_score * 100) if max_score > 0 else 0.0
    feedback_parts.append(f"## 🎯 Executive Summary\n")
    feedback_parts.append(f"**Score:** {total_score}/{max_score} ({score_pct:.1f}%)")
    feedback_parts.append(f"**Investment Decision:** {investment_decision}")
    feedback_parts.append(f"**Funding Readiness:** {funding_recommendation}\n")

    strengths = [a for a in assessments if a.get("awarded_points", 0) >= a.get("max_points", 1) * 0.8]
    if strengths:
        feedback_parts.append("## 🚀 Key Strengths\n")
        for item in strengths[:3]:
            feedback_parts.append(f"- **{item.get('criteria_name')}**: {item.get('reason')}")
        feedback_parts.append("")

    gaps = [a for a in assessments if a.get("awarded_points", 0) < a.get("max_points", 1) * 0.6]
    if gaps:
        feedback_parts.append("## ⚠️ Critical Gaps\n")
        for item in gaps:
            feedback_parts.append(f"- **{item.get('criteria_name')}** ({item.get('awarded_points')}/{item.get('max_points')} pts): {item.get('reason')}")
        feedback_parts.append("")

    feedback_parts.append("## 💡 Investor Perspective\n")
    if key_risks:
        feedback_parts.append("**Key Risks Identified:**")
        for risk in key_risks:
            feedback_parts.append(f"- {risk}")
        feedback_parts.append("")

    feedback_parts.append("**What to Focus On:**")
    if gaps:
        for g in gaps[:3]:
            name = g.get("criteria_name", "Unknown")
            pts = g.get("awarded_points", 0)
            mx = g.get("max_points", 1)
            feedback_parts.append(f"- **{name}** scored {pts}/{mx} — revisit and strengthen this area")

    if investment_decision == "Pass":
        feedback_parts.append("- Strong foundation — reserve capital for execution.")
    elif investment_decision == "Needs Work":
        feedback_parts.append("- Fill the critical data gaps identified before your next pitch.")
    else:
        feedback_parts.append("- Core assumptions need validation before seeking investment.")

    feedback_parts.append("\n---\n*Generated by GradeWise Business Plan Evaluator*")
    final_feedback = "\n".join(feedback_parts)

    grade_result = GradeResult(
        score=total_score,
        feedback=final_feedback,
        citations=[],
        thinking_process=state.get("thinking_process", []),
        confidence_score=confidence_score
    )

    return {
        "final_feedback": final_feedback,
        "grade_result": grade_result,
        "thinking_process": ["Business feedback generation completed"]
    }

def check_validation(state: Dict) -> str:
    is_valid = state.get("is_valid", False)
    revision_number = state.get("revision_number", 0)
    if is_valid:
        return "generate_business_feedback"
    elif revision_number < 3:
        print(f"---RETRYING GRADING (Attempt {revision_number + 1}/3)---")
        return "grade_business_plan"
    else:
        return "generate_business_feedback"

business_workflow = StateGraph(AgentState)
business_workflow.add_node("business_retrieve", business_retrieve)
business_workflow.add_node("grade_business_plan", grade_business_plan)
business_workflow.add_node("validate_business_grade", validate_business_grade)
business_workflow.add_node("generate_business_feedback", generate_business_feedback)

business_workflow.set_entry_point("business_retrieve")
business_workflow.add_edge("business_retrieve", "grade_business_plan")
business_workflow.add_edge("grade_business_plan", "validate_business_grade")
business_workflow.add_conditional_edges(
    "validate_business_grade",
    check_validation,
    {
        "grade_business_plan": "grade_business_plan",
        "generate_business_feedback": "generate_business_feedback"
    }
)
business_workflow.add_edge("generate_business_feedback", END)
business_app = business_workflow.compile()
print("Business agent workflow compiled successfully")
