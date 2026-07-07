"""Tests for the reliability-metric engine.

This is the number shown to the board, so the coverage is deliberately heavy:
known-answer fixtures, edge cases (ties, constants, small n), the data-leakage
guard, and both manifest formats.
"""
import json
import math

import pytest

from backend.src import validation as V


# ----------------------------- correlation ---------------------------------- #

def test_pearson_perfect_positive():
    assert V.pearson([1, 2, 3], [2, 4, 6]) == pytest.approx(1.0)


def test_pearson_perfect_negative():
    assert V.pearson([1, 2, 3], [6, 4, 2]) == pytest.approx(-1.0)


def test_pearson_known_value():
    # classic small example
    r = V.pearson([1, 2, 3, 4, 5], [2, 4, 5, 4, 5])
    assert r == pytest.approx(0.7745966, abs=1e-6)


def test_pearson_undefined_for_constant_series():
    assert V.pearson([5, 5, 5], [1, 2, 3]) is None


def test_pearson_undefined_for_single_point():
    assert V.pearson([1], [1]) is None


def test_spearman_monotonic_nonlinear_is_one():
    # squares are monotonic in the input -> ranks match -> spearman == 1
    assert V.spearman([1, 2, 3, 4], [1, 4, 9, 16]) == pytest.approx(1.0)


def test_spearman_handles_ties():
    # both series constant-ish should not crash; genuine ties averaged
    assert V.spearman([1, 2, 2, 3], [10, 20, 20, 30]) == pytest.approx(1.0)


def test_rank_averages_ties():
    assert V.rank([10, 20, 20, 40]) == [1.0, 2.5, 2.5, 4.0]


def test_rank_all_equal():
    assert V.rank([7, 7, 7]) == [2.0, 2.0, 2.0]


# ------------------------------- error metrics ------------------------------ #

def test_mae_zero_when_identical():
    assert V.mae([1, 2, 3], [1, 2, 3]) == 0.0


def test_mae_value():
    assert V.mae([1, 2, 3], [2, 2, 2]) == pytest.approx((1 + 0 + 1) / 3)


def test_rmse_value():
    assert V.rmse([0, 0], [3, 4]) == pytest.approx(math.sqrt((9 + 16) / 2))


def test_length_mismatch_raises():
    with pytest.raises(ValueError):
        V.mae([1, 2], [1, 2, 3])


def test_empty_returns_none():
    assert V.mae([], []) is None


# --------------------------------- CI --------------------------------------- #

def test_fisher_ci_brackets_r():
    ci = V.fisher_ci(0.8, n=30)
    assert ci is not None
    lo, hi = ci
    assert lo < 0.8 < hi
    assert -1.0 <= lo <= hi <= 1.0


def test_fisher_ci_none_for_small_n():
    assert V.fisher_ci(0.8, n=3) is None


def test_fisher_ci_handles_r_one_without_crashing():
    ci = V.fisher_ci(1.0, n=20)  # atanh(1) would be inf if not clamped
    assert ci is not None
    assert ci[1] <= 1.0


def test_fisher_ci_none_when_r_none():
    assert V.fisher_ci(None, n=50) is None


def test_ci_wide_at_small_n():
    # The whole point of reporting CI at n=15: it should be visibly wide.
    ci = V.fisher_ci(0.7, n=15)
    assert ci is not None
    assert (ci[1] - ci[0]) > 0.4


# --------------------------- leave-one-out guard ---------------------------- #

def test_leave_one_out_excludes_self():
    loo = V.leave_one_out_indices(4)
    assert loo == [[1, 2, 3], [0, 2, 3], [0, 1, 3], [0, 1, 2]]
    for i, others in enumerate(loo):
        assert i not in others  # the data-leakage guard


def test_leave_one_out_n_zero():
    assert V.leave_one_out_indices(0) == []


# ------------------------------ weighted total ------------------------------ #

def test_weighted_total_80_20():
    assert V.weighted_total(plan_score=10, video_score=5) == pytest.approx(10 * 0.8 + 5 * 0.2)


def test_weighted_total_rejects_bad_weight():
    with pytest.raises(ValueError):
        V.weighted_total(1, 1, plan_weight=1.5)


# ---------------------------- compute_agreement ----------------------------- #

def test_compute_agreement_end_to_end():
    ai = [8, 6, 9, 4, 7]
    human = [7, 6, 9, 5, 7]
    res = V.compute_agreement(ai, human)
    assert res.n == 5
    assert res.spearman is not None
    assert res.mae is not None
    assert "n=5" in res.summary()


def test_compute_agreement_per_criterion():
    ai = [8, 6]
    human = [7, 6]
    res = V.compute_agreement(
        ai, human,
        per_criterion_ai={"Financials": [4, 3], "Market": [4, 3]},
        per_criterion_human={"Financials": [3, 3], "Market": [4, 3]},
    )
    assert set(res.per_criterion.keys()) == {"Financials", "Market"}
    assert res.per_criterion["Market"].mae == 0.0


def test_compute_agreement_degrades_without_per_criterion():
    res = V.compute_agreement([1, 2], [1, 2])
    assert res.per_criterion == {}


# ------------------------------ manifest loading ---------------------------- #

