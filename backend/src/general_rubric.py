"""A general-purpose business-plan rubric (not competition-specific).

Universal dimensions that apply to any business plan, derived from studying a
range of real plans (formal-numbered, loose prose, and pitch-style) AND the BYUMS
competition rubric's structure (Problem, Business Venture, Market, Marketing,
Financials, Management), minus its competition-only items (video, use-of-prize-
money, "link in video"). The grader maps a plan's content to these criteria
regardless of the plan's own headings.

Total = 100 points. Financials is weighted heaviest (18, incl. a credibility
check reusing the data-consistency rule); Market (14) and Marketing (12) next.
Management/Team and Operations are lighter, since many early-stage plans are thin
there.

Criterion names use the "Section - Label" convention so the frontend groups them
into sections (same as the BYUMS rubric).
"""
from typing import List

from backend.src.models import RubricItem

# (criteria, max_points, full-marks description)
_ROWS = [
    ("Executive Summary - Clear, compelling overview", 3,
     "A concise, compelling summary of the business and why it will succeed."),
    ("Executive Summary - Covers the key points", 3,
     "Summarizes the opportunity, offering, target market, and the goal or ask."),

    ("Problem & Solution - Problem clearly defined", 4,
     "Clearly defines a real, specific customer problem or pain point."),
    ("Problem & Solution - Evidence of need or demand", 3,
     "Evidence the problem is real and sizable (data or credible first-hand evidence)."),
    ("Problem & Solution - Solution fits the problem", 3,
     "The product or service clearly and effectively addresses the stated problem."),

    ("Business & Model - What the business does and its mission", 3,
     "Clearly describes the business, its stage (new/existing), and its mission or purpose."),
    ("Business & Model - Revenue model", 7,
     "Explains clearly how the business makes money — pricing, unit economics, or monetization."),

    ("Products & Services - Offering described", 3,
     "Clear description of the products or services offered."),
    ("Products & Services - Value proposition", 4,
     "A clear value proposition — the concrete reason customers choose this."),
    ("Products & Services - Differentiation", 3,
     "Explains the competitive advantage over alternatives."),

    ("Market Analysis - Target market identified", 4,
     "Clearly identifies who the customers or buyers are."),
    ("Market Analysis - Market size and demand", 4,
     "Provides evidence of market size, demand, or growth."),
    ("Market Analysis - Competitors identified", 3,
     "Names the main competitors."),
    ("Market Analysis - Competitor strengths and weaknesses", 3,
     "Analyzes competitors' strengths and weaknesses."),

    ("Marketing & Sales - Customer acquisition", 4,
     "A concrete plan to acquire customers."),
    ("Marketing & Sales - Sales channels", 3,
     "Identifies how and where sales happen (channels)."),
    ("Marketing & Sales - Pricing strategy", 3,
     "A clear, justified pricing approach."),
    ("Marketing & Sales - Promotion tactics", 2,
     "Specific marketing or promotion tactics."),

    ("Operations - Delivery or production plan", 4,
     "Explains how the product or service is produced or delivered."),
    ("Operations - Location, facilities, capacity", 2,
     "Covers location, facilities, and capacity."),
    ("Operations - Suppliers and logistics", 2,
     "Addresses key suppliers, inputs, or logistics."),

    ("Management & Team - Roles and expertise", 4,
     "Identifies the team, their roles, and relevant expertise."),
    ("Management & Team - Ability to execute", 2,
     "Demonstrates the team can realistically execute the plan."),

    ("Financials - Startup costs / capital needs", 4,
     "States startup costs or capital requirements with a breakdown."),
    ("Financials - Revenue projections", 4,
     "Provides revenue or sales projections."),
    ("Financials - Expense breakdown", 3,
     "Provides an expense or cost-structure breakdown."),
    ("Financials - Profitability / break-even", 4,
     "Addresses profit margins, profitability, or break-even."),
    ("Financials - Credibility of figures", 3,
     "Financial figures are internally consistent and realistic (profit = revenue - expenses; no impossible numbers)."),

    ("Growth & Risk - Growth or expansion plan", 3,
     "A credible plan to grow or scale the business."),
    ("Growth & Risk - Risk factors and mitigation", 3,
     "Identifies key risks and how they will be managed."),
]

GENERAL_RUBRIC: List[RubricItem] = [
    RubricItem(criteria=c, max_points=m, description=d) for c, m, d in _ROWS
]


def total_points() -> float:
    return sum(item.max_points for item in GENERAL_RUBRIC)


def to_dicts() -> List[dict]:
    return [item.model_dump() for item in GENERAL_RUBRIC]
