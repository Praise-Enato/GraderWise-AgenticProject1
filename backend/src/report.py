"""Server-side PDF report for a graded business plan.

Pure-Python (fpdf2) so it runs anywhere the backend does; the SAME builder feeds
both the /grade/report download and the emailed attachment. Everything is derived
from the GradeResult, so it is generic across rubrics — nothing here is
BYUMS-competition-specific.

Bulletproof by design: every section is guarded, and if the full render fails for
any reason a minimal valid PDF is returned instead — the endpoint never 500s on
report content.
"""
from __future__ import annotations

import re
import traceback
import unicodedata
from datetime import date
from typing import Callable, Dict, List, Optional, Tuple

from fpdf import FPDF

from backend.src.models import GradeResult


def _section_of(name: str) -> str:
    return name.split(" - ")[0].strip() if " - " in name else "Other"


def _fmt(n: float) -> str:
    r = round(float(n or 0), 2)
    return str(int(r)) if r == int(r) else str(r)


# fpdf2 core fonts are latin-1 only; map common unicode punctuation to ASCII and
# drop anything else so the report never crashes on a smart quote, dash, or bullet.
_UNI = {
    "‘": "'", "’": "'", "“": '"', "”": '"',
    "–": "-", "—": "-", "…": "...", "•": "-",
    " ": " ", "→": "->",
}


def _ascii(s: Optional[str]) -> str:
    if not s:
        return ""
    for k, v in _UNI.items():
        s = s.replace(k, v)
    s = re.sub(r"[*_`#]+", "", s)  # drop markdown emphasis markers
    # Strip combining accents rather than let them become "?" — the business name
    # is the report heading, and African/Yoruba names carry diacritics
    # ("Ọ̀ṣun" -> "Osun" reads; "???un" does not).
    s = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
    return s.encode("latin-1", "replace").decode("latin-1")


# Colours (R, G, B) reused from the UI's green/amber/red language.
_GREEN = (16, 122, 87)
_AMBER = (180, 120, 10)
_RED = (200, 55, 55)
_INK = (30, 41, 59)
_MUTE = (110, 120, 135)


def _pct_color(pct: float) -> Tuple[int, int, int]:
    if pct >= 80:
        return _GREEN
    if pct >= 50:
        return _AMBER
    return _RED


def _award_color(awarded: float, mx: float) -> Tuple[int, int, int]:
    if mx > 0 and awarded >= mx:
        return _GREEN
    if awarded <= 0:
        return _RED
    return _AMBER


_DOC_KIND = "Business Plan Evaluation"


def _heading(team_name: Optional[str]) -> str:
    """The report's H1: the business name, or the generic document kind when the
    judge graded without naming the business."""
    return _ascii(team_name).strip() or _DOC_KIND


def _subtitle_parts(team_name: Optional[str], rubric_label: Optional[str]) -> List[str]:
    """Meta line under the heading. Carries the document kind only when the
    heading is the business name — otherwise it would just repeat it."""
    parts: List[str] = []
    if _heading(team_name) != _DOC_KIND:
        parts.append(_DOC_KIND)
    parts += [p for p in [_ascii(rubric_label).strip(), date.today().isoformat()] if p]
    return parts


def _grouped_sections(result: GradeResult) -> List[Tuple[str, float, float]]:
    """[(section, awarded_sum, max_sum)] preserving first-seen order."""
    order: List[str] = []
    agg: Dict[str, List[float]] = {}
    for a in result.assessments or []:
        sec = _section_of(a.criteria_name)
        if sec not in agg:
            agg[sec] = [0.0, 0.0]
            order.append(sec)
        agg[sec][0] += a.awarded_points
        agg[sec][1] += a.max_points
    return [(s, agg[s][0], agg[s][1]) for s in order]


class _Report(FPDF):
    # Business name repeated in the page footer, so page 4 of a report still
    # says whose plan it is. Set before add_page(); "" falls back to no label.
    footer_label: str = ""

    def header(self):  # noqa: D401 - fpdf hook
        pass

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", size=7)
        self.set_text_color(*_MUTE)
        label = self.footer_label or ""
        if len(label) > 60:
            label = label[:57].rstrip(" -") + "..."   # a very long name can't push the page number off
        prefix = f"{label} - " if label else ""
        self.cell(0, 6, f"{prefix}GradeWise - page {self.page_no()}", align="C")


def _new_pdf(footer_label: str = "") -> _Report:
    pdf = _Report(format="A4", unit="mm")
    pdf.footer_label = _ascii(footer_label).strip()
    pdf.set_auto_page_break(auto=True, margin=15)
    # Document title (what a PDF viewer shows in its title bar / tab).
    pdf.set_title(f"{pdf.footer_label} - {_DOC_KIND}" if pdf.footer_label else _DOC_KIND)
    pdf.add_page()
    return pdf


def _guard(section: str, fn: Callable[[], None]) -> None:
    """Render one section; on any error, log and skip it rather than failing the
    whole PDF — a single odd character or field can't 500 the download."""
    try:
        fn()
    except Exception as e:
        print(f"WARN: report section '{section}' skipped: {type(e).__name__}: {e}")


