import { describe, it, expect } from "vitest";

import {
  nextStage, STAGE_ORDER, stageIndex, applyEvent, initialStreamState, type Stage,
} from "@/lib/gradingStages";

// Pure stage machine driving the GradingTheater. It is fed the SSE events the
// backend emits (screening -> reading -> judging -> coaching -> done), plus the
// judge-retry and error cases, and the theater renders the scene for the
// returned stage. Keeping it pure makes the animation logic testable.
describe("nextStage", () => {
  it("advances through the happy-path stages", () => {
    expect(nextStage("idle", { stage: "screening" })).toBe("screening");
    expect(nextStage("screening", { stage: "reading" })).toBe("reading");
    expect(nextStage("reading", { stage: "judging", is_valid: true })).toBe("judging");
    expect(nextStage("judging", { stage: "coaching" })).toBe("coaching");
    expect(nextStage("coaching", { stage: "done" })).toBe("done");
  });

  it("shows the retry scene when the judge rejects", () => {
    expect(nextStage("reading", { stage: "judging", is_valid: false, reason: "incomplete" }))
      .toBe("retrying");
  });

  it("maps an error event to the error stage", () => {
    expect(nextStage("reading", { stage: "error", message: "boom" })).toBe("error");
  });

  it("ignores an unknown event and keeps the current stage", () => {
    expect(nextStage("reading", { stage: "who-knows" })).toBe("reading");
  });
});

describe("STAGE_ORDER / stageIndex", () => {
  it("orders the visible pipeline stages for progress display", () => {
    expect(STAGE_ORDER).toEqual(["screening", "reading", "judging", "coaching", "done"]);
  });

  it("stageIndex returns position for a pipeline stage and -1 otherwise", () => {
    expect(stageIndex("judging")).toBe(2);
    expect(stageIndex("retrying" as Stage)).toBe(-1); // transient, not a progress step
  });
});

describe("applyEvent (stream accumulation)", () => {
  it("captures screening eligibility and flags", () => {
    const s = applyEvent(initialStreamState, {
      stage: "screening", eligibility_status: "needs_review",
      dq_reasons: ["missing license"], ai_content_flag: true,
    });
    expect(s.stage).toBe("screening");
    expect(s.screening).toEqual({
      eligibility_status: "needs_review", dq_reasons: ["missing license"], ai_content_flag: true,
    });
  });

  it("accumulates reading progress and running score", () => {
    const s = applyEvent(initialStreamState, { stage: "reading", criteria_scored: 4, score: 22 });
    expect(s.criteriaScored).toBe(4);
    expect(s.score).toBe(22);
  });

  it("records a judge rejection (moves to retrying, keeps the reason)", () => {
    const s = applyEvent(initialStreamState, {
      stage: "judging", is_valid: false, reason: "incomplete grade", revision_number: 1,
    });
    expect(s.stage).toBe("retrying");
    expect(s.judge).toEqual({ is_valid: false, reason: "incomplete grade", revision_number: 1 });
  });

  it("captures the final result on done and an error message on error", () => {
    const done = applyEvent(initialStreamState, { stage: "done", grade_result: { score: 7 } } as never);
    expect(done.stage).toBe("done");
    expect(done.result).toEqual({ score: 7 });
    const err = applyEvent(initialStreamState, { stage: "error", message: "boom" });
    expect(err.stage).toBe("error");
    expect(err.error).toBe("boom");
  });

  it("threads a full happy-path sequence", () => {
    const events = [
      { stage: "screening", eligibility_status: "eligible" },
      { stage: "reading", criteria_scored: 12, score: 74 },
      { stage: "judging", is_valid: true, revision_number: 0 },
      { stage: "coaching" },
      { stage: "done", grade_result: { score: 74 } },
    ];
    const final = events.reduce(applyEvent, initialStreamState);
    expect(final.stage).toBe("done");
    expect(final.criteriaScored).toBe(12);
    expect(final.result).toEqual({ score: 74 });
  });
});
