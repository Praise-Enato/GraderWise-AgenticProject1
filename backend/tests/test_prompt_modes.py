"""Tests for competition-vs-general prompt framing.

The grader/feedback prompts carry BYUMS-competition framing (prize money,
"competition", non-native-English participants). That framing must appear in
competition mode and must NOT leak into general-rubric mode.
"""
from langchain_core.prompts import ChatPromptTemplate

from backend.src import agent as A


def test_grader_competition_mode_has_prize_framing():
    gs = A.grader_system(competition=True)
    assert "prize money" in gs
    assert "Competition" in gs


def test_grader_general_mode_drops_competition_framing():
    gs = A.grader_system(competition=False)
    assert "prize money" not in gs
    assert "Competition" not in gs
    # still a strict evaluator — strictness is universal, only the framing changed
    assert "STRICT" in gs


def test_feedback_competition_mode_has_competition_framing():
    fs = A.feedback_system(competition=True)
    assert "ONLY prize" in fs
    assert "first language" in fs


def test_feedback_general_mode_drops_competition_framing():
    fs = A.feedback_system(competition=False)
    assert "prize" not in fs
    assert "competition" not in fs.lower()
    assert "first language" not in fs


def test_default_mode_is_competition():
    assert A.grader_system() == A.grader_system(competition=True)
    assert A.feedback_system() == A.feedback_system(competition=True)


def test_no_leftover_placeholder_tokens():
    for comp in (True, False):
        assert "__" not in A.grader_system(comp)
        assert "__" not in A.feedback_system(comp)


def test_universal_rules_survive_in_both_modes():
    # the rules/output-format below the framing are mode-independent
    for comp in (True, False):
        assert "The Rubric is Law" in A.grader_system(comp)
        assert "What you did well" in A.feedback_system(comp)


def test_format_rubric_renders_course_guide_when_present():
    from backend.src.models import RubricItem
    with_guide = RubricItem(criteria="X - y", max_points=5, description="full",
                            course_guide="what this criterion means")
    without = RubricItem(criteria="Z - w", max_points=5, description="full")
    rendered = A._format_rubric([with_guide, without])
    assert "[WHAT THIS MEANS]: what this criterion means" in rendered
    # criterion without a guide simply omits the line (no empty label)
    assert rendered.count("[WHAT THIS MEANS]") == 1


def test_resolved_prompts_are_valid_chat_templates():
    # guards against brace breakage: the JSON {{ }} in GRADER_SYSTEM must stay
    # escaped and no framing text may introduce stray {vars}
    for comp in (True, False):
        ChatPromptTemplate.from_messages(
            [("system", A.grader_system(comp)), ("user", A.GRADER_USER)]
        )
        ChatPromptTemplate.from_messages(
            [("system", A.feedback_system(comp)), ("user", A.FEEDBACK_USER)]
        )
