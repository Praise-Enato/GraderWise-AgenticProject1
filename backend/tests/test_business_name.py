"""Tests for reading the business name out of the plan document.

Every case below is a shape that appears in the real submission corpus — the
BYUMS slide template's "YOUR BUSINESS NAME" label, prose plans that bury the name
in the exec summary, bare title lines, deck titles split across two text boxes,
and PDFs whose text layer lost every space.

The most important tests here are the negative ones. This extractor feeds a
report heading, so a confidently WRONG name is worse than none: the caller falls
back to the file name on "", and a judge seeing a file name knows to check.
"""
from backend.src.business_name import extract, extract_business_name


# --- Explicit label -------------------------------------------------------- #

def test_label_on_the_same_line():
    text = "Business Plan for Kingsley Electronic Business\nExecutive Summary:\nBusiness Name: Kingsley Electronic Business\nBusiness Type: Electronics retail\n"
    assert extract_business_name(text) == "Kingsley Electronic Business"


def test_byums_template_label_sits_above_the_name():
    # The competition's own slide template ships this label; entrants type under it.
    text = ("BYU Management Society\nAfrica Business Plan Competition\n2026\n"
            "YOUR BUSINESS NAME\nJIDEOFOR RAYMOND ENTERPRISE\nIncreasing Sales Through Alternative\n")
    assert extract_business_name(text) == "Jideofor Raymond Enterprise"


def test_label_variants():
    for label in ("Business Name", "Company Name", "Name of Business",
                  "Name of the Business", "Enterprise Name", "Trading Name"):
        assert extract_business_name(f"{label}: Acme Ventures\nLocation: Lagos\n") == "Acme Ventures"


def test_value_is_cut_at_the_next_field_label():
    text = "Business Name: Acme Ventures Owner: Jane Doe\n"
    assert extract_business_name(text) == "Acme Ventures"


# --- Titles ---------------------------------------------------------------- #

def test_title_prefix():
    assert extract_business_name("BUSINESS PLAN: FROST FLOW ICE VENTURES\nLocation: Kakata\n") == "Frost Flow Ice Ventures"


def test_title_prefix_with_for():
    assert extract_business_name("Business Plan for Howe Gold-link Liberia\nExecutive Summary\n") == "Howe Gold-link Liberia"


def test_title_suffix():
    assert extract_business_name("FAMILY TREE Business Plan\nExecutive Summary\n") == "Family Tree"


def test_bare_title_line():
    text = "Howe Gold-link Liberia\nCamp Johnson Road, Clay Street\nMonrovia, Liberia\nBusiness Plan\n"
    assert extract_business_name(text) == "Howe Gold-link Liberia"


def test_boilerplate_before_the_name_is_skipped():
    # Same template as above, but the entrant deleted the label line.
    text = ("BYU Management Society\nAfrica Business Plan Competition\n2026\n"
            "PRINCESS CHIDIEBUBE FASHION\nENTERPRISES\nProblem or Customer Pain Point\n")
    assert extract_business_name(text) == "Princess Chidiebube Fashion Enterprises"


def test_deck_title_split_across_two_text_boxes():
    text = "PROJECT PROPOSAL  ·  2024\nLIGHT REACH\nLIBERIA\nLighting Liberia, Empowering Lives\n"
    assert extract_business_name(text) == "Light Reach Liberia"


def test_continuation_does_not_absorb_mixed_case_body_text():
    text = "ACME VENTURES\nWe sell affordable solar lanterns to rural households.\n"
    assert extract_business_name(text) == "Acme Ventures"


def test_pipeline_slide_markers_are_not_the_business_name():
    # extract_pptx_text prefixes each slide "[Slide N]". That is furniture from our
    # own extractor, not content — without skipping it, every .pptx plan was named
    # "[Slide 1]" (found by running the real adapters over the corpus).
    text = "[Slide 1]\nPROJECT PROPOSAL  ·  2024\nLIGHT REACH\nLIBERIA\nLighting Liberia\n"
    assert extract_business_name(text) == "Light Reach Liberia"


def test_marker_alone_yields_nothing():
    assert extract_business_name("[Slide 1]\n[Slide 2]\n") == ""


def test_bracketed_placeholder_rejected():
    assert extract_business_name("[Your business name here]\n") == ""


# --- PDF text layer with no spaces ----------------------------------------- #

def test_despaced_pdf_run():
    # pypdf can return a whole slide as one token with every space lost.
    text = ("BUSINESSWORKPLANBusinessNameKindnessMobilePhoneTradingandRefurbishment"
            "EnterpriseOwnerRolandKindnessGaysueLocationPaynesville\n")
    got = extract_business_name(text)
    assert got.startswith("Kindness Mobile Phone")
    assert "Enterprise" in got
    assert "Owner" not in got and "Roland" not in got   # cut at the next field
    # The glued "Tradingand" survives: splitting lowercase runs needs a dictionary,
    # and guessing would turn "Brand" into "Br and".
    assert got.replace(" ", "") == "KindnessMobilePhoneTradingandRefurbishmentEnterprise"


# --- Negative cases: "" is the right answer -------------------------------- #

def test_prose_narrative_yields_nothing():
    # A real corpus plan opens like this and never states a business name.
    text = ("My name is patience comfort kollie. I was born February 4,1997 in fendell.\n"
            "I grew up with my uncle in harbel, Division 45, Firestone Liberia.\n")
    assert extract_business_name(text) == ""


def test_empty_and_whitespace():
    assert extract_business_name("") == ""
    assert extract_business_name("   \n\n  \t \n") == ""
    assert extract_business_name(None) == ""


def test_only_boilerplate_yields_nothing():
    assert extract_business_name("BYU Management Society\nAfrica Business Plan Competition\n2026\n") == ""


def test_a_sentence_is_not_a_name():
    assert extract_business_name("This business will sell solar lanterns to rural households.\n") == ""


def test_an_overlong_line_is_not_a_name():
    assert extract_business_name("Acme Ventures Limited Incorporated Holdings Group International Trading Company Worldwide\n") == ""


def test_headings_with_bullet_punctuation_rejected():
    assert extract_business_name("• Acme Ventures\n") == ""


def test_a_bare_year_is_not_a_name():
    assert extract_business_name("2026\n2025\n") == ""


# --- Caps softening ------------------------------------------------------- #

def test_shouted_name_is_title_cased():
    assert extract_business_name("FROST FLOW ICE VENTURES\nLocation: Kakata\n") == "Frost Flow Ice Ventures"


def test_mixed_case_name_is_left_alone():
    assert extract_business_name("Howe Gold-link Liberia\nMonrovia, Liberia\n") == "Howe Gold-link Liberia"


def test_vowel_free_acronyms_survive_caps_softening():
    assert extract_business_name("MTN NIGERIA VENTURES\nLagos\n") == "MTN Nigeria Ventures"


def test_single_letter_tokens_survive():
    assert extract_business_name("G & V SALON\nKakata, Margibi County\n") == "G & V Salon"


# --- Reported provenance -------------------------------------------------- #

def test_source_is_reported_for_the_agent_log():
    got = extract("Business Name: Acme Ventures\n")
    assert got.name == "Acme Ventures"
    assert "label" in got.source
    assert bool(got) is True


def test_falsey_when_nothing_found():
    assert not extract("2026\n")
