import { Info } from "lucide-react";

/** Nudge toward PDF uploads.
 *
 * A PDF's pages are rendered to images and read by the vision model. Every other
 * accepted format is graded from its extracted text (plus any pictures it
 * embeds) — page rendering for DOCX/PPTX would need LibreOffice, which is not in
 * the image. That difference is measurable: on the deployed model the same plan
 * graded from text alone scored ~5 points lower (of 80) than with its pages
 * rendered, the gap concentrated in the Financials criteria — a flat list of
 * table cells reads worse than a table. Hence "preferred", not just "supported".
 */
export function PdfTip() {
    return (
        <div className="flex items-start gap-2 rounded-lg border border-indigo-100 dark:border-indigo-900/40 bg-indigo-50/60 dark:bg-indigo-900/10 px-3 py-2 text-xs text-slate-600 dark:text-slate-300">
            <Info className="w-3.5 h-3.5 mt-0.5 shrink-0 text-indigo-500" />
            <span>
                <b className="text-slate-800 dark:text-slate-100">PDF preferred.</b> A PDF&apos;s pages are
                rendered and read as images, which scores most consistently. DOCX, PPTX, TXT and MD are
                accepted, but they are graded from their text (plus any pictures they embed), so tables,
                charts and layout aren&apos;t seen as laid out — the same plan can score lower. In Word or
                PowerPoint: <i>File → Save As → PDF</i>.
            </span>
        </div>
    );
}
