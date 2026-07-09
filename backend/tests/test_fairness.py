"""Tests for fairness / disparate-impact scaffolding.

The eng review's outside voice (OV#13) flagged that an LLM grader for an African
competition with variable English fluency carries language/fluency bias, and
that AI-content detectors fire disproportionately on non-native and
template-using founders. This module computes the disparity metrics a human
reviewer needs. It measures; it never auto-decides. Pure Python, TDD.

Wiring to real per-plan group attributes (language, region) is a later step —
the metrics are unit-tested now against explicit records.
"""
import pytest

from backend.src import fairness
from backend.src.fairness import GroupRecord as G


def test_flag_rate_by_group():
    records = [
        G(group="en", flagged=False),
        G(group="en", flagged=False),
        G(group="en", flagged=True),   # 1/3
        G(group="fr", flagged=True),
        G(group="fr", flagged=True),    # 2/2
    ]
    rates = fairness.flag_rate_by_group(records)
    assert rates["en"] == pytest.approx(1 / 3)
    assert rates["fr"] == pytest.approx(1.0)


def test_disparate_impact_ratio_is_min_over_max():
    rates = {"a": 0.4, "b": 0.5}
    assert fairness.disparate_impact_ratio(rates) == pytest.approx(0.8)


def test_disparate_impact_ratio_flags_strong_disparity():
    rates = {"a": 0.1, "b": 0.5, "c": 0.4}
    # 0.1 / 0.5 = 0.2 -> well below the four-fifths (0.8) rule of thumb
    assert fairness.disparate_impact_ratio(rates) == pytest.approx(0.2)


def test_disparate_impact_ratio_none_when_under_two_groups_or_all_zero():
    assert fairness.disparate_impact_ratio({"a": 0.5}) is None
    assert fairness.disparate_impact_ratio({"a": 0.0, "b": 0.0}) is None


def test_ai_flag_false_positive_rate_by_group():
    # Among AI-flagged AND human-adjudicated plans, the fraction the human
    # CLEARED (ai_flag_confirmed is False) is the false-positive rate.
    records = [
        G(group="non_native", ai_flag=True, ai_flag_confirmed=False),  # FP
        G(group="non_native", ai_flag=True, ai_flag_confirmed=False),  # FP
        G(group="non_native", ai_flag=True, ai_flag_confirmed=True),   # true positive
        G(group="native", ai_flag=True, ai_flag_confirmed=True),       # true positive
        G(group="native", ai_flag=False),                              # not flagged, ignored
        G(group="non_native", ai_flag=True, ai_flag_confirmed=None),   # unadjudicated, ignored
    ]
    fpr = fairness.ai_flag_false_positive_rate_by_group(records)
    assert fpr["non_native"] == pytest.approx(2 / 3)  # 2 FP of 3 adjudicated
    assert fpr["native"] == pytest.approx(0.0)


def test_mean_score_by_group_ignores_missing_scores():
    records = [
        G(group="a", score=80.0),
        G(group="a", score=60.0),
        G(group="b", score=None),   # no score -> excluded
        G(group="b", score=50.0),
    ]
    means = fairness.mean_score_by_group(records)
    assert means["a"] == pytest.approx(70.0)
    assert means["b"] == pytest.approx(50.0)
