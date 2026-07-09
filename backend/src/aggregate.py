"""Defensible ensemble aggregate for the Business Plan Grader.

A plan is graded N times (A4). This module combines those runs into ONE
per-criterion score and a total, in a way that can be defended to a competition
board and in a dispute:

  - Per criterion, the award is the MEDIAN across runs (CQ1) — robust to a
    single outlier run.
  - The spread across runs (max - min) is reported and, when it exceeds a
    threshold, the criterion is FLAGGED for human review. Spread is grader
    DISAGREEMENT, not a calibrated confidence (X1) — never presented as "how
    sure the AI is."
  - At the shortlist cutoff, plans whose totals fall within a tie band are a
    statistical tie (OV#2); the band keeps a sub-noise gap from silently
    deciding a prize.

Pure Python, stdlib only (statistics.median), unit-tested.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from statistics import median as _median
from typing import Dict, List, Sequence, Tuple


@dataclass
class CriterionAgg:
    median: float
    spread: float          # max - min across runs (peak disagreement, in points)
    flagged: bool          # spread exceeded the review threshold
    n: int                 # number of runs that scored this criterion


@dataclass
class EnsembleResult:
    per_criterion: Dict[str, CriterionAgg]
    total: float                                   # sum of per-criterion medians
    flagged_criteria: List[str] = field(default_factory=list)


def aggregate_ensemble(
    runs: Sequence[Dict[str, float]],
    flag_threshold: float = 2.0,
) -> EnsembleResult:
    """Aggregate N ensemble runs into per-criterion medians + a total.

    `runs` is a list of {criterion_name: awarded_points} dicts, one per run.
    A criterion is flagged when its spread (max - min across runs) is >=
    flag_threshold points. Criteria are unioned across runs so a criterion any
    run scored is represented; missing values are simply not counted for that run.
    """
    names: List[str] = []
    for run in runs:
        for name in run:
            if name not in names:
                names.append(name)

    per_criterion: Dict[str, CriterionAgg] = {}
    flagged: List[str] = []
    total = 0.0
    for name in names:
        values = [run[name] for run in runs if name in run]
        med = float(_median(values))
        spread = float(max(values) - min(values)) if values else 0.0
        is_flagged = spread >= flag_threshold
        per_criterion[name] = CriterionAgg(median=med, spread=spread, flagged=is_flagged, n=len(values))
        total += med
        if is_flagged:
            flagged.append(name)
    return EnsembleResult(per_criterion=per_criterion, total=total, flagged_criteria=flagged)


def within_tie_band(a: float, b: float, band: float) -> bool:
    """True if two totals are within the least-significant-difference band, i.e.
    a statistical tie the grader's noise cannot legitimately separate."""
    return abs(a - b) <= band


def cutoff_tie_zone(
    scored: Sequence[Tuple[str, float]],
    k: int,
    band: float,
) -> List[str]:
    """Plans in a statistical tie with the shortlist cutoff (OV#2).

    `scored` is (id, total) pairs; `k` is the shortlist size. Returns, in
    descending-score order, the ids whose total is within `band` of the k-th
    (cutoff) plan's total — the admit/reject boundary a human must resolve
    rather than letting a sub-noise gap decide. Returns [] when k is out of
    range (no meaningful boundary).
    """
    ordered = sorted(scored, key=lambda pair: pair[1], reverse=True)
    if not (1 <= k < len(ordered)):
        return []
    cutoff_score = ordered[k - 1][1]
    return [pid for pid, score in ordered if within_tie_band(score, cutoff_score, band)]
