"use client";

import { useState, useEffect } from "react";
import { GradeWiseAPI, RubricItem, GradeResult, SUPPORTED_PLAN_TYPES, isSupportedPlanFile } from "@/lib/api";
import { Upload, FileText, Trash2, Sparkles, Loader2, CheckCircle, AlertTriangle, Briefcase, Eye, Download } from "lucide-react";
import { PdfTip } from "@/components/PdfTip";
import { motion, AnimatePresence } from "framer-motion";
import GradeBreakdown from "@/components/GradeBreakdown";
import { planBusinessName } from "@/lib/planName";

export default function BpcGradingPage() {
    const [rubric, setRubric] = useState<RubricItem[]>([]);
    const [guideline, setGuideline] = useState("");
    const [planTotal, setPlanTotal] = useState(0);
    const [rubricError, setRubricError] = useState<string | null>(null);
    const [rubricMode, setRubricMode] = useState<"byums" | "general">("byums");

    const [teamName, setTeamName] = useState("");
    const [files, setFiles] = useState<{ filename: string; content: string; file?: File }[]>([]);
    const [isExtracting, setIsExtracting] = useState(false);
    const [vision, setVision] = useState(false);

    const [isGrading, setIsGrading] = useState(false);
    const [result, setResult] = useState<GradeResult | null>(null);
    const [error, setError] = useState<string | null>(null);
    // Business the displayed result belongs to, snapshotted at grade time — the
    // heading must not drift if the name field or the file list is edited after.
    const [gradedBusiness, setGradedBusiness] = useState("");

    // Report delivery (PDF download)
    const [action, setAction] = useState<"" | "pdf">("");
    const rubricLabel = rubricMode === "byums" ? "BYUMS Competition (80)" : "General Business (100)";

    useEffect(() => {
        let active = true;  // ignore stale responses if the mode is switched mid-fetch
        setRubricError(null); setRubric([]); setResult(null);
        if (rubricMode === "general") {
            GradeWiseAPI.getGeneralRubric()
                .then((d) => { if (!active) return; setRubric(d.rubric); setGuideline(""); setPlanTotal(d.total); })
                .catch((e) => { if (active) setRubricError(e?.message || "Could not load the general rubric."); });
        } else {
            GradeWiseAPI.getBpcRubric()
                .then((data) => { if (!active) return; setRubric(data.plan); setGuideline(data.guideline || ""); setPlanTotal(data.plan_total); })
                .catch((e) => { if (active) setRubricError(e?.message || "Could not load the BYUMS rubric from the backend."); });
        }
        return () => { active = false; };
    }, [rubricMode]);

    const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const list = e.target.files;
        if (!list || list.length === 0) return;
        setIsExtracting(true);
        setError(null);
        try {
            const fileArray = Array.from(list);
            const extracted = await GradeWiseAPI.extractFilesContent(fileArray);
            // keep the raw File alongside extracted text (vision mode uploads the PDF)
            setFiles((prev) => [...prev, ...extracted.map((e, i) => ({ ...e, file: fileArray[i] }))]);
        } catch (err: any) {
            setError(err?.message || "Failed to extract text from the file.");
        } finally {
            setIsExtracting(false);
            e.target.value = "";
        }
    };

    const grade = async () => {
        if (files.length === 0) { setError("Upload a plan first (PDF, PPTX, or DOCX)."); return; }
        if (rubric.length === 0) { setError("Rubric not loaded yet."); return; }
        setIsGrading(true);
        setError(null);
        setResult(null);
        const planFile = files[0]?.filename || files[0]?.file?.name;
        try {
            let data;
            if (vision) {
                if (!files[0]?.file) {
                    setError("Vision mode needs the original file — please re-upload it.");
                    setIsGrading(false);
                    return;
                }
                if (!isSupportedPlanFile(files[0].file.name)) {
                    setError(`Vision mode can't read this file type. Supported: ${SUPPORTED_PLAN_TYPES.join(", ")}.`);
                    setIsGrading(false);
                    return;
                }
                // vision MVP grades the first uploaded plan
                data = await GradeWiseAPI.gradeVision(files[0].file, teamName.trim() || "team", rubric, guideline, rubricMode === "byums");
            } else {
                data = await GradeWiseAPI.gradeSubmission(
                    files.map((f) => ({ filename: f.filename, content: f.content })),
                    teamName.trim() || "team",
                    rubric,
                    { guideline, skip_rag: true, max_retries: 1, use_calibration: rubricMode === "byums" }
                );
            }
            setResult(data);
            // Typed name wins; otherwise the name the backend read out of the plan;
            // the file name only as a last resort.
            setGradedBusiness(planBusinessName(teamName, data.business_name, planFile));
        } catch (err: any) {
            setError(err?.response?.data?.detail || err?.message || "Grading failed.");
        } finally {
            setIsGrading(false);
        }
    };

    const downloadPdf = async () => {
        if (!result) return;
        setAction("pdf");
        setError(null);
        try {
            // planTotal is the rubric's real total; without it the PDF's denominator
            // is just the sum of the criteria the grader returned.
            await GradeWiseAPI.downloadReport(result, gradedBusiness, rubricLabel, planTotal);
        } catch (err: any) {
            setError(err?.response?.data?.detail || err?.message || "Could not generate the PDF.");
        } finally {
            setAction("");
        }
    };


    return (
        <div className="h-screen overflow-y-auto bg-slate-50 dark:bg-background p-6 md:p-8 transition-colors">
            <div className="max-w-6xl mx-auto pb-20 space-y-6">
                {/* Header */}
                <header className="flex flex-wrap justify-between items-start gap-4">
                    <div>
                        <h1 className="text-3xl font-bold text-slate-900 dark:text-white flex items-center gap-3">
                            <Briefcase className="w-7 h-7 text-emerald-600" /> Business Plan Grader
                        </h1>
                        <p className="text-slate-500 dark:text-slate-400 mt-1">
                            {rubricMode === "byums"
                                ? "BYU Africa BPC 2026 — plan component (80 pts). Text grading, or vision mode to also read page images."
                                : "General business-plan rubric (100 pts) — grades any business plan; no competition guideline."}
                        </p>
                    </div>
                    {/* Rubric status chip */}
                    {rubric.length > 0 ? (
                        <span className="text-xs font-medium text-emerald-700 dark:text-emerald-300 bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800 px-3 py-1.5 rounded-full flex items-center gap-2">
                            <CheckCircle className="w-3.5 h-3.5" />
                            {rubricMode === "byums" ? "BYUMS plan rubric" : "General business rubric"} — {rubric.length} criteria / {planTotal} pts{guideline ? " + judges' guideline" : ""}
                        </span>
                    ) : rubricError ? (
                        <span className="text-xs font-medium text-red-700 dark:text-red-300 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 px-3 py-1.5 rounded-full flex items-center gap-2">
                            <AlertTriangle className="w-3.5 h-3.5" /> {rubricError}
                        </span>
                    ) : (
                        <span className="text-xs text-slate-400 flex items-center gap-2"><Loader2 className="w-3.5 h-3.5 animate-spin" /> loading rubric…</span>
                    )}
                </header>

                {/* Rubric selector */}
                <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-sm text-slate-500">Rubric:</span>
                    <div className="inline-flex rounded-lg border border-slate-200 dark:border-slate-700 overflow-hidden text-sm">
                        <button onClick={() => setRubricMode("byums")} disabled={isGrading}
                            className={`px-3 py-1.5 transition-colors ${rubricMode === "byums" ? "bg-emerald-600 text-white" : "bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700"}`}>
                            BYUMS Competition (80)
                        </button>
                        <button onClick={() => setRubricMode("general")} disabled={isGrading}
                            className={`px-3 py-1.5 border-l border-slate-200 dark:border-slate-700 transition-colors ${rubricMode === "general" ? "bg-emerald-600 text-white" : "bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700"}`}>
                            General Business (100)
                        </button>
                    </div>
                </div>

                {/* Input card */}
                <div className="bg-white dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm p-5 space-y-4">
                    <div className="flex flex-wrap items-center gap-3">
                        <input
                            type="text"
                            placeholder="Business / team name (optional — read from the plan if left blank)"
                            value={teamName}
                            onChange={(e) => setTeamName(e.target.value)}
                            className="flex-1 min-w-[200px] px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-white focus:ring-2 focus:ring-emerald-500/20 outline-none"
                        />
                        <label className="cursor-pointer px-3 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors flex items-center gap-2">
                            {isExtracting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
                            Upload plan (PDF, PPTX, DOCX)
                            <input type="file" className="hidden" multiple accept=".pdf,.pptx,.docx,.txt,.md" onChange={handleUpload} />
                        </label>
                    </div>

                    <PdfTip />

                    {files.length > 0 ? (
                        <div className="space-y-2">
                            {files.map((f, i) => (
                                <div key={i} className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800/50 rounded-xl border border-slate-100 dark:border-slate-800 group">
                                    <div className="flex items-center gap-3 min-w-0">
                                        <div className="p-2 bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 text-emerald-600"><FileText className="w-4 h-4" /></div>
                                        <div className="min-w-0">
                                            <div className="text-sm font-medium text-slate-900 dark:text-white truncate max-w-[420px]">{f.filename}</div>
                                            <div className="text-xs text-slate-500">{f.content.length.toLocaleString()} chars extracted{f.content.trim().length === 0 ? " — ⚠ no text (scanned PDF?)" : ""}</div>
                                        </div>
                                    </div>
                                    <button onClick={() => setFiles((prev) => prev.filter((_, x) => x !== i))} className="p-2 text-slate-400 hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100"><Trash2 className="w-4 h-4" /></button>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="text-center text-slate-400 py-8 border border-dashed border-slate-200 dark:border-slate-700 rounded-xl">
                            <Upload className="w-7 h-7 mx-auto mb-2 opacity-50" />
                            <p className="text-sm">Upload a business plan PDF (the slide deck export)</p>
                        </div>
                    )}

                    {error && (
                        <div className="p-3 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm rounded-lg flex items-center gap-2">
                            <AlertTriangle className="w-4 h-4 shrink-0" /> {error}
                        </div>
                    )}

                    <label className="flex items-start gap-2 text-sm text-slate-600 dark:text-slate-300 cursor-pointer select-none">
                        <input type="checkbox" checked={vision} onChange={(e) => setVision(e.target.checked)} className="mt-0.5 rounded accent-emerald-600" />
                        <span className="flex items-center gap-1.5">
                            <Eye className="w-4 h-4 text-emerald-600" />
                            <span><b>Vision mode</b> — read the plan with Gemini: page images where the document has them (PDF, and pictures embedded in PPTX/DOCX), and its text. Sees financial tables, licences and bank statements; catches inconsistent numbers. Text-only files (.docx without pictures, .txt, .md) are graded from their text. Slower, and grades the first plan only.</span>
                        </span>
                    </label>

                    <button
                        onClick={grade}
                        disabled={isGrading || files.length === 0 || rubric.length === 0}
                        className="w-full py-3 bg-emerald-600 text-white rounded-xl font-bold hover:bg-emerald-700 active:scale-[0.99] transition-all flex items-center justify-center gap-2 disabled:opacity-60 disabled:cursor-not-allowed"
                    >
                        {isGrading
                            ? <><Loader2 className="w-4 h-4 animate-spin" /> {vision ? "Reading slides with vision…" : `Grading against ${rubric.length} criteria…`}</>
                            : <>{vision ? <Eye className="w-4 h-4" /> : <Sparkles className="w-4 h-4" />} Grade Plan{vision ? " (vision)" : ""}</>}
                    </button>
                </div>

                {/* Result */}
                <AnimatePresence>
                    {result && (
                        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-5">
                            {/* Score header */}
                            <div className="bg-white dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm p-6">
                                <div className="flex items-center justify-between flex-wrap gap-4">
                                    <div className="min-w-0">
                                        <h2 className="text-2xl font-bold text-slate-900 dark:text-white leading-snug break-words">
                                            {gradedBusiness || "Business plan"}
                                        </h2>
                                        <p className="text-sm text-slate-500 mt-0.5">{rubricMode === "byums" ? "Plan score (80% component — excludes the 20% video)" : "Business plan score (general rubric)"}</p>
                                        <div className="text-4xl font-black text-slate-900 dark:text-white mt-1">
                                            {result.score}<span className="text-2xl text-slate-400"> / {planTotal}</span>
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <div className="text-3xl font-bold text-slate-700 dark:text-slate-200">
                                            {planTotal > 0 ? Math.round((result.score / planTotal) * 100) : 0}%
                                        </div>
                                    </div>
                                </div>

                                {/* Report delivery — download the PDF report */}
                                <div className="mt-5 pt-4 border-t border-slate-100 dark:border-slate-800 flex flex-wrap items-center gap-3">
                                    <button
                                        onClick={downloadPdf}
                                        disabled={action !== ""}
                                        className="px-4 py-2 rounded-xl text-sm font-semibold border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors flex items-center gap-2 disabled:opacity-60 disabled:cursor-not-allowed"
                                    >
                                        {action === "pdf" ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
                                        Download PDF
                                    </button>
                                </div>
                            </div>

                            {/* Eligibility + per-criterion breakdown + feedback + log (shared component) */}
                            <div className="bg-white dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm p-6">
                                <GradeBreakdown result={result} businessName={gradedBusiness} />
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </div>
    );
}
