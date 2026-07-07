"""Regression tests from the Phase 1a adversarial verification pass.

Each test is labeled with the finding number it locks down, so the audit trail
from code -> finding -> fix -> test is explicit.
"""
import json

import pytest

from backend.src import validation as V
from backend.src.grading import parse_grader_response, to_grade_result
from backend.src.eligibility import screen_eligibility
from backend.src.input_adapter import find_youtube_url
from backend.src.models import RubricItem, ELIGIBILITY_INELIGIBLE, ELIGIBILITY_NEEDS_REVIEW


def rubric():
    return [
        RubricItem(criteria="Financials", max_points=10, description="records"),
        RubricItem(criteria="Market", max_points=20, description="local market"),
    ]


# --- #1: non-finite awarded_points must be flagged, never poison the total ---- #

def test_nan_literal_award_flagged():
    bad = '{"assessments": [{"criteria_index": 1, "criteria_name": "Financials", "awarded_points": NaN}]}'
    gd = parse_grader_response(bad, rubric())
    assert gd.graded_ok is False
    assert "Non-finite" in gd.error


def test_nan_string_award_flagged():
    bad = json.dumps({"assessments": [{"criteria_index": 1, "criteria_name": "Financials", "awarded_points": "nan"}]})
    gd = parse_grader_response(bad, rubric())
    assert gd.graded_ok is False
    assert "Non-finite" in gd.error


def test_infinity_award_flagged():
    bad = '{"assessments": [{"criteria_index": 1, "criteria_name": "Financials", "awarded_points": Infinity}]}'
    gd = parse_grader_response(bad, rubric())
    assert gd.graded_ok is False
    assert "Non-finite" in gd.error


# --- #4/#7: over-award to a criterion with no resolvable max is untrustworthy - #

def test_unknown_criterion_no_max_positive_award_flagged():
    j = json.dumps({"assessments": [{"criteria_name": "Mystery", "awarded_points": 9999}]})
    gd = parse_grader_response(j, rubric())
    assert gd.graded_ok is False
    assert "unknown criterion" in gd.error


def test_unknown_criterion_zero_award_is_ok():
    j = json.dumps({"assessments": [
        {"criteria_index": 1, "criteria_name": "Financials", "awarded_points": 5},
        {"criteria_name": "Mystery", "awarded_points": 0},
    ]})
    gd = parse_grader_response(j, rubric())
    assert gd.graded_ok is True
    assert gd.score == 5.0


# --- #6: non-dict element inside the assessments list is flagged --------------- #

def test_non_dict_assessment_item_flagged():
    gd = parse_grader_response(json.dumps({"assessments": [42]}), rubric())
    assert gd.graded_ok is False
    assert "not an object" in gd.error


def test_valid_then_non_dict_assessment_flagged():
    j = json.dumps({"assessments": [
        {"criteria_index": 1, "criteria_name": "Financials", "awarded_points": 8},
        "oops",
    ]})
    gd = parse_grader_response(j, rubric())
    assert gd.graded_ok is False


# --- #14: a failed grade must NOT downgrade an already-ineligible status ------- #

def test_failed_grade_keeps_ineligible_status():
    gd = parse_grader_response("garbage", rubric())
    gr = to_grade_result(gd, feedback="", eligibility_status=ELIGIBILITY_INELIGIBLE)
    assert gr.eligibility_status == ELIGIBILITY_INELIGIBLE  # not overwritten to needs_review
    assert gr.graded_ok is False


def test_failed_grade_eligible_becomes_needs_review():
    gd = parse_grader_response("garbage", rubric())
    gr = to_grade_result(gd, feedback="")  # default eligible
    assert gr.eligibility_status == ELIGIBILITY_NEEDS_REVIEW


# --- #17: criteria_index fallback (positional / non-numeric) ------------------ #

def test_criteria_index_positional_fallback():
    j = json.dumps({"assessments": [{"criteria_name": "Market", "awarded_points": 10}]})
    gd = parse_grader_response(j, rubric())
    assert gd.assessments[0].criteria_index == 1  # positional (first item)


def test_criteria_index_non_numeric_fallback():
    j = json.dumps({"assessments": [{"criteria_index": "abc", "criteria_name": "Market", "awarded_points": 10}]})
    gd = parse_grader_response(j, rubric())
    assert gd.assessments[0].criteria_index == 1


# --- #5/#8: component='plan' must NOT fall back to total (video confound) ------ #

def test_join_plan_component_no_fallback_to_total():
    grades = [V.PlanGrade("a.pdf", 60)]
    gt = [V.GroundTruthRecord("a.pdf", human_total=80, human_plan=None)]
    rep = V.join_and_aggregate(grades, gt, component="plan")
    assert rep.matched == 0                       # NOT compared against the 100% total
    assert "a.pdf" in rep.missing_human_score


# --- #9: component='video' path --------------------------------------------- #

def test_join_uses_video_component():
    grades = [V.PlanGrade("a.pdf", 4), V.PlanGrade("b.pdf", 5)]
    gt = [
        V.GroundTruthRecord("a.pdf", human_total=80, human_video=4),
        V.GroundTruthRecord("b.pdf", human_video=5),
    ]
    rep = V.join_and_aggregate(grades, gt, component="video")
    assert rep.matched == 2
    assert rep.agreement.mae == 0.0


