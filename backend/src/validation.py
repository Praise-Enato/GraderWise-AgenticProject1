"""Validation metric engine for the Business Plan Grader reliability harness.

This module is the correctness-critical core: its output is the agreement number
shown to the competition board. A bug here means silently reporting a wrong
reliability figure, so it is pure Python (no numpy/scipy), fully unit-tested,
and free of any heavy dependency (no torch/langgraph/chromadb).

Design notes from the engineering review:
- Report correlation WITH a confidence interval. At n=15 the CI is wide; that
  honesty is a strength in front of a board, not a weakness.
- The leave-one-out helper is the data-leakage guard: when the grader uses a few
  scored plans as calibration examples, a plan must never see itself as an
  example, or the reported agreement is inflated.
"""
from __future__ import annotations

import csv
import json
import math
import random
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Sequence


# --------------------------------------------------------------------------- #
# Core statistics (pure Python)
# --------------------------------------------------------------------------- #

def _check_pair(xs: Sequence[float], ys: Sequence[float]) -> None:
    if len(xs) != len(ys):
        raise ValueError(f"length mismatch: {len(xs)} vs {len(ys)}")


def mae(xs: Sequence[float], ys: Sequence[float]) -> Optional[float]:
    """Mean absolute error. Returns None for empty input."""
    _check_pair(xs, ys)
    if not xs:
        return None
    return sum(abs(a - b) for a, b in zip(xs, ys)) / len(xs)


def rmse(xs: Sequence[float], ys: Sequence[float]) -> Optional[float]:
    _check_pair(xs, ys)
    if not xs:
        return None
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(xs, ys)) / len(xs))


def pearson(xs: Sequence[float], ys: Sequence[float]) -> Optional[float]:
    """Pearson correlation. Returns None when it is undefined (n < 2 or a
    constant series with zero variance)."""
    _check_pair(xs, ys)
    n = len(xs)
    if n < 2:
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    cov = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    vx = sum((a - mx) ** 2 for a in xs)
    vy = sum((b - my) ** 2 for b in ys)
    if vx == 0 or vy == 0:
        return None  # a constant series cannot be correlated
    return cov / math.sqrt(vx * vy)


