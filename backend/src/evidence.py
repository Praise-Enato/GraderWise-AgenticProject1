"""Evidence-quote validation for the Business Plan Grader.

The grader is asked to return, per criterion, the exact quote from the
submission that justifies its award. Before that quote is trusted (shown to a
judge as the highlighted "why", used to resolve a dispute) the pure-Python
Judge must confirm the quote is really in the submission — otherwise the grader
can hallucinate supporting text (OV#7 from the engineering review).

Exact substring matching is too brittle for real submissions:
  - OCR/PDF extraction hyphenates across line breaks ("micro-\\nfinance")
  - ligatures and smart quotes differ from what the model emits ("'" vs "'")
  - whitespace and case vary freely

So matching is done on a normalized form, with a fuzzy fallback (stdlib
difflib) that tolerates minor extraction drift while still rejecting quotes
that are simply not present. Pure module: stdlib only, unit-tested.
"""
from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher

# Smart quotes / dashes / ligatures the model or the PDF may disagree on.
_TRANSLATE = {
    "‘": "'", "’": "'", "‛": "'",       # single quotes
    "“": '"', "”": '"', "„": '"',       # double quotes
    "–": "-", "—": "-", "−": "-",        # en/em/minus dashes
    "ﬁ": "fi", "ﬂ": "fl",                     # common ligatures
    " ": " ",                                       # non-breaking space
}


def normalize(text: str) -> str:
    """Canonicalize text for tolerant comparison: strip accents/ligatures,
    unify quotes and dashes, de-hyphenate across line breaks, lowercase, and
    collapse all whitespace to single spaces."""
    if not text:
        return ""
    # De-hyphenate words split across a line break: "micro-\nfinance" -> "microfinance".
    text = re.sub(r"-\s*\n\s*", "", text)
    text = "".join(_TRANSLATE.get(ch, ch) for ch in text)
    # Decompose remaining ligatures/accents (NFKD) and drop combining marks.
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def evidence_supported(quote: str, submission: str, min_ratio: float = 0.85) -> bool:
    """True if `quote` is genuinely present in `submission`.

    A normalized exact substring is supported outright. Otherwise a fuzzy
    coverage check (fraction of the quote's characters matched contiguously
    against the submission, via difflib) must reach `min_ratio`. Empty or
    whitespace-only quotes are never supported — the grader gave no evidence.
    """
    q = normalize(quote)
    s = normalize(submission)
    if not q or not s:
        return False
    if q in s:
        return True
    matcher = SequenceMatcher(None, q, s, autojunk=False)
    matched = sum(block.size for block in matcher.get_matching_blocks())
    return (matched / len(q)) >= min_ratio
