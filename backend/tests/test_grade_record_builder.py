"""Tests for grade_record.record_for — assembling a GradeOfRecord from a graded
result so it can be pinned on the response and persisted (X4/OV#8)."""
import pytest

from backend.src import grade_record as GR


_RUBRIC = [{"criteria": "Market", "max_points": 8, "description": "x"},
           {"criteria": "Financials", "max_points": 6, "description": "y"}]
_SUB = "We serve 2.3 million smallholder farmers."


class _A:  # duck-typed CriterionAssessment
    def __init__(self, name, pts):
        self.criteria_name = name
        self.awarded_points = pts


def test_record_for_pins_inputs_and_per_criterion():
    rec = GR.record_for(
        _RUBRIC, _SUB, model="deepseek-chat", temperatures=[0.4, 0.4, 0.4],
        assessments=[_A("Market", 6), _A("Financials", 3)], total=9.0, ai_flag=True,
    )
    assert rec.model == "deepseek-chat"
    assert rec.input_hash == GR.content_hash(_RUBRIC, _SUB)  # stable, re-derivable
    assert rec.per_criterion == {"Market": 6.0, "Financials": 3.0}
    assert rec.total == pytest.approx(9.0)
    assert rec.ai_flag is True


def test_record_for_accepts_dict_assessments_and_round_trips():
    rec = GR.record_for(
        _RUBRIC, _SUB, model="m", temperatures=[0.0],
        assessments=[{"criteria_name": "Market", "awarded_points": 8}], total=8.0,
    )
    assert rec.per_criterion == {"Market": 8.0}
    assert GR.GradeOfRecord.from_dict(rec.to_dict()) == rec
