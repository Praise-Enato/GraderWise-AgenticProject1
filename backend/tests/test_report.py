"""Tests for the downloadable PDF report — specifically that it is headed by the
business name.

A report you cannot attribute is useless to a judge, so the heading rules are
pinned here: the business name is the H1, the generic document kind is only a
fallback, and accented names must stay readable rather than degrade to "???"
(fpdf2 core fonts are latin-1).
"""
import pytest

pytest.importorskip("fpdf", reason="fpdf2 not installed (see requirements-dev.txt)")

from backend.src.models import CriterionAssessment, GradeResult
from backend.src.report import (
    _DOC_KIND,
    _ascii,
    _heading,
    _new_pdf,
    _subtitle_parts,
    build_report_pdf,
)

RUBRIC_LABEL = "BYUMS Competition (80)"


def _result(n_criteria: int = 4) -> GradeResult:
    assessments = [
        CriterionAssessment(
            criteria_index=i,
            criteria_name=f"Section {i // 2} - Criterion {i}",
            awarded_points=float(i % 3),
            max_points=5.0,
            reason="Reason text for this criterion.",
        )
        for i in range(n_criteria)
    ]
    return GradeResult(
        score=sum(a.awarded_points for a in assessments),
        feedback="**Strong** opening — tighten the financials.",
        citations=[],
        thinking_process=["retrieve", "grade"],
        confidence_score=0.8,
        assessments=assessments,
        graded_ok=True,
        eligibility_status="eligible",
        dq_reasons=[],
        ai_content_flag=False,
    )


# --- Heading rules --------------------------------------------------------- #

def test_business_name_is_the_heading():
    assert _heading("Jideofor Enterprise") == "Jideofor Enterprise"


@pytest.mark.parametrize("blank", ["", "   ", None])
def test_heading_falls_back_to_the_document_kind(blank):
    assert _heading(blank) == _DOC_KIND


def test_subtitle_carries_the_document_kind_when_the_heading_is_a_business():
    parts = _subtitle_parts("Jideofor Enterprise", RUBRIC_LABEL)
    assert parts[0] == _DOC_KIND
    assert RUBRIC_LABEL in parts


def test_subtitle_does_not_repeat_the_document_kind_when_unnamed():
    # Heading is already "Business Plan Evaluation" — saying it twice reads as a bug.
    assert _DOC_KIND not in _subtitle_parts("", RUBRIC_LABEL)


# --- Latin-1 safety of the heading ----------------------------------------- #

def test_accented_names_transliterate_instead_of_becoming_question_marks():
    # A heading of "???un" defeats the point of naming the business.
    assert _ascii("Ọ̀ṣun Agro–Tech “Naija” Ltd") == 'Osun Agro-Tech "Naija" Ltd'
    assert "?" not in _ascii("Café Zoë Ürban Süd")


# --- Rendered document ----------------------------------------------------- #

def test_pdf_metadata_title_names_the_business():
    pdf = build_report_pdf(_result(), team_name="Jideofor Enterprise", rubric_label=RUBRIC_LABEL)
    assert pdf.startswith(b"%PDF")
    assert b"/Title (Jideofor Enterprise - Business Plan Evaluation)" in pdf


def test_pdf_metadata_title_falls_back_when_unnamed():
    pdf = build_report_pdf(_result(), team_name="", rubric_label=RUBRIC_LABEL)
    assert pdf.startswith(b"%PDF")
    assert f"/Title ({_DOC_KIND})".encode() in pdf


def test_footer_label_is_the_business_name():
    assert _new_pdf("Jideofor Enterprise").footer_label == "Jideofor Enterprise"
    assert _new_pdf("").footer_label == ""


@pytest.mark.parametrize("name", [
    "",
    "Jideofor Enterprise",
    "Ọ̀ṣun Agro–Tech “Naija” Ltd",
    "FrostFlow Ice Ventures & Cold-Chain Logistics Cooperative of Greater Enugu Limited",
])
def test_report_builds_for_any_business_name(name):
    # A long name must wrap, not overflow or raise; the builder never 500s.
    pdf = build_report_pdf(_result(40), team_name=name, rubric_label=RUBRIC_LABEL)
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 500
