import { describe, it, expect } from "vitest";

import { nextStage, STAGE_ORDER, stageIndex, type Stage } from "@/lib/gradingStages";

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
