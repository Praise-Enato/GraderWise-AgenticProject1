"""Tests for the SSE stage-event contract (Phase 3 flagship).

LangGraph streams node updates as {node_name: state_delta}. This mapper turns
each into the JSON stage event the GradingTheater consumes
(screening -> reading -> judging -> coaching -> done), so the frontend animation
is driven by REAL pipeline progress instead of a timer. Pure + tested; the SSE
endpoint just forwards what this returns.
"""
from backend.src.stream_events import stage_event


def test_prepare_maps_to_screening_with_eligibility():
    delta = {"eligibility": {"status": "needs_review", "reasons": ["missing license"],
                             "ai_content_flag": True}}
    ev = stage_event("prepare", delta)
    assert ev["stage"] == "screening"
    assert ev["eligibility_status"] == "needs_review"
    assert ev["dq_reasons"] == ["missing license"]
    assert ev["ai_content_flag"] is True


def test_grade_submission_maps_to_reading_with_progress():
    class _GD:  # duck-typed GradeData
        score = 12.0
        assessments = [object(), object(), object()]
    ev = stage_event("grade_submission", {"grade_data": _GD()})
    assert ev["stage"] == "reading"
    assert ev["criteria_scored"] == 3
    assert ev["score"] == 12.0


def test_validate_grade_valid_maps_to_judging():
    ev = stage_event("validate_grade", {"is_valid": True, "grader_feedback": "", "revision_number": 0})
    assert ev["stage"] == "judging"
    assert ev["is_valid"] is True
    assert ev["revision_number"] == 0


def test_validate_grade_invalid_carries_reason_for_retry_scene():
    ev = stage_event("validate_grade", {"is_valid": False,
                                        "grader_feedback": "incomplete grade", "revision_number": 1})
    assert ev["stage"] == "judging"
    assert ev["is_valid"] is False
    assert ev["reason"] == "incomplete grade"


def test_generate_feedback_maps_to_coaching():
    ev = stage_event("generate_feedback", {"final_feedback": "well done"})
    assert ev["stage"] == "coaching"


def test_unknown_node_returns_none():
    assert stage_event("some_internal_node", {}) is None
