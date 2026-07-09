"""Grade-of-record + content hashing for reproducibility and caching.

The eng review accepted X4/OV#8: a prize competition must be able to re-derive
and defend a disputed score. Because grading is a stochastic ensemble over a
server-side model that drifts week to week, the ONLY way "why did I get 6/8?"
has a defensible answer is to pin the exact inputs and settings that produced
the canonical grade. This module provides:

  - content_hash: a stable hash of the graded inputs (rubric + submission).
  - cache_key: content + model + temperature + run-index, so ensemble samples
    stay distinct (OV#6 — caching must not collapse the ensemble) while an
    identical re-submission still hits cache.
  - GradeOfRecord: the pinned canonical grade (model, temperatures, seeds,
    prompt hash, per-criterion result, total), serializable for persistence.

Pure module: stdlib only, unit-tested.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def content_hash(rubric, submission: str) -> str:
    """Stable hash of the graded inputs. `rubric` is any JSON-serializable
    structure (e.g. a list of criterion dicts); `submission` is the plan text.
    Rubric order is significant (it is significant to grading). Whitespace at
    the ends of the submission is ignored so trivial edits don't change the id.
    """
    payload = json.dumps(
        {"rubric": rubric, "submission": (submission or "").strip()},
        sort_keys=True, default=str, ensure_ascii=False,
    )
    return _sha256(payload)


def cache_key(input_hash: str, model: str, temperature: float, run_index: int) -> str:
    """Ensemble-reconciled cache key. Including temperature and run_index means
    each ensemble sample has its own key (they are meant to differ), so caching
    never silently collapses N runs into one value — while an identical
    (input, model, temperature, run_index) re-request still hits cache."""
    return _sha256(f"{input_hash}|{model}|{temperature!r}|{run_index}")


def _award(a) -> tuple:
    """(criteria_name, awarded_points) from a CriterionAssessment-like object or dict."""
    if isinstance(a, dict):
        return str(a.get("criteria_name", "")), float(a.get("awarded_points", 0.0))
    return str(getattr(a, "criteria_name", "")), float(getattr(a, "awarded_points", 0.0))


def record_for(rubric, submission: str, *, model: str, temperatures, assessments,
               total: float, seeds=None, prompt_hash: str = "", ai_flag: bool = False,
               flagged_criteria=None, created_at=None) -> "GradeOfRecord":
    """Assemble a GradeOfRecord from a graded result. `assessments` may be
    CriterionAssessment objects or dicts. The input hash is derived from the
    exact rubric + submission so the grade is re-derivable in a dispute."""
    per = {}
    for a in assessments or []:
        name, pts = _award(a)
        if name:
            per[name] = pts
    return GradeOfRecord(
        input_hash=content_hash(rubric, submission),
        model=model,
        temperatures=list(temperatures or []),
        seeds=list(seeds or []),
        prompt_hash=prompt_hash,
        per_criterion=per,
        total=float(total),
        created_at=created_at,
        ai_flag=bool(ai_flag),
        flagged_criteria=list(flagged_criteria or []),
    )


@dataclass
class GradeOfRecord:
    """The canonical, re-derivable grade used for ranking and dispute defense."""
    input_hash: str
    model: str
    temperatures: List[float]
    seeds: List[int]
    prompt_hash: str
    per_criterion: Dict[str, float]
    total: float
    created_at: Optional[str] = None   # ISO timestamp, supplied by the caller
    ai_flag: bool = False
    flagged_criteria: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "GradeOfRecord":
        return GradeOfRecord(
            input_hash=d["input_hash"],
            model=d["model"],
            temperatures=list(d.get("temperatures", [])),
            seeds=list(d.get("seeds", [])),
            prompt_hash=d["prompt_hash"],
            per_criterion=dict(d.get("per_criterion", {})),
            total=float(d["total"]),
            created_at=d.get("created_at"),
            ai_flag=bool(d.get("ai_flag", False)),
            flagged_criteria=list(d.get("flagged_criteria", [])),
        )
