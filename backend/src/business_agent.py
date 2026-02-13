from dotenv import load_dotenv
import os
import json
from typing import Dict
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from backend.src.models import RubricItem, GradeResult, AgentState
from backend.src.business_rag import BusinessRAG

# Load environment variables
load_dotenv()

# Import logging
import logging
logger = logging.getLogger(__name__)

# --- LLM SETUP ---
api_key = os.getenv("DEEPSEEK_API_KEY")
if not api_key:
    logger.warning("DEEPSEEK_API_KEY not found in environment")

llm = ChatOpenAI(
    model="deepseek-chat",
    openai_api_key=api_key,
    openai_api_base="https://api.deepseek.com",
    temperature=0,
    max_retries=3,
    request_timeout=120
)

# Note: Using dict as state type for flexibility with agent.py's AgentState
# The actual AgentState TypedDict is defined in agent.py and includes:
# submission_files, rubric, context, grade_data, final_feedback, grading_type, etc.

# --- BUSINESS GRADING PROMPT ---
BUSINESS_GRADER_PROMPT = """You are a Senior Venture Capital Partner and Business Plan Evaluator with extensive experience in early-stage investing.

**YOUR TASK:**
Evaluate this business plan submission against the provided rubric with the rigor and expertise of a top-tier investor.

**EVALUATION PRINCIPLES:**
1. **Market Realism**: Validate market size claims against industry benchmarks and typical market sizing methodologies
2. **Financial Feasibility**: Check if financial projections align with typical growth rates for the business stage (seed/Series A typically <100% MoM sustained growth)
3. **Competitive Awareness**: Assess if competitive analysis acknowledges obvious players and provides credible differentiation
4. **Team Credibility**: Evaluate if the team has relevant domain experience and execution capability for their specific market
5. **Presentation Quality**: Judge if the pitch deck meets investor-ready standards (professional design, clear narrative, data visualization)

**BUSINESS-SPECIFIC SCORING RULES:**
- **For Financial Projections**: Flag any sustained monthly growth >100% for more than 6 months as unrealistic unless extraordinary justification provided
- **For Market Opportunity**: Verify that TAM/SAM/SOM breakdown has clear methodology and credible sources (not just "X billion market")
- **For Business Model**: REQUIRE clear definition of CAC (Customer Acquisition Cost), LTV (Lifetime Value), and unit margins - partial credit only if incomplete
- **For Competition**: Automatically deduct points if claims "no competition" or ignores obvious category leaders
- **For Team**: Give credit for relevant exits, domain expertise, complementary skills - deduct for obvious gaps or lack of operational experience

**CRITICAL ANALYSIS AREAS:**
1. **Revenue Model Clarity**: Can you understand how they make money in 30 seconds?
2. **Unit Economics**: Do the CAC:LTV ratios make sense (typically need 3:1 for healthy SaaS)?
3. **Market Sizing**: Is the TAM calculation bottom-up or top-down? Are assumptions reasonable?
4. **Competitive Moat**: What prevents competitors from copying this? Is it defensible?
5. **Execution Risk**: What are the major risks to execution? Does the team acknowledge them?

**OUTPUT FORMAT:**
Return JSON with the following structure:

{{
    "assessments": [
        {{
            "criteria_index": 1,
            "criteria_name": "Problem Statement",
            "awarded_points": 12,
            "max_points": 15,
            "reason": "Clear customer pain point identified with specific examples, but lacks quantitative evidence of market urgency"
        }},
        ...
    ],
    "general_feedback": "Overall assessment of the business plan quality, highlighting major strengths and critical gaps. Be direct and specific - this is for entrepreneurs who need honest feedback.",
    "investment_decision": "Pass / Needs Work / Not Fundable",
    "key_risks": ["Risk 1: Market timing uncertain", "Risk 2: High CAC assumptions"],
    "funding_recommendation": "Pre-seed / Seed / Series A / Not Ready"
}}

**INSTRUCTIONS:**
1. Evaluate each rubric criteria independently - do NOT let one strong/weak area bias others
2. Be rigorous - partial credit is common, perfect scores are rare
3. Cite specific evidence from the submission in your reasoning
4. If key information is missing (e.g., no financial projections), award zero points for that criteria
5. Think like an investor: Would you invest your own money based on this plan?

---

**RUBRIC CRITERIA:**
{rubric_text}

---

**BUSINESS PLAN SUBMISSION:**
{submission_text}

---

**ADDITIONAL CONTEXT (if available):**
{context_text}

Now evaluate this business plan. Return ONLY the JSON response, no additional text."""


