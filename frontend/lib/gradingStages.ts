// Pure stage machine for the Live Grading Theater (eng review Phase 3).
//
// The backend streams SSE events (screening -> reading -> judging -> coaching
// -> done, plus error) produced from the REAL pipeline. This reducer maps each
// event to the stage whose scene the theater should show, so the animation is
// driven by actual progress rather than a timer. Keeping it pure means the
// hook (useGradingStream) and the component stay thin and this stays testable.

export type Stage =
  | "idle"
  | "screening"
  | "reading"
  | "judging"
  | "retrying"
  | "coaching"
  | "done"
  | "error";

// The stages shown as ordered progress steps. "retrying" is transient (the
// judge bounced a grade back) and "idle"/"error" are not progress steps.
export const STAGE_ORDER: Stage[] = ["screening", "reading", "judging", "coaching", "done"];

export interface StageEvent {
  stage: string;
  is_valid?: boolean;
  reason?: string;
  message?: string;
  [key: string]: unknown;
}

export function nextStage(current: Stage, event: StageEvent): Stage {
  switch (event.stage) {
    case "screening":
      return "screening";
    case "reading":
      return "reading";
    case "judging":
      // A rejected grade loops back to the grader; show the retry scene.
      return event.is_valid === false ? "retrying" : "judging";
    case "coaching":
      return "coaching";
    case "done":
      return "done";
    case "error":
      return "error";
    default:
      return current; // unknown event: hold the current scene
  }
}

export function stageIndex(stage: Stage): number {
  return STAGE_ORDER.indexOf(stage);
}
