"""
Few-Shot Grading Examples — Pre-structured examples from human-graded
business plans, used to calibrate the AI grader's scoring behavior.

Provides 3 representative examples (low / mid / high) and a calibration
guide derived from patterns observed across all 6 human-graded plans.
"""

import json


def _format_example_assessments(criteria_scores: list) -> str:
    """Format a list of criteria scores as a JSON assessments snippet."""
    assessments = []
    for c in criteria_scores:
        assessments.append({
            "criteria_name": c["criteria"],
            "awarded_points": c["awarded"],
            "max_points": c["max"],
        })
    return json.dumps(assessments, indent=2)


# ============================================================
# EXAMPLE 1: LOW SCORE — Jideofor Enterprise (49/100, Logistics)
# ============================================================
EXAMPLE_LOW = {
    "business_name": "Jideofor Enterprise",
    "sector": "Logistics",
    "grand_total": 36.0,
    "max_total": 80.0,
    "category_summary": {
        "Problem/Pain Point": "2.5/10 — Problem barely defined, almost no external data, zero competitor examples",
        "Business Venture": "8/15 — Partial on solution differentiation and monetization, weak cost structure",
        "Market Size": "5.5/10 — Some market analysis but weak competitor identification",
        "Marketing/Sales": "5/10 — Basic channels identified but no risk factors mentioned at all (0/2.5)",
        "Financials": "4/15 — Very weak across the board: minimal past data, poor forecasts, sparse detail",
        "Management Team": "3/5 — Good expertise depth but weak agility demonstration",
        "Use of Prize Money": "8/10 — Good specific budget allocation",
        "Conclusion": "0/5 — No summary, no key points, no slide deck link",
    },
    "assessments": [
        {"criteria": "Problem/Pain Point - Clearly defined the problem", "awarded": 1.5, "max": 2.5},
        {"criteria": "Problem/Pain Point - Outside data confirms scalability", "awarded": 1.0, "max": 5.0},
        {"criteria": "Problem/Pain Point - Examples of other solutions", "awarded": 0.0, "max": 2.5},
        {"criteria": "Business Venture - Solution is better than alternatives", "awarded": 3.0, "max": 5.0},
        {"criteria": "Business Venture - Revenue generation (monetization)", "awarded": 2.0, "max": 5.0},
        {"criteria": "Business Venture - Cost structure", "awarded": 1.0, "max": 2.0},
        {"criteria": "Business Venture - Value proposition", "awarded": 2.0, "max": 3.0},
        {"criteria": "Market Size - Target market and growth trends", "awarded": 2.0, "max": 2.5},
        {"criteria": "Market Size - Clearly identify the buyer", "awarded": 1.5, "max": 2.5},
        {"criteria": "Market Size - Identify competitors", "awarded": 1.0, "max": 2.5},
        {"criteria": "Market Size - Strengths and weaknesses of competitors", "awarded": 1.0, "max": 2.5},
        {"criteria": "Marketing/Sales - Plan to acquire customers", "awarded": 1.5, "max": 2.5},
        {"criteria": "Marketing/Sales - Identify sales channels", "awarded": 1.5, "max": 2.5},
        {"criteria": "Marketing/Sales - Sales forecasts backed by data", "awarded": 2.0, "max": 2.5},
        {"criteria": "Marketing/Sales - Risk factors impacting sales", "awarded": 0.0, "max": 2.5},
        {"criteria": "Financials - Past 3 years provided", "awarded": 1.0, "max": 5.0},
        {"criteria": "Financials - Forecast profits and expenses", "awarded": 1.0, "max": 5.0},
        {"criteria": "Financials - Detailed breakdown", "awarded": 2.0, "max": 5.0},
        {"criteria": "Management Team - Depth of expertise", "awarded": 2.0, "max": 2.0},
        {"criteria": "Management Team - Leadership is agile", "awarded": 1.0, "max": 3.0},
        {"criteria": "Use of Prize Money - Specific budget", "awarded": 8.0, "max": 10.0},
        {"criteria": "Conclusion - Overall summary", "awarded": 0.0, "max": 2.0},
        {"criteria": "Conclusion - Highlighted key points", "awarded": 0.0, "max": 2.0},
        {"criteria": "Conclusion - Link to Google Slide Deck", "awarded": 0.0, "max": 1.0},
    ],
}