def business_retrieve(state: Dict) -> dict:
    """
    Node 0: Retrieve business context from the Business RAG collection.

    Queries the business ChromaDB with rubric criteria to pull in relevant
    industry benchmarks, financial ratios, and evaluation frameworks.
    """
    print("---RETRIEVING BUSINESS CONTEXT---")
    logger.info("Node: business_retrieve - Fetching business context from RAG")

    rubric = state.get("rubric", [])
    business_context_type = state.get("business_context_type", "startup")

    # Validate rubric is non-empty before building query
    rubric_topics = []
    if not rubric:
        logger.warning("business_retrieve called with empty rubric — using fallback query")
        query = f"Business plan evaluation context and benchmarks for {business_context_type} business plans"
    else:
        # Build query from rubric criteria — same approach as academic retrieve
        rubric_topics = [item.criteria for item in rubric]
        rubric_details = [item.description for item in rubric]
        query = f"Business plan evaluation context for: {', '.join(rubric_topics)}. {' '.join(rubric_details)}"

    query = query[:2000]  # Respect embedding limits

    try:
        context = BusinessRAG.retrieve_business_context(
            query=query,
            context_type=business_context_type,
            k=5
        )
        logger.info(f"Retrieved {len(context)} business context chunks for type '{business_context_type}'")
    except Exception as e:
        logger.error(f"Business RAG retrieval error: {e}")
        context = []

    topic_summary = ", ".join(rubric_topics) if rubric_topics else "general business evaluation"
    return {
        "context": context,
        "thinking_process": [
            f"Retrieving business context for type: {business_context_type}",
            f"Query topics: {topic_summary}",
            f"Found {len(context)} context chunks."
        ]
    }


def grade_business_plan(state: Dict) -> dict:
    """
    Node 1: Grade business plan using business-specific rubric logic.

    This node evaluates the business plan submission against the rubric
    using investor/VC partner evaluation criteria.
    """
    print("---GRADING BUSINESS PLAN---")
    logger.info("Node: grade_business_plan - Starting business plan evaluation")

    submission_files = state.get("submission_files", [])
    rubric = state.get("rubric", [])
    context = state.get("context", [])
    grader_feedback = state.get("grader_feedback", "")

    # Combine all submission content (PPTX + documents)
    submission_parts = []
    for file in submission_files:
        filename = file.get("filename", "unknown")
        content = file.get("content", "")
        submission_parts.append(f"### {filename}\n\n{content}")

    submission_text = "\n\n---\n\n".join(submission_parts)

    # Truncate if too long (max ~10K chars per file for token efficiency)
    max_chars = 10000 * len(submission_files)
    if len(submission_text) > max_chars:
        submission_text = submission_text[:max_chars] + "\n\n[... content truncated for length ...]"

    # Format rubric for prompt
    rubric_text = ""
    for idx, item in enumerate(rubric, 1):
        rubric_text += f"\n{idx}. **{item.criteria}** (Max: {item.max_points} points)\n"
        rubric_text += f"   - Full credit: {item.description}\n"
        if item.developing_description:
            rubric_text += f"   - Partial credit ({item.developing_points} pts): {item.developing_description}\n"
        if item.zero_description:
            rubric_text += f"   - Zero points: {item.zero_description}\n"

    # Format context
    context_text = "\n".join(context) if context else "No additional context provided."

    # Build prompt — use str.replace() instead of .format() to avoid brace issues
    # with submission content that may contain { } characters
    prompt_text = BUSINESS_GRADER_PROMPT.replace(
        "{rubric_text}", rubric_text
    ).replace(
        "{submission_text}", submission_text
    ).replace(
        "{context_text}", context_text
    )
    # The template uses {{ }} for JSON examples — convert to literal braces
    prompt_text = prompt_text.replace("{{", "{").replace("}}", "}")

    # Add grader feedback if this is a retry
    if grader_feedback:
        prompt_text += f"\n\n**JUDGE FEEDBACK (Previous attempt was rejected):**\n{grader_feedback}\n\nPlease revise your grading based on this feedback."

    # Use direct messages instead of ChatPromptTemplate to avoid
    # LangChain re-interpreting { } in the already-formatted prompt as variables
    messages = [
        SystemMessage(content=prompt_text),
        HumanMessage(content="Evaluate this business plan and return JSON with your assessment.")
    ]

    # Bind JSON mode
    json_llm = llm.bind(response_format={"type": "json_object"})

    # Invoke LLM
    try:
        response = json_llm.invoke(messages)
        response_text = response.content

        # Parse JSON
        grade_data = json.loads(response_text)

        # Calculate total score from assessments
        total_score = sum(item.get("awarded_points", 0) for item in grade_data.get("assessments", []))
        grade_data["total_score"] = total_score

        logger.info(f"Business plan graded successfully. Total score: {total_score}")

        thinking = [f"Business plan evaluation completed. Investment decision: {grade_data.get('investment_decision', 'N/A')}"]

        return {
            "grade_data": grade_data,
            "thinking_process": thinking
        }

    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {e}")
        # Return error grade data
        return {
            "grade_data": {
                "assessments": [],
                "total_score": 0.0,
                "general_feedback": "Error parsing grading response",
                "investment_decision": "Error",
                "key_risks": ["Technical error in grading process"],
                "funding_recommendation": "Error"
            },
            "thinking_process": [f"JSON parsing error: {str(e)}"]
        }
    except Exception as e:
        logger.error(f"Grading error: {e}")
        return {
            "grade_data": {
                "assessments": [],
                "total_score": 0.0,
                "general_feedback": f"Error during grading: {str(e)}",
                "investment_decision": "Error",
                "key_risks": ["Technical error"],
                "funding_recommendation": "Error"
            },
            "thinking_process": [f"Error: {str(e)}"]
        }


