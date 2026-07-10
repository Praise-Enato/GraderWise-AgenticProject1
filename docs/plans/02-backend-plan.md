# GradeWise — Backend Improvement Plan

**For:** BPC competition judges. **Posture:** blue-sky first. **Status:** plan only, not implemented.
Stack: FastAPI, LangGraph, langchain-openai (DeepSeek `deepseek-chat`), ChromaDB/HF embeddings (RAG, mostly skipped for plans), pypdfium2 + Pillow (vision), python-pptx, pandas/openpyxl/xlsxwriter. Tests: 200 passing under `pytest`.

Pipeline today ([agent.py](../../backend/src/agent.py)): `prepare → grade_submission → validate_grade (Judge retry loop) → generate_feedback`, exposed as one blocking [`POST /grade`](../../backend/src/main.py#L103) that runs `agent.app.invoke(...)` in a threadpool and returns only at the end.

---

## Flagship: streaming grading pipeline (SSE)

This is the engine half of the [Live Grading Theater](01-frontend-plan.md#flagship-live-grading-theater). Everything the pipeline knows is thrown away until the end; stream it instead.

### The build
- Add **`POST /grade/stream`** returning Server-Sent Events (FastAPI `StreamingResponse` or `sse-starlette`).
- Drive it with LangGraph's native streaming: `async for event in agent.app.astream(inputs, stream_mode="updates")`. Each node's output becomes an SSE event:
  - `screening` — from `prepare`: `{eligibility_status, dq_reasons, ai_content_flag}`.
  - `reading` — from `grade_submission`: emit `{criteria_scored, total_criteria, last: {name, awarded, max}}`. Node-level first; per-criterion is the stretch below.
  - `judging` — from `validate_grade`: `{is_valid, reason, revision_number}`. When the Judge rejects and loops, the frontend shows the re-score. This is the highest-value event and today it is invisible.
  - `coaching` — from `generate_feedback`: optionally stream feedback tokens.
  - `done` — the final `GradeResult`.
- Keep `POST /grade` as-is for callers that want one shot (batch workers, tests).

### Per-criterion streaming (stretch)
To make the "reading" stage tick criterion by criterion, either (a) switch the grader to token streaming and parse assessments incrementally as the JSON array fills, or (b) grade the rubric in chunks and emit after each chunk. Start with node-level events (4 stages + judge retries); add per-criterion once the shape is proven. Chunked grading also helps long rubrics where a single call silently drops criteria (the Judge already catches this via `find_missing_criteria`).

**Effort:** (human: ~3-4 days / CC: ~1 day) for node-level SSE; per-criterion is +2-3 days.

---

## More amazing features (ranked by judge impact)

### 1. Evidence spans & citations
Have the grader return, per criterion, the **exact quote (and character offset) from the submission** that justifies the award. Add `evidence: str` (and optional `evidence_offset`) to [CriterionAssessment](../../backend/src/models.py#L20). It already survives to the API response, so the frontend can highlight it (see [frontend → Evidence-linked feedback](01-frontend-plan.md#2-evidence-linked-feedback)).

**Impact:** the biggest trust and auditability win for a competition — every point is traceable to a line in the plan. Also makes disputes resolvable. **Effort:** (human: ~2-3 days / CC: ~1 day) — mostly prompt + schema + a validation check that the quote actually appears in the source (reject hallucinated evidence in the Judge).

### 2. Ensemble grading + real confidence
`confidence_score` is **fake** today — derived from retry count, and [models.py:49](../../backend/src/models.py#L49) admits "NOT calibrated to correctness." Replace it:
- Grade each plan **N times** (same model, or a small panel of models via the `llm.py` abstraction) and aggregate per criterion (median / majority).
- Report **real confidence** as inverse variance across runs. Flag high-variance criteria for human review.

**Impact:** fairness and defensibility — a competition ranking backed by "we graded it 5 times and it was stable" is a different product than one LLM call. **Effort:** (human: ~3-4 days / CC: ~1-1.5 days). Cost scales with N — pair with caching (#9) and the batch service (#4).

### 3. Real calibration & evaluation harness
You already have the raw materials: `few_shot_examples.json`, human reference scores, `bpc-headtohead`, and `scripts/run_bpc_validation.py`. Turn them into a standing eval:
- Score the full human-graded set on every prompt change; report **MAE, correlation, and per-section bias** (AI vs human).
- Detect systematic severity drift (too generous on financials? too harsh on risk?) and feed it back into calibration.
- Gate prompt/model changes on the eval as a regression test (wire into `pytest` / CI).

**Impact:** this is what makes the grader trustworthy *and* improvable over time — the difference between "we think it's good" and "it agrees with our judges within X points." **Effort:** (human: ~1 week / CC: ~2 days).

### 4. Async batch grading service
Screening currently fires N separate HTTP calls from the browser at concurrency 2. Move batching server-side:
- **`POST /grade/batch`** accepts many submissions, runs a bounded worker pool, reports progress via SSE or a job-status poll.
- Handle provider rate limits properly — `benchmark_testing.md` notes Groq hit a 100k-tokens/day cap; add backoff + queueing so a big competition run doesn't fail halfway.

**Impact:** scales to a real competition (hundreds of plans) and powers the [live leaderboard](01-frontend-plan.md#1-live-judge-leaderboard). **Effort:** (human: ~4-5 days / CC: ~1.5 days).

### 5. Vision + text fusion
Today it's vision **or** text (`/grade` vs `/grade-vision`, one plan per call). Fuse them: extract text **and** render slides, grade with both so figures inside images and the narrative in text both count. The grader prompt already warns hard about "text-only, don't infer from headings" — fusion removes that blind spot instead of working around it.

**Impact:** fixes the core accuracy gap (financial tables, licenses, bank statements live in images). **Effort:** (human: ~3-4 days / CC: ~1 day).

### 6. Ingestion robustness
- **OCR fallback** for scanned PDFs (the frontend already warns when extraction is empty).
- Better table extraction so financial tables survive as structured text.
- Confirm `.pptx` (python-pptx) and `.docx` paths are covered end to end.

**Impact:** fewer "could not read this plan" dead ends during screening. **Effort:** (human: ~2-3 days / CC: ~1 day).

### 7. Stronger AI-content detection
`ai_content_flag` is a heuristic. The competition explicitly asks judges to flag AI-generated plans, so make it a real signal (stylometry / perplexity features or a classifier) with reasons attached, feeding the [triage screen](01-frontend-plan.md#6-ai-content--needs-review-triage-screen).

**Impact:** directly serves a competition rule. **Effort:** (human: ~3-5 days / CC: ~1-2 days). Treat output as advisory to a human, never an auto-DQ.

### 8. Persistence & results store
*(blocks frontend features 1, 6, 8)* Add a real store (Postgres via the Marketplace, or SQLite to start) for submissions, grades, per-criterion assessments, judge overrides, and an **audit trail** (who changed what, when). This is the backbone for saved leaderboards, the triage queue, multi-judge consensus, and report packs.

**Impact:** high — most of the durable judge workflow depends on it. **Effort:** (human: ~4-5 days / CC: ~1.5 days).

### 9. Cost & rate-limit resilience
- Retry/backoff + **provider failover** through the `llm.py` abstraction (DeepSeek primary → Groq/OpenAI fallback).
- **Cache** grades keyed by `(rubric hash + submission hash + model)` so re-runs and ensemble passes don't re-pay.
- Token budgeting per batch.

**Impact:** keeps a large competition run from failing or over-spending. **Effort:** (human: ~2-3 days / CC: ~1 day).

### 10. Judge report export endpoint
Render the leaderboard + per-plan scorecards to PDF/XLSX (openpyxl/xlsxwriter already installed) for [the frontend report pack](01-frontend-plan.md#5-judge-report-pack-export).

**Impact:** the committee's end deliverable. **Effort:** (human: ~2-3 days / CC: ~1 day).

---

## Foundations to not skip

- **Security / ops.** CORS is `allow_origins=["*"]` ([main.py:25](../../backend/src/main.py#L25)) and there is no auth. Before this is judge-facing: lock CORS to known origins, add auth on judge/admin endpoints, request size limits, and structured logging. Add a `/health` endpoint for the Docker/compose stack.
- **Remove dead code.** The commented-out `/chat` endpoint block ([main.py:141-192](../../backend/src/main.py#L141)) — delete or revive it deliberately.
- **Confidence honesty.** Until the ensemble (#2) lands, do not surface `confidence_score` as a real number in the UI (the frontend currently shows it). Either hide it or label it clearly as a heuristic.
- **Config.** BPC rubric/guideline are file-path env vars (`BPC_RUBRIC_CSV`, `BPC_GUIDELINE_MD`) — fine for now; move to the DB when persistence lands so a competition can be configured without redeploying.
- **Test coverage extensions.** The 200-test suite is a real asset. Extend it to cover the streaming endpoint, evidence-span validation, ensemble aggregation, and the calibration eval as a regression gate.

---

## Suggested sequence

1. **SSE streaming endpoint** (flagship) — unblocks the frontend theater.
2. **Evidence spans** (#1) — small, high trust, unblocks evidence-linked feedback.
3. **Persistence** (#8) + **batch service** (#4) — unblock leaderboard, triage, report pack.
4. **Ensemble + real confidence** (#2) and **calibration harness** (#3) — the credibility core; pair with caching (#9).
5. **Vision fusion** (#5), **ingestion** (#6), **AI-content** (#7), **export** (#10).
6. Security/ops and dead-code cleanup folded in continuously, not saved for the end.
