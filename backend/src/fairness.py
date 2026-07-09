"""Fairness / disparate-impact scaffolding for the Business Plan Grader.

The eng review's outside voice (OV#13) flagged real fairness risks for an
African competition with variable English fluency: language/fluency bias and
length bias in the grader, and AI-content detectors that fire
disproportionately on non-native and template-using founders. Flagging a plan
"needs review" imposes a cost on the population least able to contest it.

This module computes the disparity metrics a human reviewer needs to SEE that
risk — grouped flag rates, a four-fifths-style disparate-impact ratio, the
AI-flag false-positive rate per group, and mean score per group. It measures;
it never auto-decides. Pure Python, stdlib only, unit-tested.

The group attribute (language, region, ...) is supplied by the caller. Wiring
it to real per-plan metadata is a later step; the metrics are testable now.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence


@dataclass
class GroupRecord:
    group: str
    score: Optional[float] = None
    flagged: bool = False                      # needs_review / any human-review flag
    ai_flag: bool = False                      # AI-content suspicion raised by the pipeline
    ai_flag_confirmed: Optional[bool] = None   # human verdict: True=real, False=false positive, None=unadjudicated


def _by_group(records: Sequence[GroupRecord]) -> Dict[str, List[GroupRecord]]:
    groups: Dict[str, List[GroupRecord]] = {}
    for r in records:
        groups.setdefault(r.group, []).append(r)
    return groups


def flag_rate_by_group(records: Sequence[GroupRecord]) -> Dict[str, float]:
    """Fraction of plans flagged for human review, per group."""
    return {
        g: sum(1 for r in rs if r.flagged) / len(rs)
        for g, rs in _by_group(records).items()
    }


def disparate_impact_ratio(rates: Dict[str, float]) -> Optional[float]:
    """min(rate) / max(rate) across groups — the four-fifths rule of thumb.

    1.0 means groups are treated evenly; a value below ~0.8 signals a notable
    disparity worth human attention. Returns None when there are fewer than 2
    groups or the maximum rate is 0 (ratio undefined).
    """
    if len(rates) < 2:
        return None
    hi = max(rates.values())
    if hi == 0:
        return None
    return min(rates.values()) / hi


def ai_flag_false_positive_rate_by_group(records: Sequence[GroupRecord]) -> Dict[str, float]:
    """Per group, the false-positive rate of the AI-content flag: among plans
    that were AI-flagged AND human-adjudicated, the fraction the human CLEARED
    (ai_flag_confirmed is False). Groups with no adjudicated AI-flags are omitted.
    """
    fpr: Dict[str, float] = {}
    for g, rs in _by_group(records).items():
        adjudicated = [r for r in rs if r.ai_flag and r.ai_flag_confirmed is not None]
        if not adjudicated:
            continue
        false_positives = sum(1 for r in adjudicated if r.ai_flag_confirmed is False)
        fpr[g] = false_positives / len(adjudicated)
    return fpr


def mean_score_by_group(records: Sequence[GroupRecord]) -> Dict[str, Optional[float]]:
    """Mean score per group over records that have a score (missing scores
    excluded). A group with no scored records maps to None."""
    means: Dict[str, Optional[float]] = {}
    for g, rs in _by_group(records).items():
        scores = [r.score for r in rs if r.score is not None]
        means[g] = (sum(scores) / len(scores)) if scores else None
    return means
