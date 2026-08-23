"""Pure grade-parsing and grade-assembly logic.

Extracted from the LangGraph agent so it can be unit-tested without importing
langchain/langgraph/chromadb. This is where the engineering review's Issue #4
lives: a malformed grader response must NOT become a real-looking score of 0
(which would bury a good plan at the bottom of a ranking). Instead it becomes
graded_ok=False, flagged for human review.
"""
from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from backend.src.models import (
    CriterionAssessment,
    GradeResult,
    RubricItem,
    ELIGIBILITY_ELIGIBLE,
    ELIGIBILITY_NEEDS_REVIEW,
)

# A per-criterion award below this (on a 0..max scale) is surfaced as a warning
# in the critique list, matching the previous agent behaviour.
_LOW_AWARD_THRESHOLD = 5.0


@dataclass
class GradeData:
    score: float
    assessments: List[CriterionAssessment] = field(default_factory=list)
    critique_points: List[str] = field(default_factory=list)
    rubric_performance: Dict[str, str] = field(default_factory=dict)
    graded_ok: bool = True
    error: Optional[str] = None
    general_feedback: str = ""


def _safe_int(value, default: int) -> int:
    """Coerce a possibly-messy value to int, falling back to default."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def strip_code_fences(text: str) -> str:
    """Remove a leading ```json / ``` fence and trailing ``` if present."""
    s = text.strip()
    if s.startswith("```json"):
        s = s[len("```json"):]
    elif s.startswith("```"):
        s = s[len("```"):]
    if s.endswith("```"):
        s = s[:-3]
    return s.strip()


def _loads_lenient(cleaned: str):
    """json.loads, but tolerant of the ways models wrap/garnish JSON: try strict
    first, then the outermost {...} object (drops any prose before/after), then a
    trailing-comma repair. Raises json.JSONDecodeError if none parse. Does NOT fix
    truncated JSON — that's prevented upstream via a generous max_tokens."""
    try:
        return json.loads(cleaned)
    except (json.JSONDecodeError, ValueError):
        pass
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        frag = cleaned[start:end + 1]
        try:
            return json.loads(frag)
        except (json.JSONDecodeError, ValueError):
            repaired = re.sub(r",(\s*[}\]])", r"\1", frag)  # drop trailing commas
            return json.loads(repaired)
    return json.loads(cleaned)  # re-raise the original error


def _rubric_lookups(rubric: List[RubricItem]):
    by_index = {i + 1: item for i, item in enumerate(rubric)}   # 1-based
    by_name = {item.criteria.strip().lower(): item for item in rubric}
    return by_index, by_name


def _resolve_max_points(item_json: dict, rubric: List[RubricItem], by_index, by_name):
    """Find the criterion's max points from the rubric (by index, then name),
    falling back to any max the model supplied.

    Returns (max_points, resolved). resolved is False when the criterion matched
    nothing in the rubric and the model supplied no max — i.e. a phantom criterion
    whose award we cannot bound (handled as untrustworthy by the caller)."""
    idx = item_json.get("criteria_index")
    if isinstance(idx, (int, float)) and not isinstance(idx, bool) and int(idx) in by_index:
        return float(by_index[int(idx)].max_points), True
    name = str(item_json.get("criteria_name", "")).strip().lower()
    if name in by_name:
        return float(by_name[name].max_points), True
    supplied = item_json.get("max_points")
    if isinstance(supplied, (int, float)) and not isinstance(supplied, bool) and math.isfinite(float(supplied)):
        return float(supplied), True
    return 0.0, False


