"""Tests for the defensible ensemble aggregate.

Decisions from the eng review this implements:
  A4  — grade every plan N times.
  CQ1 — combine runs as the MEDIAN per criterion, flag high spread for review.
  X1  — spread is grader DISAGREEMENT, not calibrated confidence.
  OV#2 — a tie band at the shortlist cutoff so sub-noise gaps don't decide prizes.

Pure Python, TDD.
"""
import pytest

from backend.src import aggregate


def test_median_per_criterion_and_total():
    runs = [
        {"Market": 4.0, "Financials": 2.0},
        {"Market": 6.0, "Financials": 3.0},
        {"Market": 5.0, "Financials": 1.0},
    ]
    res = aggregate.aggregate_ensemble(runs)
    assert res.per_criterion["Market"].median == pytest.approx(5.0)
    assert res.per_criterion["Financials"].median == pytest.approx(2.0)
    assert res.total == pytest.approx(7.0)  # 5 + 2, sum of medians


def test_even_number_of_runs_uses_the_two_middle_values():
    runs = [{"C": 4.0}, {"C": 6.0}]  # median of [4, 6] = 5
    assert aggregate.aggregate_ensemble(runs).per_criterion["C"].median == pytest.approx(5.0)


def test_high_spread_criterion_is_flagged_low_spread_is_not():
    runs = [
        {"stable": 5.0, "contested": 1.0},
        {"stable": 5.0, "contested": 7.0},
        {"stable": 6.0, "contested": 4.0},
    ]
    res = aggregate.aggregate_ensemble(runs, flag_threshold=2.0)
    assert res.per_criterion["stable"].flagged is False    # spread 1
    assert res.per_criterion["contested"].flagged is True  # spread 6
    assert res.per_criterion["contested"].spread == pytest.approx(6.0)
    assert res.flagged_criteria == ["contested"]


def test_criterion_missing_from_some_runs_counts_only_present_values():
    runs = [{"C": 4.0}, {}, {"C": 6.0}]  # median of [4, 6]; n = 2
    agg = aggregate.aggregate_ensemble(runs).per_criterion["C"]
    assert agg.median == pytest.approx(5.0)
    assert agg.n == 2


# --- tie band (OV#2) -------------------------------------------------------- #

def test_within_tie_band_true_when_gap_below_band():
    assert aggregate.within_tie_band(85.0, 85.4, band=0.5) is True


def test_within_tie_band_false_when_gap_exceeds_band():
    assert aggregate.within_tie_band(85.0, 86.0, band=0.5) is False


def test_cutoff_tie_zone_flags_plans_clustered_around_the_cutoff():
    # Shortlist top 3. The 2nd/3rd/4th plans sit within 0.5 pt of the cutoff.
    scored = [("a", 90.0), ("b", 82.0), ("c", 81.8), ("d", 81.5), ("e", 70.0)]
    zone = aggregate.cutoff_tie_zone(scored, k=3, band=0.5)
    assert set(zone) == {"b", "c", "d"}  # the contested admit/reject boundary


def test_cutoff_tie_zone_is_just_the_boundary_plan_when_well_separated():
    scored = [("a", 90.0), ("b", 80.0), ("c", 70.0), ("d", 60.0)]
    zone = aggregate.cutoff_tie_zone(scored, k=2, band=0.5)
    assert zone == ["b"]  # nobody else within band of the cutoff -> no contested tie
