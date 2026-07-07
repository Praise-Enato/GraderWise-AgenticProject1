"""Tests for the first-round eligibility / disqualifier screen.

Guarantees: excluded business types + non-English + AI tells flag for review
(never auto-reject); a clean legit plan passes; deliverable-absence in text is
advisory only and does not change status.
"""
from backend.src.eligibility import (
    EligibilityResult,
    detect_ai_content,
    looks_english,
    screen_eligibility,
)
from backend.src.models import ELIGIBILITY_ELIGIBLE, ELIGIBILITY_NEEDS_REVIEW


CLEAN_PLAN = (
    "Our business sells solar lanterns to households in our local market. "
    "We have a registered business license and a business bank account. "
    "The market is growing and our customers value reliability. Revenue comes "
    "from unit sales and we reinvest profits to expand distribution."
)


def test_clean_plan_is_eligible():
    res = screen_eligibility(CLEAN_PLAN)
    assert res.status == ELIGIBILITY_ELIGIBLE
    assert res.reasons == []
    assert res.ai_content_flag is False


def test_mlm_plan_flagged_for_review():
    res = screen_eligibility("We use a multi-level marketing model where members recruit members.")
    assert res.status == ELIGIBILITY_NEEDS_REVIEW
    assert any("multi-level marketing" in r for r in res.reasons)
    # flagged, NOT auto-rejected
    assert res.status != "ineligible"


def test_franchise_flagged():
    res = screen_eligibility("We plan to sell franchise units of our restaurant brand across regions.")
    assert res.status == ELIGIBILITY_NEEDS_REVIEW
    assert any("franchise" in r for r in res.reasons)


def test_get_rich_quick_flagged():
    res = screen_eligibility("This is a get rich quick opportunity to double your money fast.")
    assert res.status == ELIGIBILITY_NEEDS_REVIEW


def test_non_english_flagged():
    french = ("Ceci est un plan d'affaires pour notre entreprise qui vend des produits "
              "agricoles aux clients locaux avec une bonne rentabilite prevue.")
    res = screen_eligibility(french)
    assert res.status == ELIGIBILITY_NEEDS_REVIEW
    assert any("English" in r for r in res.reasons)


def test_missing_deliverables_is_advisory_not_status_change():
    plan = ("Our company builds affordable furniture and sells it to families in town. "
            "We focus on quality and our customers keep coming back for more products.")
    res = screen_eligibility(plan)
    # no serious reasons -> still eligible
    assert res.status == ELIGIBILITY_ELIGIBLE
    # but advisory notes surface the unconfirmed deliverables
    assert any("license" in n.lower() for n in res.advisory_notes)
    assert any("bank" in n.lower() for n in res.advisory_notes)


def test_ai_content_flag_and_review():
    res = screen_eligibility("As an AI language model, I cannot start a business, but here is a plan.")
    assert res.ai_content_flag is True
    assert res.status == ELIGIBILITY_NEEDS_REVIEW


def test_empty_text_is_eligible_no_flags():
    res = screen_eligibility("")
    assert res.status == ELIGIBILITY_ELIGIBLE
    assert res.reasons == []
    assert res.advisory_notes == []


def test_all_reasons_includes_advisory_prefixed():
    res = EligibilityResult(status="needs_review", reasons=["serious"], advisory_notes=["soft"])
    combined = res.all_reasons()
    assert "serious" in combined
    assert "(advisory) soft" in combined


# ------------------------------ helpers ------------------------------------- #

def test_looks_english_true_for_english():
    assert looks_english("The business is growing and we sell to our customers.") is True


def test_looks_english_false_for_other_language():
    assert looks_english("Ceci est un plan d'affaires pour notre entreprise agricole locale rentable.") is False


def test_looks_english_short_text_defaults_true():
    assert looks_english("solar lamps") is True  # too short to judge -> don't flag


def test_detect_ai_content_positive():
    assert detect_ai_content("Certainly! Here is a business plan for you.") is True


def test_detect_ai_content_negative():
    assert detect_ai_content("We sell handmade soap to local shops.") is False


def test_business_type_reason_includes_context_and_verify_note():
    # Real-world false-positive shape (from an actual submitted plan): a POS
    # business that mentions an "agent sub-franchise system" as a growth idea.
    # It should flag for review with actionable context, not a terse 'matched: franchise'.
    plan = "We will introduce an agent sub-franchise system to grow our POS business next year."
    res = screen_eligibility(plan)
    assert res.status == ELIGIBILITY_NEEDS_REVIEW
    joined = " ".join(res.reasons).lower()
    assert "franchise" in joined
    assert "sub-franchise" in joined   # surrounding context is quoted
    assert "verify" in joined          # actionable guidance for the human reviewer
