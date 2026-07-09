"""Inter-rater (human ceiling) agreement for the reliability harness.

The engineering review's outside voice raised OV#3: AI-vs-human agreement is
meaningless without a human baseline. If the judges themselves only agree at
rho ~= 0.6, then an AI that agrees with the aggregate human score at 0.6 is
already AT the human ceiling, and "improving" past it just fits one rater's
idiosyncrasies. This module measures how much the human raters agree with each
other, so AI agreement (from validation.compute_agreement) can be read against
that ceiling.

Pure Python, stdlib only. Reuses the tie-aware spearman in
backend.src.validation (DRY) so there is one rank-correlation implementation.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Optional, Sequence

from backend.src.validation import spearman


def mean_pairwise_spearman(raters: Sequence[Sequence[float]]) -> Optional[float]:
    """Mean Spearman rank correlation across every pair of raters.

    `raters` is a list of score vectors, one per rater, each vector holding that
    rater's score for the same ordered list of items (raters[r][i] is rater r's
    score for item i). Returns the mean of all pairwise Spearman correlations,
    or None when it is undefined (fewer than 2 raters, or every pair is
    undefined because a rater has <2 items or zero variance).
    """
    pairwise = [
        spearman(raters[i], raters[j])
        for i, j in combinations(range(len(raters)), 2)
    ]
    defined = [c for c in pairwise if c is not None]
    if not defined:
        return None
    return sum(defined) / len(defined)


@dataclass
class InterRaterResult:
    """The human ceiling: how much the human raters agree among themselves."""
    n_raters: int
    n_items: int
    mean_pairwise_spearman: Optional[float]


def compute_interrater(raters: Sequence[Sequence[float]]) -> InterRaterResult:
    """Structured inter-rater result. n_items is the number of scored items
    (length of the first rater's vector), 0 when there are no raters."""
    n_raters = len(raters)
    n_items = len(raters[0]) if n_raters else 0
    return InterRaterResult(
        n_raters=n_raters,
        n_items=n_items,
        mean_pairwise_spearman=mean_pairwise_spearman(raters),
    )


def interpret_vs_ceiling(
    ai_vs_human: Optional[float],
    human_ceiling: Optional[float],
    tol: float = 0.05,
) -> str:
    """Read AI agreement against the human ceiling.

    Returns one of:
      - "no_baseline"          — no human ceiling to compare against
      - "below_ceiling"        — AI agrees with humans less than humans agree
                                 with each other (real room to improve)
      - "at_ceiling"           — AI is within `tol` of the human ceiling; this is
                                 effectively as good as a human judge and the
                                 realistic target — do not chase higher
      - "above_ceiling_watch"  — AI agrees MORE than the humans do with each
                                 other; a red flag for overfitting one rater's
                                 idiosyncrasies, not a genuine win
    """
    if ai_vs_human is None or human_ceiling is None:
        return "no_baseline"
    if ai_vs_human > human_ceiling + tol:
        return "above_ceiling_watch"
    if ai_vs_human < human_ceiling - tol:
        return "below_ceiling"
    return "at_ceiling"
