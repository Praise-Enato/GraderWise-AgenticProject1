# GradeWise — Eng Review Decisions & Locked Plan

**Date:** 2026-07-07 · **Reviewer:** `/plan-eng-review` (full-depth) + independent outside voice · **Mode:** FULL_REVIEW
**Status:** reviewed, **NOT approved for implementation**. This document is the output of the review. Nothing is built until you give explicit approval.

This supersedes the sequencing in [00-OVERVIEW.md](00-OVERVIEW.md). The feature content in [01-frontend-plan.md](01-frontend-plan.md) and [02-backend-plan.md](02-backend-plan.md) still stands; the decisions and build order below override where they differ.

---

## The headline change

The review reordered the plan. The original flagship (grading-theater animation) moved from **first** to **Phase 3**, because an animation that presents scores the grader hasn't been shown to produce correctly **manufactures trust in unvalidated numbers**. Calibration and a defensible score come first. The theater still ships — it's still the signature experience — just after the numbers are trustworthy.

---

## Locked decisions

| # | Decision | Choice |
|---|----------|--------|
| A1 | Stream transport | **Job-id + EventSource GET** — `POST /grade/jobs` → `GET /grade/stream/{id}`; add a **Last-Event-ID replay** contract so a refresh/resume doesn't break the theater (OV#14) |
| A2 | Batch runner | **In-process asyncio workers + SQLite jobs table**, resume-after-restart required; **isolate batch from the interactive/SSE path** so a 1000-plan run can't starve live grading (OV#10); define resume granularity (per-plan) and single state owner (jobs table, not LangGraph checkpointer) |
| A3 | Persistence | **Backend-owned (Python/SQLAlchemy)**, SQLite→Postgres; **drop the unused frontend Prisma** |
| A4 | Ensemble coverage | Grade **every plan N times** (full coverage) |
| CQ1 | Aggregation | **Median per criterion + flag high spread**; add a **tie band / least-significant-difference** at the shortlist cutoff so sub-noise gaps don't decide prizes (OV#2) |
| CQ2 | Cleanup | **Include** dead-code + unused-Prisma removal in the work |
| CQ3 | Stream errors | **Explicit `error` SSE event + UI error state** with retry |
| T1 | Frontend tests | **Vitest + RTL + Playwright** (frontend has zero tests today) |
| T2 | Eval gate | **Calibration/eval harness is a prerequisite** and gates grader-prompt changes |
| P1 | Ensemble variance | **Reversed:** NOT temperature-varied. Use N samples at a **single fixed temperature or a real model panel**; report spread as *grader disagreement*, never as calibrated confidence (OV#1) |
| P2 | Cost control | **Two-pass triage + caching**, with a **fairness-safe cut**: never DQ on text alone — run vision on image-heavy/borderline plans; define the cut criterion (OV#5); reconcile cache keys with ensemble so caching doesn't collapse or bypass it (OV#6) |
| P3 | DB concurrency | **SQLite (WAL) now, Postgres later** |
| X4 | Grade-of-record | **Pin a canonical grade** per plan: model version, temperature(s), seeds, prompt hash, rendered-input hash — the ranking uses this re-derivable record (OV#8) |
| Video | Video grading | **Later phase**, and via the **native Gemini Files API** (the OpenAI-compatible route in `llm.py` won't accept video); video needs its **own calibration** — today's harness excludes the 20% video component (OV#4) |

Folded in as requirements (OV #2,3,4,6,7,10,11,12,13,14): tie-band; calibration statistical power + **inter-human agreement baseline**; video Files-API + calibration; cache↔ensemble reconciliation; **fuzzy/normalized evidence matching + a vision-mode evidence contract (slide/bbox)** since exact-substring fails on OCR/vision (OV#7); batch/interactive isolation + resume granularity; **auth as a prerequisite** for overrides/audit/multi-judge (OV#11); **prompt-injection defense** for attacker-controlled PDFs (OV#12); **fairness/disparate-impact analysis + AI-flag false-positive profile** for a variable-fluency African field (OV#13); SSE Last-Event-ID.

---

## What already exists (reuse, don't rebuild)

- **[backend/src/llm.py](../../backend/src/llm.py)** — model router (DeepSeek text + Gemini vision/video, task→model, unit-tested). The model-panel option for ensemble (P1) and any provider failover build on this. Caveat: its Gemini *video* config uses the OpenAI-compatible endpoint, which won't accept video — the video phase needs the native Files API.
- **`/grade-vision`** — already renders slides + grades multimodally. Vision fusion and the vision evidence contract extend it.
- **[bpc-screening](../../frontend/app/(dashboard)/bpc-screening/page.tsx)** — concurrency pool + leaderboard + flagged/error buckets. The live leaderboard builds on it.
- **`run_bpc_validation.py` + few-shot + head-to-head + human refs** — the calibration harness (T2) wires these into a standing eval. Reality check: only **one** few-shot example is committed and the gate is `--min-spearman 0.7` — statistically underpowered; add data and an inter-human baseline first (OV#3).
- **Judge / eligibility / per-criterion assessments** — already in the pipeline; evidence spans and validation attach to the existing `validate_grade`.

## NOT in scope (explicitly deferred, with rationale)

- **Video grading** — deferred to a later phase; needs Files API + separate calibration + a cost/wall-clock spike (~83h of source video across 1000 plans). Tracked in [TODOS.md](../../TODOS.md).
- **Multi-judge consensus UI** — deferred until auth + persistence land (depends on both).
- **Postgres migration** — deferred; SQLite (WAL) is adequate for a single-box competition run.
- **Redis/Celery queue** — rejected (A2): two innovation tokens of infra a solo deploy doesn't need.
- **RAG/grounding corpus for business plans** — already effectively off (`skip_rag` default); not revived here.

---

## Revised build order (calibration-first)

```
Phase 0 — Foundations
  persistence (SQLAlchemy, SQLite WAL) · auth + lock CORS · pin langgraph + add SSE lib
  · dead-code + Prisma cleanup · frontend test harness (Vitest+RTL+Playwright)

Phase 1 — Trust core  (GATES everything downstream)
  calibration/eval harness + inter-human baseline (prereq, gates grader changes)
  · evidence spans w/ fuzzy + vision contract + Judge rejection
  · defensible aggregate: fixed-temp OR model-panel ensemble → median + spread flag
    + tie-band + pinned grade-of-record
  · prompt-injection defense · fairness/disparate-impact + AI-flag FP profile

Phase 2 — Scale
  in-process workers + jobs table + resume + interactive isolation
  · two-pass fairness-safe triage + content-hash caching (reconciled w/ ensemble)

Phase 3 — Experience  (only after Phase 1 makes numbers trustworthy)
  SSE endpoint (job-id + Last-Event-ID) + error event · GradingTheater + useGradingStream
  · live leaderboard · evidence-linked UI · report pack · AI-flag/needs-review triage screen

Phase 4 — Later
  video via Gemini Files API + video calibration · multi-judge consensus
```

---

## Failure modes (new codepaths)

| Codepath | Realistic failure | Test? | Error handling? | User sees | Verdict |
|----------|-------------------|-------|-----------------|-----------|---------|
| SSE behind nginx | proxy buffers → stream hangs | needs E2E | `X-Accel-Buffering: no` + `proxy_buffering off` | silent hang | **CRITICAL** — addressed by A1/Phase 3 |
| Batch worker crash mid-run | in-flight work lost | needs test | resume from jobs table | partial leaderboard | addressed by A2 |
| Prompt injection in PDF | inflated score | needs test | input isolation + strip/flag | wrong score, integrity breach | **CRITICAL** — Phase 1 |
| Evidence quote not in source (OCR/vision) | hallucinated highlight or false-reject | needs test | fuzzy match + vision contract + Judge reject | wrong/absent highlight | addressed by Phase 1 |
| Triage drops image-strong plan | unfair DQ on weak text pass | needs test | vision-on-borderline cut | plan unfairly eliminated | **CRITICAL (fairness)** — P2 |
| Ensemble 1/N fails | skewed median | needs test | aggregate N-1; all-fail → `graded_ok=False` | none | addressed by A4/CQ1 |
| SQLite locked under workers | write failure mid-batch | needs test | WAL + writer discipline | batch error | addressed by P3 |

## Worktree parallelization

| Lane | Workstream | Modules | Depends on |
|------|-----------|---------|------------|
| A | Backend core: persistence → aggregate → triage/caching | `backend/src/` | — (persistence first) |
| B | Calibration/eval harness | `backend/scripts/`, `backend/tests/` | A (to store runs) |
| C | Frontend: test harness → theater/leaderboard/evidence UI | `frontend/` | SSE endpoint (A) + calibration gate (B) before theater |
| D | Security: auth + CORS + injection defense | `backend/src/main.py` + middleware | coordinates with A (shared `main.py`) |

**Execution:** launch A, B, C-harness in parallel worktrees. **Conflict flag:** D and A both touch `main.py` — sequence D's middleware after A's endpoint scaffolding or coordinate. C's theater waits on A's SSE endpoint and B's calibration gate.

---

## Implementation Tasks
Synthesized from this review. P1 blocks ship, P2 same-branch, P3 follow-up. Not to be started until approved.

- [ ] **T1 (P1, human: ~1wk / CC: ~2d)** — calibration — Build eval harness + inter-human baseline; gate grader-prompt changes on it.
  - Surfaced by: Test review T2 + OV#3. Files: `backend/scripts/`, `backend/tests/`. Verify: eval runs on human set, reports MAE/Spearman/section-bias.
- [ ] **T2 (P1, human: ~4d / CC: ~1.5d)** — grading — Evidence spans: grader returns quote; fuzzy/normalized match; vision-mode slide/bbox contract; Judge rejects unfound quotes.
  - Surfaced by: Code Quality + OV#7. Files: `backend/src/agent.py`, `models.py`. Verify: hallucinated quote rejected; OCR-mangled quote still matches.
- [ ] **T3 (P1, human: ~4d / CC: ~1.5d)** — grading — Defensible aggregate: fixed-temp or model-panel ensemble → median + spread flag + tie-band + pinned grade-of-record.
  - Surfaced by: Perf P1 + OV#1,#2,#8. Files: `backend/src/agent.py`, `grading.py`. Verify: variance predicts human disagreement; canonical grade re-derivable.
- [ ] **T4 (P1, human: ~3d / CC: ~1d)** — security — Prompt-injection defense (input isolation, strip/flag injected instructions) + lock CORS + auth on judge/admin/batch.
  - Surfaced by: Arch + OV#11,#12. Files: `backend/src/main.py`, middleware. Verify: white-text "award full marks" PDF doesn't inflate score; unauthenticated judge endpoint rejected.
- [ ] **T5 (P1, human: ~1wk / CC: ~2d)** — fairness — Disparate-impact analysis across language/region + AI-flag false-positive profile.
  - Surfaced by: OV#13. Files: `backend/scripts/`, `eligibility.py`. Verify: measured FP rate on non-native-English sample.
- [ ] **T6 (P1, human: ~4-5d / CC: ~1.5d)** — persistence — Backend-owned store (SQLAlchemy, SQLite WAL); drop frontend Prisma.
  - Surfaced by: Arch A3/P3 + CQ2. Files: `backend/src/`, `frontend/package.json`. Verify: concurrent worker writes don't lock.
- [ ] **T7 (P1, human: ~3d / CC: ~1d)** — frontend — Test harness: Vitest + RTL + Playwright.
  - Surfaced by: Test review T1. Files: `frontend/`. Verify: `npm test` runs; one theater E2E green.
- [ ] **T8 (P2, human: ~5d / CC: ~1.5d)** — batch — In-process workers + jobs table + resume + interactive isolation.
  - Surfaced by: Arch A2 + OV#10. Files: `backend/src/`. Verify: kill mid-run → resume, no lost plans.
- [ ] **T9 (P2, human: ~5d / CC: ~1.5d)** — batch — Two-pass fairness-safe triage + caching reconciled with ensemble.
  - Surfaced by: Perf P2 + OV#5,#6. Files: `backend/src/`. Verify: image-strong plan reaches vision; cache doesn't collapse ensemble.
- [ ] **T10 (P2, human: ~4-6d / CC: ~1.5d)** — frontend — SSE endpoint (job-id + Last-Event-ID + error event) + GradingTheater + useGradingStream. **After Phase 1.**
  - Surfaced by: Arch A1/CQ3 + OV#9,#14. Files: `backend/src/main.py`, `frontend/`. Verify: real stages; refresh mid-grade replays cleanly.
- [ ] **T11 (P3, human: ~1wk / CC: ~2d)** — video — Video grading via Gemini Files API + video calibration.
  - Surfaced by: OV#4 + TODOS.md. Files: `backend/src/llm.py`, `vision_grade.py`. Verify: 5-min video graded; cost/wall-clock measured.
- [ ] **T12 (P3, human: ~1d / CC: ~2h)** — deps — Pin langgraph, add SSE lib, remove dead code (GradeDetailsModal, GRADING_MESSAGES, /chat, scaffolding comments).
  - Surfaced by: Arch/CQ2. Files: `requirements.txt`, `frontend/`. Verify: build clean, no unused imports.

---

## GSTACK REVIEW REPORT

| Review | Trigger | Why | Runs | Status | Findings |
|--------|---------|-----|------|--------|----------|
| CEO Review | `/plan-ceo-review` | Scope & strategy | 0 | — | not run (optional) |
| Eng Review | `/plan-eng-review` | Architecture & tests (required) | 1 | issues_open → resolved | 4 arch + 3 quality + 3 perf decisions; 14 outside-voice findings (4 reversals accepted, 10 folded); 3 critical gaps |
| Design Review | `/plan-design-review` | UI/UX gaps | 0 | — | not run (suggested — Phase 3 has heavy UI) |
| Outside Voice | Claude subagent | Independent 2nd opinion | 1 | issues_found | 14 findings; Codex not installed (fell back to subagent) |

- **CROSS-MODEL:** review and outside voice agreed the plan was sound in shape but mis-calibrated on trust/order; four reversals (ensemble variance, build order, triage fairness, grade-of-record) accepted by the user.
- **VERDICT:** ENG REVIEW COMPLETE — plan hardened and reordered (calibration-first). **Awaiting explicit user approval before any implementation.** Design review suggested before Phase 3 (UI-heavy).

NO UNRESOLVED DECISIONS