def validate_business_grade(state: Dict) -> dict:
    """
    Node 2: Validate business plan grade with business-specific rules.

    Checks for consistency and business-specific validation (e.g., unrealistic financials).
    """
    print("---VALIDATING BUSINESS GRADE---")
    logger.info("Node: validate_business_grade - Starting validation")

    grade_data = state.get("grade_data", {})
    rubric = state.get("rubric", [])
    revision_number = state.get("revision_number", 0)

    # Calculate max possible score
    max_score = sum(item.max_points for item in rubric)
    total_score = grade_data.get("total_score", 0.0)

    # Standard validations
    is_valid = True
    rejection_reason = ""

    # 1. Check if score is 0 (likely JSON parsing error)
    if total_score == 0.0:
        is_valid = False
        rejection_reason = "Score is 0 - likely parsing error or missing evaluation"

    # 2. Check if score exceeds maximum
    elif total_score > max_score + 0.1:  # Small tolerance for floating point
        is_valid = False
        rejection_reason = f"Score {total_score} exceeds maximum possible {max_score}"

    # 3. Consistency check: perfect score but critique mentions issues
    elif total_score >= max_score - 1 and "issue" in grade_data.get("general_feedback", "").lower():
        is_valid = False
        rejection_reason = "Near-perfect score but feedback mentions issues - inconsistent"

    # 4. Consistency check: low score but feedback says "excellent"
    elif total_score < max_score * 0.5 and any(word in grade_data.get("general_feedback", "").lower() for word in ["excellent", "outstanding", "perfect"]):
        is_valid = False
        rejection_reason = "Low score but feedback is overly positive - inconsistent"

    # 5. Business-specific: Check for missing critical sections
    assessments = grade_data.get("assessments", [])
    if len(assessments) < len(rubric):
        is_valid = False
        rejection_reason = f"Missing assessments: expected {len(rubric)}, got {len(assessments)}"

    # Increment revision counter if invalid
    if not is_valid:
        revision_number += 1
        logger.info(f"Validation FAILED (attempt {revision_number}): {rejection_reason}")
    else:
        logger.info("Validation PASSED")

    return {
        "is_valid": is_valid,
        "grader_feedback": rejection_reason,
        "revision_number": revision_number,
        "thinking_process": [f"Validation: {'PASSED' if is_valid else 'FAILED - ' + rejection_reason}"]
    }


