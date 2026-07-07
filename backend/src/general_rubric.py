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

Each criterion carries FOUR grader signals (like the BYUMS rubric): a `course_guide`
(what the criterion means / what good looks like), a full-marks `description`, a
`developing_description` (partial credit), and a `zero_description` (what earns 0).
The tier descriptions make partial-credit boundaries explicit so scoring is
consistent. Criterion names use the "Section - Label" convention so the frontend
groups them into sections.
"""
from typing import List

from backend.src.models import RubricItem

# Each row: criteria, max_points, guide (intent), full (full marks),
# partial (developing), zero (absent/unsupported).
_ROWS = [
    {
        "criteria": "Executive Summary - Clear, compelling overview",
        "max": 3,
        "guide": "The 30-second pitch: could a busy reader grasp the business and why it wins from this alone?",
        "full": "A concise, compelling summary of the business and why it will succeed.",
        "partial": "A summary is present but vague, generic, or missing the hook.",
        "zero": "No executive summary, or it conveys nothing about the business.",
    },
    {
        "criteria": "Executive Summary - Covers the key points",
        "max": 3,
        "guide": "A good summary previews the whole plan: opportunity, offering, market, and the goal/ask.",
        "full": "Summarizes the opportunity, offering, target market, and the goal or ask.",
        "partial": "Covers some of these but omits one or more key elements.",
        "zero": "Covers none of the key elements.",
    },
    {
        "criteria": "Problem & Solution - Problem clearly defined",
        "max": 4,
        "guide": "A sharp, specific customer pain beats a broad societal theme. 'Who hurts, and how?'",
        "full": "Clearly defines a real, specific customer problem or pain point.",
        "partial": "A problem is mentioned but stays broad, generic, or loosely defined.",
        "zero": "No clear problem, or only a vague theme with no customer pain.",
    },
    {
        "criteria": "Problem & Solution - Evidence of need or demand",
        "max": 3,
        "guide": "Is the problem real and sizable? Data OR credible first-hand evidence both count.",
        "full": "Evidence the problem is real and sizable (data or credible first-hand evidence).",
        "partial": "Some evidence, but thin, unsourced, or only anecdotal.",
        "zero": "Asserts a need with no evidence at all.",
    },
    {
        "criteria": "Problem & Solution - Solution fits the problem",
        "max": 3,
        "guide": "The offering should directly resolve the stated problem — not an adjacent one.",
        "full": "The product or service clearly and effectively addresses the stated problem.",
        "partial": "A solution is described but only loosely connected to the problem.",
        "zero": "The solution does not address the stated problem, or none is given.",
    },
    {
        "criteria": "Business & Model - What the business does and its mission",
        "max": 3,
        "guide": "What is this business, at what stage, and why does it exist?",
        "full": "Clearly describes the business, its stage (new/existing), and its mission or purpose.",
        "partial": "Describes the business but leaves stage or mission unclear.",
        "zero": "Cannot tell what the business actually does.",
    },
    {
        "criteria": "Business & Model - Revenue model",
        "max": 7,
        "guide": "The engine of the business: exactly how it makes money. Weighted heavily for a reason.",
        "full": "Explains clearly how the business makes money — pricing, unit economics, or monetization.",
        "partial": "A revenue idea is present but incomplete (e.g. 'we sell X' with no pricing or unit economics).",
        "zero": "No explanation of how the business earns revenue.",
    },
    {
        "criteria": "Products & Services - Offering described",
        "max": 3,
        "guide": "A concrete description of what the customer actually gets.",
        "full": "Clear description of the products or services offered.",
        "partial": "The offering is named but not really described.",
        "zero": "No description of what is offered.",
    },
    {
        "criteria": "Products & Services - Value proposition",
        "max": 4,
        "guide": "The concrete reason a customer picks this over doing nothing or buying elsewhere.",
        "full": "A clear value proposition — the concrete reason customers choose this.",
        "partial": "A benefit is claimed but generic or not customer-specific.",
        "zero": "No value proposition — nothing tells the customer why to choose it.",
    },
    {
        "criteria": "Products & Services - Differentiation",
        "max": 3,
        "guide": "What makes this hard to copy or clearly better than alternatives?",
        "full": "Explains the competitive advantage over alternatives.",
        "partial": "Claims to be different/better but without a concrete edge.",
        "zero": "No differentiation stated.",
    },
    {
        "criteria": "Market Analysis - Target market identified",
        "max": 4,
        "guide": "A specific customer segment beats 'everyone'. Precision here signals real understanding.",
        "full": "Clearly identifies who the customers or buyers are.",
        "partial": "Names a market but too broadly (e.g. 'all of the country').",
        "zero": "No identified target customer.",
    },
    {
        "criteria": "Market Analysis - Market size and demand",
        "max": 4,
        "guide": "Is the opportunity big enough? TAM/SAM/SOM, growth trends, or credible bottom-up counts.",
        "full": "Provides evidence of market size, demand, or growth.",
        "partial": "Gestures at size/demand but without figures or a credible basis.",
        "zero": "No sense of how big or growing the market is.",
    },
    {
        "criteria": "Market Analysis - Competitors identified",
        "max": 3,
        "guide": "Every business has competition (including 'the status quo'). Naming it shows awareness.",
        "full": "Names the main competitors.",
        "partial": "Acknowledges competition only in general terms.",
        "zero": "Claims 'no competition', or ignores competitors entirely.",
    },
    {
        "criteria": "Market Analysis - Competitor strengths and weaknesses",
        "max": 3,
        "guide": "Understanding rivals' strengths/weaknesses is where the plan's own edge is justified.",
        "full": "Analyzes competitors' strengths and weaknesses.",
        "partial": "Lists competitors but with shallow or one-sided analysis.",
        "zero": "No analysis of competitors beyond naming (or not) them.",
    },
    {
        "criteria": "Marketing & Sales - Customer acquisition",
        "max": 4,
        "guide": "How will the first and next 1,000 customers actually be reached?",
        "full": "A concrete plan to acquire customers.",
        "partial": "A general intent to market, but no concrete acquisition plan.",
        "zero": "No plan for how customers will be acquired.",
    },
    {
        "criteria": "Marketing & Sales - Sales channels",
        "max": 3,
        "guide": "Where and how the transaction happens (direct, retail, online, distributors).",
        "full": "Identifies how and where sales happen (channels).",
        "partial": "Mentions a channel vaguely without detail.",
        "zero": "No sales channels described.",
    },
    {
        "criteria": "Marketing & Sales - Pricing strategy",
        "max": 3,
        "guide": "A price with a rationale (cost-plus, value-based, competitive) beats a bare number.",
        "full": "A clear, justified pricing approach.",
        "partial": "States a price but with no rationale.",
        "zero": "No pricing information.",
    },
    {
        "criteria": "Marketing & Sales - Promotion tactics",
        "max": 2,
        "guide": "Specific tactics (channels, campaigns, partnerships) rather than 'we will advertise'.",
        "full": "Specific marketing or promotion tactics.",
        "partial": "Generic promotion mentions with no specifics.",
        "zero": "No promotion tactics.",
    },
    {
        "criteria": "Operations - Delivery or production plan",
        "max": 4,
        "guide": "How the thing actually gets made or delivered, repeatably.",
        "full": "Explains how the product or service is produced or delivered.",
        "partial": "A partial or high-level operations description.",
        "zero": "No production or delivery plan.",
    },
    {
        "criteria": "Operations - Location, facilities, capacity",
        "max": 2,
        "guide": "Where it operates and whether capacity matches the plan's ambitions.",
        "full": "Covers location, facilities, and capacity.",
        "partial": "Mentions location or facilities but not capacity (or vice versa).",
        "zero": "No location/facilities/capacity information.",
    },
    {
        "criteria": "Operations - Suppliers and logistics",
        "max": 2,
        "guide": "Key inputs, suppliers, and how goods/services move — the supply chain reality.",
        "full": "Addresses key suppliers, inputs, or logistics.",
        "partial": "Touches on suppliers/logistics superficially.",
        "zero": "No supplier or logistics consideration.",
    },
    {
        "criteria": "Management & Team - Roles and expertise",
        "max": 4,
        "guide": "Who runs this and why they're credible to do so.",
        "full": "Identifies the team, their roles, and relevant expertise.",
        "partial": "Names people but without clear roles or relevant expertise.",
        "zero": "No team information.",
    },
    {
        "criteria": "Management & Team - Ability to execute",
        "max": 2,
        "guide": "Evidence (track record, advisors, early traction) that this team can actually deliver.",
        "full": "Demonstrates the team can realistically execute the plan.",
        "partial": "Some indication of capability but not convincing.",
        "zero": "Nothing supports the team's ability to execute.",
    },
    {
        "criteria": "Financials - Startup costs / capital needs",
        "max": 4,
        "guide": "What it costs to start and what funding is needed, itemized — not a round guess.",
        "full": "States startup costs or capital requirements with a breakdown.",
        "partial": "A total figure with little or no breakdown.",
        "zero": "No startup cost or capital information.",
    },
    {
        "criteria": "Financials - Revenue projections",
        "max": 4,
        "guide": "Forward sales/revenue with a basis. Round, aspirational numbers with no basis score low.",
        "full": "Provides revenue or sales projections.",
        "partial": "Projections given but with a weak or missing basis.",
        "zero": "No revenue projections.",
    },
    {
        "criteria": "Financials - Expense breakdown",
        "max": 3,
        "guide": "The cost structure — fixed vs variable, main line items.",
        "full": "Provides an expense or cost-structure breakdown.",
        "partial": "Partial cost information without a real breakdown.",
        "zero": "No expense information.",
    },
    {
        "criteria": "Financials - Profitability / break-even",
        "max": 4,
        "guide": "Does it make money, and when? Margins, break-even point, or path to profit.",
        "full": "Addresses profit margins, profitability, or break-even.",
        "partial": "Mentions profit loosely without margins or a break-even point.",
        "zero": "No profitability or break-even analysis.",
    },
    {
        "criteria": "Financials - Credibility of figures",
        "max": 3,
        "guide": "The numbers must add up. Inconsistent or impossible figures signal error or fabrication.",
        "full": "Financial figures are internally consistent and realistic (profit = revenue - expenses; no impossible numbers).",
        "partial": "Mostly plausible figures with minor inconsistencies.",
        "zero": "Figures are internally inconsistent, impossible, or contradictory (e.g. profit exceeds revenue).",
    },
    {
        "criteria": "Growth & Risk - Growth or expansion plan",
        "max": 3,
        "guide": "A credible path to scale beyond the starting point.",
        "full": "A credible plan to grow or scale the business.",
        "partial": "A vague aspiration to grow without a concrete plan.",
        "zero": "No growth or expansion plan.",
    },
    {
        "criteria": "Growth & Risk - Risk factors and mitigation",
        "max": 3,
        "guide": "Honest, specific risks WITH mitigations. The bar is high — vague risk sections score low.",
        "full": "Identifies key risks and how they will be managed.",
        "partial": "Names risks but without mitigation (or vice versa).",
        "zero": "No risk consideration, or 'there are no risks'.",
    },
]

GENERAL_RUBRIC: List[RubricItem] = [
    RubricItem(
        criteria=r["criteria"],
        max_points=r["max"],
        description=r["full"],
        developing_description=r["partial"],
        zero_description=r["zero"],
        course_guide=r["guide"],
    )
    for r in _ROWS
]


def total_points() -> float:
    return sum(item.max_points for item in GENERAL_RUBRIC)


def to_dicts() -> List[dict]:
    return [item.model_dump() for item in GENERAL_RUBRIC]
