"""Tests for multi-rater ground truth + the human-ceiling verdict.

To interpret AI-vs-human agreement (OV#3) the harness needs per-rater human
scores, not just an aggregated total. The manifest gains optional per-rater
columns (CSV: `rater_<name>`; JSON: a `raters` object), and interrater
computes the human ceiling over the plans every rater scored. TDD.
"""
import json

from backend.src import validation as V
from backend.src import interrater


def test_json_manifest_loads_per_rater_scores(tmp_path):
    p = tmp_path / "gt.json"
    p.write_text(json.dumps([
        {"filename": "a.pdf", "human_plan": 80, "raters": {"alice": 80, "bob": 78}},
        {"filename": "b.pdf", "human_plan": 60, "raters": {"alice": 62, "bob": 59}},
    ]))
    recs = V.load_ground_truth(str(p))
    assert recs[0].raters == {"alice": 80.0, "bob": 78.0}
    assert recs[1].raters["bob"] == 59.0


def test_csv_manifest_loads_rater_columns(tmp_path):
    p = tmp_path / "gt.csv"
    p.write_text(
        "filename,human_plan,rater_alice,rater_bob\n"
        "a.pdf,80,80,78\n"
        "b.pdf,60,62,59\n"
    )
    recs = V.load_ground_truth(str(p))
    assert recs[0].raters == {"alice": 80.0, "bob": 78.0}


def test_human_ceiling_over_complete_cases():
    # Two raters, four plans, ranks agree perfectly -> ceiling spearman 1.0.
    recs = [
        V.GroundTruthRecord(filename="a", raters={"alice": 10, "bob": 1}),
        V.GroundTruthRecord(filename="b", raters={"alice": 20, "bob": 2}),
        V.GroundTruthRecord(filename="c", raters={"alice": 30, "bob": 3}),
        V.GroundTruthRecord(filename="d", raters={"alice": 40, "bob": 4}),
    ]
    ceiling = interrater.human_ceiling(recs)
    assert ceiling.n_raters == 2
    assert ceiling.n_items == 4
    assert ceiling.mean_pairwise_spearman == 1.0


def test_human_ceiling_uses_only_plans_all_raters_scored():
    # bob missed plan 'c'; complete cases are a, b, d (3 items).
    recs = [
        V.GroundTruthRecord(filename="a", raters={"alice": 10, "bob": 1}),
        V.GroundTruthRecord(filename="b", raters={"alice": 20, "bob": 2}),
        V.GroundTruthRecord(filename="c", raters={"alice": 30}),
        V.GroundTruthRecord(filename="d", raters={"alice": 40, "bob": 4}),
    ]
    ceiling = interrater.human_ceiling(recs)
    assert ceiling.n_items == 3


def test_human_ceiling_none_when_under_two_raters():
    recs = [V.GroundTruthRecord(filename="a", raters={"alice": 10})]
    ceiling = interrater.human_ceiling(recs)
    assert ceiling.mean_pairwise_spearman is None


def test_join_and_aggregate_threads_bootstrap_to_agreement():
    grades = [
        V.PlanGrade("a", 80.0), V.PlanGrade("b", 60.0),
        V.PlanGrade("c", 70.0), V.PlanGrade("d", 90.0),
    ]
    gt = [
        V.GroundTruthRecord("a", human_plan=78), V.GroundTruthRecord("b", human_plan=62),
        V.GroundTruthRecord("c", human_plan=71), V.GroundTruthRecord("d", human_plan=88),
    ]
    rep = V.join_and_aggregate(grades, gt, component="plan",
                               bootstrap_resamples=200, bootstrap_seed=1)
    assert rep.matched == 4
    assert rep.agreement.boot_ci95 is not None
