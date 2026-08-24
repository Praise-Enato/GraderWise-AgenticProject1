"""Read the business name out of the plan document itself.

The name is what identifies a grade everywhere it surfaces — the on-screen
heading, the PDF report header, the History row. Deriving it from the uploaded
file name is wrong often enough to be useless ("Copy of Africa Business Plan
Competition - 2026  (1).pdf" names the competition, not the business), so it is
read from the plan's own text.

Deliberately deterministic (stdlib only, no model call), for the same reason the
Judge and the score summation are: a name is a fact printed in the document, not
something to infer. It costs nothing, adds no latency, and is unit-testable
against real plans.

Tuned against the real submission corpus, which is messier than it sounds:
  - The BYUMS slide template ships a literal "YOUR BUSINESS NAME" label; some
    entrants leave the label in above their name, others delete it.
  - Prose documents bury the name in "Business Name: X" inside the exec summary.
  - Titles arrive as "BUSINESS PLAN: X", "X Business Plan", or a bare line.
  - Deck titles split across two text boxes ("LIGHT REACH" / "LIBERIA").
  - PDF extraction sometimes loses every space in a run
    ("BusinessNameKindnessMobilePhoneTradingandRefurbishmentEnterpriseOwner...").

PRECISION OVER RECALL. A confidently wrong name on a report is worse than no
name: a judge who sees a blank falls back on the file name and knows to check,
whereas a plausible wrong name is believed. So every candidate must pass
`_plausible`, and anything doubtful yields "" for the caller to fall back on.
Some plans genuinely never state their name (one corpus plan opens "My name is
..." and is a personal narrative) — "" is the correct answer there.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional

# Only the front of the document is searched: a business plan names itself on the
# title page / first slide / exec summary, and scanning further only invites
# false positives from body prose.
_SEARCH_CHARS = 4000
_SEARCH_LINES = 40

# Longest plausible name, in words and characters. A "name" of 12 words is a
# sentence that happened to sit on the title page.
_MAX_WORDS = 8
_MAX_CHARS = 80

# Lines that are document furniture, never the business name. Compared against a
# normalized (lowercased, punctuation-stripped) form of the line.
_BOILERPLATE = {
    "byu management society", "africa business plan competition",
    "business plan", "the business plan", "business work plan", "work plan",
    "business proposal", "project proposal", "proposal", "presented by",
    "your business name", "insert business name", "company name",
    "executive summary", "confidential", "confidential business plan",
    "document type", "table of contents", "contents", "introduction",
    "overview", "company overview", "company profile", "about us",
    "mission statement", "vision statement", "problem", "the problem",
}

# Labels that introduce the name. Matched case-insensitively at a line start,
# optionally followed by a separator; the value is the rest of the line, or the
# next usable line when the label sits alone (the BYUMS template's own layout).
_NAME_LABELS = [
    "your business name", "insert business name",
    "business/company name", "business / company name",
    "name of the business", "name of business", "name of the company",
    "name of company", "business name", "company name", "enterprise name",
    "venture name", "trading name", "trading as",
]

# Field labels that terminate a name value. Needed because a de-spaced PDF run
# glues the next field straight onto the name
# ("...RefurbishmentEnterpriseOwnerRoland..." -> stop at "Owner").
#
# Kept deliberately SHORT. Every entry here can also truncate a legitimate name,
# so a word only qualifies if it is common as a form label and rare inside a
# business name. "Phone", "Vision", "City", "Industry", "Mission" and "Location"
# were all tried and removed: they cut real names in the corpus ("Kindness Mobile
# Phone Trading..." became "Kindness Mobile"), and dropping them costs nothing
# because an earlier label ("Owner") already ends the run.
_VALUE_STOPWORDS = [
    "owner", "proprietor", "address", "contact", "email",
    "business type", "type of business", "business goal",
    "executive summary", "prepared by", "submitted by",
]

# "BUSINESS PLAN: X" / "BUSINESS PLAN FOR X"
_TITLE_PREFIX_RE = re.compile(
    r"^\s*(?:a\s+)?business\s+(?:plan|proposal)\s*(?::|-|–|—|\bfor\b)\s*(.+)$",
    re.IGNORECASE,
)
# "X Business Plan" — only a document-type trailing word is stripped, so a real
# name ending in "... Business Services" is left intact.
_TITLE_SUFFIX_RE = re.compile(
    r"^(.+?)[\s\-–—]+business\s+(?:plan|proposal|outline|document|report|summary)\s*$",
    re.IGNORECASE,
)

# Prose openings — a title page never starts this way.
_PROSE_START_RE = re.compile(
    r"^\s*(?:i|we|my|our|this|these|the\s+purpose|it\s|there\s|in\s+this)\b",
    re.IGNORECASE,
)

_YEAR_RE = re.compile(r"^\s*(?:19|20)\d{2}\s*$")
# Location markers the extractors themselves insert ("[Slide 1]" from
# extract_pptx_text) — furniture from OUR pipeline, not content from the document.
# Without this a .pptx plan is named "[Slide 1]".
_MARKER_RE = re.compile(r"^\[\s*(?:slide|page)\s*\d+\s*\]$", re.IGNORECASE)
_VOWEL_RE = re.compile(r"[AEIOUaeiou]")


@dataclass
class ExtractedName:
    """The name and how it was found — `source` is surfaced in the agent log so a
    judge can see why the grader named the business what it did."""
    name: str = ""
    source: str = ""

    def __bool__(self) -> bool:
        return bool(self.name)


def _normalize(s: str) -> str:
    """Lowercase, strip punctuation/extra space — for boilerplate comparison."""
    return re.sub(r"[^a-z0-9 ]+", " ", (s or "").lower()).strip()


def _collapse(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def _despace(line: str) -> str:
    """Re-split a run that lost all its spaces during PDF text extraction.

    A slide or table can come back as one long token
    ("BusinessNameKindnessMobilePhoneTrading..."); inserting a space at each
    lower->upper boundary makes the label patterns above able to see it. Only
    applied to long, space-free lines so ordinary text is untouched.
    """
    if " " in line or len(line) < 25:
        return line
    return re.sub(r"(?<=[a-z])(?=[A-Z])", " ", line)


def _usable_lines(text: str) -> List[str]:
    """The first handful of non-empty lines from the front of the document, with
    space-less PDF runs re-split."""
    head = (text or "")[:_SEARCH_CHARS]
    out: List[str] = []
    for raw in head.splitlines():
        line = _collapse(_despace(raw.strip()))
        if line and not _MARKER_RE.match(line):
            out.append(line)
        if len(out) >= _SEARCH_LINES:
            break
    return out


def _is_boilerplate(line: str) -> bool:
    n = _normalize(line)
    if not n or n in _BOILERPLATE:
        return True
    if _YEAR_RE.match(line.strip()):
        return True
    # "PROJECT PROPOSAL · 2024", "BUSINESS PLAN 2026" — furniture plus a year.
    stripped = re.sub(r"\b(?:19|20)\d{2}\b", "", n).strip()
    return bool(stripped) and stripped in _BOILERPLATE


def _truncate_at_stopword(value: str) -> str:
    """Cut a name value at the next field label (see _VALUE_STOPWORDS)."""
    low = value.lower()
    cut = len(value)
    for word in _VALUE_STOPWORDS:
        # Word-boundary search so "Ownership" doesn't trip "owner"... but "Owner"
        # glued to the name by _despace is preceded by a space, so \b is enough.
        for m in re.finditer(r"\b" + re.escape(word) + r"\b", low):
            if 0 < m.start() < cut:
                cut = m.start()
    return value[:cut].strip(" :–-—,;")


def _plausible(candidate: str) -> bool:
    """Reject anything that is not credibly a business name. This is the gate that
    keeps a wrong name off a report — err towards returning False."""
    c = _collapse(candidate).strip(" \t:;,.-–—\"'")
    if not c or len(c) < 2 or len(c) > _MAX_CHARS:
        return False
    words = c.split()
    if len(words) > _MAX_WORDS:
        return False
    if len(re.findall(r"[A-Za-z]", c)) < 2:
        return False
    if _is_boilerplate(c):
        return False
    if _PROSE_START_RE.match(c):
        return False
    # A sentence, not a name: internal sentence punctuation, or a terminal stop
    # after several words.
    if re.search(r"[.!?]\s+\S", c) or re.search(r"[;:]", c):
        return False
    if c.endswith((".", "!", "?")) and len(words) > 3:
        return False
    # Bullet/heading punctuation that never appears in a name.
    if re.search(r"[•·\|\*]", c):
        return False
    # Brackets mean a marker ("[Slide 1]") or an unfilled template placeholder
    # ("[Your business name here]") — never a real name. Parentheses are allowed:
    # "Acme (Nigeria) Ltd" is a legitimate name.
    if re.search(r"[\[\]<>{}]", c):
        return False
    return True


def _clean(candidate: str) -> str:
    return _collapse(candidate).strip(" \t:;,.-–—\"'")


def _soften_caps(name: str) -> str:
    """Title-case a SHOUTED name so it reads as a heading.

    Entrants type title slides in caps ("JIDEOFOR RAYMOND ENTERPRISE"); rendered
    as a report H1 that shouts. Tokens with no vowel are left alone so genuine
    acronyms survive (MTN, GTB, LTD). A vowel-bearing acronym is the known
    limitation — "BYU" would become "Byu" — which is why nothing here runs unless
    the whole candidate is uppercase.
    """
    if not name or re.search(r"[a-z]", name):
        return name
    out: List[str] = []
    for tok in name.split(" "):
        letters = re.sub(r"[^A-Za-z]", "", tok)
        if len(letters) <= 1 or not _VOWEL_RE.search(letters):
            out.append(tok)          # "G", "&", "MTN", "LTD"
        else:
            out.append(tok[:1].upper() + tok[1:].lower())
        # Note: only the first letter is capitalized, so "O'BRIEN" -> "O'brien".
    return " ".join(out)


def _finalize(candidate: str, source: str) -> Optional[ExtractedName]:
    c = _clean(candidate)
    if not _plausible(c):
        return None
    return ExtractedName(name=_soften_caps(c), source=source)


def _join_continuation(lines: List[str], i: int) -> str:
    """Join a title split across consecutive text boxes / lines.

    A deck title is often two shapes ("LIGHT REACH" + "LIBERIA") or wraps
    ("PRINCESS CHIDIEBUBE FASHION" + "ENTERPRISES"). Only ALL-CAPS short
    neighbours are joined, and at most one, so body text is never absorbed.
    """
    first = lines[i]
    if re.search(r"[a-z]", first) or len(first.split()) > 4:
        return first
    if i + 1 >= len(lines):
        return first
    nxt = lines[i + 1]
    if (not re.search(r"[a-z]", nxt) and len(nxt.split()) <= 3
            and not _is_boilerplate(nxt) and not _YEAR_RE.match(nxt)):
        return f"{first} {nxt}"
    return first


def extract(text: str) -> ExtractedName:
    """Best-effort business name from the plan's own text.

    Returns an empty ExtractedName when the document does not state a name
    credibly — the caller then falls back (typed name, then file name).
    """
    lines = _usable_lines(text)
    if not lines:
        return ExtractedName()

    # 1. An explicit label wins: the entrant told us outright.
    for i, line in enumerate(lines):
        low = line.lower()
        for label in _NAME_LABELS:
            if not low.startswith(label):
                continue
            rest = line[len(label):].lstrip(" :–-—\t")
            if rest:
                got = _finalize(_truncate_at_stopword(rest), f"label '{label}'")
                if got:
                    return got
            # Label alone on its line (the BYUMS template) — value is below it.
            for nxt in lines[i + 1:i + 3]:
                if _is_boilerplate(nxt):
                    continue
                got = _finalize(_join_continuation([nxt], 0), f"label '{label}' (next line)")
                if got:
                    return got
            break

    # 1b. The same labels, but anywhere in the line. Needed for a de-spaced PDF
    # run, where the label lands mid-line ("BUSINESSWORKPLANBusiness Name Kind...").
    # Looser, so it runs only after the line-start pass and only near the top.
    for line in lines[:12]:
        low = line.lower()
        for label in _NAME_LABELS:
            # No leading \b: the whole point of this pass is a label glued to the
            # text before it ("BUSINESSWORKPLANBusiness Name ..."), where a
            # word-boundary assertion cannot match.
            m = re.search(re.escape(label) + r"\b", low)
            if not m:
                continue
            rest = line[m.end():].lstrip(" :–-—\t")
            got = _finalize(_truncate_at_stopword(rest), f"label '{label}' (mid-line)")
            if got:
                return got

    # 2. A self-describing title: "BUSINESS PLAN: X" or "X Business Plan".
    for line in lines[:12]:
        m = _TITLE_PREFIX_RE.match(line)
        if m:
            got = _finalize(m.group(1), "title prefix")
            if got:
                return got
        m = _TITLE_SUFFIX_RE.match(line)
        if m:
            got = _finalize(m.group(1), "title suffix")
            if got:
                return got

    # 3. The first line that looks like a title rather than furniture or prose.
    for i, line in enumerate(lines[:12]):
        if _is_boilerplate(line):
            continue
        got = _finalize(_join_continuation(lines, i), "title line")
        if got:
            return got

    return ExtractedName()


def extract_business_name(text: str) -> str:
    """`extract`, as a plain string ("" when nothing credible was found)."""
    return extract(text).name