def parse_grader_response(raw_content: str, rubric: List[RubricItem]) -> GradeData:
    """Parse the grader model's JSON output into structured, trustworthy data.

    Returns graded_ok=False (never a silent 0) when the output is unparseable,
    empty, or contains non-numeric awards.
    """
    if raw_content is None or str(raw_content).strip() == "":
        return GradeData(score=0.0, graded_ok=False, error="Empty grader response")

    cleaned = strip_code_fences(str(raw_content))
    try:
        parsed = _loads_lenient(cleaned)
    except (json.JSONDecodeError, ValueError) as e:
        return GradeData(score=0.0, graded_ok=False, error=f"Unparseable grader JSON: {e}")

    if not isinstance(parsed, dict):
        return GradeData(score=0.0, graded_ok=False, error="Grader JSON was not an object")

    raw_assessments = parsed.get("assessments")
    if not isinstance(raw_assessments, list) or len(raw_assessments) == 0:
        return GradeData(score=0.0, graded_ok=False,
                         error="Grader returned no per-criterion assessments")

    by_index, by_name = _rubric_lookups(rubric)

    total = 0.0
    assessments: List[CriterionAssessment] = []
    critique_points: List[str] = []
    rubric_performance: Dict[str, str] = {}

    for i, item in enumerate(raw_assessments):
        if not isinstance(item, dict):
            return GradeData(score=0.0, graded_ok=False,
                             error=f"Assessment #{i} was not an object")
        name = str(item.get("criteria_name", "Unknown")).strip() or "Unknown"
        raw_points = item.get("awarded_points", None)
        try:
            points = float(raw_points)
        except (TypeError, ValueError):
            # Non-numeric award = untrustworthy grade. Flag, don't fabricate.
            return GradeData(score=0.0, graded_ok=False,
                             error=f"Non-numeric awarded_points for '{name}'")
        # Non-finite (NaN/Infinity) would slip past the numeric check, defeat the
        # clamp (all NaN comparisons are False), and poison the total. Reject it.
        if not math.isfinite(points):
            return GradeData(score=0.0, graded_ok=False,
                             error=f"Non-finite awarded_points for '{name}'")

        max_points, max_resolved = _resolve_max_points(item, rubric, by_index, by_name)
        # A positive award to a criterion we cannot bound (not in the rubric, no
        # supplied max) is untrustworthy — it would inflate the total unchecked.
        if not max_resolved and points != 0:
            return GradeData(score=0.0, graded_ok=False,
                             error=f"Awarded {points} to unknown criterion '{name}' with no resolvable max points")
        reason = str(item.get("reason", "")).strip()

        # Clamp into [0, max] so an over-award can't inflate the total; make the
        # clamp visible rather than silent.
        clamped = points
        if max_points > 0 and points > max_points:
            clamped = max_points
            reason = (reason + f" [clamped from {points} to max {max_points}]").strip()
        if clamped < 0:
            clamped = 0.0
            reason = (reason + f" [clamped up from {points} to 0]").strip()

        total += clamped
        assessments.append(CriterionAssessment(
            criteria_index=_safe_int(item.get("criteria_index"), i + 1),
            criteria_name=name,
            awarded_points=clamped,
            max_points=max_points,
            reason=reason,
            evidence=str(item.get("evidence", "")).strip(),
        ))
        rubric_performance[name] = f"{clamped} pts - {reason}"
        if clamped == 0.0:
            critique_points.append(f"❌ {name}: {reason}")
        elif clamped < _LOW_AWARD_THRESHOLD:
            critique_points.append(f"⚠️ {name}: {reason}")

    return GradeData(
        score=total,
        assessments=assessments,
        critique_points=critique_points,
        rubric_performance=rubric_performance,
        graded_ok=True,
        error=None,
        general_feedback=str(parsed.get("general_feedback", "")),
    )


def unsupported_evidence(assessments: List[CriterionAssessment], submission_text: str) -> List[str]:
    """Names of criteria whose (non-empty) evidence quote is NOT found in the
    submission — hallucinated support the Judge should reject (OV#7). Criteria
    with no evidence quote are skipped (absence is not hallucination). Uses the
    fuzzy, normalized matcher so OCR/quote drift doesn't cause false rejections."""
    from backend.src.evidence import evidence_supported  # local import: keep module load light
    bad: List[str] = []
    for a in assessments:
        quote = (getattr(a, "evidence", "") or "").strip()
        if not quote:
            continue
        if not evidence_supported(quote, submission_text):
            bad.append(a.criteria_name)
    return bad


