/**
 * The business name is what identifies a graded plan — on screen, and as the
 * heading of the downloaded PDF report. A report whose owner you have to guess
 * from the file name is not usable, so resolve it in one place:
 *
 *   1. the business/team name the judge typed, if any
 *   2. otherwise the uploaded plan's file name with its extension stripped
 *
 * Returns "" when neither is available — callers fall back to their own generic
 * label (the PDF builder falls back to "Business Plan Evaluation").
 */
export function planBusinessName(typedName?: string | null, filename?: string | null): string {
    const typed = (typedName || "").trim();
    if (typed) return typed;
    return (filename || "").replace(/\.[^./\\]+$/, "").trim();
}
