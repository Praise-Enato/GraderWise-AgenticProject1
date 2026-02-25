import os
import re

file_path = "backend/src/business_rubric_templates.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Define the new BYUMS_RUBRIC list as a string
new_rubric_str = '''BYUMS_RUBRIC = [
    # --- Problem/Pain Point (10 pts) ---
    RubricItem(
        criteria="Problem/Pain Point - Clearly defined the problem",
        max_points=2.5,
        description="Clearly defined the problem/pain being addressed. Must have a compelling narrative.",
        developing_points=1.25,
        developing_description="Problem is mentioned but lacks depth, clarity, or compelling urgency.",
        zero_points=0,
        zero_description="Missing problem statement or extremely vague definition."
    ),
    RubricItem(
        criteria="Problem/Pain Point - Outside data confirms scalability",
        max_points=5.0,
        description="Outside data confirms the problem is huge (scalable). Must cite specific sources/statistics.",
        developing_points=2.5,
        developing_description="Some data provided but unsourced, anecdotal, or doesn't prove large scalability.",
        zero_points=0,
        zero_description="No external data or statistics provided at all to back up the problem size."
    ),
    RubricItem(
        criteria="Problem/Pain Point - Examples of other solutions",
        max_points=2.5,
        description="Specific examples of what others are doing to solve the problem (existing alternatives).",
        developing_points=1.25,
        developing_description="Mentions alternatives briefly but lacks specific company names or detailed examples.",
        zero_points=0,
        zero_description="Claims there are no other solutions without proof, or simply ignores existing alternatives."
    ),
    # --- Business Venture Product and Service (15 pts) ---
    RubricItem(
        criteria="Business Venture - Solution is better than alternatives",
        max_points=5.0,
        description="Describe how your solution is explicitly better than the other options (competitive moat/advantage).",
        developing_points=2.5,
        developing_description="Claims to be better but lacks strong evidence of a defensible moat or 10x improvement.",
        zero_points=0,
        zero_description="Does not explain why the solution is better than existing options."
    ),
    RubricItem(
        criteria="Business Venture - Revenue generation (monetization)",
        max_points=5.0,
        description="Clear explanation of how the business generates revenue (monetization strategy, pricing model).",
        developing_points=2.5,
        developing_description="Mentions making money but pricing model is vague or unrealistic.",
        zero_points=0,
        zero_description="No monetization strategy or revenue model provided."
    ),
    RubricItem(
        criteria="Business Venture - Cost structure",
        max_points=2.0,
        description="Describe cost structure (fixed vs variable costs, key expense drivers).",
        developing_points=1.0,
        developing_description="Mentions costs vaguely (e.g., 'marketing and servers') without structure.",
        zero_points=0,
        zero_description="Completely omits discussion of business costs."
    ),
    RubricItem(
        criteria="Business Venture - Value proposition",
        max_points=3.0,
        description="Explain value proposition clearly and concisely.",
        developing_points=1.5,
        developing_description="Value prop exists but is confusing, jargon-heavy, or unconvincing.",
        zero_points=0,
        zero_description="Missing a clear value proposition."
    ),
    # --- Market Size/Growth Potential (10 pts) ---
    RubricItem(
        criteria="Market Size - Target market and growth trends",
        max_points=2.5,
        description="Detailed analysis of the target market, segment size, and growth trends with data.",
        developing_points=1.25,
        developing_description="Market mentioned but lacks hard numbers, sizing methodologies, or trend data.",
        zero_points=0,
        zero_description="No target market analysis or growth trends documented."
    ),
    RubricItem(
        criteria="Market Size - Clearly identify the buyer",
        max_points=2.5,
        description="Clearly identify exactly who the buyer/customer persona is.",
        developing_points=1.25,
        developing_description="Identifies a broad, generic buyer (e.g., 'everyone' or 'women') without specific personas.",
        zero_points=0,
        zero_description="Fails to identify the target buyer."
    ),
    RubricItem(
        criteria="Market Size - Identify competitors",
        max_points=2.5,
        description="Identify specifically who competitors are by name.",
        developing_points=1.25,
        developing_description="Mentions competitors exist but doesn't name specific key players, or only lists indirect competitors.",
        zero_points=0,
        zero_description="Fails to name any competitors."
    ),
    RubricItem(
        criteria="Market Size - Strengths and weaknesses of competitors",
        max_points=2.5,
        description="Honest analysis of the strengths and weaknesses of named competitors.",
        developing_points=1.25,
        developing_description="Superficial competitive analysis (e.g., 'they are expensive, we are cheap').",
        zero_points=0,
        zero_description="No analysis of competitor strengths/weaknesses."
    ),
    # --- Marketing and Sales Strategy (10 pts) ---
    RubricItem(
        criteria="Marketing/Sales - Plan to acquire customers",
        max_points=2.5,
        description="Specific, actionable plan to acquire customers (CAC strategies, campaigns).",
        developing_points=1.25,
        developing_description="Vague acquisition plan (e.g., 'we will use social media') without specifics.",
        zero_points=0,
        zero_description="No customer acquisition plan."
    ),
    RubricItem(
        criteria="Marketing/Sales - Identify sales channels",
        max_points=2.5,
        description="Identify clear sales channels (e.g., direct-to-consumer, B2B, retail partnerships).",
        developing_points=1.25,
        developing_description="Mentions sales vaguely but unclear on the specific channel mechanics.",
        zero_points=0,
        zero_description="Missing identification of sales channels."
    ),
    RubricItem(
        criteria="Marketing/Sales - Sales forecasts backed by data",
        max_points=2.5,
        description="Sales volume forecasting backed by reasonable assumptions and data.",
        developing_points=1.25,
        developing_description="Sales forecasts are present but unrealistic, or lack backing data.",
        zero_points=0,
        zero_description="No sales forecasts provided."
    ),
    RubricItem(
        criteria="Marketing/Sales - Risk factors impacting sales",
        max_points=2.5,
        description="Explicitly identified and quantified risk factors that will severely impact sales goals.",
        developing_points=1.25,
        developing_description="Mentions generic risks but not specific sales-impacting risks with mitigation plans.",
        zero_points=0,
        zero_description="Completely omits any discussion of risk factors."
    ),
    # --- Financials (15 pts) ---
    RubricItem(
        criteria="Financials - Past 3 years provided",
        max_points=5.0,
        description="Financial data for the past 3 years is provided (if applicable).",
        developing_points=2.5,
        developing_description="Provides 1-2 years of data, or data is poorly formatted.",
        zero_points=0,
        zero_description="No past financial data provided (if a new venture with no history, score 0)."
    ),
    RubricItem(
        criteria="Financials - Forecast profits and expenses",
        max_points=5.0,
        description="Clear 3-5 year forecast of profits and expenses with realistic assumptions.",
        developing_points=2.5,
        developing_description="Forecasts exist but lack reasonable assumptions, P&L structure, or seem drastically inflated.",
        zero_points=0,
        zero_description="No future financial projections provided."
    ),
    RubricItem(
        criteria="Financials - Detailed breakdown",
        max_points=5.0,
        description="Detailed, granular breakdown of the financials (not just high-level summaries).",
        developing_points=2.5,
        developing_description="Some breakdown provided, but missing key line items or categorizations.",
        zero_points=0,
        zero_description="Only provides high-level top/bottom line numbers with no breakdown."
    ),
    # --- Current Management Team (5 pts) ---
    RubricItem(
        criteria="Management Team - Depth of expertise",
        max_points=2.0,
        description="Depth of expertise relevant to the business venture.",
        developing_points=1.0,
        developing_description="Resumes provided but missing key technical or domain expertise for the specific venture.",
        zero_points=0,
        zero_description="No team information provided."
    ),
    RubricItem(
        criteria="Management Team - Leadership is agile",
        max_points=3.0,
        description="Demonstrate leadership is agile, coachable, or capable of pivoting.",
        developing_points=1.5,
        developing_description="Mentions team ambition but fails to show evidence of agility or past pivots.",
        zero_points=0,
        zero_description="No demonstration of leadership capability."
    ),
    # --- Use of Prize Money (10 pts) ---
    RubricItem(
        criteria="Use of Prize Money - Specific budget",
        max_points=10.0,
        description="Highly specific, line-item budget for how the prize money will be allocated.",
        developing_points=5.0,
        developing_description="Vague allocation (e.g., '50% marketing, 50% ops') rather than specific initiatives.",
        zero_points=0,
        zero_description="Does not explain what the prize money will be used for."
    ),
    # --- Conclusion (5 pts) ---
    RubricItem(
        criteria="Conclusion - Overall summary",
        max_points=2.0,
        description="A strong overall summary wrapping up the pitch.",
        developing_points=1.0,
        developing_description="Weak or abrupt summary.",
        zero_points=0,
        zero_description="No conclusion or summary slide."
    ),
    RubricItem(
        criteria="Conclusion - Highlighted key points",
        max_points=2.0,
        description="Clearly reiterated the most important key points for judges to remember.",
        developing_points=1.0,
        developing_description="Mentioned some points but failed to highlight the true core value.",
        zero_points=0,
        zero_description="Did not highlight any key takeaways."
    ),
    RubricItem(
        criteria="Conclusion - Link to Google Slide Deck",
        max_points=1.0,
        description="A valid link provided to the Google Slide Deck.",
        developing_points=0.5,
        developing_description="Link provided but inaccessible or not a Google Slide Deck.",
        zero_points=0,
        zero_description="No link to the slide deck provided whatsoever."
    ),
]'''

# Use regex to find and replace BYUMS_RUBRIC list
pattern = r"BYUMS_RUBRIC\s*=\s*\[.*?^\]"
new_content = re.sub(pattern, new_rubric_str, content, flags=re.DOTALL | re.MULTILINE)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(new_content)
    
print("Replaced BYUMS_RUBRIC successfully.")
