/**
 * The business name is what identifies a graded plan — on screen, and as the
 * heading of the downloaded PDF report. A report whose owner you have to guess
 * is not usable, so resolve it in one place, in this order:
 *
 *   1. the business/team name the judge typed, if any (an explicit override)
 *   2. the name the backend read out of the plan document itself
 *      (GradeResult.business_name — see backend/src/business_name.py)
 *   3. only then the uploaded file's name, extension stripped
 *
 * The file name is genuinely last: entrants submit things like "Copy of Africa
 * Business Plan Competition - 2026  (1).pdf", which names the competition rather
 * than the business. It stays as a fallback because a few plans never state
 * their name anywhere in the document, and there the file name is the only clue.
 *
 * Returns "" when nothing is available — callers fall back to their own generic
 * label (the PDF builder falls back to "Business Plan Evaluation").
 */
export function planBusinessName(
    typedName?: string | null,
    extractedName?: string | null,
    filename?: string | null,
): string {
    const typed = (typedName || "").trim();
    if (typed) return typed;
    const extracted = (extractedName || "").trim();
    if (extracted) return extracted;
    return (filename || "").replace(/\.[^./\\]+$/, "").trim();
}
