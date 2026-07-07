"""Convert the BYUMS competition rubric CSV into structured RubricItems.

The competition rubric is a single flat 100-point sheet (28 criteria) with the
columns:

    Criteria, Distinguished (Full Marks), Proficient / Developing (Partial),
    No Marks (Zero), Max Pts

Crucially, the video component is embedded as 4 line items whose names start with
"Video - " (20 pts total). The remaining criteria are the plan/content component
(80 pts). Phase 1a grades the PLAN criteria only (the text grader cannot see the
video), so this module can split the rubric into (plan, video).

Pure and unit-tested — imports only stdlib + models.
"""
from __future__ import annotations

import csv
import re
from typing import List, Tuple

from backend.src.models import RubricItem

_POINTS_RE = re.compile(r"\(\s*([0-9]*\.?[0-9]+)\s*\)\s*pts", re.IGNORECASE)
# Strip a leading "(2.5) pts:" / "(1.25) pts" prefix from a cell's description.
_PREFIX_RE = re.compile(r"^\(\s*[0-9]*\.?[0-9]+\s*\)\s*pts\s*:?\s*", re.IGNORECASE)

VIDEO_PREFIX = "video - "


def extract_points(cell: str):
    """Return the first '(N) pts' number in a cell, or None."""
    if cell is None:
        return None
    m = _POINTS_RE.search(str(cell))
    return float(m.group(1)) if m else None


def strip_points_prefix(cell: str) -> str:
    """Remove a leading '(N) pts:' prefix, leaving the human description."""
    if cell is None:
        return ""
    return _PREFIX_RE.sub("", str(cell)).strip()


def is_video_criterion(name: str) -> bool:
    return str(name).strip().lower().startswith(VIDEO_PREFIX)


def _row_to_item(row: dict) -> RubricItem:
    name = (row.get("Criteria") or "").strip()
    distinguished = row.get("Distinguished (Full Marks)") or ""
    partial = row.get("Proficient / Developing (Partial)") or ""
    zero = row.get("No Marks (Zero)") or ""
    max_cell = row.get("Max Pts") or ""

    # Max points: prefer the Max Pts column, fall back to the Distinguished prefix.
    max_points = extract_points(max_cell)
    if max_points is None:
        max_points = extract_points(distinguished)
    if max_points is None:
        max_points = 0.0

    description = strip_points_prefix(distinguished) or name
    developing_points = extract_points(partial)
    developing_description = strip_points_prefix(partial) or None
    zero_points = extract_points(zero)
    zero_description = strip_points_prefix(zero) or None

    return RubricItem(
        criteria=name,
        max_points=max_points,
        description=description,
        developing_points=developing_points,
        developing_description=developing_description,
        zero_points=zero_points if zero_points is not None else 0.0,
        zero_description=zero_description,
    )


def parse_byums_rubric_csv(path: str) -> List[RubricItem]:
    """Parse the BYUMS rubric CSV into RubricItems (all criteria, in order)."""
    items: List[RubricItem] = []
    with open(path, "r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None or "Criteria" not in reader.fieldnames:
            raise ValueError("rubric CSV must have a 'Criteria' column")
        for row in reader:
            if not (row.get("Criteria") or "").strip():
                continue  # skip blank rows
            items.append(_row_to_item(row))
    return items


def split_video_plan(items: List[RubricItem]) -> Tuple[List[RubricItem], List[RubricItem]]:
    """Split into (plan_items, video_items). Video items are those named 'Video - ...'."""
    plan = [it for it in items if not is_video_criterion(it.criteria)]
    video = [it for it in items if is_video_criterion(it.criteria)]
    return plan, video


def total_points(items: List[RubricItem]) -> float:
    return sum(it.max_points for it in items)


def rubric_to_dicts(items: List[RubricItem]) -> List[dict]:
    """Serialize to plain dicts for a rubric JSON file (harness / API input)."""
    return [it.model_dump() for it in items]