# ============================================================
# EXAMPLE 2: MID SCORE — Mwana Mboka Logistics (61/100, Agriculture)
# ============================================================
EXAMPLE_MID = {
    "business_name": "Mwana Mboka Logistics Sarlu",
    "sector": "Agriculture",
    "grand_total": 48.0,
    "max_total": 80.0,
    "category_summary": {
        "Problem/Pain Point": "5/10 — Problem defined but not strongly, some external data, minimal competitor examples",
        "Business Venture": "9/15 — Mid-range across all criteria, decent monetization explanation",
        "Market Size": "6/10 — Reasonable market analysis, basic competitor identification",
        "Marketing/Sales": "4/10 — Basic plans but weak forecasting and zero risk identification",
        "Financials": "10/15 — Strong past data (5/5), but weaker on forecasts and detail",
        "Management Team": "4/5 — Good expertise and agility demonstration",
        "Use of Prize Money": "8/10 — Good specific budget",
        "Conclusion": "2/5 — Some summary and key points but no slide deck link",
    },
    "assessments": [
        {"criteria": "Problem/Pain Point - Clearly defined the problem", "awarded": 2.0, "max": 2.5},
        {"criteria": "Problem/Pain Point - Outside data confirms scalability", "awarded": 2.0, "max": 5.0},
        {"criteria": "Problem/Pain Point - Examples of other solutions", "awarded": 1.0, "max": 2.5},
        {"criteria": "Business Venture - Solution is better than alternatives", "awarded": 3.0, "max": 5.0},
        {"criteria": "Business Venture - Revenue generation (monetization)", "awarded": 3.0, "max": 5.0},
        {"criteria": "Business Venture - Cost structure", "awarded": 1.0, "max": 2.0},
        {"criteria": "Business Venture - Value proposition", "awarded": 2.0, "max": 3.0},
        {"criteria": "Market Size - Target market and growth trends", "awarded": 2.0, "max": 2.5},
        {"criteria": "Market Size - Clearly identify the buyer", "awarded": 2.0, "max": 2.5},
        {"criteria": "Market Size - Identify competitors", "awarded": 1.0, "max": 2.5},
        {"criteria": "Market Size - Strengths and weaknesses of competitors", "awarded": 1.0, "max": 2.5},
        {"criteria": "Marketing/Sales - Plan to acquire customers", "awarded": 1.0, "max": 2.5},
        {"criteria": "Marketing/Sales - Identify sales channels", "awarded": 2.0, "max": 2.5},
        {"criteria": "Marketing/Sales - Sales forecasts backed by data", "awarded": 1.0, "max": 2.5},
        {"criteria": "Marketing/Sales - Risk factors impacting sales", "awarded": 0.0, "max": 2.5},
        {"criteria": "Financials - Past 3 years provided", "awarded": 5.0, "max": 5.0},
        {"criteria": "Financials - Forecast profits and expenses", "awarded": 2.0, "max": 5.0},
        {"criteria": "Financials - Detailed breakdown", "awarded": 3.0, "max": 5.0},
        {"criteria": "Management Team - Depth of expertise", "awarded": 2.0, "max": 2.0},
        {"criteria": "Management Team - Leadership is agile", "awarded": 2.0, "max": 3.0},
        {"criteria": "Use of Prize Money - Specific budget", "awarded": 8.0, "max": 10.0},
        {"criteria": "Conclusion - Overall summary", "awarded": 1.0, "max": 2.0},
        {"criteria": "Conclusion - Highlighted key points", "awarded": 1.0, "max": 2.0},
        {"criteria": "Conclusion - Link to Google Slide Deck", "awarded": 0.0, "max": 1.0},
    ],
}

# ============================================================
# EXAMPLE 3: HIGH SCORE — Kalemie Mobile Health Outreach (75.5/100, Healthcare)
# ============================================================
EXAMPLE_HIGH = {
    "business_name": "Kalemie Mobile Health Outreach",
    "sector": "Healthcare",
    "grand_total": 62,
    "max_total": 80.0,
    "category_summary": {
        "Problem/Pain Point": "7.5/10 — Strong problem definition, excellent external data (4/5), some competitor examples",
        "Business Venture": "15/15 — PERFECT score: strong differentiation, clear monetization, full cost structure, compelling value prop",
        "Market Size": "6/10 — Reasonable but not exceptional across all criteria",
        "Marketing/Sales": "6/10 — Good customer acquisition plan, but weak forecasting and zero risk identification",
        "Financials": "10/15 — No past data (0/5), but excellent forecasts (5/5) and detailed breakdown (5/5)",
        "Management Team": "5/5 — PERFECT: strong expertise and agile leadership",
        "Use of Prize Money": "9/10 — Very specific budget allocation",
        "Conclusion": "2/5 — Basic summary and key points, no slide deck link",
    },
    "assessments": [
        {"criteria": "Problem/Pain Point - Clearly defined the problem", "awarded": 2.5, "max": 2.5},
        {"criteria": "Problem/Pain Point - Outside data confirms scalability", "awarded": 4.0, "max": 5.0},
        {"criteria": "Problem/Pain Point - Examples of other solutions", "awarded": 1.0, "max": 2.5},
        {"criteria": "Business Venture - Solution is better than alternatives", "awarded": 5.0, "max": 5.0},
        {"criteria": "Business Venture - Revenue generation (monetization)", "awarded": 5.0, "max": 5.0},
        {"criteria": "Business Venture - Cost structure", "awarded": 2.0, "max": 2.0},
        {"criteria": "Business Venture - Value proposition", "awarded": 3.0, "max": 3.0},
        {"criteria": "Market Size - Target market and growth trends", "awarded": 2.0, "max": 2.5},
        {"criteria": "Market Size - Clearly identify the buyer", "awarded": 2.0, "max": 2.5},
        {"criteria": "Market Size - Identify competitors", "awarded": 1.0, "max": 2.5},
        {"criteria": "Market Size - Strengths and weaknesses of competitors", "awarded": 1.0, "max": 2.5},
        {"criteria": "Marketing/Sales - Plan to acquire customers", "awarded": 2.0, "max": 2.5},
        {"criteria": "Marketing/Sales - Identify sales channels", "awarded": 2.0, "max": 2.5},
        {"criteria": "Marketing/Sales - Sales forecasts backed by data", "awarded": 2.0, "max": 2.5},
        {"criteria": "Marketing/Sales - Risk factors impacting sales", "awarded": 0.0, "max": 2.5},
        {"criteria": "Financials - Past 3 years provided", "awarded": 0.0, "max": 5.0},
        {"criteria": "Financials - Forecast profits and expenses", "awarded": 5.0, "max": 5.0},
        {"criteria": "Financials - Detailed breakdown", "awarded": 5.0, "max": 5.0},
        {"criteria": "Management Team - Depth of expertise", "awarded": 2.0, "max": 2.0},
        {"criteria": "Management Team - Leadership is agile", "awarded": 3.0, "max": 3.0},
        {"criteria": "Use of Prize Money - Specific budget", "awarded": 9.0, "max": 10.0},
        {"criteria": "Conclusion - Overall summary", "awarded": 1.0, "max": 2.0},
        {"criteria": "Conclusion - Highlighted key points", "awarded": 1.0, "max": 2.0},
        {"criteria": "Conclusion - Link to Google Slide Deck", "awarded": 0.0, "max": 1.0},
    ],
}

