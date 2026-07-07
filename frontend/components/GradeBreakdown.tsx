"use client";

import { useState, useEffect } from "react";
import { GradeResult, CriterionAssessment } from "@/lib/api";
import {
    CheckCircle, AlertTriangle, ShieldAlert, Bot, ChevronRight, ChevronDown, Sparkles,
} from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";
import ReactMarkdown from "react-markdown";

// "Financials - Detailed Breakdown" -> section "Financials", label "Detailed Breakdown"
export function sectionOf(name: string): string {
    return name.includes(" - ") ? name.split(" - ")[0].trim() : "Other";
}
export function labelOf(name: string): string {
    return name.includes(" - ") ? name.split(" - ").slice(1).join(" - ").trim() : name;
}
function awardColor(a: CriterionAssessment): string {
    if (a.max_points > 0 && a.awarded_points >= a.max_points) return "text-emerald-600 dark:text-emerald-400";
    if (a.awarded_points <= 0) return "text-red-500 dark:text-red-400";
    return "text-amber-600 dark:text-amber-400";
}
function barColor(a: CriterionAssessment): string {
    if (a.max_points > 0 && a.awarded_points >= a.max_points) return "bg-emerald-500";
    if (a.awarded_points <= 0) return "bg-red-400";
    return "bg-amber-500";
}

/**
 * Renders the rich detail of a GradeResult: eligibility banner, per-criterion
 * breakdown grouped by rubric section, participant feedback, and the agent log.
 * Shared by the single-plan grader and the screening dashboard drill-down.
 */
