"""First-round eligibility / disqualifier screen for the Business Plan Grader.

The BYUMS competition excludes whole business categories (MLM, franchises,
get-rich schemes...), requires deliverables (license, bank account), requires
English, and asks judges to flag suspected AI-generated entries. A plain scorer
would rank an ineligible plan #1; this screen catches that BEFORE ranking.

Design (from the engineering review):
- Text-inferable checks only (Phase 1a). Image/video-based DQ (face visible,
  video length, license/bank images) is deferred to the multimodal phase.
- The screen FLAGS FOR REVIEW; it never auto-rejects. Keyword heuristics have
  false positives (a plan may say "unlike a pyramid scheme, we..."), so a hit
  means needs_review with the matched reason, and a human decides. Status is
  therefore either "eligible" or "needs_review" — never automatic "ineligible".
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

from backend.src.models import ELIGIBILITY_ELIGIBLE, ELIGIBILITY_NEEDS_REVIEW


# Excluded business types (Handbook: Business Type Exclusions / Automatic Disqualifiers).
# label -> phrases that suggest it. Kept lowercase; matched as substrings/word-ish.
EXCLUDED_BUSINESS_TYPES = {
    "multi-level marketing / network marketing": [
        "multi-level marketing", "multi level marketing", "mlm", "network marketing",
    ],
    "pyramid scheme": ["pyramid scheme", "pyramid schemes"],
    "get-rich-quick scheme": ["get rich quick", "get-rich-quick", "get rich fast", "double your money"],
    "buyout": ["buyout", "buy-out"],
    "real estate syndication": ["real estate syndication", "real-estate syndication"],
    "tax shelter": ["tax shelter"],
    "franchise": ["franchise", "franchising"],
    "distribution licensing agreement": ["licensing agreement for distribution", "distribution licensing"],
}

# Terms that suggest a required deliverable is present in the TEXT. Absence is a
# weak signal (the deliverable is usually an image at the end of the deck), so it
# is advisory only and does NOT flip the status.
LICENSE_TERMS = ["business license", "license", "licence", "proof of registration",
                 "registered business", "registration number", "cac", "incorporation"]
BANK_TERMS = ["bank account", "bank statement", "business bank", "account number"]

# Common English function words used for a low-false-positive language check.
ENGLISH_STOPWORDS = {
    "the", "and", "of", "to", "for", "with", "we", "our", "is", "are", "this",
    "that", "in", "on", "will", "business", "market", "customers", "revenue",
}

# Conservative tells of AI-generated content. Robust detection is future work;
# this catches only obvious giveaways to keep false positives near zero.
AI_TELL_PHRASES = [
    "as an ai language model", "as a large language model", "as an ai model",
    "i cannot provide", "i'm unable to", "i am unable to",
    "certainly! here", "certainly, here", "here is a business plan for you",
    "here's a business plan for you", "sure! here", "sure, here is",
    "as requested, here", "i hope this helps", "let me know if you need",
]

_WORD_RE = re.compile(r"[a-zA-Z]+")


def _context_snippet(text: str, phrase: str, width: int = 45) -> str:
    """Return a short context window around the first occurrence of phrase, so a
    human reviewer can see WHY a plan was flagged (e.g. 'sub-franchise system'
    is a growth-model mention, not a franchise business)."""
    low = text.lower()
    idx = low.find(phrase)
    if idx == -1:
        return ""
    start = max(0, idx - width)
    end = min(len(text), idx + len(phrase) + width)
    snippet = " ".join(text[start:end].split())
    return f"...{snippet}..."


@dataclass
class EligibilityResult:
    status: str                              # eligible | needs_review
    reasons: List[str] = field(default_factory=list)          # serious -> drive status
    advisory_notes: List[str] = field(default_factory=list)   # informational only
    ai_content_flag: bool = False

    def all_reasons(self) -> List[str]:
        """Serious reasons plus advisory notes (prefixed), for surfacing in the API."""
        return list(self.reasons) + [f"(advisory) {n}" for n in self.advisory_notes]


def looks_english(text: str) -> bool:
    """Low-false-positive English check: True unless we have enough words AND
    almost none are common English function words. Short text -> assume English
    (insufficient evidence to flag)."""
    tokens = [t.lower() for t in _WORD_RE.findall(text or "")]
    if len(tokens) < 5:
        return True  # too little to judge; don't flag
    hits = sum(1 for t in tokens[:200] if t in ENGLISH_STOPWORDS)
    return hits >= 2


def detect_ai_content(text: str) -> bool:
    """Conservative: flag only obvious AI tells."""
    low = (text or "").lower()
    return any(phrase in low for phrase in AI_TELL_PHRASES)


def _mentions_any(text_lower: str, terms: List[str]) -> bool:
    return any(term in text_lower for term in terms)


def screen_eligibility(plan_text: str) -> EligibilityResult:
    """Run the text-inferable eligibility screen over a plan's text."""
    text = plan_text or ""
    low = text.lower()
    reasons: List[str] = []
    advisory: List[str] = []

    # 1. Excluded business types (serious -> needs_review). Keyword heuristics have
    # false positives (a plan may only MENTION a franchise), so we flag for human
    # review with the surrounding context and an explicit "verify IS vs mentions" note.
    for label, phrases in EXCLUDED_BUSINESS_TYPES.items():
        matched = [p for p in phrases if p in low]
        if matched:
            snippet = _context_snippet(text, matched[0])
            reason = f"Possible excluded business type: {label} (matched '{matched[0]}'"
            if snippet:
                reason += f" in: {snippet}"
            reason += "). Verify the business IS this type, not merely mentions it."
            reasons.append(reason)

    # 2. Language requirement (serious -> needs_review)
    if text.strip() and not looks_english(text):
        reasons.append("Submission may not be in English (competition requires English).")

    # 3. Required deliverables (advisory only — usually images at end of deck)
    if text.strip():
        if not _mentions_any(low, LICENSE_TERMS):
            advisory.append("No business license/registration mentioned in text — verify in slides/images.")
        if not _mentions_any(low, BANK_TERMS):
            advisory.append("No business bank account mentioned in text — verify in slides/images.")

    # 4. Suspected AI-generated content (the org asks judges to flag this)
    ai_flag = detect_ai_content(text)
    if ai_flag:
        reasons.append("Suspected AI-generated content (obvious tell present).")

    status = ELIGIBILITY_NEEDS_REVIEW if reasons else ELIGIBILITY_ELIGIBLE
    return EligibilityResult(status=status, reasons=reasons, advisory_notes=advisory, ai_content_flag=ai_flag)
