# GradeWise — Frontend Improvement Plan

**For:** BPC competition judges. **Posture:** blue-sky first. **Status:** plan only, not implemented.
Stack: Next.js 16 (App Router), React 19, TypeScript strict, Tailwind v4, framer-motion, next-themes, axios.

---

## Flagship: Live Grading Theater

Your explicit ask: *"where the grading is happening there should be image animations for each stage."* This is that, done for real.

### What's wrong today
- [GradingLoader.tsx](../../frontend/components/GradingLoader.tsx) shows 5 phases cycling on `setInterval(1800)` with `phaseIndex = (prev+1) % 5` — pure fiction, decoupled from the backend. The comment on line 55 says "to simulate progress."
- One advertised phase ("Retrieving Context / RAG vector db") does not even run for business plans (`skip_rag` defaults true).
- [grading/page.tsx](../../frontend/app/(dashboard)/grading/page.tsx) has a second stage array (`GRADING_MESSAGES` + `gradingStatusIndex`) that is **never rendered** — dead code.
- The BPC pages show only a generic `Loader2` spinner. No stages at all.

### The build
A single reusable `<GradingTheater />` component, driven by a real event stream (backend delivers it over SSE — see [backend plan](02-backend-plan.md#flagship-streaming-grading-pipeline-sse)).

1. **Consume the stream.** New hook `useGradingStream(payload)` opens an `EventSource`/fetch-stream to the backend's streaming grade endpoint. It maps incoming events to a stage machine: `screening → reading → judging → coaching → done` (plus `retrying` and `error`). Falls back to the current timer behavior if the stream endpoint is unavailable, so nothing regresses.
2. **A scene per stage.** Each stage gets a distinct illustrated animation, not an icon swap:
   - **Screening the gate** — a document sliding through a checkpoint; eligibility result stamps in (green "eligible" / amber "needs review" / red "ineligible") with the DQ reasons listed as they arrive. The AI-content flag appears here if set.
   - **Reading the plan** — pages turning. In **vision mode**, show the actual rendered slides flipping (the backend already renders them — surface them). A criterion ticker animates in: "Scored 3 / 12 — Market Sizing: 6/8." This is the moment that proves the plan was read.
   - **Second opinion** — a balance scale. If the Judge rejects and retries, the scale visibly rejects and the copy changes to "Judge sent it back: {reason} — re-scoring." Judges love seeing the self-correction; it is the app's most credible feature and today it is invisible.
   - **Coaching the team** — a pen writing; feedback text can stream in token by token if the backend streams it.
   - **Verdict** — score counts up; per-criterion bars animate from 0 to their values; the view hands off to `<GradeBreakdown />`.
3. **Art direction.** Use **Lottie** (`lottie-react`, vector, small, controllable play/pause/segment) for the five scenes, or hand-built framer-motion SVG scenes if you want zero new deps. Lottie is the faster path to "amazing" and lets a designer hand you `.json` scenes. Each scene plays on stage-enter and loops until the stage completes, then transitions out. Respect `prefers-reduced-motion` (drop to a calm static illustration + text).
4. **Honesty rule.** A stage only advances when its real event arrives. If grading is fast, stages flash by — that is correct and fine. No more fake 1.8s pacing.

**Effort:** frontend (human: ~4-6 days incl. sourcing/commissioning 5 scenes / CC: ~1-1.5 days for the machine + wiring, art sourced separately). Depends on the backend SSE endpoint landing first.

**Reuse everywhere:** `grading`, `bpc-grading`, `bpc-headtohead` all swap their spinner for `<GradingTheater />`. `mass-grading` and `bpc-screening` get the batch variant below.

---

## More amazing features (ranked by judge impact)

### 1. Live judge leaderboard (batch)
[bpc-screening/page.tsx](../../frontend/app/(dashboard)/bpc-screening/page.tsx) is already the strongest page (real determinate bar, client concurrency of 2, tie-aware shortlist, flagged/error buckets). Make it cinematic:
- Rows **reorder with animation** as scores land (framer-motion `layout` on a sorted list). A judge watches the ranking form in real time.
- A **shortlist cutoff line** that slides up/down as new scores push plans above/below it.
- Per-row mini-theater: the active row shows the current stage inline.
- Backed by a real batch service (today it fires N separate HTTP calls from the browser) — see [backend plan → Async batch service](02-backend-plan.md#4-async-batch-grading-service).

**Impact:** this is the judge's main workspace for a real competition. **Effort:** (human: ~3 days / CC: ~1 day) on top of the batch endpoint.

### 2. Evidence-linked feedback
When the backend returns the **evidence span** for each criterion (see [backend plan → Evidence spans](02-backend-plan.md#1-evidence-spans--citations)), make each criterion's reason clickable → scroll-to + highlight the exact passage in the plan that earned or lost the points. Split-pane: plan on the left, scorecard on the right.

**Impact:** the single biggest trust feature for judges — no more "why did it say that?" **Effort:** (human: ~2-3 days / CC: ~1 day). **Depends on** the backend returning spans.

### 3. Comparison & head-to-head upgrade
[bpc-headtohead/page.tsx](../../frontend/app/(dashboard)/bpc-headtohead/page.tsx) already aggregates by section. Add:
- A **radar chart** per plan (score by rubric section) with AI vs human overlaid, or plan A vs plan B.
- A **section-delta heatmap** so a judge sees at a glance where AI and human diverge.
- Pick-any-two comparison from the leaderboard.

**Impact:** competitions are decided at the margin; comparison is how judges break ties. **Effort:** (human: ~2 days / CC: ~0.5 day). Use a charting lib that renders inline (Recharts).

### 4. Vision slide gallery
When a plan is graded in vision mode, show the rendered slides in a gallery with per-slide annotations ("financials detected on slide 7", "license image on slide 12"). Makes the vision path tangible and shows *what the model actually saw*.

**Impact:** turns the hidden vision path into a visible advantage. **Effort:** (human: ~2 days / CC: ~0.5 day). **Depends on** the backend returning per-slide artifacts.

### 5. Judge report pack (export)
One-click export from the leaderboard: a committee-ready PDF/XLSX with the ranking, per-plan scorecards, per-criterion breakdown, feedback, and flags. Backend renders it (it already has `openpyxl`/`xlsxwriter`).

**Impact:** this is the deliverable the competition committee actually needs at the end. **Effort:** (human: ~2 days / CC: ~0.5 day front-end trigger + download UX). **Depends on** a backend export endpoint.

### 6. AI-content & needs-review triage screen
A dedicated queue for plans the pipeline flagged (`eligibility_status = needs_review`, `ai_content_flag = true`), showing the flag reasons, the plan, and a **judge override** (confirm / clear / disqualify) with an audit note. The competition explicitly asks judges to flag AI content — give them the workflow.

**Impact:** closes the human-in-the-loop that competition rules require. **Effort:** (human: ~2-3 days / CC: ~1 day). **Depends on** persistence + judge overrides in the backend.

### 7. Visual rubric builder
Replace the manual rows + hardcoded `handleAutoFillRubric` template in [grading/page.tsx](../../frontend/app/(dashboard)/grading/page.tsx) with a real rubric editor: tiered descriptions (full / partial / zero), max points, per-criterion teaching note (`course_guide`), live preview, and import from CSV/PDF (the backend already parses these via `/parse-rubric`).

**Impact:** lets a competition define its own rubric without touching code. **Effort:** (human: ~3 days / CC: ~1 day).

### 8. Multi-judge consensus view
Treat the AI as one judge among several humans. Show inter-rater agreement per plan, surface disagreements above a threshold for discussion. This is what elevates the tool from "AI grader" to "judging platform."

**Impact:** high, but the biggest lift — **depends on** judge accounts + persistence. Slot it after foundations. **Effort:** (human: ~1-2 weeks / CC: ~2-3 days).

---

## Foundations to not skip

These are secondary to the blue-sky work, but several features above sit directly on top of them. Flagged with which feature needs them.

- **Real persistence** *(blocks features 1, 6, 8)*. Today: a flat `data/submissions.json` (not concurrency-safe, non-durable in Docker/serverless) plus scattered `localStorage`; **BPC grading results are never saved at all** (lost on navigation). `@prisma/client` and `prisma` are installed but there is **no schema and zero usage** — either wire Prisma to SQLite/Postgres or pick a real store. See [backend plan → Persistence](02-backend-plan.md#8-persistence--results-store).
- **Error / loading / not-found boundaries**. `app/**` has no `error.tsx`, `loading.tsx`, or `not-found.tsx`. A backend 500 currently falls through to ad-hoc inline state. Add route-level boundaries.
- **Accessibility**. Exactly **one** `aria-*` attribute exists in the whole `.tsx` tree. Modals lack `role="dialog"`, focus trapping, and Esc-to-close; icon-only buttons rely on `title`. Do a pass, especially on the grading modal and theater.
- **Config hygiene**. [mass-grading/page.tsx](../../frontend/app/(dashboard)/mass-grading/page.tsx) hardcodes `http://127.0.0.1:8000` (lines 259, 313) — breaks on any non-local deploy; route it through `lib/api.ts`. `student_id` is hardcoded `"student-123"` in [grading/page.tsx:206](../../frontend/app/(dashboard)/grading/page.tsx#L206).
- **Unify the result view**. `/grading` uses a bespoke inline modal (score + feedback only, no per-criterion breakdown), while the BPC pages use the far richer [GradeBreakdown.tsx](../../frontend/components/GradeBreakdown.tsx). Make everything use `GradeBreakdown`.
- **Delete dead/shipped scaffolding**. Orphaned [GradeDetailsModal.tsx](../../frontend/components/GradeDetailsModal.tsx) (unused, diverges: percentage scoring + plain-text feedback), AI-authoring comments in `grading/page.tsx` (~lines 221-244), the unrendered `GRADING_MESSAGES` array.
- **Save-flow bug**. In `grading/page.tsx`, `handleSave` early-returns unless `?id=` is in the URL, so a freshly graded single submission can't be saved. History "re-grade" also grades placeholder text (`sub.title + "(Content loaded from history)"`, line 42), not the real submission.
- **Tests + mobile**. Zero frontend tests. Grading pages use `h-screen` + fixed two-column grids that are desktop-only; leaderboard/terminal tables aren't responsive.

---

## Suggested sequence

1. Backend SSE endpoint lands (backend plan flagship).
2. `<GradingTheater />` + `useGradingStream` (flagship) — reuse across single-grade pages.
3. Evidence-linked feedback (needs backend spans) + comparison charts (no backend dep) in parallel.
4. Real persistence, then live leaderboard + report pack + triage screen.
5. Foundations (a11y, boundaries, config hygiene, dead-code removal) folded in as you touch each page — don't batch them to the end.
