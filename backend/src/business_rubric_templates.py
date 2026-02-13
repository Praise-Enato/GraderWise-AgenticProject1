from backend.src.models import RubricItem
from typing import List


# Startup Pitch Deck Rubric (for early-stage startups, seed/Series A)
STARTUP_RUBRIC = [
    RubricItem(
        criteria="Problem Statement",
        max_points=15,
        description="Clear articulation of customer pain point with evidence of market need and specific examples",
        developing_points=8,
        developing_description="Problem identified but lacks specificity, evidence, or compelling urgency",
        zero_points=0,
        zero_description="Vague, missing, or unconvincing problem statement"
    ),
    RubricItem(
        criteria="Market Opportunity (TAM/SAM/SOM)",
        max_points=15,
        description="Market sizing with credible sources, clear methodology, and realistic TAM/SAM/SOM breakdown",
        developing_points=8,
        developing_description="Market size mentioned but lacks breakdown, sourcing, or realistic assumptions",
        zero_points=0,
        zero_description="No market analysis or completely unrealistic/unsourced numbers"
    ),
    RubricItem(
        criteria="Business Model & Unit Economics",
        max_points=15,
        description="Clear revenue model with pricing strategy, defined unit economics (CAC, LTV, margins), and path to profitability",
        developing_points=8,
        developing_description="Revenue model described but missing key metrics, unit economics, or unclear monetization",
        zero_points=0,
        zero_description="Unclear how the business makes money or missing business model entirely"
    ),
    RubricItem(
        criteria="Financial Projections (3-5 year)",
        max_points=20,
        description="Realistic 3-5 year projections with P&L, cash flow, clear assumptions, and achievable growth rates (typically <100% MoM)",
        developing_points=10,
        developing_description="Basic projections present but missing detail, unrealistic growth, or lacks key assumptions",
        zero_points=0,
        zero_description="No financial projections or completely unrealistic/unsubstantiated numbers"
    ),
    RubricItem(
        criteria="Competitive Analysis",
        max_points=10,
        description="Identifies key competitors, provides clear differentiation, and explains defensible competitive moat or advantages",
        developing_points=5,
        developing_description="Competitors listed but weak differentiation or ignores obvious competition",
        zero_points=0,
        zero_description="Claims no competition, ignores obvious competitors, or missing competitive analysis"
    ),
    RubricItem(
        criteria="Team & Execution Capability",
        max_points=10,
        description="Team has relevant domain experience, complementary skills, and demonstrated execution track record",
        developing_points=5,
        developing_description="Team listed but lacking relevant experience, gaps in skillset, or no track record",
        zero_points=0,
        zero_description="No team information, clearly unqualified team, or critical skill gaps"
    ),
    RubricItem(
        criteria="Presentation Quality (Pitch Deck)",
        max_points=15,
        description="Professional design, clear visual hierarchy, compelling narrative flow, effective data visualization",
        developing_points=8,
        developing_description="Functional presentation but lacks polish, clarity, or has design/flow issues",
        zero_points=0,
        zero_description="Unprofessional, confusing, or poorly designed presentation"
    )
]


# Enterprise Business Plan Rubric (for established companies, strategic initiatives)
ENTERPRISE_RUBRIC = [
    RubricItem(
        criteria="Strategic Alignment & Objectives",
        max_points=15,
        description="Clear strategic objectives aligned with corporate goals, measurable KPIs, and defined success metrics",
        developing_points=8,
        developing_description="Objectives stated but weak alignment, vague KPIs, or missing success metrics",
        zero_points=0,
        zero_description="No clear objectives or misaligned with corporate strategy"
    ),
    RubricItem(
        criteria="Market & Competitive Analysis",
        max_points=15,
        description="Comprehensive market research, industry trends analysis, competitive positioning, and SWOT analysis",
        developing_points=8,
        developing_description="Basic market analysis but lacking depth, missing competitive insights, or incomplete SWOT",
        zero_points=0,
        zero_description="No market analysis or superficial research"
    ),
    RubricItem(
        criteria="Operational Plan",
        max_points=15,
        description="Detailed operational strategy, resource requirements, timeline with milestones, and risk mitigation plans",
        developing_points=8,
        developing_description="Basic operational outline but missing detail, vague timeline, or inadequate risk planning",
        zero_points=0,
        zero_description="No operational plan or completely impractical approach"
    ),
    RubricItem(
        criteria="Financial Analysis & ROI",
        max_points=25,
        description="Comprehensive financial model with P&L, cash flow, NPV/IRR analysis, clear ROI projection, and sensitivity analysis",
        developing_points=13,
        developing_description="Financial model present but missing key metrics, unrealistic assumptions, or weak ROI justification",
        zero_points=0,
        zero_description="No financial analysis or completely unrealistic projections"
    ),
    RubricItem(
        criteria="Implementation & Change Management",
        max_points=15,
        description="Clear implementation roadmap, change management strategy, stakeholder communication plan, and success metrics",
        developing_points=8,
        developing_description="Basic implementation plan but weak change management or missing stakeholder strategy",
        zero_points=0,
        zero_description="No implementation plan or ignores organizational change challenges"
    ),
    RubricItem(
        criteria="Documentation & Presentation Quality",
        max_points=15,
        description="Professional documentation, executive summary, clear structure, supporting data/appendices",
        developing_points=8,
        developing_description="Adequate documentation but lacks polish, organization, or supporting materials",
        zero_points=0,
        zero_description="Poor documentation quality or confusing structure"
    )
]