# ============================================================
# CALIBRATION GUIDE — Patterns extracted from all 6 human-graded plans
# ============================================================
CALIBRATION_GUIDE = """
**CALIBRATION GUIDE — Derived from human grading of 6 BYUMS competition plans using the 80-point rubric:**

1. **Risk Factors (0/2.5 across ALL 6 plans):** Human judges gave 0 to every single plan for "Identified risk factors that will impact sales goals." This means the bar is extremely high — only award points if the plan explicitly names specific, quantified risks to their sales trajectory. Vague statements like "market conditions may change" get 0.

2. **Competitor Examples & Analysis:** Human judges are very strict on "Examples of what others are doing to solve the problem" and "Strengths and weakness of competitors." Even top-tier plans scored 1/2.5. Require detailed, specific competitive advantages to award > 1.0.

3. **Financials can be polarized:** Some plans score 0/5 for "Past 3 years" (new ventures without history). If a business is pre-revenue and provides no past data, SCORE THEM 0 for past data. Do not award pity points (like 1 or 2.5). However, strong forecasts can still score 5/5.

4. **Conclusion section is commonly weak:** Most plans fail to include an adequate conclusion. The "Link to Google Slide Deck" criterion was 0/1 for ALL plans if missing. Do not award 0.5 if the link is factually missing.

5. **Use of Prize Money is generally strong (avg ~8.0/10):** Most applicants do well here. Only deduct significantly if the budget is truly vague.

6. **Score distribution guidance:** Across 6 plans, scores ranged from 36 to 62 out of 80. The average was ~48. A "good" plan scores ~55+, an "average" plan is 45-55, and "below average" is under 45.
   - **IMPORTANT: Do NOT default to median scores (e.g., 2.5/5) just to be safe.**
   - If a criterion is fundamentally missing or severely lacking, award 0.
   - If a criterion is exceptionally well-documented with data and charts, award the absolute maximum (e.g., 5/5). Perfect scores ARE possible (e.g., Kalemie got 15/15 on Business Venture).
"""


def get_few_shot_prompt_section() -> str:
    """
    Generate the few-shot examples section to inject into the business
    grading system prompt.

    Returns a formatted string with 3 examples and calibration guidance.
    """
    sections = []

    sections.append("**GRADING CALIBRATION EXAMPLES:**")
    sections.append("Below are real examples from human judges grading business plans using this same rubric.")
    sections.append("Study these carefully and calibrate your scoring to match their standards.\n")

    # Format each example
    for label, example in [
        ("LOW SCORE", EXAMPLE_LOW),
        ("MID SCORE", EXAMPLE_MID),
        ("HIGH SCORE", EXAMPLE_HIGH),
    ]:
        sections.append(f"--- **{label} EXAMPLE: {example['business_name']}** ({example['sector']}) — {example['grand_total']}/{example['max_total']} ---")

        # Category summaries
        sections.append("Category Breakdown:")
        for cat, summary in example["category_summary"].items():
            sections.append(f"  • {cat}: {summary}")

        # Key scores as compact JSON
        sections.append("Scores:")
        for a in example["assessments"]:
            sections.append(f"  {a['criteria']}: {a['awarded']}/{a['max']}")

        sections.append("")

    # Add calibration guide
    sections.append(CALIBRATION_GUIDE)

    return "\n".join(sections)


if __name__ == "__main__":
    prompt_section = get_few_shot_prompt_section()
    print(prompt_section)
    print(f"\n--- Total characters: {len(prompt_section)} ---")
