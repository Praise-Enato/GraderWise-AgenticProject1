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
  if (!event) return current; // ignore a missing/malformed frame rather than crash
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

// Accumulated view of a grading stream, built purely from the events so the
// hook (useGradingStream) is thin wiring and this stays unit-testable.
export interface StreamState {
  stage: Stage;
  screening: { eligibility_status: string; dq_reasons: string[]; ai_content_flag: boolean } | null;
  criteriaScored: number;
  score: number | null;
  judge: { is_valid: boolean; reason: string; revision_number: number } | null;
  result: unknown | null;
  error: string | null;
}

export const initialStreamState: StreamState = {
  stage: "idle",
  screening: null,
  criteriaScored: 0,
  score: null,
  judge: null,
  result: null,
  error: null,
};

export function applyEvent(state: StreamState, event: StageEvent): StreamState {
  if (!event) return state; // no-op on a missing/malformed frame
  const next: StreamState = { ...state, stage: nextStage(state.stage, event) };
  switch (event.stage) {
    case "screening":
      next.screening = {
        eligibility_status: String(event.eligibility_status ?? "eligible"),
        dq_reasons: (event.dq_reasons as string[]) ?? [],
        ai_content_flag: Boolean(event.ai_content_flag),
      };
      break;
    case "reading":
      next.criteriaScored = Number(event.criteria_scored ?? state.criteriaScored);
      next.score = event.score == null ? state.score : Number(event.score);
      break;
    case "judging":
      next.judge = {
        is_valid: Boolean(event.is_valid),
        reason: String(event.reason ?? ""),
        revision_number: Number(event.revision_number ?? 0),
      };
      break;
    case "done":
      next.result = (event as { grade_result?: unknown }).grade_result ?? null;
      break;
    case "error":
      next.error = String(event.message ?? "Grading failed");
      break;
  }
  return next;
}
