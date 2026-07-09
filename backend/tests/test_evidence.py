"""Tests for evidence-quote validation.

The grader returns, per criterion, an exact quote from the submission that
justifies the award. The pure-Python Judge must verify that quote actually
appears in the submission, or "evidence-linked" feedback links to hallucinated
text (OV#7). Exact substring fails on real inputs (OCR hyphenation, ligatures,
smart quotes, whitespace, case), so matching is normalized + fuzzy. TDD.
"""
import pytest

from backend.src import evidence


def test_exact_quote_is_supported():
    sub = "Our target market is 2.3 million smallholder farmers in Kenya."
    assert evidence.evidence_supported("2.3 million smallholder farmers", sub) is True


def test_case_and_whitespace_differences_are_supported():
    sub = "Our target   market is 2.3 MILLION\nsmallholder farmers."
    assert evidence.evidence_supported("2.3 million smallholder farmers", sub) is True


def test_smart_quotes_and_dashes_are_supported():
    sub = "The founder said “we are pre-revenue” — a candid admission."
    assert evidence.evidence_supported('"we are pre-revenue" - a candid admission', sub) is True


def test_hyphenation_across_line_break_is_supported():
    sub = "We serve the micro-\nfinance sector across three regions."
    assert evidence.evidence_supported("microfinance sector", sub) is True


def test_minor_ocr_drift_within_a_word_is_supported():
    # OCR dropped an 'l' from 'smallholder'; the evidence is really there.
    sub = "Our target market is 2.3 million smallholder farmers in Kenya."
    assert evidence.evidence_supported("2.3 million smalholder farmers in Kenya", sub) is True


def test_hallucinated_quote_is_not_supported():
    sub = "Our target market is 2.3 million smallholder farmers in Kenya."
    assert evidence.evidence_supported(
        "we hold three patents and a signed government contract", sub
    ) is False


def test_paraphrase_not_present_verbatim_is_not_supported():
    sub = "Revenue was 40,000 dollars in the first year of trading."
    assert evidence.evidence_supported(
        "the company earned substantial profits in year one", sub
    ) is False


def test_empty_or_whitespace_quote_is_not_supported():
    sub = "Anything at all here."
    assert evidence.evidence_supported("", sub) is False
    assert evidence.evidence_supported("   ", sub) is False


def test_empty_submission_is_not_supported():
    assert evidence.evidence_supported("some claim", "") is False


# Realistic long submission: a hallucinated quote must not be "supported" just
# because a long document happens to share many common characters/words.
_LONG_SUBMISSION = (
    "AgriConnect is a mobile platform linking smallholder farmers in western "
    "Kenya to buyers in Nairobi. We launched in March 2024 and have onboarded "
    "1,200 farmers across three counties. Revenue in the first year was "
    "42,000 US dollars, driven by a 4 percent transaction fee. Our team of "
    "five includes two agronomists and a logistics lead. The main risk is "
    "cold-chain reliability during the rainy season, which we mitigate with "
    "regional aggregation points and pre-cooling sheds."
)


def test_hallucinated_quote_against_long_submission_is_not_supported():
    assert evidence.evidence_supported(
        "we secured a two million dollar grant from the World Bank", _LONG_SUBMISSION
    ) is False


def test_real_quote_from_long_submission_is_supported():
    assert evidence.evidence_supported(
        "onboarded 1,200 farmers across three counties", _LONG_SUBMISSION
    ) is True
