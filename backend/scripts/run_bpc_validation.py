"""Business Plan Grader — reliability validation harness (the go/no-go gate).

Grades the ground-truth plans through the running backend and reports how well
the AI's scores agree with the human judges' scores. This is Phase 1a's gate:
if agreement is good, proceed to video grading + the dashboard; if not, fix the
grader before building any UI.

It validates the PLAN component (80%) by default, because the text grader cannot
see the 20% video — comparing against the human TOTAL would be a confounded
target (see the engineering review).

The correctness-critical aggregation lives in backend.src.validation (pure,
unit-tested). This script is only the IO: read inputs, call /grade concurrently
with backoff, hand results to the tested functions, print the report.

Usage:
    python -m backend.scripts.run_bpc_validation \
        --manifest backend/data/bpc/ground_truth.csv \
        --plans-dir backend/data/bpc/plans \
        --rubric backend/data/bpc/rubric.json \
        --guideline backend/data/bpc/guideline.txt \
        --component plan \
        --api-url http://127.0.0.1:8000/grade \
        --concurrency 4 --max-retries 1 --min-spearman 0.7
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys

# Ensure repo root on path when run as a file (also works via -m).
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.src import validation as V
from backend.src import interrater as IR
from backend.src.input_adapter import get_adapter

RETRYABLE_STATUS = {429, 500, 502, 503, 504}


def _load_rubric(path: str) -> list:
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if isinstance(data, dict):
        data = data.get("rubric") or data.get("items") or []
    if not isinstance(data, list) or not data:
        raise ValueError(f"rubric file {path} must contain a non-empty list of criteria")
    return data


def _load_guideline(path: str | None) -> str:
    if not path:
        return ""
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def _plan_text(plans_dir: str, filename: str) -> tuple[str, list]:
    """Extract plan text via the input adapter. Returns (text, notes)."""
    path = filename if os.path.isabs(filename) else os.path.join(plans_dir, filename)
    normalized = get_adapter(path).load(path)
    return normalized.text, normalized.notes


async def _grade_one(client, api_url, record, plans_dir, rubric, guideline,
                     max_retries, sem, backoff_base=1.5):
    import httpx  # lazy: only needed at run time

    async with sem:
        try:
            text, notes = _plan_text(plans_dir, record.filename)
        except Exception as e:
            print(f"  ! {record.filename}: could not read plan ({e})")
            return V.PlanGrade(record.filename, 0.0, graded_ok=False, eligibility_status="needs_review")

        if not text.strip():
            print(f"  ! {record.filename}: no text extracted (scanned PDF? notes={notes})")

        payload = {
            "submission_files": [{"filename": record.filename, "content": text}],
            "student_id": record.filename,
            "rubric": rubric,
            "guideline": guideline,
            "skip_rag": True,
            "max_retries": max_retries,
        }

        attempt = 0
        while True:
            attempt += 1
            try:
                resp = await client.post(api_url, json=payload, timeout=180)
                if resp.status_code in RETRYABLE_STATUS:
                    raise _Retry(f"HTTP {resp.status_code}")
                resp.raise_for_status()
                data = resp.json()
                criteria = {
                    a.get("criteria_name", f"c{i}"): float(a.get("awarded_points", 0.0))
                    for i, a in enumerate(data.get("assessments", []))
                }
                print(f"  ✓ {record.filename}: score={data.get('score')} "
                      f"graded_ok={data.get('graded_ok', True)} "
                      f"eligibility={data.get('eligibility_status', 'eligible')}")
                return V.PlanGrade(
                    filename=record.filename,
                    ai_score=float(data.get("score", 0.0)),
                    graded_ok=bool(data.get("graded_ok", True)),
                    eligibility_status=data.get("eligibility_status", "eligible"),
                    criteria=criteria,
                )
            except (_Retry, httpx.TimeoutException, httpx.HTTPError) as e:
                if attempt > 3:
                    print(f"  ! {record.filename}: giving up after {attempt} attempts ({e})")
                    return V.PlanGrade(record.filename, 0.0, graded_ok=False,
                                       eligibility_status="needs_review")
                sleep_s = backoff_base ** attempt
                print(f"  ~ {record.filename}: retry {attempt} in {sleep_s:.1f}s ({e})")
                await asyncio.sleep(sleep_s)


class _Retry(Exception):
    pass


async def _run(args):
    import httpx
    ground_truth = V.load_ground_truth(args.manifest)
    rubric = _load_rubric(args.rubric)
    guideline = _load_guideline(args.guideline)
    print(f"Loaded {len(ground_truth)} ground-truth plans, {len(rubric)} rubric criteria. "
          f"Component={args.component}. Concurrency={args.concurrency}, max_retries={args.max_retries}.")

    sem = asyncio.Semaphore(args.concurrency)
    async with httpx.AsyncClient() as client:
        tasks = [
            _grade_one(client, args.api_url, rec, args.plans_dir, rubric, guideline,
                       args.max_retries, sem)
            for rec in ground_truth
        ]
        grades = await asyncio.gather(*tasks)

    report = V.join_and_aggregate(
        list(grades), ground_truth, component=args.component,
        bootstrap_resamples=args.bootstrap, bootstrap_seed=args.bootstrap_seed,
    )
    # Human ceiling from per-rater manifest scores (empty verdict when the
    # manifest carries no per-rater columns — degrades gracefully).
    ceiling = IR.human_ceiling(ground_truth)
    return report, ceiling


def _print_report(report: V.ValidationReport, min_spearman: float, ceiling=None) -> int:
    ag = report.agreement
    print("\n" + "=" * 64)
    print("RELIABILITY REPORT (honest — small n, wide CI expected)")
    print("=" * 64)
    print(f"  plans graded:        {report.scored + report.flagged}")
    print(f"  scored (eligible):   {report.scored}")
    print(f"  flagged for review:  {report.flagged}")
    print(f"  matched to human:    {report.matched}")
    if report.unmatched_filenames:
        print(f"  unmatched (no GT):   {report.unmatched_filenames}")
    if report.missing_human_score:
        print(f"  missing human score: {report.missing_human_score}")
    print(f"\n  {ag.summary()}")
    if ag.per_criterion:
        print("  per-criterion:")
        for name, sub in ag.per_criterion.items():
            print(f"    - {name}: {sub.summary()}")

    # Human ceiling: agreement is only meaningful relative to how much the
    # human judges agree with each other (OV#3). Printed only when the manifest
    # carried per-rater scores.
    if ceiling is not None and ceiling.mean_pairwise_spearman is not None:
        hc = ceiling.mean_pairwise_spearman
        verdict = IR.interpret_vs_ceiling(ag.spearman, hc)
        readable = {
            "below_ceiling": "BELOW the human ceiling — real room to improve",
            "at_ceiling": "AT the human ceiling — effectively as good as a human judge",
            "above_ceiling_watch": "ABOVE the human ceiling — WATCH: likely overfitting one rater",
            "no_baseline": "no baseline",
        }.get(verdict, verdict)
        print(f"\n  human ceiling (inter-rater): spearman={hc:.3f} "
              f"over {ceiling.n_items} plans, {ceiling.n_raters} raters")
        print(f"  AI vs ceiling: {readable}")

    print("\n  NOTE: with a small n the confidence interval is wide. Report this as an")
    print("  ENCOURAGING SIGNAL, not proof. Lean on per-criterion agreement and reading")
    print("  a few justifications aloud (face validity), not a single correlation number.")

    # GO/NO-GO hint (advisory only)
    sp = ag.spearman
    verdict = "INSUFFICIENT DATA"
    if sp is not None:
        verdict = "GO (signal above threshold)" if sp >= min_spearman else "NO-GO (below threshold — fix grader)"
    print(f"\n  GO/NO-GO hint (spearman >= {min_spearman}?): {verdict}")
    print("=" * 64)
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description="BPC grader reliability validation harness")
    p.add_argument("--manifest", required=True, help="ground-truth CSV/JSON (filename + human scores)")
    p.add_argument("--plans-dir", default=".", help="directory holding the plan PDFs")
    p.add_argument("--rubric", required=True, help="rubric JSON (list of criteria)")
    p.add_argument("--guideline", default=None, help="judges' guideline text file (optional)")
    p.add_argument("--component", default="plan", choices=["plan", "total", "video"],
                   help="which human score to compare against (default: plan / 80%%)")
    p.add_argument("--api-url", default="http://127.0.0.1:8000/grade")
    p.add_argument("--concurrency", type=int, default=4)
    p.add_argument("--max-retries", type=int, default=1, help="Judge retries per plan (batch: keep low)")
    p.add_argument("--min-spearman", type=float, default=0.7, help="advisory go/no-go threshold")
    p.add_argument("--bootstrap", type=int, default=0,
                   help="bootstrap resamples for a distribution-free CI on Spearman (0 = off)")
    p.add_argument("--bootstrap-seed", type=int, default=None,
                   help="seed for a reproducible bootstrap CI")
    args = p.parse_args(argv)

    report, ceiling = asyncio.run(_run(args))
    return _print_report(report, args.min_spearman, ceiling)


if __name__ == "__main__":
    raise SystemExit(main())