def test_join_video_missing_reported():
    grades = [V.PlanGrade("a.pdf", 4)]
    gt = [V.GroundTruthRecord("a.pdf", human_total=10, human_video=None)]
    rep = V.join_and_aggregate(grades, gt, component="video")
    assert "a.pdf" in rep.missing_human_score


# --- #10: custom-confidence CI path (Acklam inverse-normal) ------------------ #

def test_z_critical_known_values():
    assert V._z_critical(0.95) == pytest.approx(1.959963984540054)
    assert V._z_critical(0.90) == pytest.approx(1.6448536269514722)
    assert V._z_critical(0.99) == pytest.approx(2.5758293035489004)


def test_z_critical_noncached_uses_inv_norm():
    assert V._z_critical(0.80) == pytest.approx(1.2815515594, abs=1e-4)
    assert V._z_critical(0.975) == pytest.approx(2.2414027276, abs=1e-4)


def test_fisher_ci_custom_confidence_wider_for_99():
    ci90 = V.fisher_ci(0.6, n=30, confidence=0.90)
    ci99 = V.fisher_ci(0.6, n=30, confidence=0.99)
    assert (ci99[1] - ci99[0]) > (ci90[1] - ci90[0])


# --- #3: Spearman variance correction widens the interval -------------------- #

def test_fisher_ci_variance_factor_widens():
    base = V.fisher_ci(0.7, n=20, variance_factor=1.0)
    wider = V.fisher_ci(0.7, n=20, variance_factor=1.03)
    assert (wider[1] - wider[0]) > (base[1] - base[0])


# --- #11: JSON manifest 'records' wrapper + unknown wrapper ------------------ #

def test_load_json_records_wrapper(tmp_path):
    p = tmp_path / "gt.json"
    p.write_text(json.dumps({"records": [{"filename": "a.pdf", "human_total": 1}]}), encoding="utf-8")
    assert len(V.load_ground_truth(str(p))) == 1


def test_load_json_unknown_wrapper_empty(tmp_path):
    p = tmp_path / "gt.json"
    p.write_text(json.dumps({"foo": [{"filename": "a.pdf"}]}), encoding="utf-8")
    assert V.load_ground_truth(str(p)) == []


# --- #2: JSON null/empty criterion value must not crash the load ------------- #

def test_load_json_null_criterion_dropped(tmp_path):
    p = tmp_path / "gt.json"
    p.write_text(json.dumps([
        {"filename": "a.pdf", "human_total": 80, "criteria": {"team": None, "market": 7}},
    ]), encoding="utf-8")
    recs = V.load_ground_truth(str(p))
    assert recs[0].criteria == {"market": 7.0}   # null dropped, no crash


# --- #12: CSV alternate criterion prefixes + blank cell --------------------- #

def test_csv_alternate_criterion_prefixes(tmp_path):
    p = tmp_path / "gt.csv"
    p.write_text("filename,human_total,human_crit_Financials,criterion_Market\na.pdf,80,9,7\n", encoding="utf-8")
    recs = V.load_ground_truth(str(p))
    assert recs[0].criteria == {"Financials": 9.0, "Market": 7.0}


def test_csv_blank_criterion_cell_skipped(tmp_path):
    p = tmp_path / "gt.csv"
    p.write_text("filename,human_total,crit_Financials,crit_Market\na.pdf,80,,7\n", encoding="utf-8")
    recs = V.load_ground_truth(str(p))
    assert recs[0].criteria == {"Market": 7.0}


# --- #13: leave_one_out negative-n guard ------------------------------------ #

def test_leave_one_out_negative_raises():
    with pytest.raises(ValueError):
        V.leave_one_out_indices(-1)


# --- #15: youtube /shorts/ and /live/ forms --------------------------------- #

def test_find_youtube_shorts():
    assert find_youtube_url("https://youtube.com/shorts/dQw4w9WgXcQ") == \
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


def test_find_youtube_live():
    assert find_youtube_url("https://www.youtube.com/live/dQw4w9WgXcQ") == \
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


def test_find_youtube_short_id_none():
    assert find_youtube_url("youtu.be/abc") is None  # id shorter than 11 chars


# --- #16: every excluded business-type category flags for review ------------- #

@pytest.mark.parametrize("phrase,label", [
    ("we run a network marketing business", "network marketing"),
    ("this is a pyramid scheme opportunity", "pyramid"),
    ("we plan a buyout of a competitor", "buyout"),
    ("a real estate syndication fund", "real estate syndication"),
    ("this is a tax shelter vehicle", "tax shelter"),
    ("we sell franchise units", "franchise"),
])
def test_excluded_categories_flagged(phrase, label):
    res = screen_eligibility(phrase + " serving our local customers and market")
    assert res.status == ELIGIBILITY_NEEDS_REVIEW
    assert any(label in r.lower() for r in res.reasons)


def test_two_excluded_categories_both_reported():
    res = screen_eligibility("our franchise also uses network marketing to recruit our members")
    joined = " ".join(res.reasons).lower()
    assert "franchise" in joined and "network marketing" in joined
