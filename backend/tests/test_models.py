"""Tests for the extended grading data models.

Focus: the new fields must be backward compatible (old construction still works)
and default sensibly, and CriterionAssessment must round-trip cleanly.
"""
from backend.src.models import (
    CriterionAssessment,
    GradeResult,
    RubricItem,
    ELIGIBILITY_ELIGIBLE,
    ELIGIBILITY_INELIGIBLE,
    ELIGIBILITY_NEEDS_REVIEW,
)


def test_grade_result_minimal_is_backward_compatible():
    # The old call sites only passed score + feedback (+ optional lists).
    gr = GradeResult(score=42.0, feedback="ok")
    assert gr.score == 42.0
    assert gr.feedback == "ok"
    # New fields must default to safe, non-breaking values.
    assert gr.assessments == []
    assert gr.graded_ok is True
    assert gr.error is None
    assert gr.eligibility_status == ELIGIBILITY_ELIGIBLE
    assert gr.dq_reasons == []
    assert gr.ai_content_flag is False
    assert gr.citations == []
    assert gr.thinking_process == []


def test_grade_result_carries_per_criterion_assessments():
    a = CriterionAssessment(
        criteria_index=1,
        criteria_name="Financials",
        awarded_points=7.5,
        max_points=10,
        reason="Provided 2 of 3 years of records.",
    )
    gr = GradeResult(score=7.5, feedback="see notes", assessments=[a])
    assert len(gr.assessments) == 1
    assert gr.assessments[0].criteria_name == "Financials"
    assert gr.assessments[0].awarded_points == 7.5
    # round-trips to plain dict for the API layer
    dumped = gr.model_dump()
    assert dumped["assessments"][0]["max_points"] == 10.0


def test_failed_grade_is_flagged_not_zero():
    gr = GradeResult(
        score=0.0,
        feedback="",
        graded_ok=False,
        error="Unparseable model output",
        eligibility_status=ELIGIBILITY_NEEDS_REVIEW,
    )
    assert gr.graded_ok is False
    assert gr.error == "Unparseable model output"
    # A caller can distinguish this from a genuine zero via graded_ok.
    assert gr.eligibility_status == ELIGIBILITY_NEEDS_REVIEW


def test_ineligibility_fields():
    gr = GradeResult(
        score=0.0,
        feedback="",
        eligibility_status=ELIGIBILITY_INELIGIBLE,
        dq_reasons=["Appears to be a multi-level marketing business"],
        ai_content_flag=True,
    )
    assert gr.eligibility_status == ELIGIBILITY_INELIGIBLE
    assert "multi-level" in gr.dq_reasons[0]
    assert gr.ai_content_flag is True


def test_rubric_item_still_parses():
    item = RubricItem(criteria="Market", max_points=20, description="local market analysis")
    assert item.max_points == 20
    assert item.zero_points == 0.0
