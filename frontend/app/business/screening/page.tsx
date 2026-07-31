"use client";

import { useState, useEffect } from "react";
import { GradeWiseAPI, RubricItem, GradeResult, friendlyApiError } from "@/lib/api";
import {
    Upload, FileText, Loader2, CheckCircle, AlertTriangle, Trophy, Eye, Trash2,
    ChevronDown, ChevronRight, Flag,
} from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";
import GradeBreakdown from "@/components/GradeBreakdown";

type Row = {
    id: string;   // stable unique key (filenames can collide in bulk uploads)
    name: string;
    status: "pending" | "grading" | "done" | "error";
    result?: GradeResult;
    error?: string;
};

const CONCURRENCY = 2;

export default function BpcScreeningPage() {
    const [rubric, setRubric] = useState<RubricItem[]>([]);
    const [guideline, setGuideline] = useState("");
    const [planTotal, setPlanTotal] = useState(0);
    const [rubricError, setRubricError] = useState<string | null>(null);

    const [files, setFiles] = useState<File[]>([]);
    const [vision, setVision] = useState(false);
    const [topN, setTopN] = useState(3);
    const [rows, setRows] = useState<Row[]>([]);
    const [running, setRunning] = useState(false);
    const [openRow, setOpenRow] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        GradeWiseAPI.getBpcRubric()
            .then((d) => { setRubric(d.plan); setGuideline(d.guideline || ""); setPlanTotal(d.plan_total); })
            .catch((e) => setRubricError(friendlyApiError(e, "Could not load the BYUMS rubric.")));
    }, []);

    const addFiles = (e: React.ChangeEvent<HTMLInputElement>) => {
        const list = e.target.files;
        if (!list) return;
        setFiles((prev) => [...prev, ...Array.from(list)]);
        e.target.value = "";
    };
    const removeFile = (i: number) => setFiles((prev) => prev.filter((_, j) => j !== i));

    const screenAll = async () => {
        if (files.length === 0) { setError("Add at least one plan PDF."); return; }
        if (rubric.length === 0) { setError("Rubric not loaded yet."); return; }
        setError(null);
        setRunning(true);
        setOpenRow(null);
        const init: Row[] = files.map((f, i) => ({ id: String(i), name: f.name, status: "pending" }));
        setRows(init);

        // Text mode: extract all up front (aligned by index with files).
        let extracted: { filename: string; content: string }[] = [];
        if (!vision) {
            try {
                extracted = await GradeWiseAPI.extractFilesContent(files);
            } catch {
                setRows(init.map((r) => ({ ...r, status: "error", error: "text extraction failed" })));
                setRunning(false);
                return;
            }
        }

        const queue = files.map((_, i) => i);
        const worker = async () => {
            while (queue.length) {
                const i = queue.shift()!;
                setRows((prev) => prev.map((r, j) => (j === i ? { ...r, status: "grading" } : r)));
                // The backend returns "Error extracting text: …" as content (never throws)
                // for scanned/failed PDFs — route those to the error bucket, don't grade them.
                if (!vision) {
                    const content = extracted[i]?.content || "";
                    if (!content.trim() || content.startsWith("Error extracting text")) {
                        setRows((prev) => prev.map((r, j) => (j === i ? { ...r, status: "error", error: "no text extracted (scanned PDF?) — try Vision mode" } : r)));
                        continue;
                    }
                }
                try {
                    const res = vision
                        ? await GradeWiseAPI.gradeVision(files[i], files[i].name, rubric, guideline)
                        : await GradeWiseAPI.gradeSubmission(
                            [{ filename: extracted[i].filename, content: extracted[i].content }],
                            files[i].name, rubric, { guideline, skip_rag: true, max_retries: 1 });
                    setRows((prev) => prev.map((r, j) => (j === i ? { ...r, status: "done", result: res } : r)));
                } catch (e: any) {
                    const msg = e?.response?.data?.detail || e?.message || "grading failed";
                    setRows((prev) => prev.map((r, j) => (j === i ? { ...r, status: "error", error: msg } : r)));
                }
            }
        };
        await Promise.all(Array.from({ length: CONCURRENCY }, worker));
        setRunning(false);
    };

    const isEligible = (r: Row) => r.result && r.result.graded_ok !== false && (r.result.eligibility_status || "eligible") === "eligible";
    const done = rows.filter((r) => r.status === "done" && r.result);
    const scored = done.filter(isEligible).sort((a, b) => (b.result!.score) - (a.result!.score));
    const flagged = done.filter((r) => !isEligible(r));
    const errored = rows.filter((r) => r.status === "error");
    const completed = rows.filter((r) => r.status === "done" || r.status === "error").length;
    // Tie-aware shortlist: include everyone whose score is >= the score at rank topN
    // (so two plans with an equal score are never split across the cutoff).
    const cutoffScore = scored.length > 0 ? scored[Math.min(topN, scored.length) - 1].result!.score : 0;
    const shortlistCount = scored.filter((r) => r.result!.score >= cutoffScore).length;

    const pct = (s: number) => (planTotal > 0 ? Math.round((s / planTotal) * 100) : 0);

    return (
        <div className="h-screen overflow-y-auto bg-slate-50 dark:bg-background p-6 md:p-8 transition-colors">
            <div className="max-w-6xl mx-auto pb-20 space-y-6">
                <header className="flex flex-wrap justify-between items-start gap-4">
                    <div>
                        <h1 className="text-3xl font-bold text-slate-900 dark:text-white flex items-center gap-3">
                            <Trophy className="w-7 h-7 text-emerald-600" /> Competition Screening
                        </h1>
                        <p className="text-slate-500 dark:text-slate-400 mt-1">
                            Grade many plans, rank them, and shortlist the top applicants (plan component, 80 pts).
                        </p>
                    </div>
                    {rubric.length > 0 ? (
                        <span className="text-xs font-medium text-emerald-700 dark:text-emerald-300 bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800 px-3 py-1.5 rounded-full flex items-center gap-2">
                            <CheckCircle className="w-3.5 h-3.5" /> BYUMS plan rubric — {rubric.length} criteria / {planTotal} pts
                        </span>
                    ) : rubricError ? (
                        <span className="text-xs text-red-600 flex items-center gap-2"><AlertTriangle className="w-3.5 h-3.5" /> {rubricError}</span>
                    ) : <span className="text-xs text-slate-400 flex items-center gap-2"><Loader2 className="w-3.5 h-3.5 animate-spin" /> loading rubric…</span>}
                </header>

                {/* Controls */}
                <div className="bg-white dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm p-5 space-y-4">
                    <div className="flex flex-wrap items-center gap-3">
                        <label className="cursor-pointer px-3 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors flex items-center gap-2">
                            <Upload className="w-4 h-4" /> Add plans (PDF, PPTX, DOCX)
                            <input type="file" className="hidden" multiple accept=".pdf,.pptx,.docx,.txt" onChange={addFiles} />
                        </label>
                        <span className="text-sm text-slate-500">{files.length} plan{files.length === 1 ? "" : "s"} queued</span>
                        <div className="ml-auto flex items-center gap-2 text-sm text-slate-600 dark:text-slate-300">
                            Shortlist top
                            <input type="number" min={1} value={topN} onChange={(e) => setTopN(Math.max(1, parseInt(e.target.value) || 1))}
                                className="w-16 px-2 py-1 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-center" />
                        </div>
                    </div>

                    {files.length > 0 && (
                        <div className="flex flex-wrap gap-2">
                            {files.map((f, i) => (
                                <span key={i} className="inline-flex items-center gap-2 text-xs bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800 rounded-lg px-2.5 py-1.5">
                                    <FileText className="w-3.5 h-3.5 text-emerald-600" />
                                    <span className="max-w-[220px] truncate">{f.name}</span>
                                    <button onClick={() => removeFile(i)} className="text-slate-400 hover:text-red-500"><Trash2 className="w-3.5 h-3.5" /></button>
                                </span>
                            ))}
                        </div>
                    )}

                    <label className="flex items-start gap-2 text-sm text-slate-600 dark:text-slate-300 cursor-pointer select-none">
                        <input type="checkbox" checked={vision} onChange={(e) => setVision(e.target.checked)} className="mt-0.5 rounded accent-emerald-600" />
                        <span className="flex items-center gap-1.5"><Eye className="w-4 h-4 text-emerald-600" /><span><b>Vision mode</b> — read slide images with Gemini (sees financials/license/bank; slower).</span></span>
                    </label>

                    {error && <div className="p-3 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm rounded-lg flex items-center gap-2"><AlertTriangle className="w-4 h-4" /> {error}</div>}

                    <button onClick={screenAll} disabled={running || files.length === 0 || rubric.length === 0}
                        className="w-full py-3 bg-emerald-600 text-white rounded-xl font-bold hover:bg-emerald-700 active:scale-[0.99] transition-all flex items-center justify-center gap-2 disabled:opacity-60 disabled:cursor-not-allowed">
                        {running
                            ? <><Loader2 className="w-4 h-4 animate-spin" /> Screening… {completed}/{rows.length}</>
                            : <><Trophy className="w-4 h-4" /> Screen {files.length} plan{files.length === 1 ? "" : "s"}</>}
                    </button>
                    {running && (
                        <div className="h-1.5 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                            <div className="h-full bg-emerald-500 transition-all" style={{ width: `${rows.length ? (completed / rows.length) * 100 : 0}%` }} />
                        </div>
                    )}
                </div>

                {/* Leaderboard */}
                {scored.length > 0 && (
                    <div className="bg-white dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm overflow-hidden">
                        <div className="p-4 border-b border-slate-100 dark:border-slate-800 font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                            <Trophy className="w-4 h-4 text-amber-500" /> Leaderboard — {scored.length} eligible, top {shortlistCount} shortlisted
                        </div>
                        <div className="divide-y divide-slate-100 dark:divide-slate-800">
                            {scored.map((r, idx) => {
                                const rank = idx + 1;
                                const shortlisted = r.result!.score >= cutoffScore;
                                const open = openRow === r.id;
                                return (
                                    <div key={r.id} className={shortlisted ? "bg-emerald-50/40 dark:bg-emerald-900/10" : ""}>
                                        <button onClick={() => setOpenRow(open ? null : r.id)} className="w-full flex items-center gap-4 p-4 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors text-left">
                                            <span className={`w-8 text-center font-black ${rank <= 3 ? "text-amber-500" : "text-slate-400"}`}>#{rank}</span>
                                            {open ? <ChevronDown className="w-4 h-4 text-slate-400" /> : <ChevronRight className="w-4 h-4 text-slate-400" />}
                                            <span className="flex-1 min-w-0 truncate text-slate-800 dark:text-slate-200">{r.name}</span>
                                            {shortlisted && <span className="text-[10px] font-bold uppercase tracking-wide bg-emerald-100 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-300 px-2 py-0.5 rounded-full">shortlist</span>}
                                            <span className="font-mono font-bold text-slate-900 dark:text-white shrink-0">{r.result!.score}<span className="text-slate-400">/{planTotal}</span></span>
                                            <span className="w-12 text-right text-sm text-slate-500 shrink-0">{pct(r.result!.score)}%</span>
                                        </button>
                                        <AnimatePresence>
                                            {open && (
                                                <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden">
                                                    <div className="p-4 pt-0"><GradeBreakdown result={r.result!} /></div>
                                                </motion.div>
                                            )}
                                        </AnimatePresence>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                )}

                {/* Flagged for review */}
                {flagged.length > 0 && (
                    <div className="bg-white dark:bg-slate-900/50 border border-amber-200 dark:border-amber-900/40 rounded-2xl shadow-sm overflow-hidden">
                        <div className="p-4 border-b border-amber-100 dark:border-amber-900/40 font-semibold text-amber-700 dark:text-amber-300 flex items-center gap-2">
                            <Flag className="w-4 h-4" /> Needs human review — {flagged.length} (not ranked)
                        </div>
                        <div className="divide-y divide-slate-100 dark:divide-slate-800">
                            {flagged.map((r) => {
                                const open = openRow === r.id;
                                return (
                                    <div key={r.id}>
                                        <button onClick={() => setOpenRow(open ? null : r.id)} className="w-full flex items-center gap-3 p-4 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors text-left">
                                            {open ? <ChevronDown className="w-4 h-4 text-slate-400" /> : <ChevronRight className="w-4 h-4 text-slate-400" />}
                                            <span className="flex-1 min-w-0 truncate text-slate-800 dark:text-slate-200">{r.name}</span>
                                            <span className="text-xs font-medium text-amber-700 dark:text-amber-300 capitalize">{(r.result!.eligibility_status || "").replace("_", " ") || "review"}</span>
                                        </button>
                                        <AnimatePresence>
                                            {open && (
                                                <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden">
                                                    <div className="p-4 pt-0"><GradeBreakdown result={r.result!} /></div>
                                                </motion.div>
                                            )}
                                        </AnimatePresence>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                )}

                {/* Errors */}
                {errored.length > 0 && (
                    <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-2xl p-4 text-sm text-red-700 dark:text-red-300">
                        <div className="font-semibold mb-1 flex items-center gap-2"><AlertTriangle className="w-4 h-4" /> {errored.length} plan(s) failed to grade</div>
                        <ul className="list-disc pl-5 space-y-0.5 text-xs">
                            {errored.map((r) => <li key={r.id}>{r.name}: {r.error}</li>)}
                        </ul>
                    </div>
                )}
            </div>
        </div>
    );
}
