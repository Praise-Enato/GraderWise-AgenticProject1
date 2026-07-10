# GradeWise — Improvement Plan (Overview)

**Date:** 2026-07-07
**Primary user this plan optimizes for:** BYUMS Africa Business Plan Competition **judges** (screening and ranking many plans against a fixed rubric).
**Posture:** blue-sky features first. The exciting, differentiating work leads; the foundational fixes are listed honestly but come second.
**Status:** plan only. Nothing here is implemented.

Read this file first, then:
- [Frontend plan](01-frontend-plan.md) — the judge-facing experience (grading theater, live leaderboard, evidence-linked feedback, report packs).
- [Backend plan](02-backend-plan.md) — the engine (streaming pipeline, evidence spans, ensemble scoring, real calibration, batch service).

---

## Where the product is today (one screen)

GradeWise grades business plans against a rubric with an agentic pipeline:

```
prepare (eligibility screen + optional RAG/grounding + few-shot calibration)
  → grade_submission (DeepSeek LLM, one assessment per criterion, JSON)
  → validate_grade (pure-Python Judge: bounds + completeness, self-correcting retry loop)
  → generate_feedback (BYUMS-voice participant feedback + assemble GradeResult)
```

That pipeline lives in [backend/src/agent.py](../../backend/src/agent.py) and is exposed as a single blocking call at [`POST /grade`](../../backend/src/main.py#L103). A vision path ([`POST /grade-vision`](../../backend/src/main.py#L200)) renders PDF slides to images and grades them multimodally.

The frontend (Next.js 16, React 19, Tailwind v4, framer-motion) has five grading surfaces: `grading` (single), `mass-grading` (batch), `bpc-grading`, `bpc-screening` (the strongest page — real leaderboard + concurrency), and `bpc-headtohead` (AI vs human).

**The gap that defines this plan:** the app *markets* a multi-stage agent (analyze → context → rubric → judge → refine) in its loader copy, but the frontend gets one request and one response. Every "stage" the judge sees today is a timer or a hardcoded string ([GradingLoader.tsx:54-60](../../frontend/components/GradingLoader.tsx#L54-L60) literally comments "to simulate progress"). The real stages, the judge's self-correction, the per-criterion scoring, the eligibility flags — all of it happens invisibly and lands at once.

---

## The flagship: Live Grading Theater (spans both plans)

Turn the wait into the product's signature moment. While a plan is graded, the judge watches the **real** pipeline happen, stage by stage, each with its own illustrated animation and real substance streamed in:

| Stage | What the judge sees | Real data behind it |
|-------|--------------------|---------------------|
| **Screening the gate** | A plan sliding through a checkpoint; eligibility flags stamp in | `prepare` node: eligibility status, DQ reasons, AI-content flag |
| **Reading the plan** | Pages turning / slides rendering (vision mode shows the actual slides) | `grade_submission`: criteria scored, ticking in one by one |
| **Second opinion** | A scale balancing; if the Judge rejects, it visibly bounces back — "re-scoring" | `validate_grade`: valid / rejected + the rejection reason, retry count |
| **Coaching the team** | A pen writing feedback | `generate_feedback`: BYUMS-voice feedback assembling |
| **Verdict** | Score reveal, per-criterion bars animate to their values | final `GradeResult` |

This needs two halves that are split across the two plans:
- **Backend** streams real pipeline events over SSE (langgraph `astream`). See [backend plan → Flagship](02-backend-plan.md#flagship-streaming-grading-pipeline-sse).
- **Frontend** consumes the stream and drives per-stage image animations off real events. See [frontend plan → Flagship](01-frontend-plan.md#flagship-live-grading-theater).

Why it matters for judges: it converts dead waiting time into a trust-building window. A judge sees the plan was actually read, sees the self-correction fire, sees which criteria scored and why. That is the difference between "an AI spat out a number" and "I watched it work."

---

## How the two plans are organized

Each plan is ordered the way you asked — **blue-sky first**:

1. **Flagship** — the grading theater half for that side.
2. **More amazing features** — ranked by judge impact, each with why / impact / rough effort.
3. **Foundations to not skip** — the real gaps found in review. Secondary, but some of the blue-sky features sit on top of them (real persistence, evidence spans), so they are flagged where a feature depends on one.

Effort is dual-scaled where useful: **(human: X / CC: Y)** — human-team estimate vs Claude Code assisted.

---

## The five bets, if you only read this page

1. **Live Grading Theater** — real streamed stages + rich per-stage imagery. The signature feature. (FE + BE)
2. **Evidence-linked scoring** — every criterion award cites the exact passage in the plan. Trust and auditability for a competition. (BE returns spans → FE highlights them)
3. **Live judge leaderboard** — batch screening with animated rank changes and a moving shortlist cutoff line. (FE, on top of a real batch service in BE)
4. **Real calibration + confidence** — measure AI-vs-human agreement on the human-scored set, report a real confidence (today's is fake, derived from retry count), flag high-variance plans for human review. (BE)
5. **Judge report pack** — one-click export of the leaderboard + per-plan scorecards to PDF/XLSX for the competition committee. (FE trigger, BE render)