def aggregate_grade_data(grade_datas: List["GradeData"], flag_threshold: float = 2.0) -> "GradeData":
    """Combine N ensemble runs into one GradeData: per-criterion MEDIAN award,
    total = sum of medians, high grader disagreement noted in the critique
    (A4/CQ1/X1). Only runs that graded_ok are aggregated; if none did, the
    result is graded_ok=False (flagged for human review, never a fake 0)."""
    from backend.src.aggregate import aggregate_ensemble  # local import: avoids load-time coupling

    usable = [g for g in grade_datas if g.graded_ok]
    if not usable:
        return GradeData(score=0.0, graded_ok=False, error="all ensemble runs failed to grade")

    runs = [{a.criteria_name: a.awarded_points for a in g.assessments} for g in usable]
    ens = aggregate_ensemble(runs, flag_threshold=flag_threshold)

    # Carry criterion metadata (max/reason/evidence/index) from the first run that has it.
    meta: Dict[str, CriterionAssessment] = {}
    for g in usable:
        for a in g.assessments:
            meta.setdefault(a.criteria_name, a)

    assessments: List[CriterionAssessment] = []
    critique_points: List[str] = []
    rubric_performance: Dict[str, str] = {}
    for name, agg in ens.per_criterion.items():
        m = meta.get(name)
        reason = m.reason if m else ""
        assessments.append(CriterionAssessment(
            criteria_index=m.criteria_index if m else 0,
            criteria_name=name,
            awarded_points=agg.median,
            max_points=m.max_points if m else 0.0,
            reason=reason,
            evidence=getattr(m, "evidence", "") if m else "",
        ))
        rubric_performance[name] = f"{agg.median} pts - {reason}"
        if agg.flagged:
            critique_points.append(f"⚖️ {name}: graders disagreed (spread {agg.spread})")
        if agg.median == 0.0:
            critique_points.append(f"❌ {name}: {reason}")
        elif agg.median < _LOW_AWARD_THRESHOLD:
            critique_points.append(f"⚠️ {name}: {reason}")

    return GradeData(
        score=ens.total,
        assessments=assessments,
        critique_points=critique_points,
        rubric_performance=rubric_performance,
        graded_ok=True,
        general_feedback=usable[0].general_feedback,
    )


def find_missing_criteria(assessments: List[CriterionAssessment],
                          rubric: List[RubricItem]) -> List[str]:
    """Return the names of rubric criteria NOT covered by any assessment (matched by
    1-based index or by case-insensitive name).

    A single grader call can silently drop criteria on a long rubric, yielding an
    artificially low total that still passes score-bounds validation. The Judge uses
    this to reject an incomplete grade and retry, so every criterion is scored.
    """
    n = len(rubric)
    names = {item.criteria.strip().lower(): i for i, item in enumerate(rubric)}
    covered = set()
    for a in assessments:
        nm = (getattr(a, "criteria_name", "") or "").strip().lower()
        idx = getattr(a, "criteria_index", None)
        # Trust an in-range index ONLY when the name agrees with that slot. parse_grader_
        # response defaults a missing index to the list position, so a phantom/mislabeled
        # entry ("Overall", no index) would otherwise get a positional index that silently
        # covers a genuinely dropped criterion — defeating this very check.
        if (isinstance(idx, int) and 1 <= idx <= n
                and nm == rubric[idx - 1].criteria.strip().lower()):
            covered.add(idx - 1)
            continue
        if nm in names:
            covered.add(names[nm])
    return [rubric[i].criteria for i in range(n) if i not in covered]


def summarize_performance(assessments: List[CriterionAssessment],
                          strong: float = 0.8, weak: float = 0.6):
    """Split criteria into (strengths, gaps) by the fraction of max points earned.
    Deterministic — it reads the actual per-criterion scores rather than asking the
    LLM — so feedback about what went well/poorly cannot hallucinate. Criteria with
    no resolvable max are skipped."""
    strengths: List[str] = []
    gaps: List[str] = []
    for a in assessments:
        mx = getattr(a, "max_points", 0) or 0
        if mx <= 0:
            continue
        frac = a.awarded_points / mx
        if frac >= strong:
            strengths.append(a.criteria_name)
        elif frac < weak:
            gaps.append(a.criteria_name)
    return strengths, gaps


def to_grade_result(
    grade_data: GradeData,
    feedback: str,
    thinking_process: Optional[List[str]] = None,
    confidence_score: float = 1.0,
    eligibility_status: str = ELIGIBILITY_ELIGIBLE,
    dq_reasons: Optional[List[str]] = None,
    ai_content_flag: bool = False,
    business_name: str = "",
) -> GradeResult:
    """Assemble the API-facing GradeResult, propagating grade status + eligibility."""
    # A grade that failed to parse should never present as an eligible real score.
    status = eligibility_status
    if not grade_data.graded_ok and status == ELIGIBILITY_ELIGIBLE:
        status = ELIGIBILITY_NEEDS_REVIEW
    return GradeResult(
        score=grade_data.score,
        feedback=feedback,
        citations=[],
        thinking_process=thinking_process or [],
        confidence_score=confidence_score,
        assessments=grade_data.assessments,
        graded_ok=grade_data.graded_ok,
        error=grade_data.error,
        eligibility_status=status,
        dq_reasons=dq_reasons or [],
        ai_content_flag=ai_content_flag,
        business_name=business_name,
    )
