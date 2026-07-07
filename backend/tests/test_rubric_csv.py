"""Tests for the BYUMS rubric CSV converter."""
import pytest

from backend.src import rubric_csv as R
from backend.src.models import RubricItem


HEADER = "Criteria,Distinguished (Full Marks),Proficient / Developing (Partial),No Marks (Zero),Max Pts\n"


def _write(tmp_path, rows):
    p = tmp_path / "rubric.csv"
    p.write_text(HEADER + rows, encoding="utf-8")
    return str(p)


# ------------------------------- helpers ------------------------------------ #

def test_extract_points_basic():
    assert R.extract_points("(2.5) pts") == 2.5
    assert R.extract_points("(10.0) pts: Quality") == 10.0
    assert R.extract_points("(1.25) pts Proficient / Developing: ...") == 1.25
    assert R.extract_points("(0) pts: Fails") == 0.0


def test_extract_points_none():
    assert R.extract_points("no points here") is None
    assert R.extract_points(None) is None


def test_strip_points_prefix():
    assert R.strip_points_prefix("(2.5) pts: Contestant face on video.") == "Contestant face on video."
    assert R.strip_points_prefix("(1.25) pts Proficient / Developing: Partially demonstrates.") == \
        "Proficient / Developing: Partially demonstrates."


def test_is_video_criterion():
    assert R.is_video_criterion("Video - Contestant face on video") is True
    assert R.is_video_criterion("Financials - Past 3 years Provided") is False
    # 'Conclusion - Link in video...' is NOT a video component criterion
    assert R.is_video_criterion("Conclusion - Link in video to the Google Slide Deck") is False


# ------------------------------- parsing ------------------------------------ #

def test_parse_single_row(tmp_path):
    path = _write(
        tmp_path,
        '"Video - Quality of content","(10.0) pts: has merit.",'
        '"(5) pts Proficient / Developing: Partial.","(0) pts: Fails.","(10) pts"\n',
    )
    items = R.parse_byums_rubric_csv(path)
    assert len(items) == 1
    it = items[0]
    assert isinstance(it, RubricItem)
    assert it.criteria == "Video - Quality of content"
    assert it.max_points == 10.0
    assert it.description == "has merit."
    assert it.developing_points == 5.0
    assert "Partial" in it.developing_description
    assert it.zero_points == 0.0


def test_parse_skips_blank_rows(tmp_path):
    path = _write(tmp_path, ',,,,\n"Financials - X","(5.0) pts: recs.","(2.5) pts P.","(0) pts: F.","(5) pts"\n')
    items = R.parse_byums_rubric_csv(path)
    assert len(items) == 1
    assert items[0].criteria == "Financials - X"


def test_parse_missing_criteria_column_raises(tmp_path):
    p = tmp_path / "bad.csv"
    p.write_text("Name,Max Pts\nx,1\n", encoding="utf-8")
    with pytest.raises(ValueError):
        R.parse_byums_rubric_csv(str(p))


def test_max_points_falls_back_to_distinguished(tmp_path):
    # No Max Pts value -> use the Distinguished prefix
    path = _write(tmp_path, '"Conclusion - Summary","(2.0) pts: overall.","(1) pts P.","(0) pts: F.",""\n')
    items = R.parse_byums_rubric_csv(path)
    assert items[0].max_points == 2.0


# ------------------------------- splitting ---------------------------------- #

def test_split_video_plan(tmp_path):
    rows = (
        '"Video - Face","(2.5) pts: face.","(1.25) pts P.","(0) pts: F.","(2.5) pts"\n'
        '"Video - Length","(2.5) pts: 4-5 min.","(1.25) pts P.","(0) pts: F.","(2.5) pts"\n'
        '"Financials - Past 3 years","(5.0) pts: recs.","(2.5) pts P.","(0) pts: F.","(5) pts"\n'
        '"Conclusion - Link in video","(1.0) pts: link.","(0.5) pts P.","(0) pts: F.","(1) pts"\n'
    )
    items = R.parse_byums_rubric_csv(_write(tmp_path, rows))
    plan, video = R.split_video_plan(items)
    assert [i.criteria for i in video] == ["Video - Face", "Video - Length"]
    # the 'Conclusion - Link in video' stays in the PLAN set (not a Video- criterion)
    assert {i.criteria for i in plan} == {"Financials - Past 3 years", "Conclusion - Link in video"}
    assert R.total_points(video) == 5.0
    assert R.total_points(plan) == 6.0


def test_rubric_to_dicts_roundtrip(tmp_path):
    path = _write(tmp_path, '"Market - Buyer","(2.5) pts: buyer.","(1.25) pts P.","(0) pts: F.","(2.5) pts"\n')
    items = R.parse_byums_rubric_csv(path)
    dicts = R.rubric_to_dicts(items)
    assert dicts[0]["criteria"] == "Market - Buyer"
    assert dicts[0]["max_points"] == 2.5
    # round-trips back into a RubricItem (valid harness/API payload)
    assert RubricItem(**dicts[0]).max_points == 2.5
