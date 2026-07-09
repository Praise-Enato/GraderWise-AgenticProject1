"""Tests for inter-rater (human ceiling) agreement.

The eng review's outside voice flagged that AI-vs-human agreement is
uninterpretable without knowing how much the human judges agree with EACH
OTHER: if judges only agree at rho~0.6, an AI at 0.6 is already at the human
ceiling. This module measures that ceiling. Pure Python, TDD.
"""
import pytest

from backend.src import interrater


def test_two_raters_in_perfect_rank_agreement_score_1():
    # Two judges rank four plans identically (values differ, ranks match).
    raters = [[10, 20, 30, 40], [1, 2, 3, 4]]
    assert interrater.mean_pairwise_spearman(raters) == pytest.approx(1.0)


def test_perfect_rank_disagreement_scores_minus_1():
    raters = [[1, 2, 3, 4], [4, 3, 2, 1]]
    assert interrater.mean_pairwise_spearman(raters) == pytest.approx(-1.0)


def test_three_raters_averages_the_three_pairwise_correlations():
    # A==B perfectly (1.0); C is the reverse of both (-1.0 vs each).
    # pairs: (A,B)=1.0, (A,C)=-1.0, (B,C)=-1.0 -> mean = -1/3.
    a = [1, 2, 3, 4]
    b = [10, 20, 30, 40]
    c = [40, 30, 20, 10]
    assert interrater.mean_pairwise_spearman([a, b, c]) == pytest.approx(-1.0 / 3.0)


def test_fewer_than_two_raters_is_none():
    assert interrater.mean_pairwise_spearman([[1, 2, 3]]) is None
    assert interrater.mean_pairwise_spearman([]) is None


def test_constant_rater_makes_pair_undefined_and_is_skipped():
    # B has zero variance -> its pairs are undefined; only (A,C) counts, = 1.0.
    a = [1, 2, 3, 4]
    b = [5, 5, 5, 5]
    c = [2, 4, 6, 8]
    assert interrater.mean_pairwise_spearman([a, b, c]) == pytest.approx(1.0)


def test_length_mismatch_raises():
    with pytest.raises(ValueError):
        interrater.mean_pairwise_spearman([[1, 2, 3], [1, 2]])


# --- compute_interrater (structured result) --------------------------------- #

def test_compute_interrater_reports_shape_and_ceiling():
    res = interrater.compute_interrater([[1, 2, 3, 4], [1, 2, 3, 4]])
    assert res.n_raters == 2
    assert res.n_items == 4
    assert res.mean_pairwise_spearman == pytest.approx(1.0)


def test_compute_interrater_zero_raters_has_zero_items():
    res = interrater.compute_interrater([])
    assert res.n_raters == 0
    assert res.n_items == 0
    assert res.mean_pairwise_spearman is None


# --- interpret_vs_ceiling --------------------------------------------------- #

def test_interpret_none_ceiling_reports_no_baseline():
    assert interrater.interpret_vs_ceiling(0.7, None) == "no_baseline"


def test_interpret_ai_within_tolerance_is_at_ceiling():
    assert interrater.interpret_vs_ceiling(0.62, 0.60, tol=0.05) == "at_ceiling"


def test_interpret_ai_well_below_ceiling():
    assert interrater.interpret_vs_ceiling(0.40, 0.75, tol=0.05) == "below_ceiling"


def test_interpret_ai_well_above_ceiling_is_flagged():
    # Beating the humans' own agreement is a red flag for overfitting, not a win.
    assert interrater.interpret_vs_ceiling(0.95, 0.60, tol=0.05) == "above_ceiling_watch"