def generate_business_feedback(state: Dict) -> dict:
    """
    Node 3: Generate investor/mentor-style feedback for entrepreneurs.

    Tone: Business mentor (not academic tutor) - direct, actionable, focused on execution.
    """
    print("---GENERATING BUSINESS FEEDBACK---")
    logger.info("Node: generate_business_feedback - Generating mentor feedback")

    grade_data = state.get("grade_data", {})
    rubric = state.get("rubric", [])
    revision_number = state.get("revision_number", 0)

    # Calculate confidence score (decreases with retries)
    confidence_map = {0: 0.99, 1: 0.90, 2: 0.80, 3: 0.75}
    confidence_score = confidence_map.get(revision_number, 0.75)

    # Extract key information
    total_score = grade_data.get("total_score", 0.0)
    max_score = sum(item.max_points for item in rubric) if rubric else 0
    assessments = grade_data.get("assessments", [])
    investment_decision = grade_data.get("investment_decision", "Needs Work")
    key_risks = grade_data.get("key_risks", [])
    funding_recommendation = grade_data.get("funding_recommendation", "Not specified")

    # Build feedback sections
    feedback_parts = []

    # Executive Summary
    score_pct = (total_score / max_score * 100) if max_score > 0 else 0.0
    feedback_parts.append(f"## 🎯 Executive Summary\n")
    feedback_parts.append(f"**Score:** {total_score}/{max_score} ({score_pct:.1f}%)")
    feedback_parts.append(f"**Investment Decision:** {investment_decision}")
    feedback_parts.append(f"**Funding Readiness:** {funding_recommendation}\n")

    # Strengths
    strengths = [a for a in assessments if a.get("awarded_points", 0) >= a.get("max_points", 1) * 0.8]
    if strengths:
        feedback_parts.append("## 🚀 Key Strengths\n")
        for item in strengths[:3]:  # Top 3 strengths
            feedback_parts.append(f"- **{item.get('criteria_name')}**: {item.get('reason')}")
        feedback_parts.append("")

    # Critical Gaps
    gaps = [a for a in assessments if a.get("awarded_points", 0) < a.get("max_points", 1) * 0.6]
    if gaps:
        feedback_parts.append("## ⚠️ Critical Gaps\n")
        for item in gaps:
            feedback_parts.append(f"- **{item.get('criteria_name')}** ({item.get('awarded_points')}/{item.get('max_points')} pts): {item.get('reason')}")
        feedback_parts.append("")

    # Investor Perspective & Guidance
    feedback_parts.append("## 💡 Investor Perspective\n")
    if key_risks:
        feedback_parts.append("**Key Risks Identified:**")
        for risk in key_risks:
            feedback_parts.append(f"- {risk}")
        feedback_parts.append("")

    # Actionable guidance based on investment decision AND actual gaps
    feedback_parts.append("**What to Focus On:**")

    # Build dynamic guidance from the weakest-scoring criteria
    if gaps:
        for g in gaps[:3]:  # Top 3 weakest areas
            name = g.get("criteria_name", "Unknown")
            pts = g.get("awarded_points", 0)
            mx = g.get("max_points", 1)
            if pts == 0:
                feedback_parts.append(f"- **{name}** scored 0/{mx} — this section needs to be added or completely reworked")
            else:
                feedback_parts.append(f"- **{name}** scored {pts}/{mx} — revisit and strengthen this area")

    if investment_decision == "Pass":
        feedback_parts.append("- Strong foundation — focus on execution and hitting early milestones")
    elif investment_decision == "Needs Work":
        feedback_parts.append("- Address the critical gaps above before your next pitch")
    else:  # Not Fundable
        feedback_parts.append("- This needs significant rework before being investor-ready")
        feedback_parts.append("- Talk to more customers and validate core assumptions")

    feedback_parts.append("")
    feedback_parts.append("---")
    feedback_parts.append("*Generated by GradeWise Business Plan Evaluator*")

    final_feedback = "\n".join(feedback_parts)

    # Create GradeResult
    grade_result = GradeResult(
        score=total_score,
        feedback=final_feedback,
        citations=[],  # Business plans don't have course material citations
        thinking_process=state.get("thinking_process", []),
        confidence_score=confidence_score
    )

    logger.info(f"Feedback generated. Score: {total_score}/{max_score}")

    return {
        "final_feedback": final_feedback,
        "grade_result": grade_result,
        "thinking_process": ["Business feedback generation completed"]
    }


# --- CONDITIONAL EDGE FUNCTION ---
def check_validation(state: Dict) -> str:
    """
    Determine next node based on validation result.

    Returns:
        - "generate_business_feedback" if valid or max retries reached
        - "grade_business_plan" if invalid and retries remaining
    """
    is_valid = state.get("is_valid", False)
    revision_number = state.get("revision_number", 0)
    MAX_RETRIES = 3

    if is_valid:
        return "generate_business_feedback"
    elif revision_number < MAX_RETRIES:
        print(f"---RETRYING GRADING (Attempt {revision_number + 1}/{MAX_RETRIES})---")
        return "grade_business_plan"
    else:
        print("---MAX RETRIES REACHED, PROCEEDING WITH BEST EFFORT---")
        return "generate_business_feedback"


# --- BUILD BUSINESS WORKFLOW GRAPH ---
business_workflow = StateGraph(AgentState)  # Using AgentState for consistent type checking

# Add nodes
business_workflow.add_node("business_retrieve", business_retrieve)
business_workflow.add_node("grade_business_plan", grade_business_plan)
business_workflow.add_node("validate_business_grade", validate_business_grade)
business_workflow.add_node("generate_business_feedback", generate_business_feedback)

# Set entry point — retrieve context first, then grade
business_workflow.set_entry_point("business_retrieve")

# Add edges
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

# Compile
business_app = business_workflow.compile()

print("Business agent workflow compiled successfully")
