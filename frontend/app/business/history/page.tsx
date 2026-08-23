"use client";

import { useEffect, useState } from "react";
import { GradeWiseAPI, HistoryRow, HistoryDetail } from "@/lib/api";
import { planBusinessName } from "@/lib/planName";
import {
    History as HistoryIcon, Loader2, AlertTriangle, Download, FileText,
    ChevronDown, ChevronRight, RefreshCw, CheckCircle, Flag,
} from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";

export default function BusinessHistoryPage() {
    const [rows, setRows] = useState<HistoryRow[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [openId, setOpenId] = useState<number | null>(null);
    const [detail, setDetail] = useState<HistoryDetail | null>(null);
    const [detailLoading, setDetailLoading] = useState(false);

    const load = () => {
        setLoading(true);
        setError(null);
        GradeWiseAPI.getGradeHistory()
            .then(setRows)
            .catch((e) => setError(e?.response?.data?.detail || e?.message || "Could not load history."))
            .finally(() => setLoading(false));
    };
    useEffect(load, []);

    const toggle = async (id: number) => {
        if (openId === id) { setOpenId(null); setDetail(null); return; }
        setOpenId(id);
        setDetail(null);
        setDetailLoading(true);
        try {
            setDetail(await GradeWiseAPI.getGradeHistoryDetail(id));
        } catch {
            setDetail(null);
        } finally {
            setDetailLoading(false);
        }
    };

    const fmtDate = (iso: string) => {
        try { return new Date(iso).toLocaleString(); } catch { return iso; }
    };

    // `team` is whatever the run was graded under: the business name from the
    // single-plan grader, the file name from bulk screening, or the legacy "team"
    // placeholder on older runs — fall back to the file name for the last two.
    const businessOf = (r: HistoryRow) =>
        planBusinessName(r.team && r.team !== "team" && r.team !== r.filename ? r.team : "", r.filename);

    return (
        <div className="h-screen overflow-y-auto bg-slate-50 dark:bg-background p-6 md:p-8 transition-colors">
            <div className="max-w-5xl mx-auto pb-20 space-y-6">
                <header className="flex flex-wrap justify-between items-start gap-4">
                    <div>
                        <h1 className="text-3xl font-bold text-slate-900 dark:text-white flex items-center gap-3">
                            <HistoryIcon className="w-7 h-7 text-indigo-600" /> History
                        </h1>
                        <p className="text-slate-500 dark:text-slate-400 mt-1">
                            Every plan graded on this server — click a row for the full breakdown, or re-download the original file.
                        </p>
                    </div>
                    <button
                        onClick={load}
                        className="inline-flex items-center gap-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-2 text-sm font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
                    >
                        <RefreshCw className="w-4 h-4" /> Refresh
                    </button>
                </header>

                {loading ? (
                    <div className="flex items-center gap-2 text-slate-500 dark:text-slate-400 p-8 justify-center">
                        <Loader2 className="w-5 h-5 animate-spin" /> Loading history…
                    </div>
                ) : error ? (
                    <div className="p-4 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm rounded-xl flex items-center gap-2">
                        <AlertTriangle className="w-4 h-4" /> {error}
                    </div>
                ) : rows.length === 0 ? (
                    <div className="text-center text-slate-500 dark:text-slate-400 p-12 border border-dashed border-slate-200 dark:border-slate-800 rounded-2xl">
                        No graded plans yet. Grade a plan from <b>Business Plan Grader</b> or <b>Competition Screening</b> and it will appear here.
                    </div>
                ) : (
                    <div className="bg-white dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm overflow-hidden divide-y divide-slate-100 dark:divide-slate-800">
                        {rows.map((r) => {
                            const eligible = r.graded_ok && (r.eligibility_status || "eligible") === "eligible";
                            const isOpen = openId === r.submission_id;
                            const business = businessOf(r);
                            // Only show the file name when it adds something beyond the business name.
                            const showFile = !r.filename.startsWith(`${business}.`);
                            return (
                                <div key={r.submission_id}>
                                    <button
                                        onClick={() => toggle(r.submission_id)}
                                        className="w-full flex items-center gap-3 p-4 text-left hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors"
                                    >
                                        {isOpen ? <ChevronDown className="w-4 h-4 text-slate-400 shrink-0" /> : <ChevronRight className="w-4 h-4 text-slate-400 shrink-0" />}
                                        <FileText className="w-4 h-4 text-indigo-500 shrink-0" />
                                        <span className="flex-1 min-w-0 truncate">
                                            <span className="font-medium text-slate-800 dark:text-slate-200">{business}</span>
                                            {showFile && <span className="text-slate-400 dark:text-slate-500"> · {r.filename}</span>}
                                        </span>
                                        {eligible ? (
                                            <span className="hidden sm:inline-flex items-center gap-1 text-xs text-emerald-700 dark:text-emerald-300"><CheckCircle className="w-3.5 h-3.5" /> eligible</span>
                                        ) : (
                                            <span className="hidden sm:inline-flex items-center gap-1 text-xs text-amber-600"><Flag className="w-3.5 h-3.5" /> {r.eligibility_status || "flagged"}</span>
                                        )}
                                        <span className="text-xs text-slate-400 hidden md:inline w-40 text-right">{fmtDate(r.created_at)}</span>
                                        <span className="font-mono font-bold text-indigo-600 dark:text-indigo-400 w-20 text-right">
                                            {r.score}<span className="text-slate-400 font-normal">/{r.total_points || "—"}</span>
                                        </span>
                                    </button>

                                    <AnimatePresence initial={false}>
                                        {isOpen && (
                                            <motion.div
                                                initial={{ height: 0, opacity: 0 }}
                                                animate={{ height: "auto", opacity: 1 }}
                                                exit={{ height: 0, opacity: 0 }}
                                                className="overflow-hidden bg-slate-50/60 dark:bg-slate-900/40"
                                            >
                                                <div className="p-4 space-y-4">
                                                    <div className="flex flex-wrap items-center gap-3">
                                                        {r.has_file ? (
                                                            <a
                                                                href={GradeWiseAPI.planFileUrl(r.submission_id)}
                                                                className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 text-white px-3 py-2 text-sm font-medium hover:bg-indigo-700 transition-colors"
                                                            >
                                                                <Download className="w-4 h-4" /> Download plan
                                                            </a>
                                                        ) : (
                                                            <span className="text-xs text-slate-400">Original file not stored for this run (text-mode grade).</span>
                                                        )}
                                                    </div>

                                                    {detailLoading && !detail ? (
                                                        <div className="flex items-center gap-2 text-slate-500 text-sm"><Loader2 className="w-4 h-4 animate-spin" /> Loading breakdown…</div>
                                                    ) : detail && detail.submission_id === r.submission_id ? (
                                                        <>
                                                            {detail.feedback && (
                                                                <div className="text-sm text-slate-600 dark:text-slate-300">
                                                                    <div className="mb-2">
                                                                        <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500">Participant feedback</p>
                                                                        <div className="font-bold text-slate-900 dark:text-white text-base leading-snug break-words">{business}</div>
                                                                    </div>
                                                                    {detail.feedback}
                                                                </div>
                                                            )}
                                                            <div className="rounded-xl border border-slate-200 dark:border-slate-800 overflow-hidden">
                                                                {detail.assessments.map((a, i) => (
                                                                    <div key={i} className="flex items-start gap-3 p-3 text-sm border-b border-slate-100 dark:border-slate-800 last:border-0">
                                                                        <span className="flex-1 min-w-0">
                                                                            <span className="font-medium text-slate-800 dark:text-slate-200">{a.criteria_name}</span>
                                                                            {a.reason && <span className="block text-slate-500 dark:text-slate-400 mt-0.5">{a.reason}</span>}
                                                                        </span>
                                                                        <span className="font-mono text-indigo-600 dark:text-indigo-400 shrink-0">{a.awarded_points}/{a.max_points}</span>
                                                                    </div>
                                                                ))}
                                                            </div>
                                                        </>
                                                    ) : (
                                                        <div className="text-sm text-slate-400">Could not load the breakdown for this run.</div>
                                                    )}
                                                </div>
                                            </motion.div>
                                        )}
                                    </AnimatePresence>
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>
        </div>
    );
}
