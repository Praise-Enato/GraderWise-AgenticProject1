from backend.src.models import RubricItem
from typing import List


# BYUMS Business Plan Competition Rubric (28 criteria, 100 total points)
BYUMS_RUBRIC = [
    RubricItem(
        criteria="Problem/Pain Point - Clearly defined the problem",
        max_points=2.5,
        description="Clearly defined the problem/pain being addressed. Must have a compelling narrative.",
        developing_points=1.25,
        developing_description="Problem is mentioned but lacks depth, clarity, or compelling urgency.",
        zero_points=0.0,
        zero_description="Missing problem statement or extremely vague definition.",
        course_guide="""Every successful business exists to solve a problem or relieve a "pain point" for its customers. If you do not clearly define the problem, the rest of your business plan is irrelevant because nobody will care about your solution. You must articulate exactly what the issue is, who experiences it, and why it is frustrating, costly, or time-consuming for them. The best problem definitions are highly relatable and often elicit a "nod of agreement" from the audience. Make the judges feel the pain before you introduce the cure."""
    ),
    RubricItem(
        criteria="Problem/Pain Point - Outside data confirms scalability",
        max_points=5.0,
        description="Outside data confirms the problem is huge (scalable). Must cite specific sources/statistics.",
        developing_points=2.5,
        developing_description="Some data provided but unsourced, anecdotal, or doesn't prove large scalability.",
        zero_points=0.0,
        zero_description="No external data or statistics provided at all to back up the problem size.",
        course_guide=""""""
    ),
    RubricItem(
        criteria="Problem/Pain Point - Examples of other solutions",
        max_points=2.5,
        description="Specific examples of what others are doing to solve the problem (existing alternatives).",
        developing_points=1.25,
        developing_description="Mentions alternatives briefly but lacks specific company names or detailed examples.",
        zero_points=0.0,
        zero_description="Claims there are no other solutions without proof, or simply ignores existing alternatives.",
        course_guide=""""""
    ),
    RubricItem(
        criteria="Business Venture - Solution is better than alternatives",
        max_points=5.0,
        description="Describe how your solution is explicitly better than the other options (competitive moat/advantage).",
        developing_points=2.5,
        developing_description="Claims to be better but lacks strong evidence of a defensible moat or 10x improvement.",
        zero_points=0.0,
        zero_description="Does not explain why the solution is better than existing options.",
        course_guide=""""""
    ),
    RubricItem(
        criteria="Business Venture - Revenue generation (monetization)",
        max_points=5.0,
        description="Clear explanation of how the business generates revenue (monetization strategy, pricing model).",
        developing_points=2.5,
        developing_description="Mentions making money but pricing model is vague or unrealistic.",
        zero_points=0.0,
        zero_description="No monetization strategy or revenue model provided.",
        course_guide=""""""
    ),
    RubricItem(
        criteria="Business Venture - Cost structure",
        max_points=2.0,
        description="Describe cost structure (fixed vs variable costs, key expense drivers).",
        developing_points=1.0,
        developing_description="Mentions costs vaguely (e.g., 'marketing and servers') without structure.",
        zero_points=0.0,
        zero_description="Completely omits discussion of business costs.",
        course_guide="""Understanding how you make money is only half the equation; you must also understand how you spend it. You need to outline both your fixed costs (rent, salaries, software subscriptions) and your variable costs (materials, shipping, manufacturing per unit). Demonstrating a firm grasp on your cost structure proves that you understand the underlying unit economics of your business. It allows judges to see at what point your business becomes profitable and how efficiently you can scale operations."""
    ),
    RubricItem(
        criteria="Business Venture - Value proposition",
        max_points=3.0,
        description="Explain value proposition clearly and concisely.",
        developing_points=1.5,
        developing_description="Value prop exists but is confusing, jargon-heavy, or unconvincing.",
        zero_points=0.0,
        zero_description="Missing a clear value proposition.",
        course_guide="""Your value proposition is the core promise you make to your customer. It is a clear, concise statement that summarizes why a consumer should buy your product or use your service. While "how your solution is better" focuses on the competition, the value proposition focuses on the *customer's outcome*. It bridges the gap between the features of your product and the direct benefits the user will experience (e.g., saving 10 hours a week, increasing their sales by 20%, or providing peace of mind)."""
    ),
    RubricItem(
        criteria="Market Size - Target market and growth trends",
        max_points=2.5,
        description="Detailed analysis of the target market, segment size, and growth trends with data.",
        developing_points=1.25,
        developing_description="Market mentioned but lacks hard numbers, sizing methodologies, or trend data.",
        zero_points=0.0,
        zero_description="No target market analysis or growth trends documented.",
        course_guide="""Investors want to board a moving train, not a stationary one. You must analyze the broader industry landscape. Is your target market expanding or shrinking? What are the current macroeconomic trends, technological shifts, or cultural changes driving this market? Provide metrics like the Compound Annual Growth Rate (CAGR). Showing that you are entering a growing market means that even if you only capture a small slice of the pie, that slice will naturally grow larger over time."""
    ),
    RubricItem(
        criteria="Market Size - Clearly identify the buyer",
        max_points=2.5,
        description="Clearly identify exactly who the buyer/customer persona is.",
        developing_points=1.25,
        developing_description="Identifies a broad, generic buyer (e.g., 'everyone' or 'women') without specific personas.",
        zero_points=0.0,
        zero_description="Fails to identify the target buyer.",
        course_guide=""""""
    ),
    RubricItem(
        criteria="Market Size - Identify competitors",
        max_points=2.5,
        description="Identify specifically who competitors are by name.",
        developing_points=1.25,
        developing_description="Mentions competitors exist but doesn't name specific key players, or only lists indirect competitors.",
        zero_points=0.0,
        zero_description="Fails to name any competitors.",
        course_guide=""""""
    ),
    RubricItem(
        criteria="Market Size - Strengths and weaknesses of competitors",
        max_points=2.5,
        description="Honest analysis of the strengths and weaknesses of named competitors.",
        developing_points=1.25,
        developing_description="Superficial competitive analysis (e.g., 'they are expensive, we are cheap').",
        zero_points=0.0,
        zero_description="No analysis of competitor strengths/weaknesses.",
        course_guide="""Once you have identified your competitors, you must analyze them objectively. What do they do exceptionally well? (Do they have a massive marketing budget? Brand loyalty?) More importantly, where are they failing? What are their blind spots, negative reviews, or technological limitations? By mapping out their strengths and weaknesses, you reveal the exact vulnerabilities in the market that your business is designed to exploit."""
    ),
    RubricItem(
        criteria="Marketing/Sales - Plan to acquire customers",
        max_points=2.5,
        description="Specific, actionable plan to acquire customers (CAC strategies, campaigns).",
        developing_points=1.25,
        developing_description="Vague acquisition plan (e.g., 'we will use social media') without specifics.",
        zero_points=0.0,
        zero_description="No customer acquisition plan.",
        course_guide="""Having a great product does not guarantee that people will find it. You must outline a concrete Go-To-Market (GTM) strategy. How will you generate awareness and drive traffic? This involves detailing your marketing campaigns, whether it is through SEO, content marketing, paid social media advertising, influencer partnerships, or PR. You need to explain the journey a customer takes from never having heard of you to making their first purchase, and roughly what it will cost to acquire them (Customer Acquisition Cost - CAC)."""
    ),
    RubricItem(
        criteria="Marketing/Sales - Identify sales channels",
        max_points=2.5,
        description="Identify clear sales channels (e.g., direct-to-consumer, B2B, retail partnerships).",
        developing_points=1.25,
        developing_description="Mentions sales vaguely but unclear on the specific channel mechanics.",
        zero_points=0.0,
        zero_description="Missing identification of sales channels.",
        course_guide="""A sales channel is the specific medium through which your product is delivered to the end consumer. Will you sell directly to consumers via your own e-commerce website? Will you use third-party marketplaces like Amazon? Will you sell through brick-and-mortar retail stores, or use a B2B direct sales team doing cold outreach? Clearly defining your sales channels explains the logistics of your revenue generation and the intermediaries involved."""
    ),
    RubricItem(
        criteria="Marketing/Sales - Sales forecasts backed by data",
        max_points=2.5,
        description="Sales volume forecasting backed by reasonable assumptions and data.",
        developing_points=1.25,
        developing_description="Sales forecasts are present but unrealistic, or lack backing data.",
        zero_points=0.0,
        zero_description="No sales forecasts provided.",
        course_guide="""Projections show your ambition, but data shows your grounding in reality. You need to provide sales forecasts for the upcoming months/years, but they cannot be arbitrary numbers pulled from thin air. Your forecasts must be justified by your marketing strategy, market size, and current traction. For example, "If we spend X on marketing based on an industry-average conversion rate of Y%, we expect to acquire Z customers." Show the math behind your milestones."""
    ),
    RubricItem(
        criteria="Marketing/Sales - Risk factors impacting sales",
        max_points=2.5,
        description="Explicitly identified and quantified risk factors that will severely impact sales goals.",
        developing_points=1.25,
        developing_description="Mentions generic risks but not specific sales-impacting risks with mitigation plans.",
        zero_points=0.0,
        zero_description="Completely omits any discussion of risk factors.",
        course_guide=""""""
    ),
    RubricItem(
        criteria="Financials - Past 3 years provided",
        max_points=5.0,
        description="Financial data for the past 3 years is provided (if applicable).",
        developing_points=2.5,
        developing_description="Provides 1-2 years of data, or data is poorly formatted.",
        zero_points=0.0,
        zero_description="No past financial data provided (if a new venture with no history, score 0).",
        course_guide="""If your business is already operating, historical financial data is the ultimate proof of concept. Providing your past financials (Profit & Loss statements, revenue growth, cash flow) shows how you have managed money thus far. It provides a baseline to prove that your business model actually works in the real world. If you are a pre-revenue startup, this section might be adapted to show the history of your funding, grants, or the personal capital you have invested to get to this point."""
    ),
    RubricItem(
        criteria="Financials - Forecast profits and expenses",
        max_points=5.0,
        description="Clear 3-5 year forecast of profits and expenses with realistic assumptions.",
        developing_points=2.5,
        developing_description="Forecasts exist but lack reasonable assumptions, P&L structure, or seem drastically inflated.",
        zero_points=0.0,
        zero_description="No future financial projections provided.",
        course_guide="""This is your financial roadmap for the future (Pro Forma statements). You must project your expected revenues, gross margins, operating expenses, and net profit over the next 3 to 5 years. This shows the judges the ultimate financial potential of the company. It reveals when you expect to break even and when the company will become highly profitable. It also shows if you truly understand the scale of expenses required to grow your business."""
    ),
    RubricItem(
        criteria="Financials - Detailed breakdown",
        max_points=5.0,
        description="Detailed, granular breakdown of the financials (not just high-level summaries).",
        developing_points=2.5,
        developing_description="Some breakdown provided, but missing key line items or categorizations.",
        zero_points=0.0,
        zero_description="Only provides high-level top/bottom line numbers with no breakdown.",
        course_guide="""High-level summaries are not enough for the financial section; the devil is in the details. You must provide a granular breakdown of your numbers. Instead of just saying "Marketing: $50,000," break it down into exactly what that entails (e.g., $20k for ad spend, $15k for an agency, $15k for trade shows). This detailed breakdown allows judges to evaluate your assumptions. It proves that you have thought through every operational requirement of the business."""
    ),
    RubricItem(
        criteria="Management Team - Depth of expertise",
        max_points=2.0,
        description="Depth of expertise relevant to the business venture.",
        developing_points=1.0,
        developing_description="Resumes provided but missing key technical or domain expertise for the specific venture.",
        zero_points=0.0,
        zero_description="No team information provided.",
        course_guide="""Ideas are cheap; execution is everything. Investors invest in teams. Why are *you* and your co-founders the absolute best people in the world to build this specific business? You must highlight the relevant domain expertise, past successes, technical skills, and industry connections of your management team. If you are building medical software, having a doctor or healthcare compliance expert on your team provides massive credibility. Highlight what makes your team uniquely capable."""
    ),
    RubricItem(
        criteria="Management Team - Leadership is agile",
        max_points=3.0,
        description="Demonstrate leadership is agile, coachable, or capable of pivoting.",
        developing_points=1.5,
        developing_description="Mentions team ambition but fails to show evidence of agility or past pivots.",
        zero_points=0.0,
        zero_description="No demonstration of leadership capability.",
        course_guide="""Startups rarely end up exactly where they started. You will face unforeseen challenges, market shifts, and product failures. You must demonstrate that your leadership team is agile—meaning you are capable of learning quickly, pivoting when the data tells you to, and adapting to new realities without falling apart. Share brief examples of how you have overcome obstacles, adapted to feedback, or changed your approach based on new evidence. Coachability and resilience are key indicators of an agile team."""
    ),
    RubricItem(
        criteria="Use of Prize Money - Specific budget",
        max_points=10.0,
        description="Highly specific, line-item budget for how the prize money will be allocated.",
        developing_points=5.0,
        developing_description="Vague allocation (e.g., '50% marketing, 50% ops') rather than specific initiatives.",
        zero_points=0.0,
        zero_description="Does not explain what the prize money will be used for.",
        course_guide="""If you win this competition, what exactly are you going to do with the funds? Investors and judges do not want to hand over money for "general operations" or to pay founders' salaries in the early days. They want to fund growth. You must provide a highly specific, itemized budget for the prize money. Explain exactly what milestones this specific amount of money will unlock (e.g., "The $10,000 will be used specifically to finalize the patent filing ($4k) and manufacture the first 500 beta units ($6k)"). Prove that the prize money will create a tangible ROI."""
    ),
    RubricItem(
        criteria="Conclusion - Overall summary",
        max_points=2.0,
        description="A strong overall summary wrapping up the pitch.",
        developing_points=1.0,
        developing_description="Weak or abrupt summary.",
        zero_points=0.0,
        zero_description="No conclusion or summary slide.",
        course_guide="""As you wrap up your pitch, you need to bring everything back together in a powerful elevator pitch. Remind the judges of the core narrative: the severe problem, your brilliant solution, and the massive market opportunity. The overall summary should leave no ambiguity about what your business does and why it matters. It is your final chance to cement your core message in their minds."""
    ),
    RubricItem(
        criteria="Conclusion - Highlighted key points",
        max_points=2.0,
        description="Clearly reiterated the most important key points for judges to remember.",
        developing_points=1.0,
        developing_description="Mentioned some points but failed to highlight the true core value.",
        zero_points=0.0,
        zero_description="Did not highlight any key takeaways.",
        course_guide="""While the summary is narrative, highlighting key points serves as a rapid-fire recap of your most impressive metrics and milestones. Did you secure a letter of intent? Do you have 500 people on a waitlist? Are your profit margins exceptionally high? Reiterate the 2 or 3 most impressive, unarguable facts from your presentation. This ensures the judges are thinking about your strongest assets as they fill out their rubrics."""
    ),
    RubricItem(
        criteria="Conclusion - Link to Google Slide Deck",
        max_points=1.0,
        description="A valid link provided to the Google Slide Deck.",
        developing_points=0.5,
        developing_description="Link provided but inaccessible or not a Google Slide Deck.",
        zero_points=0.0,
        zero_description="No link to the slide deck provided whatsoever.",
        course_guide=""""""
    ),
]


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
        "byums": BYUMS_RUBRIC,
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
