"""Tests for few-shot calibration (parsing + block building + anti-overfit guards)."""
import json

from backend.src import calibration as C
from backend.src.calibration import FewShotExample, ScoredItem


SCORED_CSV = (
    ",\n"
    "Business Nme,Jideofor Enterprise\n"
    ",\n"
    "Problem/Pain Point - 10 points,\n"
    "2.5 - Clearly defined the problem/pain being addressed,1.5\n"
    "5 - Outside data confirms the problem is huge (scalable),1\n"
    "2.5 - Examples of what other are doing to solve the problem,0\n"
    "Total,2.5\n"
    ",\n"
    "Financials - 15 points,\n"
    "5 - Past 3 years Provided,1\n"
    "Total,1\n"
    "Grand Total,3.5\n"
    "Potential to be successful ,Moderate\n"
)


def _write(tmp_path, text):
    p = tmp_path / "scores.csv"
    p.write_text(text, encoding="utf-8")
    return str(p)


# ------------------------------ CSV parsing --------------------------------- #

def test_parse_reconstructs_full_criterion_names(tmp_path):
    parsed = C.parse_scored_plan_csv(_write(tmp_path, SCORED_CSV))
    names = [it.criteria for it in parsed["items"]]
    assert "Problem/Pain Point - Clearly defined the problem/pain being addressed" in names
    assert "Problem/Pain Point - Outside data confirms the problem is huge (scalable)" in names
    assert "Financials - Past 3 years Provided" in names


def test_parse_scores_and_max(tmp_path):
    parsed = C.parse_scored_plan_csv(_write(tmp_path, SCORED_CSV))
    by = {it.criteria: it for it in parsed["items"]}
    ex = by["Problem/Pain Point - Examples of what other are doing to solve the problem"]
    assert ex.awarded == 0.0 and ex.max_points == 2.5
    clear = by["Problem/Pain Point - Clearly defined the problem/pain being addressed"]
    assert clear.awarded == 1.5 and clear.max_points == 2.5


def test_parse_business_name_and_total(tmp_path):
    parsed = C.parse_scored_plan_csv(_write(tmp_path, SCORED_CSV))
    assert parsed["business_name"] == "Jideofor Enterprise"
    assert parsed["human_total"] == 3.5


def test_parse_skips_section_total_and_qualitative_rows(tmp_path):
    parsed = C.parse_scored_plan_csv(_write(tmp_path, SCORED_CSV))
    # "Total", "Grand Total", "Potential to be successful" must NOT become criteria
    names = [it.criteria for it in parsed["items"]]
    assert not any("Total" in n for n in names)
    assert not any("Potential" in n for n in names)
    assert len(parsed["items"]) == 4


# --------------------------- example load/save ------------------------------ #

def test_example_roundtrip(tmp_path):
    ex = FewShotExample("plan.pdf", "Acme", "some plan text", [ScoredItem("Market - Buyer", 1.5, 2.5)], 36.0)
    p = tmp_path / "ex.json"
    p.write_text(json.dumps([ex.to_dict()]), encoding="utf-8")
    loaded = C.load_examples(str(p))
    assert len(loaded) == 1
    assert loaded[0].filename == "plan.pdf"
    assert loaded[0].items[0].awarded == 1.5
    assert loaded[0].human_total == 36.0


def test_load_examples_missing_file_returns_empty(tmp_path):
    assert C.load_examples(str(tmp_path / "nope.json")) == []


# --------------------- block building + anti-overfit ------------------------ #

def _example(name="plan.pdf"):
    return FewShotExample(name, "Acme", "PLAN TEXT HERE", [ScoredItem("Financials - Detailed Breakdown", 2.0, 5.0)], 36.0)


def test_block_contains_scores_and_anti_copy_instruction():
    block = C.build_calibration_block([_example()])
    assert "CALIBRATION REFERENCE" in block
    assert "Financials - Detailed Breakdown: 2.0/5.0" in block
    assert "36.0 / 80" in block
    assert "Do NOT copy" in block            # anti-overfit instruction present
    assert "on its own evidence" in block


def test_leave_one_out_excludes_self():
    # grading the same plan must NOT inject that plan as its own example (no leakage)
    block = C.build_calibration_block([_example("plan.pdf")], exclude_filenames={"plan.pdf"})
    assert block == ""


def test_exclusion_leaves_other_examples():
    block = C.build_calibration_block(
        [_example("a.pdf"), _example("b.pdf")], exclude_filenames={"a.pdf"}
    )
    assert block != ""
    # only b.pdf's example remains (a excluded) -> block builds
    assert "CALIBRATION REFERENCE" in block


def test_empty_examples_yield_empty_block():
    assert C.build_calibration_block([]) == ""


def test_long_plan_text_is_truncated():
    big = FewShotExample("p.pdf", "Big", "x" * 9000, [ScoredItem("A - B", 1, 2)], 10.0)
    block = C.build_calibration_block([big], max_plan_chars=100)
    assert "[example plan truncated]" in block
    # the massive text is not dumped verbatim
    assert block.count("x") < 300


# ------------------------------ overrides ----------------------------------- #

def _ex_multi():
    return FewShotExample("p.pdf", "Acme", "text", [
        ScoredItem("Problem/Pain Point - Outside data confirms the problem is huge (scalable)", 1.0, 5.0),
        ScoredItem("Market Size/Growth Potential - Identify who competitors are", 1.0, 2.5),
        ScoredItem("Financials - Past 3 years Provided", 1.0, 5.0),
    ], human_total=3.0)


def test_apply_overrides_updates_scores_notes_and_total():
    ex = _ex_multi()
    changes = C.apply_overrides(ex, [
        {"criteria": "Problem/Pain Point - Outside data confirms the problem is huge (scalable)",
         "awarded": 1.5, "note": "first-hand data"},
        {"criteria": "Market Size/Growth Potential - Identify who competitors are",
         "awarded": 2.0, "note": "clearly named"},
    ])
    by = {it.criteria: it for it in ex.items}
    assert by["Problem/Pain Point - Outside data confirms the problem is huge (scalable)"].awarded == 1.5
    assert by["Market Size/Growth Potential - Identify who competitors are"].awarded == 2.0
    # financials untouched (user supported the human's harsh score)
    assert by["Financials - Past 3 years Provided"].awarded == 1.0
    assert ex.human_total == 4.5   # 1.5 + 2.0 + 1.0
    assert len(changes) == 2
    assert by["Problem/Pain Point - Outside data confirms the problem is huge (scalable)"].note == "first-hand data"


def test_apply_overrides_ignores_unmatched():
    ex = _ex_multi()
    changes = C.apply_overrides(ex, [{"criteria": "Nonexistent - Thing", "awarded": 9}])
    assert changes == []
    assert ex.human_total == 3.0


def test_override_note_appears_in_block():
    ex = _ex_multi()
    C.apply_overrides(ex, [{"criteria": "Market Size/Growth Potential - Identify who competitors are",
                            "awarded": 2.0, "note": "clearly named"}])
    block = C.build_calibration_block([ex])
    assert "(clearly named)" in block
