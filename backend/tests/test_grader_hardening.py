"""Tests for grader-hardening helpers: rubric-completeness check + deterministic
strengths/gaps extraction."""
import json

from backend.src.grading import find_missing_criteria, summarize_performance, parse_grader_response
from backend.src.models import CriterionAssessment, RubricItem


def _rubric():
    return [
        RubricItem(criteria="A - one", max_points=10, description="d"),
        RubricItem(criteria="B - two", max_points=10, description="d"),
        RubricItem(criteria="C - three", max_points=10, description="d"),
    ]


def _a(idx, name, pts, mx=10):
    return CriterionAssessment(criteria_index=idx, criteria_name=name,
                               awarded_points=pts, max_points=mx, reason="r")


def test_missing_none_when_all_covered_by_index():
    r = _rubric()
    a = [_a(1, "A - one", 5), _a(2, "B - two", 5), _a(3, "C - three", 5)]
    assert find_missing_criteria(a, r) == []


def test_missing_none_when_covered_by_name_despite_bad_index():
    r = _rubric()
    # indices are wrong/zero, but names match (case-insensitive)
    a = [_a(0, "a - one", 5), _a(0, "B - TWO", 5), _a(0, "c - three", 5)]
    assert find_missing_criteria(a, r) == []


def test_missing_reports_dropped_criterion():
    r = _rubric()
    a = [_a(1, "A - one", 5), _a(2, "B - two", 5)]  # C dropped
    assert find_missing_criteria(a, r) == ["C - three"]


def test_duplicate_does_not_mask_a_missing_one():
    r = _rubric()
    a = [_a(1, "A - one", 5), _a(1, "A - one", 5)]  # B and C missing, A dup
    assert find_missing_criteria(a, r) == ["B - two", "C - three"]


def test_missing_all_when_no_assessments():
    r = _rubric()
    assert find_missing_criteria([], r) == ["A - one", "B - two", "C - three"]


def test_index_coverage_requires_name_agreement():
    # A mislabeled entry sitting on a valid index slot must NOT count as coverage.
    r = _rubric()
    a = [_a(1, "A - one", 5), _a(2, "B - two", 5), _a(3, "totally different name", 0)]
    assert find_missing_criteria(a, r) == ["C - three"]


def test_phantom_padding_through_parse_is_caught():
    # Regression for the review finding: parse defaults a missing index to the list
    # position, so an appended phantom ("Overall", no index) gets index 3 and would
    # silently "cover" the dropped criterion C unless coverage requires name agreement.
    r = _rubric()  # [A - one, B - two, C - three]
    raw = json.dumps({
        "assessments": [
            {"criteria_index": 1, "criteria_name": "A - one", "awarded_points": 5},
            {"criteria_index": 2, "criteria_name": "B - two", "awarded_points": 5},
            {"criteria_name": "Overall", "awarded_points": 0},  # no index -> defaults to 3
        ],
        "general_feedback": "x",
    })
    gd = parse_grader_response(raw, r)
    assert gd.graded_ok  # phantom (0 pts) parses fine
    assert find_missing_criteria(gd.assessments, r) == ["C - three"]  # C correctly flagged


def test_summarize_splits_by_fraction():
    a = [
        _a(1, "strong", 9),    # 90% -> strength
        _a(2, "exactly80", 8), # 80% -> strength (>=)
        _a(3, "middle", 7),    # 70% -> neither
        _a(4, "weak", 5),      # 50% -> gap
        _a(5, "zero", 0),      # 0%  -> gap
    ]
    strengths, gaps = summarize_performance(a)
    assert strengths == ["strong", "exactly80"]
    assert gaps == ["weak", "zero"]


def test_summarize_skips_zero_max():
    a = [_a(1, "nomax", 0, mx=0), _a(2, "good", 10)]
    strengths, gaps = summarize_performance(a)
    assert strengths == ["good"]
    assert gaps == []  # nomax skipped, not counted as a gap
