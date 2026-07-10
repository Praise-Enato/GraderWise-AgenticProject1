# GradeWise — Implementation Audit (plan vs. what was built)

**Date:** 2026-07-09 · **Branch:** `feat/trust-core-calibration` · **HEAD:** `c641eaa`
**Tests:** backend 301 passed · frontend 25 passed · 0 regressions.
**Scope:** audits [03-eng-review-decisions.md](03-eng-review-decisions.md) against the 14 commits on this branch.

## Bottom line
The building blocks are done and well-tested, and (as of `c641eaa`) the **backend integration layer is now wired**: `/grade` persists + pins a grade-of-record, injection screening runs in the pipeline, and `/leaderboard` + `/grade/batch` drive the tie-band, fairness, persistence, and batch modules. What remains: **frontend wiring** (theater into the real pages, submission records off `submissions.json`), a few **not-started items** (auth, fairness-safe triage, Last-Event-ID replay, vision evidence contract, nginx stream config), and — the big one — **nothing that depends on the live LLM has been run end-to-end**.

Legend: ✅ done & integrated · 🟡 built but NOT wired into the running product · ⚠️ partial / deviation · ❌ not done · ⏸️ deferred on purpose

---

## Architecture decisions
| # | Decision | Status | Notes |
|---|----------|--------|-------|
| A1 | SSE stream: job-id + EventSource GET | ⚠️ | Endpoint built + handshake tested. **Last-Event-ID replay NOT implemented** (a reconnect 404s — OV#14). **nginx.conf NOT updated** (only the `X-Accel-Buffering` response header is set). Not run E2E. |
| A2 | In-process workers + jobs table + resume | ✅ | Wired via `POST /grade/batch` (+ `GET /grade/batch/{id}`); resumable, tested through the API. Caveats: runs **in-request** (move to a background worker for a large field); grading itself needs a live key. Interactive-path isolation still not implemented. |
| A3 | Backend-owned persistence (SQLAlchemy, SQLite WAL); drop Prisma | ✅ | `/grade` + `/grade/batch` persist submission + grade + assessments; Prisma dropped. Note: the Next.js **submission records** still use `submissions.json` (a separate frontend migration). |
| A4 | Ensemble every plan N times | ✅ | Wired into the grader (flag `ensemble_n`, default 1). Aggregation tested. Not verified E2E. |

## Code quality
| # | Decision | Status | Notes |
|---|----------|--------|-------|
| CQ1 | Median + spread flag | ✅ | Wired into the ensemble path, tested. |
| CQ2 | Cleanup (dead code, Prisma) | ⚠️ | `/chat` removed ✅, Prisma dropped ✅, `GradeDetailsModal` correctly kept (plan was wrong). **`GRADING_MESSAGES` dead code still present** in `grading/page.tsx` (deferred to a theater swap that hasn't happened). |
| CQ3 | Explicit stream error event + UI state | ✅ | `grade_error` event + theater error scene, tested. |

## Tests
| # | Decision | Status | Notes |
|---|----------|--------|-------|
| T1 | FE harness: Vitest + RTL + Playwright | ⚠️ | Vitest + RTL ✅ (25 tests). **Playwright E2E not set up.** |
| T2 | Eval harness gates grader changes | 🟡 | Harness enhanced (bootstrap CI, human ceiling) and wired into `run_bpc_validation`. **Not a CI gate**; grader changes are opt-in flags, not blocked by an eval run. Needs a real human-scored/multi-rater dataset. |

## Performance
| # | Decision | Status | Notes |
|---|----------|--------|-------|
| P1 | Fixed-temp (or panel) ensemble, not temp-varied | ✅ | Implemented as fixed moderate temp × N. |
| P2 | Two-pass fairness-safe triage + caching | ❌ | **Triage pipeline not built.** `cache_key` primitive exists but no cache layer is wired. |
| P3 | SQLite WAL now | ✅ | WAL + FK pragmas enabled and tested. |

## Outside-voice reversals
| # | Decision | Status | Notes |
|---|----------|--------|-------|
| X1 | Fixed temp, not temperature-varied | ✅ | Done. |
| X2 | Calibrate before the theater | ✅ | Trust-core built first; theater is preview-only (not presenting live unvalidated scores). |
| X3 | Fairness-safe triage cut | ❌ | Triage not built at all. |
| X4 | Pinned grade-of-record | ✅ | `record_for` populates a grade-of-record on every `/grade` + `/grade/batch` result and persists it (model, temps, input hash, per-criterion). Re-derivable once a grade is produced with a key. |

## The 10 folded findings
| # | Item | Status | Notes |
|---|------|--------|-------|
| 2 | Tie-band at cutoff | ✅ | Wired into `GET /leaderboard` (flags the contested admit/reject zone); tested end to end. |
| 3 | Calibration power + inter-human baseline | ✅ | Bootstrap CI + `human_ceiling` built + wired into the eval report. Needs real multi-rater data to be meaningful. |
| 4 | Video via Gemini Files API + video calibration | ⏸️ | Deferred (correct). |
| 6 | Cache ↔ ensemble reconciliation | 🟡 | `cache_key` handles it; no cache layer built. |
| 7 | Fuzzy + vision-mode evidence | ⚠️ | Fuzzy matching ✅ (wired into the Judge). **Vision-mode contract (slide/bbox) not built.** |
| 10 | Batch/interactive isolation + resume granularity | 🟡 | Per-item resume ✅. Isolation from the interactive event loop not implemented. |
| 11 | Auth as a prerequisite | ❌ | **No auth implemented** on judge/admin/batch endpoints. |
| 12 | Prompt-injection defense | ✅ | Wired into the `prepare` node as an advisory note (never auto-DQ); tested. Input isolation in the grader prompt still not applied. |
| 13 | Fairness / disparate-impact | ✅ | Wired into `GET /leaderboard` (flag rate + disparate-impact ratio + mean score per group); tested. Needs real per-plan group metadata to be meaningful. |
| 14 | SSE Last-Event-ID replay | ❌ | Not implemented. |

## Foundations / ops
- `/health` ✅ · dep pins (langgraph, sse-starlette, SQLAlchemy) ✅ · dead `/chat` removed ✅.
- **CORS**: ⚠️ overridable via `ALLOWED_ORIGINS`, but default is still `*` (documented, not locked).

## Cross-cutting gaps
1. **Integration layer — mostly wired now** (`c641eaa`). `persistence`, `batch`, `injection`, `fairness`, `tie-band`, and `grade_record` are integrated into the backend (`/grade`, `/leaderboard`, `/grade/batch`, the `prepare` node); `evidence` + `aggregate` were already wired into the grader; `interrater`/bootstrap-CI are wired into the eval script. Remaining not-wired: the **frontend** (theater into real pages; submission records off `submissions.json`).
2. **No end-to-end verification (unchanged).** Everything that calls the LLM — evidence spans, ensemble, the SSE stream, and now `/grade` persistence + `/grade/batch` grading — is verified only by pure-unit tests + endpoint tests with the model substituted, **never by a real graded plan** (no `DEEPSEEK_API_KEY` run).
3. **GradingTheater is preview-only.** It renders at `/theater-preview` (verified in a real browser) but is **not wired into `bpc-grading`/`grading`**; those pages still show their old spinner.
4. **Security not addressed** beyond CORS-overridable: no auth, no request-size limits.

## What IS done well (for balance)
- 8 pure, TDD'd modules (human ceiling, evidence guard, ensemble aggregate, injection detector, fairness, grade-of-record, bootstrap CI, batch service) — 93 new backend tests.
- Evidence + ensemble genuinely wired into the grader (opt-in, default-safe).
- Persistence schema + resumable batch service + SSE endpoint + the full stage contract, all tested.
- The flagship theater with 3D scenes, visually verified in a headless browser.
- Zero regressions across the whole run; every module built RED→GREEN.

## Recommended next steps (to actually finish)
1. **Verify E2E with a real key**: one plan through `/grade` with `use_evidence`+`ensemble_n`, and one through `/grade/stream/*` into the theater.
2. **Wire the integration layer**: `/grade` (and a new `/grade/batch`) persist via `persistence` + drive the `batch` service; call the `injection` detector on input; populate `grade_of_record`.
3. **Wire the theater** into `bpc-grading` (and remove `GRADING_MESSAGES` then).
4. **Finish the deferred security/robustness**: auth, CORS default, Last-Event-ID replay, nginx streaming config, the fairness-safe triage pipeline, the vision evidence contract.