export default function GradeBreakdown({ result }: { result: GradeResult }) {
    const [openSections, setOpenSections] = useState<Record<string, boolean>>({});
    // Recompute default-open sections whenever the result changes (so a reused
    // component instance never shows a previous plan's open/closed state).
    useEffect(() => {
        const o: Record<string, boolean> = {};
        (result.assessments || []).forEach((a) => {
            if (a.awarded_points < a.max_points) o[sectionOf(a.criteria_name)] = true;
        });
        setOpenSections(o);
    }, [result]);

    const eligibility = result.eligibility_status || "eligible";
    const eligStyle =
        eligibility === "eligible"
            ? "bg-emerald-50 dark:bg-emerald-900/20 border-emerald-200 dark:border-emerald-800 text-emerald-700 dark:text-emerald-300"
            : eligibility === "ineligible"
                ? "bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800 text-red-700 dark:text-red-300"
                : "bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800 text-amber-700 dark:text-amber-300";

    const sections = (result.assessments || []).reduce<Record<string, CriterionAssessment[]>>((acc, a) => {
        (acc[sectionOf(a.criteria_name)] ||= []).push(a);
        return acc;
    }, {});

    return (
        <div className="space-y-4">
            {result.graded_ok === false && (
                <div className="p-3 rounded-xl border bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 text-sm flex items-center gap-2">
                    <ShieldAlert className="w-4 h-4 shrink-0" /> Could not grade automatically — needs human review. {result.error}
                </div>
            )}

            <div className={`p-3 rounded-xl border text-sm ${eligStyle}`}>
                <div className="font-semibold flex items-center gap-2 capitalize">
                    {eligibility === "eligible" ? <CheckCircle className="w-4 h-4" /> : <AlertTriangle className="w-4 h-4" />}
                    Eligibility: {eligibility.replace("_", " ")}
                    {result.ai_content_flag && (
                        <span className="ml-2 inline-flex items-center gap-1 text-xs font-bold bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-300 px-2 py-0.5 rounded-full"><Bot className="w-3 h-3" /> suspected AI content</span>
                    )}
                </div>
                {result.dq_reasons && result.dq_reasons.length > 0 && (
                    <ul className="mt-2 space-y-1 list-disc pl-5 text-xs opacity-90">
                        {result.dq_reasons.map((r, i) => <li key={i}>{r}</li>)}
                    </ul>
                )}
            </div>

            {Object.keys(sections).length > 0 && (
                <div className="border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden divide-y divide-slate-100 dark:divide-slate-800">
                    {Object.entries(sections).map(([section, items]) => {
                        const awarded = items.reduce((s, a) => s + a.awarded_points, 0);
                        const max = items.reduce((s, a) => s + a.max_points, 0);
                        const open = openSections[section];
                        return (
                            <div key={section}>
                                <button
                                    onClick={() => setOpenSections((p) => ({ ...p, [section]: !p[section] }))}
                                    className="w-full flex items-center justify-between p-3 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
                                >
                                    <span className="flex items-center gap-2 font-medium text-slate-800 dark:text-slate-200 text-left text-sm">
                                        {open ? <ChevronDown className="w-4 h-4 text-slate-400" /> : <ChevronRight className="w-4 h-4 text-slate-400" />}
                                        {section}
                                    </span>
                                    <span className="text-sm font-mono text-slate-500">{awarded} / {max}</span>
                                </button>
                                <AnimatePresence>
                                    {open && (
                                        <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden">
                                            <div className="px-3 pb-3 space-y-3">
                                                {items.map((a, i) => (
                                                    <div key={i} className="pl-6">
                                                        <div className="flex items-center justify-between gap-3">
                                                            <span className="text-sm text-slate-700 dark:text-slate-300">{labelOf(a.criteria_name)}</span>
                                                            <span className={`text-sm font-mono font-semibold shrink-0 ${awardColor(a)}`}>{a.awarded_points} / {a.max_points}</span>
                                                        </div>
                                                        <div className="mt-1 h-1.5 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                                                            <div className={`h-full ${barColor(a)}`} style={{ width: `${a.max_points > 0 ? Math.min(100, (a.awarded_points / a.max_points) * 100) : 0}%` }} />
                                                        </div>
                                                        {a.reason && <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">{a.reason}</p>}
                                                    </div>
                                                ))}
                                            </div>
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                            </div>
                        );
                    })}
                </div>
            )}

            {result.feedback && (
                <div className="bg-slate-50 dark:bg-slate-800/40 border border-slate-100 dark:border-slate-800 rounded-xl p-4">
                    <h4 className="font-bold text-slate-900 dark:text-white mb-2 text-sm">Participant feedback</h4>
                    <div className="text-slate-700 dark:text-slate-300 text-sm leading-relaxed">
                        <ReactMarkdown components={{
                            p: ({ node, ...props }) => <p className="mb-2 leading-relaxed" {...props} />,
                            ul: ({ node, ...props }) => <ul className="list-disc pl-5 mb-2 space-y-1" {...props} />,
                            li: ({ node, ...props }) => <li {...props} />,
                            strong: ({ node, ...props }) => <strong className="font-semibold text-slate-900 dark:text-white" {...props} />,
                        }}>{result.feedback}</ReactMarkdown>
                    </div>
                </div>
            )}

            {result.thinking_process && result.thinking_process.length > 0 && (
                <details className="bg-slate-50 dark:bg-slate-800/40 rounded-xl border border-slate-100 dark:border-slate-800 group">
                    <summary className="flex items-center gap-2 p-3 cursor-pointer text-xs font-semibold text-slate-600 dark:text-slate-300">
                        <Sparkles className="w-4 h-4 text-purple-500" /> Agent pipeline log
                        <ChevronRight className="w-4 h-4 text-slate-400 ml-auto group-open:rotate-90 transition-transform" />
                    </summary>
                    <div className="px-3 pb-3 space-y-1">
                        {result.thinking_process.map((log, i) => (
                            <div key={i} className="flex items-start gap-2 text-xs font-mono text-slate-500 dark:text-slate-400">
                                <span className="text-slate-300 select-none">{(i + 1).toString().padStart(2, "0")}</span>{log}
                            </div>
                        ))}
                    </div>
                </details>
            )}
        </div>
    );
}
