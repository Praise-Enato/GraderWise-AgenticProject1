"""Tests for evidence wiring into the grade parse + Judge + ensemble helpers.

Live-grader wiring for the evidence-span decision (OV#7, T2) and the ensemble
decision (A4/CQ1/X1). All the tricky logic is kept PURE here; the agent's
LLM-calling glue just calls these. Backward compatible: a grader response with
no `evidence` yields an empty evidence string, so existing behavior is unchanged.
"""
import json

import pytest

from backend.src.grading import (
    parse_grader_response,
    unsupported_evidence,
    aggregate_grade_data,
)
from backend.src.models import CriterionAssessment, RubricItem


_RUBRIC = [
    RubricItem(criteria="Market", max_points=8, description="market sizing"),
    RubricItem(criteria="Financials", max_points=6, description="financial credibility"),
]


def _grader_json(market_ev="", fin_ev=""):
    return json.dumps({
        "assessments": [
            {"criteria_index": 1, "criteria_name": "Market", "awarded_points": 6, "reason": "r", "evidence": market_ev},
            {"criteria_index": 2, "criteria_name": "Financials", "awarded_points": 3, "reason": "r", "evidence": fin_ev},
        ],
        "general_feedback": "ok",
    })


def test_parse_captures_evidence_when_present():
    gd = parse_grader_response(_grader_json(market_ev="2.3 million farmers"), _RUBRIC)
    assert gd.assessments[0].evidence == "2.3 million farmers"


def test_parse_defaults_evidence_to_empty_when_absent():
    raw = json.dumps({
        "assessments": [{"criteria_index": 1, "criteria_name": "Market", "awarded_points": 6, "reason": "r"}],
        "general_feedback": "",
    })
    gd = parse_grader_response(raw, _RUBRIC)
    assert gd.assessments[0].evidence == ""


# --- unsupported_evidence (Judge guard) ------------------------------------- #

def test_unsupported_evidence_flags_only_hallucinated_nonempty_quotes():
    sub = "We target 2.3 million smallholder farmers in Kenya."
    ass = [
        CriterionAssessment(criteria_index=1, criteria_name="Market", awarded_points=6,
                            max_points=8, reason="r", evidence="2.3 million smallholder farmers"),
        CriterionAssessment(criteria_index=2, criteria_name="Financials", awarded_points=3,
                            max_points=6, reason="r", evidence="we hold three patents"),
        CriterionAssessment(criteria_index=3, criteria_name="Team", awarded_points=4,
                            max_points=5, reason="r", evidence=""),  # no quote -> skipped
    ]
    assert unsupported_evidence(ass, sub) == ["Financials"]


def test_unsupported_evidence_empty_when_all_supported_or_absent():
    sub = "Revenue was 42,000 dollars in year one."
    ass = [
        CriterionAssessment(criteria_index=1, criteria_name="Financials", awarded_points=3,
                            max_points=6, reason="r", evidence="42,000 dollars in year one"),
    ]
    assert unsupported_evidence(ass, sub) == []


# --- aggregate_grade_data (ensemble) ---------------------------------------- #

def _run(market, fin):
    return parse_grader_response(json.dumps({
        "assessments": [
            {"criteria_index": 1, "criteria_name": "Market", "awarded_points": market, "reason": "m"},
            {"criteria_index": 2, "criteria_name": "Financials", "awarded_points": fin, "reason": "f"},
        ],
        "general_feedback": "",
    }), _RUBRIC)


def test_aggregate_grade_data_takes_per_criterion_median():
    agg = aggregate_grade_data([_run(4, 2), _run(6, 3), _run(5, 1)])
    assert agg.score == pytest.approx(7.0)  # median Market 5 + median Financials 2
    market = next(a for a in agg.assessments if a.criteria_name == "Market")
    assert market.awarded_points == pytest.approx(5.0)
    assert market.max_points == pytest.approx(8.0)


def test_aggregate_grade_data_notes_high_disagreement():
    # Financials awards 1 and 7 -> spread 6 -> flagged as grader disagreement.
    agg = aggregate_grade_data([_run(5, 1), _run(5, 7)], flag_threshold=2.0)
    assert any("Financials" in c and "disagree" in c.lower() for c in agg.critique_points)


def test_aggregate_grade_data_all_failed_is_not_graded_ok():
    bad = parse_grader_response("not json", _RUBRIC)  # graded_ok=False
    agg = aggregate_grade_data([bad, bad])
    assert agg.graded_ok is False


def test_aggregate_single_run_matches_that_run():
    agg = aggregate_grade_data([_run(6, 4)])
    assert agg.score == pytest.approx(10.0)
