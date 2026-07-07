"""Generate the few-shot calibration example JSON from a human-scored plan.

Reads a plan PDF (for the example text) and its human-scored CSV, cross-checks the
criterion names against the plan rubric, and writes backend/data/bpc/few_shot_examples.json.

Usage:
    python -m backend.scripts.build_few_shot \
        --plan "Copy of Africa Business Plan Competition - 2026  (1).pdf" \
        --scores "few_shot_example - Sheet1.csv"
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.src import calibration
from backend.src import rubric_csv
from backend.src.input_adapter import get_adapter

OUT = "backend/data/bpc/few_shot_examples.json"
RUBRIC_CSV = "BYUMS RUBRIC - Sheet1.csv"


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--plan", required=True, help="plan PDF used as the example")
    p.add_argument("--scores", required=True, help="human-scored CSV for that plan")
    p.add_argument("--out", default=OUT)
    p.add_argument("--overrides", default="backend/data/bpc/few_shot_overrides.json",
                   help="optional curator score overrides (auditable adjustments)")
    args = p.parse_args(argv)

    # 1) example plan text
    ni = get_adapter(args.plan).load(args.plan)
    print(f"plan text: {len(ni.text)} chars from {args.plan}")

    # 2) human scores
    parsed = calibration.parse_scored_plan_csv(args.scores)
    items = parsed["items"]
    total_from_items = round(sum(it.awarded for it in items), 4)
    print(f"parsed {len(items)} scored criteria; sum={total_from_items}, grand_total={parsed['human_total']}")

    # 3) cross-check criterion names against the plan rubric (catch mismatches)
    plan_rubric, _ = rubric_csv.split_video_plan(rubric_csv.parse_byums_rubric_csv(RUBRIC_CSV))
    rubric_names = {r.criteria for r in plan_rubric}
    matched = [it for it in items if it.criteria in rubric_names]
    unmatched = [it for it in items if it.criteria not in rubric_names]
    print(f"criterion name match vs plan rubric: {len(matched)}/{len(items)} matched")
    if unmatched:
        print("  UNMATCHED (will not align to a rubric criterion):")
        for it in unmatched:
            print(f"   - {it.criteria!r}")
    missing = rubric_names - {it.criteria for it in items}
    if missing:
        print(f"  rubric criteria with NO human score ({len(missing)}):")
        for m in sorted(missing):
            print(f"   - {m}")

    example = calibration.FewShotExample(
        filename=os.path.basename(args.plan),
        business_name=parsed["business_name"] or "Example",
        plan_text=ni.text,
        items=matched,  # only criteria that align to the rubric
        human_total=parsed["human_total"] or total_from_items,
    )

    # Apply curator overrides (transparent, auditable adjustments to the anchor;
    # the raw human CSV is unchanged).
    if os.path.exists(args.overrides):
        with open(args.overrides, "r", encoding="utf-8") as fh:
            overrides = json.load(fh)
        changes = calibration.apply_overrides(example, overrides)
        print(f"\napplied {len(changes)} curator override(s) from {args.overrides}:")
        for ch in changes:
            print(f"   - {ch}")
        print(f"adjusted anchor total: {example.human_total}/80 (raw human was {parsed['human_total']}/80)")
    else:
        print(f"\n(no overrides file at {args.overrides})")

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump([example.to_dict()], fh, indent=2)
    print(f"\nwrote {args.out} — 1 example, {len(matched)} criteria, human_total={example.human_total}/80")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
