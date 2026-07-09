"""SSE stage-event contract for the Live Grading Theater (Phase 3).

LangGraph's `astream(..., stream_mode="updates")` yields one {node_name: delta}
per node as the grading pipeline runs. This maps each node's delta into the
JSON stage event the frontend consumes, so the theater's per-stage animation is
driven by REAL progress rather than the current timer fiction:

    prepare          -> screening   (eligibility / DQ / AI-content flag)
    grade_submission -> reading     (criteria scored so far, running score)
    validate_grade   -> judging     (valid / rejected + reason + retry count)
    generate_feedback-> coaching    (feedback being written)
    <stream end>     -> done        (final GradeResult; emitted by the endpoint)

Pure and dependency-light (duck-typed on the delta), so it is unit-tested
without langgraph/langchain. Returns None for internal nodes the UI ignores.
"""
from __future__ import annotations

from typing import Any, Dict, Optional


def _count(value: Any) -> int:
    try:
        return len(value)
    except TypeError:
        return 0


def stage_event(node_name: str, delta: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Translate one LangGraph node update into a theater stage event (or None
    when the node has no user-facing scene)."""
    if node_name == "prepare":
        elig = delta.get("eligibility", {}) or {}
        return {
            "stage": "screening",
            "eligibility_status": elig.get("status", "eligible"),
            "dq_reasons": list(elig.get("reasons", []) or []),
            "ai_content_flag": bool(elig.get("ai_content_flag", False)),
        }

    if node_name == "grade_submission":
        gd = delta.get("grade_data")
        assessments = getattr(gd, "assessments", None)
        if assessments is None and isinstance(gd, dict):
            assessments = gd.get("assessments")
        score = getattr(gd, "score", None)
        if score is None and isinstance(gd, dict):
            score = gd.get("score")
        return {
            "stage": "reading",
            "criteria_scored": _count(assessments),
            "score": score,
        }

    if node_name == "validate_grade":
        return {
            "stage": "judging",
            "is_valid": bool(delta.get("is_valid", False)),
            "reason": delta.get("grader_feedback", "") or "",
            "revision_number": int(delta.get("revision_number", 0) or 0),
        }

    if node_name == "generate_feedback":
        return {"stage": "coaching"}

    return None