def test_load_ground_truth_csv_total_only(tmp_path):
    p = tmp_path / "gt.csv"
    p.write_text("filename,human_total\nplan1.pdf,72\nplan2.pdf,55\n", encoding="utf-8")
    recs = V.load_ground_truth(str(p))
    assert len(recs) == 2
    assert recs[0].filename == "plan1.pdf"
    assert recs[0].human_total == 72.0
    assert recs[0].criteria == {}  # degrades cleanly to total-only


def test_load_ground_truth_csv_with_criteria_and_split(tmp_path):
    p = tmp_path / "gt.csv"
    p.write_text(
        "filename,human_total,human_plan,human_video,crit_Financials,crit_Market\n"
        "plan1.pdf,80,64,16,9,7\n",
        encoding="utf-8",
    )
    recs = V.load_ground_truth(str(p))
    assert recs[0].human_plan == 64.0
    assert recs[0].human_video == 16.0
    assert recs[0].criteria == {"Financials": 9.0, "Market": 7.0}


def test_load_ground_truth_csv_missing_filename_column_raises(tmp_path):
    p = tmp_path / "bad.csv"
    p.write_text("name,human_total\nx,1\n", encoding="utf-8")
    with pytest.raises(ValueError):
        V.load_ground_truth(str(p))


def test_load_ground_truth_json(tmp_path):
    p = tmp_path / "gt.json"
    p.write_text(json.dumps([
        {"filename": "a.pdf", "human_total": 70, "human_plan": 56, "human_video": 14,
         "criteria": {"Financials": 8}},
        {"filename": "b.pdf", "human_total": 40},
    ]), encoding="utf-8")
    recs = V.load_ground_truth(str(p))
    assert len(recs) == 2
    assert recs[0].criteria["Financials"] == 8.0
    assert recs[1].human_plan is None  # optional fields degrade to None


def test_load_ground_truth_json_wrapped(tmp_path):
    p = tmp_path / "gt.json"
    p.write_text(json.dumps({"plans": [{"filename": "a.pdf", "human_total": 1}]}), encoding="utf-8")
    recs = V.load_ground_truth(str(p))
    assert recs[0].filename == "a.pdf"


def test_load_ground_truth_json_missing_filename_raises(tmp_path):
    p = tmp_path / "gt.json"
    p.write_text(json.dumps([{"human_total": 1}]), encoding="utf-8")
    with pytest.raises(ValueError):
        V.load_ground_truth(str(p))


# --------------------- validation-run aggregation --------------------------- #

def test_partition_separates_flagged():
    grades = [
        V.PlanGrade("ok.pdf", 70, graded_ok=True, eligibility_status="eligible"),
        V.PlanGrade("fail.pdf", 0, graded_ok=False, eligibility_status="needs_review"),
        V.PlanGrade("mlm.pdf", 60, graded_ok=True, eligibility_status="needs_review"),
    ]
    scored, flagged = V.partition(grades)
    assert [g.filename for g in scored] == ["ok.pdf"]
    assert {g.filename for g in flagged} == {"fail.pdf", "mlm.pdf"}


def test_join_and_aggregate_total():
    grades = [
        V.PlanGrade("a.pdf", 8, criteria={"Market": 4}),
        V.PlanGrade("b.pdf", 6, criteria={"Market": 3}),
        V.PlanGrade("c.pdf", 9, criteria={"Market": 5}),
    ]
    gt = [
        V.GroundTruthRecord("a.pdf", human_total=7, criteria={"Market": 4}),
        V.GroundTruthRecord("b.pdf", human_total=6, criteria={"Market": 3}),
        V.GroundTruthRecord("c.pdf", human_total=9, criteria={"Market": 5}),
    ]
    rep = V.join_and_aggregate(grades, gt, component="total")
    assert rep.matched == 3
    assert rep.scored == 3
    assert rep.flagged == 0
    assert rep.agreement.spearman is not None
    assert "Market" in rep.agreement.per_criterion


def test_join_uses_plan_component_when_available():
    grades = [V.PlanGrade("a.pdf", 60), V.PlanGrade("b.pdf", 40)]
    gt = [
        V.GroundTruthRecord("a.pdf", human_total=80, human_plan=60, human_video=20),
        V.GroundTruthRecord("b.pdf", human_total=50, human_plan=40, human_video=10),
    ]
    rep = V.join_and_aggregate(grades, gt, component="plan")
    # perfect match on the plan component
    assert rep.agreement.mae == 0.0


def test_join_reports_unmatched_and_missing_human():
    grades = [
        V.PlanGrade("a.pdf", 8),
        V.PlanGrade("ghost.pdf", 5),          # no ground-truth record
    ]
    gt = [
        V.GroundTruthRecord("a.pdf", human_total=None),  # matched but no human score
    ]
    rep = V.join_and_aggregate(grades, gt, component="total")
    assert "ghost.pdf" in rep.unmatched_filenames
    assert "a.pdf" in rep.missing_human_score
    assert rep.matched == 0


def test_flagged_plans_excluded_from_agreement():
    grades = [
        V.PlanGrade("a.pdf", 8),
        V.PlanGrade("bad.pdf", 0, graded_ok=False),
    ]
    gt = [
        V.GroundTruthRecord("a.pdf", human_total=8),
        V.GroundTruthRecord("bad.pdf", human_total=9),
    ]
    rep = V.join_and_aggregate(grades, gt, component="total")
    assert rep.matched == 1   # bad.pdf excluded, not scored as 0
    assert rep.flagged == 1
