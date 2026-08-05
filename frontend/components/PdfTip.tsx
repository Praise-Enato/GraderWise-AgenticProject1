import { Info } from "lucide-react";

/** Nudge toward PDF uploads. PDFs render as full pages (best, most consistent
 * grading); PPTX is supported but — without server-side slide rendering — its
 * native charts/layout aren't fully captured, so it can score a little lower. */
export function PdfTip() {
    return (
        <div className="flex items-start gap-2 text-xs text-slate-500 dark:text-slate-400">
            <Info className="w-3.5 h-3.5 mt-0.5 shrink-0 text-indigo-500" />
            <span>
                <b className="text-slate-600 dark:text-slate-300">PDF recommended</b> for the most
                accurate, consistent scoring (in PowerPoint: <i>File → Save As → PDF</i>). PPTX works,
                but its charts and layout aren&apos;t fully captured, so it can score a little lower.
            </span>
        </div>
    );
}
