"""Few-shot calibration for the Business Plan Grader.

Injects an expert-judge-scored example into the grader prompt so the model
calibrates its SEVERITY to the competition's real standard (the human judges are
much stricter than an out-of-the-box LLM, especially on financials).

Designed AGAINST overfitting:
  - The example is a calibration REFERENCE, not a template to copy — the block
    carries an explicit "do not copy these numbers, grade the current plan on its
    own evidence" instruction.
  - A plan is NEVER graded using ITSELF as an example (leave-one-out: exclude by
    filename). This prevents data leakage and keeps any reliability measurement
    honest.
  - It teaches transferable severity (what earns 0 / partial / full), not
    plan-specific answers.

Pure module: stdlib only, unit-tested. The CSV parser understands the
`few_shot_example - Sheet1.csv` layout (section headers + `<max> - <label>, <score>` rows).
"""
from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass, asdict
from typing import Dict, Iterable, List

# "Problem/Pain Point - 10 points" -> section = "Problem/Pain Point"
_SECTION_RE = re.compile(r"^(.*?)\s*-\s*\d+(?:\.\d+)?\s*points\s*$", re.IGNORECASE)
# "2.5 - Clearly defined the problem/pain being addressed" -> (2.5, label)
_CRIT_RE = re.compile(r"^([\d.]+)\s*-\s*(.+)$")


@dataclass
class ScoredItem:
    criteria: str        # full criterion name, matching the rubric ("Section - Label")
    awarded: float
    max_points: float
    note: str = ""       # optional calibration note (why this score) shown to the grader


@dataclass
class FewShotExample:
    filename: str        # must match the submission filename to enable leave-one-out
    business_name: str
    plan_text: str
    items: List[ScoredItem]
    human_total: float

    def to_dict(self) -> dict:
        d = asdict(self)
        return d

    @staticmethod
    def from_dict(d: dict) -> "FewShotExample":
        return FewShotExample(
            filename=d["filename"],
            business_name=d.get("business_name", ""),
            plan_text=d.get("plan_text", ""),
            items=[ScoredItem(**it) for it in d.get("items", [])],
            human_total=float(d.get("human_total", 0.0)),
        )


def parse_scored_plan_csv(path: str) -> dict:
    """Parse a human-scored plan CSV (the `few_shot_example` layout).

    Returns {business_name, items: [ScoredItem], human_total}. Full criterion
    names are reconstructed as "<Section> - <Label>" to match the rubric.
    """
    section = None
    items: List[ScoredItem] = []
    business = ""
    grand_total = 0.0
    with open(path, "r", encoding="utf-8", newline="") as fh:
        for row in csv.reader(fh):
            c0 = row[0].strip() if len(row) > 0 else ""
            c1 = row[1].strip() if len(row) > 1 else ""
            if not c0:
                continue
            low = c0.lower()
            if low.startswith("business n"):   # "Business Nme"
                business = c1
                continue
            if low == "grand total":
                try:
                    grand_total = float(c1)
                except ValueError:
                    pass
                continue
            if low == "total":
                continue
            msec = _SECTION_RE.match(c0)
            if msec:
                section = msec.group(1).strip()
                continue
            mc = _CRIT_RE.match(c0)
            if mc and section and c1 != "":
                try:
                    awarded = float(c1)
                except ValueError:
                    continue
                items.append(ScoredItem(
                    criteria=f"{section} - {mc.group(2).strip()}",
                    awarded=awarded,
                    max_points=float(mc.group(1)),
                ))
    return {"business_name": business, "items": items, "human_total": grand_total}


def load_examples(path: str) -> List[FewShotExample]:
    """Load few-shot examples from a JSON file. Returns [] if the file is absent."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        return []
    return [FewShotExample.from_dict(d) for d in data]


def apply_overrides(example: FewShotExample, overrides: List[dict]) -> List[str]:
    """Apply curator score overrides to an example IN PLACE and recompute the total.

    Each override: {"criteria": <full name>, "awarded": <float>, "note": <why>}.
    Keeps the raw human CSV intact upstream; the adjustment is explicit and auditable.
    Returns a list of human-readable change descriptions (empty if none matched).
    """
    by_name = {it.criteria: it for it in example.items}
    changes: List[str] = []
    for ov in overrides or []:
        name = ov.get("criteria")
        if name in by_name and "awarded" in ov:
            it = by_name[name]
            old = it.awarded
            it.awarded = float(ov["awarded"])
            it.note = ov.get("note", it.note)
            if it.awarded != old:
                changes.append(f"{name}: {old} -> {it.awarded}" + (f" ({it.note})" if it.note else ""))
    example.human_total = round(sum(it.awarded for it in example.items), 4)
    return changes


_HEADER = """CALIBRATION REFERENCE — how an expert human judge applies this rubric.

Study the SEVERITY below, not the specifics. Key lessons to generalize:
- The judge is STRICT. Present-but-thin content earns partial or zero, not full marks.
- DATA CREDIBILITY: flawed or internally inconsistent numbers (totals that don't add up, profit
  exceeding revenue, contradictory figures) are NOT credible — award little or no credit. A table's
  mere presence is not evidence; wrong data signals a mistake or misrepresentation.
- FIRST-HAND DATA: the team's own counts/observations/surveys (even unsourced) earn MODEST partial
  credit — not full marks (those need well-evidenced claims), and not zero.
- CREDIT WHAT IS CLEARLY PRESENT: if a required element is genuinely there (e.g. competitors named),
  give it real marks — do not zero something that exists.
- Missing or merely-adjacent content earns 0 (e.g. listing competitors is not "examples of how
  others solve the problem")."""

_FOOTER = """END CALIBRATION REFERENCE.

Use the example ONLY to calibrate how strict to be. Do NOT copy these numbers or map them onto the
current plan. Grade the CURRENT submission independently, criterion by criterion, on its own evidence."""


def build_calibration_block(
    examples: List[FewShotExample],
    exclude_filenames: Iterable[str] = (),
    max_plan_chars: int = 6000,
) -> str:
    """Build the calibration prompt block.

    Any example whose filename is in exclude_filenames is dropped (leave-one-out:
    a plan is never calibrated against itself). Returns "" when no usable example
    remains, so grading proceeds uncalibrated rather than leaking.
    """
    excl = {f for f in (exclude_filenames or ())}
    usable = [e for e in examples if e.filename not in excl]
    if not usable:
        return ""

    parts = [_HEADER]
    for e in usable:
        excerpt = e.plan_text[:max_plan_chars]
        if len(e.plan_text) > max_plan_chars:
            excerpt += "\n...[example plan truncated]..."
        score_lines = "\n".join(
            f"  - {it.criteria}: {it.awarded}/{it.max_points}" + (f"  ({it.note})" if it.note else "")
            for it in e.items
        )
        parts.append(
            f"\n--- EXAMPLE PLAN: {e.business_name} (excerpt) ---\n{excerpt}\n"
            f"\n--- EXPERT JUDGE'S SCORES (awarded / max) ---\n{score_lines}\n"
            f"  EXPERT PLAN TOTAL: {e.human_total} / 80"
        )
    parts.append(_FOOTER)
    return "\n".join(parts)
