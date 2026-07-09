"""The grader system prompt gains an evidence instruction only when asked.

Backward compatibility: with include_evidence=False (the default) the prompt is
byte-for-byte the current prompt, so `/grade` behavior is unchanged until a
caller opts in.
"""
from backend.src.agent import grader_system


def test_default_prompt_has_no_evidence_field_instruction():
    # The word "evidence" already appears (a scoring concept); the FIELD
    # instruction (a distinctive marker) must not, by default.
    assert "EVIDENCE FIELD" not in grader_system(competition=True)


def test_include_evidence_adds_verbatim_quote_instruction():
    p = grader_system(competition=True, include_evidence=True)
    assert "EVIDENCE FIELD" in p
    assert "verbatim" in p.lower() or "exact" in p.lower()


def test_include_evidence_is_opt_in_only():
    # Same competition mode, the only difference is the flag.
    assert grader_system(competition=True, include_evidence=True) != grader_system(competition=True)
