# TODOS

## Scale: cost + wall-clock for a full ~1,000-plan multimodal run
- **What:** Estimate and de-risk running the grader over the full competition (~1,000 plans),
  where each plan means grading slide text + slide images + a ~5-minute video.
- **Why:** The demo validates on 15 plans, but the pitch promises the full field. A board will
  ask "what does one full competition cost and how long does it take?" — you need a real answer.
- **Pros:** Arms the pitch with a concrete cost/time number; forces an early batching/caching plan
  before scale bites post-funding.
- **Cons:** Real numbers need the Phase-1b multimodal pipeline to exist first (to measure token +
  video costs); premature estimates could mislead.
- **Context:** Multimodal video grading (Gemini) is the expensive path — a 5-min video is a large
  input per plan. Consider a queue + concurrency cap, caching of extracted slide text/images, and
  whether first-round triage (DQ + cheap text pass) can cut the field before the expensive video
  pass runs. Surfaced in /plan-eng-review 2026-07-03; see design doc "NOT in scope".
- **Depends on / blocked by:** Phase 1b (Gemini video grading via the model router) must exist to
  measure real per-plan cost.