def rank(values: Sequence[float]) -> List[float]:
    """Return fractional ranks (1-based), averaging ranks for ties."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        # advance over a run of equal values
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg_rank = (i + j) / 2.0 + 1.0  # 1-based average rank for the tie group
        for k in range(i, j + 1):
            ranks[order[k]] = avg_rank
        i = j + 1
    return ranks


def spearman(xs: Sequence[float], ys: Sequence[float]) -> Optional[float]:
    """Spearman rank correlation = Pearson on the ranks (tie-aware)."""
    _check_pair(xs, ys)
    if len(xs) < 2:
        return None
    return pearson(rank(xs), rank(ys))


def fisher_ci(r: Optional[float], n: int, confidence: float = 0.95,
              variance_factor: float = 1.0) -> Optional[tuple]:
    """Confidence interval for a correlation via the Fisher z-transform.

    Returns (low, high) or None when undefined (r is None or n <= 3).
    r is clamped just inside (-1, 1) so atanh does not blow up on r == +/-1.

    variance_factor scales the standard error. For Pearson r use 1.0; for
    Spearman's rho use ~1.03 (Fieller-Hartley-Pearson correction: Var(z) ~
    1.06/(n-3)), which widens the interval so certainty is not overstated.
    """
    if r is None or n <= 3:
        return None
    z_crit = _z_critical(confidence)
    r_clamped = max(min(r, 0.999999), -0.999999)
    z = math.atanh(r_clamped)
    se = variance_factor / math.sqrt(n - 3)
    lo = math.tanh(z - z_crit * se)
    hi = math.tanh(z + z_crit * se)
    return (lo, hi)


def _z_critical(confidence: float) -> float:
    """Two-sided normal critical value. Uses common values, falls back to an
    inverse-normal approximation for arbitrary confidence levels."""
    common = {0.90: 1.6448536269514722, 0.95: 1.959963984540054, 0.99: 2.5758293035489004}
    if confidence in common:
        return common[confidence]
    # Acklam's inverse normal CDF approximation for the (1 - alpha/2) quantile.
    p = 1.0 - (1.0 - confidence) / 2.0
    return _inv_norm_cdf(p)


def _inv_norm_cdf(p: float) -> float:
    # Peter Acklam's algorithm; accurate to ~1e-9, pure Python.
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00]
    plow, phigh = 0.02425, 1 - 0.02425
    if p < plow:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
               ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    if p > phigh:
        q = math.sqrt(-2 * math.log(1 - p))
        return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
               ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    q = p - 0.5
    r = q * q
    return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / \
           (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)


def _percentile(sorted_values: Sequence[float], pct: float) -> float:
    """Linear-interpolated percentile of an ALREADY-SORTED sequence. pct in [0, 100]."""
    if not sorted_values:
        raise ValueError("empty sequence")
    if len(sorted_values) == 1:
        return sorted_values[0]
    rank = (pct / 100.0) * (len(sorted_values) - 1)
    lo_i = int(math.floor(rank))
    hi_i = int(math.ceil(rank))
    if lo_i == hi_i:
        return sorted_values[lo_i]
    frac = rank - lo_i
    return sorted_values[lo_i] * (1 - frac) + sorted_values[hi_i] * frac


def bootstrap_ci(
    xs: Sequence[float],
    ys: Sequence[float],
    statistic: Callable[[Sequence[float], Sequence[float]], Optional[float]],
    n_resamples: int = 1000,
    confidence: float = 0.95,
    seed: Optional[int] = None,
) -> Optional[tuple]:
    """Percentile bootstrap confidence interval for a paired statistic.

    Resamples the paired (x, y) observations with replacement `n_resamples`
    times, recomputes `statistic` on each resample, and returns the
    (low, high) percentile interval. Unlike the Fisher CI this assumes no
    distribution, which is the honest choice on a tiny ground-truth set (OV#3).

    Resamples where the statistic is undefined (e.g. a constant draw makes a
    correlation undefined) are skipped. Returns None when fewer than 2 usable
    resample statistics remain or when there are fewer than 2 observations.
    `seed` makes the result deterministic (required for tests and reproducible
    reports).
    """
    _check_pair(xs, ys)
    n = len(xs)
    if n < 2:
        return None
    rng = random.Random(seed)
    stats: List[float] = []
    for _ in range(n_resamples):
        idx = [rng.randrange(n) for _ in range(n)]
        s = statistic([xs[i] for i in idx], [ys[i] for i in idx])
        if s is not None:
            stats.append(s)
    if len(stats) < 2:
        return None
    stats.sort()
    alpha = 1.0 - confidence
    lo = _percentile(stats, alpha / 2.0 * 100.0)
    hi = _percentile(stats, (1.0 - alpha / 2.0) * 100.0)
    return (lo, hi)


def leave_one_out_indices(n: int) -> List[List[int]]:
    """For each item i in 0..n-1, the indices of every OTHER item.

    Used so a plan graded with few-shot calibration never sees itself as an
    example. loo[i] is the pool of candidate example indices for item i.
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    return [[j for j in range(n) if j != i] for i in range(n)]


def weighted_total(plan_score: float, video_score: float, plan_weight: float = 0.8) -> float:
    """Combine plan and video component scores. Competition weighting is
    Plan 80% + Video/Q&A 20% (Handbook). Both scores must be on the same scale."""
    if not 0.0 <= plan_weight <= 1.0:
        raise ValueError("plan_weight must be in [0, 1]")
    return plan_score * plan_weight + video_score * (1.0 - plan_weight)


# --------------------------------------------------------------------------- #
# Aggregate agreement result
# --------------------------------------------------------------------------- #

@dataclass
class AgreementResult:
    n: int
    spearman: Optional[float]
    pearson: Optional[float]
    mae: Optional[float]
    ci95: Optional[tuple]  # Fisher CI on the Spearman correlation
    boot_ci95: Optional[tuple] = None  # percentile bootstrap CI on Spearman (top-level only)
    per_criterion: Dict[str, "AgreementResult"] = field(default_factory=dict)

    def summary(self) -> str:
        def f(x):
            return "n/a" if x is None else f"{x:.3f}"
        ci = "n/a" if not self.ci95 else f"[{self.ci95[0]:.2f}, {self.ci95[1]:.2f}]"
        boot = "" if not self.boot_ci95 else f" (bootstrap [{self.boot_ci95[0]:.2f}, {self.boot_ci95[1]:.2f}])"
        return (f"n={self.n} spearman={f(self.spearman)} (95% CI {ci}){boot} "
                f"pearson={f(self.pearson)} mae={f(self.mae)}")


def compute_agreement(
    ai_scores: Sequence[float],
    human_scores: Sequence[float],
    per_criterion_ai: Optional[Dict[str, Sequence[float]]] = None,
    per_criterion_human: Optional[Dict[str, Sequence[float]]] = None,
    confidence: float = 0.95,
    bootstrap_resamples: int = 0,
    bootstrap_seed: Optional[int] = None,
) -> AgreementResult:
    """Agreement between AI and human scores, with an optional per-criterion
    breakdown. Correlation is reported with a Fisher CI so small-n uncertainty
    is explicit; pass bootstrap_resamples > 0 to also attach a distribution-free
    percentile bootstrap CI (top-level only — not recomputed per criterion)."""
    _check_pair(ai_scores, human_scores)
    n = len(ai_scores)
    sp = spearman(ai_scores, human_scores)
    result = AgreementResult(
        n=n,
        spearman=sp,
        pearson=pearson(ai_scores, human_scores),
        mae=mae(ai_scores, human_scores),
        # CI is on the Spearman correlation, so use the rank-correlation variance
        # correction (1.03) rather than the Pearson SE — a slightly wider, honest interval.
        ci95=fisher_ci(sp, n, confidence, variance_factor=1.03),
        boot_ci95=(
            bootstrap_ci(ai_scores, human_scores, spearman,
                         n_resamples=bootstrap_resamples, confidence=confidence,
                         seed=bootstrap_seed)
            if bootstrap_resamples > 0 else None
        ),
    )
    if per_criterion_ai and per_criterion_human:
        for name, ai_vals in per_criterion_ai.items():
            human_vals = per_criterion_human.get(name)
            if human_vals is None:
                continue
            # per-criterion bootstrap is intentionally skipped (cost); Fisher CI only.
            result.per_criterion[name] = compute_agreement(ai_vals, human_vals, confidence=confidence)
    return result


# --------------------------------------------------------------------------- #
# Ground-truth manifest loading
# --------------------------------------------------------------------------- #

@dataclass
class GroundTruthRecord:
    filename: str
    human_total: Optional[float] = None
    human_plan: Optional[float] = None   # 80% component, when the org separates it
    human_video: Optional[float] = None  # 20% component
    criteria: Dict[str, float] = field(default_factory=dict)  # per-criterion human scores (optional)
    raters: Dict[str, float] = field(default_factory=dict)    # per-rater total for this plan (optional)


_RESERVED = {"filename", "human_total", "human_plan", "human_video"}
_CRIT_PREFIXES = ("crit_", "human_crit_", "criterion_")
_RATER_PREFIX = "rater_"


def _to_float(value) -> Optional[float]:
    if value is None:
        return None
    s = str(value).strip()
    if s == "":
        return None
    return float(s)


def _criterion_name(column: str) -> Optional[str]:
    for pref in _CRIT_PREFIXES:
        if column.startswith(pref):
            return column[len(pref):]
    return None


def load_ground_truth(path: str) -> List[GroundTruthRecord]:
    """Load the flexible ground-truth manifest.

    Supports CSV and JSON. Per-criterion scores are OPTIONAL (columns prefixed
    ``crit_`` / ``human_crit_`` / ``criterion_`` in CSV, or a ``criteria`` object
    in JSON) so the harness degrades gracefully to total-only when the org only
    provided final totals. ``human_plan`` / ``human_video`` capture the 80/20
    split when the org separates the components.
    """
    if path.lower().endswith(".json"):
        return _load_json(path)
    return _load_csv(path)


def _load_json(path: str) -> List[GroundTruthRecord]:
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if isinstance(data, dict):
        data = data.get("plans") or data.get("records") or []
    records = []
    for row in data:
        if "filename" not in row:
            raise ValueError("each manifest record needs a 'filename'")
        # Route criterion values through _to_float and drop None/empty, mirroring
        # the CSV loader so a null/empty criterion doesn't abort the whole load.
        criteria = {}
        for k, v in (row.get("criteria") or {}).items():
            fv = _to_float(v)
            if fv is not None:
                criteria[k] = fv
        raters = {}
        for k, v in (row.get("raters") or {}).items():
            fv = _to_float(v)
            if fv is not None:
                raters[k] = fv
        records.append(GroundTruthRecord(
            filename=row["filename"],
            human_total=_to_float(row.get("human_total")),
            human_plan=_to_float(row.get("human_plan")),
            human_video=_to_float(row.get("human_video")),
            criteria=criteria,
            raters=raters,
        ))
    return records


# --------------------------------------------------------------------------- #
# Validation-run aggregation (pure; the IO harness builds PlanGrades and calls these)
# --------------------------------------------------------------------------- #

# Must match models.ELIGIBILITY_ELIGIBLE. Kept as a literal so this module stays
# free of any import beyond the stdlib.
_ELIGIBLE = "eligible"


@dataclass
class PlanGrade:
    """One graded plan, as collected by the harness."""
    filename: str
    ai_score: float
    graded_ok: bool = True
    eligibility_status: str = _ELIGIBLE
    criteria: Dict[str, float] = field(default_factory=dict)  # per-criterion AI scores (optional)


def partition(grades: List[PlanGrade]):
    """Split into (scored, flagged). Only plans that graded_ok AND are eligible
    are ranked/scored; everything else is flagged for human review — never mixed
    into the agreement metric or ranked as a real score."""
    scored = [g for g in grades if g.graded_ok and g.eligibility_status == _ELIGIBLE]
    flagged = [g for g in grades if not (g.graded_ok and g.eligibility_status == _ELIGIBLE)]
    return scored, flagged


def _human_score(record: "GroundTruthRecord", component: str) -> Optional[float]:
    """Pick the human score for the requested component.

    IMPORTANT: 'plan' returns the plan-only (80%) score with NO fallback to the
    total. Falling back to human_total would compare a text-only AI (plan only)
    against a human score that includes the 20% video — the exact confound the
    phasing was built to avoid. When human_plan is missing the plan is instead
    reported under missing_human_score (visible, excluded), not silently confounded.
    """
    if component == "plan":
        return record.human_plan
    if component == "video":
        return record.human_video
    return record.human_total


@dataclass
class ValidationReport:
    agreement: AgreementResult
    matched: int
    scored: int
    flagged: int
    unmatched_filenames: List[str] = field(default_factory=list)
    missing_human_score: List[str] = field(default_factory=list)


def join_and_aggregate(
    grades: List[PlanGrade],
    ground_truth: List["GroundTruthRecord"],
    component: str = "total",
    confidence: float = 0.95,
    bootstrap_resamples: int = 0,
    bootstrap_seed: Optional[int] = None,
) -> ValidationReport:
    """Join AI grades to human ground truth by filename and compute agreement
    over the scored (eligible + graded_ok) plans only."""
    scored, flagged = partition(grades)
    gt_by_name = {r.filename: r for r in ground_truth}

    ai_scores: List[float] = []
    human_scores: List[float] = []
    per_crit_ai: Dict[str, List[float]] = {}
    per_crit_human: Dict[str, List[float]] = {}
    unmatched: List[str] = []
    missing_human: List[str] = []

    for g in scored:
        rec = gt_by_name.get(g.filename)
        if rec is None:
            unmatched.append(g.filename)
            continue
        h = _human_score(rec, component)
        if h is None:
            missing_human.append(g.filename)
            continue
        ai_scores.append(g.ai_score)
        human_scores.append(h)
        # per-criterion, only where both sides have the criterion
        for cname, ai_val in g.criteria.items():
            if cname in rec.criteria:
                per_crit_ai.setdefault(cname, []).append(ai_val)
                per_crit_human.setdefault(cname, []).append(rec.criteria[cname])

    agreement = compute_agreement(
        ai_scores, human_scores,
        per_criterion_ai=per_crit_ai or None,
        per_criterion_human=per_crit_human or None,
        confidence=confidence,
        bootstrap_resamples=bootstrap_resamples,
        bootstrap_seed=bootstrap_seed,
    )
    return ValidationReport(
        agreement=agreement,
        matched=len(ai_scores),
        scored=len(scored),
        flagged=len(flagged),
        unmatched_filenames=unmatched,
        missing_human_score=missing_human,
    )


def _load_csv(path: str) -> List[GroundTruthRecord]:
    records = []
    with open(path, "r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None or "filename" not in reader.fieldnames:
            raise ValueError("manifest CSV must have a 'filename' column")
        for row in reader:
            criteria = {}
            raters = {}
            for col, val in row.items():
                if not col:
                    continue
                cname = _criterion_name(col)
                if cname is not None:
                    fv = _to_float(val)
                    if fv is not None:
                        criteria[cname] = fv
                elif col.startswith(_RATER_PREFIX):
                    fv = _to_float(val)
                    if fv is not None:
                        raters[col[len(_RATER_PREFIX):]] = fv
            records.append(GroundTruthRecord(
                filename=(row.get("filename") or "").strip(),
                human_total=_to_float(row.get("human_total")),
                human_plan=_to_float(row.get("human_plan")),
                human_video=_to_float(row.get("human_video")),
                criteria=criteria,
                raters=raters,
            ))
    return records