# Nonprofit Proposal Rubric (for grant proposals, social enterprises)
NONPROFIT_RUBRIC = [
    RubricItem(
        criteria="Mission & Problem Statement",
        max_points=15,
        description="Clear mission aligned with social need, compelling problem statement with data/evidence, and defined beneficiaries",
        developing_points=8,
        developing_description="Mission stated but weak problem definition, lacking evidence, or unclear beneficiaries",
        zero_points=0,
        zero_description="Vague mission or unconvincing need for the initiative"
    ),
    RubricItem(
        criteria="Theory of Change & Impact Model",
        max_points=20,
        description="Clear theory of change, defined impact metrics, measurable outcomes, and evidence-based approach",
        developing_points=10,
        developing_description="Impact model present but weak logic, vague metrics, or insufficient evidence base",
        zero_points=0,
        zero_description="No theory of change or missing impact measurement framework"
    ),
    RubricItem(
        criteria="Program Design & Activities",
        max_points=15,
        description="Detailed program activities, clear implementation plan, realistic timeline, and scalability considerations",
        developing_points=8,
        developing_description="Program outlined but lacking detail, unrealistic timeline, or weak scalability plan",
        zero_points=0,
        zero_description="Vague program description or impractical design"
    ),
    RubricItem(
        criteria="Budget & Financial Sustainability",
        max_points=20,
        description="Detailed budget with justifications, diverse funding sources, sustainability plan beyond initial funding",
        developing_points=10,
        developing_description="Budget present but lacks detail, over-reliant on single source, or weak sustainability plan",
        zero_points=0,
        zero_description="No budget, unrealistic costs, or no sustainability strategy"
    ),
    RubricItem(
        criteria="Organizational Capacity",
        max_points=15,
        description="Demonstrated organizational track record, qualified team, governance structure, and community partnerships",
        developing_points=8,
        developing_description="Basic capacity outlined but limited track record, gaps in expertise, or weak partnerships",
        zero_points=0,
        zero_description="No evidence of organizational capacity or critical capability gaps"
    ),
    RubricItem(
        criteria="Evaluation & Learning Plan",
        max_points=15,
        description="Clear evaluation framework, data collection methods, success indicators, and adaptive learning approach",
        developing_points=8,
        developing_description="Basic evaluation plan but vague methods, weak indicators, or no learning strategy",
        zero_points=0,
        zero_description="No evaluation plan or inadequate measurement approach"
    )
]


# General Business Plan Rubric (universal, any business type)
GENERAL_RUBRIC = [
    RubricItem(
        criteria="Executive Summary & Problem Statement",
        max_points=15,
        description="Concise executive summary with clear problem definition, target customer, and proposed solution",
        developing_points=8,
        developing_description="Summary present but unfocused, vague problem, or missing key elements",
        zero_points=0,
        zero_description="No executive summary or fails to articulate the core problem"
    ),
    RubricItem(
        criteria="Market Analysis & Opportunity",
        max_points=15,
        description="Market sizing with methodology and sources, target segment definition, and industry trend awareness",
        developing_points=8,
        developing_description="Market discussed but lacks data, sources, or clear segmentation",
        zero_points=0,
        zero_description="No market analysis or completely unsupported claims"
    ),
    RubricItem(
        criteria="Business Model & Revenue Strategy",
        max_points=15,
        description="Clear revenue model, pricing rationale, customer acquisition strategy, and value proposition",
        developing_points=8,
        developing_description="Revenue model mentioned but incomplete, missing pricing logic, or unclear value prop",
        zero_points=0,
        zero_description="No business model or unclear how the venture generates revenue"
    ),
    RubricItem(
        criteria="Financial Plan & Projections",
        max_points=20,
        description="Revenue projections with stated assumptions, expense breakdown, funding requirements, and path to sustainability",
        developing_points=10,
        developing_description="Basic financials present but missing assumptions, no expense detail, or unrealistic projections",
        zero_points=0,
        zero_description="No financial plan or entirely unsubstantiated numbers"
    ),
    RubricItem(
        criteria="Competitive Analysis & Differentiation",
        max_points=10,
        description="Key competitors identified with honest comparison, clear differentiation, and defensibility explanation",
        developing_points=5,
        developing_description="Competitors mentioned but shallow analysis, weak differentiation, or ignores key players",
        zero_points=0,
        zero_description="No competitive analysis or claims no competition exists"
    ),
    RubricItem(
        criteria="Team & Operations",
        max_points=10,
        description="Team with relevant skills, operational plan covering key processes, and risk acknowledgment with mitigations",
        developing_points=5,
        developing_description="Team listed but skill gaps unaddressed, vague operations, or no risk awareness",
        zero_points=0,
        zero_description="No team info, no operational plan, or critical unaddressed gaps"
    ),
    RubricItem(
        criteria="Presentation & Communication Quality",
        max_points=15,
        description="Professional formatting, logical structure, clear writing, effective use of visuals and data",
        developing_points=8,
        developing_description="Readable but lacks polish, inconsistent formatting, or weak visual communication",
        zero_points=0,
        zero_description="Poorly written, confusing structure, or unprofessional presentation"
    )
]


def get_rubric_template(business_type: str) -> List[RubricItem]:
    """
    Get rubric template based on business plan type.

    Args:
        business_type: One of "startup", "enterprise", "nonprofit"

    Returns:
        List of RubricItem objects for the specified business type
    """
    templates = {
        "startup": STARTUP_RUBRIC,
        "enterprise": ENTERPRISE_RUBRIC,
        "nonprofit": NONPROFIT_RUBRIC,
        "general": GENERAL_RUBRIC
    }

    # Default to general if unknown type
    return templates.get(business_type.lower(), GENERAL_RUBRIC)


def get_rubric_total_points(rubric: List[RubricItem]) -> float:
    """Calculate total possible points for a rubric"""
    return sum(item.max_points for item in rubric)
