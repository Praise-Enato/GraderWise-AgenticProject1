"""Tests for grade parsing and assembly.

The central guarantee (eng review Issue #4): a bad grader response becomes
graded_ok=False, never a silent 0 that would bury a good plan in the ranking.
"""
import json

from backend.src.grading import (
    GradeData,
    parse_grader_response,
    strip_code_fences,
    to_grade_result,
)
from backend.src.models import RubricItem, ELIGIBILITY_ELIGIBLE, ELIGIBILITY_NEEDS_REVIEW


def rubric():
    return [
        RubricItem(criteria="Financials", max_points=10, description="3 yrs records"),
        RubricItem(criteria="Market", max_points=20, description="local market"),
    ]


def _good_json():
    return json.dumps({
        "assessments": [
            {"criteria_index": 1, "criteria_name": "Financials", "awarded_points": 8, "reason": "2/3 yrs"},
            {"criteria_index": 2, "criteria_name": "Market", "awarded_points": 15, "reason": "solid"},
        ],
        "general_feedback": "good",
    })


# ------------------------------ happy path ---------------------------------- #

def test_parse_valid_response():
    gd = parse_grader_response(_good_json(), rubric())
    assert gd.graded_ok is True
    assert gd.error is None
    assert gd.score == 23.0
    assert len(gd.assessments) == 2
    # max_points resolved from the rubric, not the model
    assert gd.assessments[0].max_points == 10.0
    assert gd.assessments[1].max_points == 20.0


def test_parse_strips_markdown_fences():
    fenced = "```json\n" + _good_json() + "\n```"
    gd = parse_grader_response(fenced, rubric())
    assert gd.graded_ok is True
    assert gd.score == 23.0


def test_strip_code_fences_plain_backticks():
    assert strip_code_fences("```\n{\"a\":1}\n```") == '{"a":1}'


# --------------------------- parse-failure guard ---------------------------- #

def test_malformed_json_is_flagged_not_zero():
    gd = parse_grader_response("this is not json at all", rubric())
    assert gd.graded_ok is False
    assert gd.score == 0.0
    assert "Unparseable" in gd.error
    assert gd.assessments == []


def test_empty_response_flagged():
    gd = parse_grader_response("", rubric())
    assert gd.graded_ok is False
    assert "Empty" in gd.error


def test_json_without_assessments_flagged():
    gd = parse_grader_response(json.dumps({"general_feedback": "nice"}), rubric())
    assert gd.graded_ok is False
    assert "no per-criterion assessments" in gd.error


def test_empty_assessment_list_flagged():
    gd = parse_grader_response(json.dumps({"assessments": []}), rubric())
    assert gd.graded_ok is False


def test_non_numeric_points_flagged():
    bad = json.dumps({"assessments": [
        {"criteria_index": 1, "criteria_name": "Financials", "awarded_points": "eight"},
    ]})
    gd = parse_grader_response(bad, rubric())
    assert gd.graded_ok is False
    assert "Non-numeric" in gd.error


def test_json_array_not_object_flagged():
    gd = parse_grader_response(json.dumps([1, 2, 3]), rubric())
    assert gd.graded_ok is False


# ------------------------------ clamping ------------------------------------ #

def test_over_max_award_is_clamped_and_noted():
    over = json.dumps({"assessments": [
        {"criteria_index": 1, "criteria_name": "Financials", "awarded_points": 50, "reason": "great"},
    ]})
    gd = parse_grader_response(over, rubric())
    assert gd.graded_ok is True
    assert gd.score == 10.0  # clamped to max, not 50
    assert "clamped" in gd.assessments[0].reason


def test_negative_award_clamped_up():
    neg = json.dumps({"assessments": [
        {"criteria_index": 1, "criteria_name": "Financials", "awarded_points": -3},
    ]})
    gd = parse_grader_response(neg, rubric())
    assert gd.score == 0.0
    assert gd.assessments[0].awarded_points == 0.0


# ----------------------- criterion resolution ------------------------------- #

def test_max_points_resolved_by_name_when_index_missing():
    j = json.dumps({"assessments": [
        {"criteria_name": "Market", "awarded_points": 10},
    ]})
    gd = parse_grader_response(j, rubric())
    assert gd.assessments[0].max_points == 20.0


def test_unknown_criterion_uses_supplied_max_or_zero():
    j = json.dumps({"assessments": [
        {"criteria_name": "Mystery", "awarded_points": 3, "max_points": 5},
    ]})
    gd = parse_grader_response(j, rubric())
    assert gd.assessments[0].max_points == 5.0
    assert gd.score == 3.0


def test_critique_points_marks_zero_and_low():
    j = json.dumps({"assessments": [
        {"criteria_index": 1, "criteria_name": "Financials", "awarded_points": 0, "reason": "missing"},
        {"criteria_index": 2, "criteria_name": "Market", "awarded_points": 3, "reason": "thin"},
    ]})
    gd = parse_grader_response(j, rubric())
    assert any(c.startswith("❌") for c in gd.critique_points)
    assert any(c.startswith("⚠️") for c in gd.critique_points)


# --------------------------- to_grade_result -------------------------------- #

def test_to_grade_result_propagates_status():
    gd = parse_grader_response(_good_json(), rubric())
    gr = to_grade_result(gd, feedback="well done", thinking_process=["x"], confidence_score=0.9)
    assert gr.score == 23.0
    assert gr.graded_ok is True
    assert gr.eligibility_status == ELIGIBILITY_ELIGIBLE
    assert len(gr.assessments) == 2
    assert gr.feedback == "well done"


def test_to_grade_result_failed_grade_forced_to_review():
    gd = parse_grader_response("garbage", rubric())
    gr = to_grade_result(gd, feedback="")
    assert gr.graded_ok is False
    # a failed grade must not present as an eligible real score
    assert gr.eligibility_status == ELIGIBILITY_NEEDS_REVIEW


def test_to_grade_result_carries_dq_info():
    gd = GradeData(score=0.0, graded_ok=True)
    gr = to_grade_result(gd, feedback="", eligibility_status="ineligible",
                         dq_reasons=["MLM"], ai_content_flag=True)
    assert gr.eligibility_status == "ineligible"
    assert gr.dq_reasons == ["MLM"]
    assert gr.ai_content_flag is True