def build_report_pdf(result: GradeResult, team_name: str = "", rubric_label: str = "") -> bytes:
    """Render a GradeResult to PDF bytes. Never raises on content: the full build
    is attempted, and any unexpected failure falls back to a minimal valid PDF."""
    try:
        return _build(result, team_name, rubric_label)
    except Exception:
        print("WARN: full PDF build failed; returning minimal report:\n" + traceback.format_exc())
        try:
            return _build_minimal(result, team_name, rubric_label)
        except Exception:
            # Absolute last resort — an empty but valid one-line PDF.
            pdf = _new_pdf(team_name)
            pdf.set_font("Helvetica", size=12)
            pdf.cell(0, 10, _heading(team_name))
            return bytes(pdf.output())


def _build_minimal(result: GradeResult, team_name: str, rubric_label: str) -> bytes:
    total = sum(a.max_points for a in (result.assessments or []))
    pdf = _new_pdf(team_name)
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(*_INK)
    pdf.multi_cell(0, 9, _heading(team_name), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=10)
    pdf.set_text_color(*_MUTE)
    pdf.cell(0, 6, " | ".join(_subtitle_parts(team_name, rubric_label)), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(*_INK)
    pdf.cell(0, 12, f"{_fmt(result.score)} / {_fmt(total)}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=10)
    pdf.set_text_color(*_MUTE)
    pdf.multi_cell(0, 5, _ascii(
        "The detailed breakdown could not be rendered in this PDF. "
        "See the on-screen results for the full section-by-section scores."
    ), new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())


def _build(result: GradeResult, team_name: str, rubric_label: str) -> bytes:
    total = sum(a.max_points for a in (result.assessments or []))
    score = float(result.score or 0.0)
    pct = (score / total * 100) if total > 0 else 0.0

    pdf = _new_pdf(team_name)
    W = pdf.epw  # effective page width

    def title():
        # The business name IS the report heading — a downloaded PDF has to say
        # whose plan it is without the reader guessing from the file name.
        pdf.set_font("Helvetica", "B", 18)
        pdf.set_text_color(*_INK)
        pdf.multi_cell(0, 9, _heading(team_name), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", size=10)
        pdf.set_text_color(*_MUTE)
        pdf.cell(0, 6, " | ".join(_subtitle_parts(team_name, rubric_label)), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)

    def score_band():
        pdf.set_fill_color(245, 247, 250)
        y0 = pdf.get_y()
        pdf.rect(pdf.l_margin, y0, W, 18, style="F")
        pdf.set_xy(pdf.l_margin + 4, y0 + 4)
        pdf.set_font("Helvetica", "B", 22)
        pdf.set_text_color(*_pct_color(pct))
        pdf.cell(60, 10, f"{_fmt(score)} / {_fmt(total)}")
        pdf.set_xy(pdf.l_margin + 4, y0 + 4)
        pdf.cell(W - 8, 10, f"{round(pct)}%", align="R")
        # Reset X too — the right-aligned cell left the cursor at the right edge,
        # which would starve the next section of horizontal space.
        pdf.set_xy(pdf.l_margin, y0 + 20)

    def eligibility():
        elig = (result.eligibility_status or "eligible").replace("_", " ")
        pdf.set_font("Helvetica", size=9)
        pdf.set_text_color(*(_GREEN if elig == "eligible" else _AMBER))
        flag = "  [suspected AI content]" if result.ai_content_flag else ""
        pdf.cell(0, 6, _ascii(f"Eligibility: {elig}{flag}"), new_x="LMARGIN", new_y="NEXT")
        for r in (result.dq_reasons or []):
            pdf.set_text_color(*_MUTE)
            pdf.multi_cell(0, 5, _ascii(f"  - {r}"), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

    def scorecard():
        sections = _grouped_sections(result)
        if not sections:
            return
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(*_INK)
        pdf.cell(0, 8, "Scorecard", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", size=10)
        for sec, aw, mx in sections:
            spct = (aw / mx * 100) if mx > 0 else 0.0
            pdf.set_text_color(*_INK)
            pdf.cell(W - 40, 6, _ascii(sec))
            pdf.set_text_color(*_pct_color(spct))
            pdf.cell(40, 6, f"{_fmt(aw)} / {_fmt(mx)}   ({round(spct)}%)", align="R",
                     new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)

    def weak():
        items = sorted(
            [a for a in (result.assessments or []) if a.awarded_points < a.max_points],
            key=lambda a: (a.max_points - a.awarded_points), reverse=True,
        )
        if not items:
            return
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(*_INK)
        pdf.cell(0, 8, "Where points were lost", new_x="LMARGIN", new_y="NEXT")
        for a in items:
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(*_award_color(a.awarded_points, a.max_points))
            pdf.cell(W - 30, 6, _ascii(a.criteria_name))
            pdf.cell(30, 6, f"{_fmt(a.awarded_points)} / {_fmt(a.max_points)}", align="R",
                     new_x="LMARGIN", new_y="NEXT")
            if a.reason:
                pdf.set_font("Helvetica", size=9)
                pdf.set_text_color(*_MUTE)
                pdf.multi_cell(0, 5, _ascii(a.reason), new_x="LMARGIN", new_y="NEXT")
            pdf.ln(1)
        pdf.ln(2)

    def feedback():
        if not result.feedback:
            return
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(*_INK)
        pdf.cell(0, 8, "Participant feedback", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", size=10)
        pdf.set_text_color(*_INK)
        pdf.multi_cell(0, 5, _ascii(result.feedback), new_x="LMARGIN", new_y="NEXT")

    title()
    _guard("score", score_band)
    _guard("eligibility", eligibility)
    _guard("scorecard", scorecard)
    _guard("weak", weak)
    _guard("feedback", feedback)
    return bytes(pdf.output())
