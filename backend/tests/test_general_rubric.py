"""Tests for the general (non-competition) business-plan rubric."""
from backend.src import general_rubric as G
from backend.src.models import RubricItem


def test_total_is_100():
    assert G.total_points() == 100.0


def test_criteria_count_and_uniqueness():
    names = [it.criteria for it in G.GENERAL_RUBRIC]
    assert len(names) == 30
    assert len(names) == len(set(names))  # no duplicates


def test_all_criteria_are_section_prefixed():
    # "Section - Label" so the frontend groups them like the BYUMS rubric
    for it in G.GENERAL_RUBRIC:
        assert " - " in it.criteria, it.criteria


def test_all_have_positive_max_and_description():
    for it in G.GENERAL_RUBRIC:
        assert it.max_points > 0
        assert it.description.strip()


def test_all_have_guide_and_tier_descriptions():
    # richer rubric: every criterion carries intent + partial + zero boundaries
    for it in G.GENERAL_RUBRIC:
        assert it.course_guide and it.course_guide.strip(), it.criteria
        assert it.developing_description and it.developing_description.strip(), it.criteria
        assert it.zero_description and it.zero_description.strip(), it.criteria


def test_financials_is_heaviest_section():
    sections: dict = {}
    for it in G.GENERAL_RUBRIC:
        s = it.criteria.split(" - ")[0]
        sections[s] = sections.get(s, 0) + it.max_points
    assert sections["Financials"] == max(sections.values())
    assert sections["Financials"] == 18


def test_to_dicts_roundtrips_to_rubric_items():
    dicts = G.to_dicts()
    assert len(dicts) == 30
    items = [RubricItem(**d) for d in dicts]  # must be valid grade/API payloads
    assert sum(i.max_points for i in items) == 100.0
