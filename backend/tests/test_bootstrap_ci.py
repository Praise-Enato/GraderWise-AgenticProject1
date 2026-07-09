"""Tests for the bootstrap confidence interval.

The eng review's outside voice (OV#3) flagged that a single correlation number
on a tiny ground-truth set is read as more certain than it is. A percentile
bootstrap CI makes the small-n uncertainty explicit without assuming normality
(unlike the Fisher CI already in this module). Deterministic via `seed`. TDD.
"""
import pytest

from backend.src import validation as V


def test_perfect_correlation_ci_is_a_tight_interval_at_one():
    xs = [1, 2, 3, 4, 5, 6]
    ci = V.bootstrap_ci(xs, xs, V.spearman, n_resamples=200, seed=1)
    lo, hi = ci
    assert lo == pytest.approx(1.0)
    assert hi == pytest.approx(1.0)


def test_identical_series_mae_ci_is_zero():
    xs = [3.0, 1.0, 4.0, 1.0, 5.0]
    lo, hi = V.bootstrap_ci(xs, xs, V.mae, n_resamples=200, seed=7)
    assert lo == pytest.approx(0.0)
    assert hi == pytest.approx(0.0)


def test_ci_brackets_the_point_estimate_and_stays_in_range():
    xs = [1, 2, 3, 4, 5, 6, 7, 8]
    ys = [2, 1, 4, 3, 6, 5, 8, 7]  # strong-but-imperfect rank agreement
    point = V.spearman(xs, ys)
    lo, hi = V.bootstrap_ci(xs, ys, V.spearman, n_resamples=500, seed=42)
    assert -1.0 <= lo <= point <= hi <= 1.0
    assert lo < hi  # a noisy relationship yields a non-degenerate interval


def test_is_deterministic_for_a_fixed_seed():
    xs = [1, 2, 3, 4, 5, 6, 7]
    ys = [1, 3, 2, 5, 4, 7, 6]
    a = V.bootstrap_ci(xs, ys, V.spearman, n_resamples=300, seed=99)
    b = V.bootstrap_ci(xs, ys, V.spearman, n_resamples=300, seed=99)
    assert a == b


def test_too_few_points_is_none():
    assert V.bootstrap_ci([1.0], [1.0], V.spearman, seed=1) is None
    assert V.bootstrap_ci([], [], V.mae, seed=1) is None


def test_compute_agreement_includes_bootstrap_ci_when_requested():
    xs = [1, 2, 3, 4, 5, 6]
    res = V.compute_agreement(xs, xs, bootstrap_resamples=200, bootstrap_seed=1)
    assert res.boot_ci95 is not None
    lo, hi = res.boot_ci95
    assert lo == pytest.approx(1.0)
    assert hi == pytest.approx(1.0)


def test_compute_agreement_has_no_bootstrap_by_default():
    res = V.compute_agreement([1, 2, 3], [3, 2, 1])
    assert res.boot_ci95 is None
