"use client";

import { useState, useEffect } from "react";
import { GradeResult, CriterionAssessment } from "@/lib/api";
import {
    CheckCircle, AlertTriangle, XCircle, ShieldAlert, Bot, ChevronRight, ChevronDown, Sparkles,
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

// Trim float artifacts from summed scores (e.g. 8.499999 -> 8.5, 6 -> 6).
function fmt(n: number): string {
    const r = Math.round(n * 100) / 100;
    return Number.isInteger(r) ? r.toString() : r.toString();
}

type Kind = "full" | "zero" | "partial";
function kindOf(a: CriterionAssessment): Kind {
    if (a.max_points > 0 && a.awarded_points >= a.max_points) return "full";
    if (a.awarded_points <= 0) return "zero";
    return "partial";
}
function awardColor(a: CriterionAssessment): string {
    const k = kindOf(a);
    if (k === "full") return "text-emerald-600 dark:text-emerald-400";
    if (k === "zero") return "text-red-500 dark:text-red-400";
    return "text-amber-600 dark:text-amber-400";
}
function barColor(a: CriterionAssessment): string {
    const k = kindOf(a);
    if (k === "full") return "bg-emerald-500";
    if (k === "zero") return "bg-red-400";
    return "bg-amber-500";
}
// Zero-score rows have a 0%-wide fill, so tint the whole track red — otherwise
// a red item reads as an empty grey line and disappears next to partial (amber) ones.
function trackClass(a: CriterionAssessment): string {
    return kindOf(a) === "zero"
        ? "bg-red-100 dark:bg-red-900/30"
        : "bg-slate-100 dark:bg-slate-800";
}
function StatusIcon({ a, className = "w-3.5 h-3.5" }: { a: CriterionAssessment; className?: string }) {
    const k = kindOf(a);
    if (k === "full") return <CheckCircle className={`${className} text-emerald-500 dark:text-emerald-400 shrink-0`} />;
    if (k === "zero") return <XCircle className={`${className} text-red-500 dark:text-red-400 shrink-0`} />;
    return <AlertTriangle className={`${className} text-amber-500 dark:text-amber-400 shrink-0`} />;
}
// Section-level scorecard colour: a %-gradient (partial is the norm for a whole
// section, so the per-criterion full/zero/partial logic would make everything amber).
function pctClasses(pct: number): { bar: string; text: string } {
    if (pct >= 80) return { bar: "bg-emerald-500", text: "text-emerald-600 dark:text-emerald-400" };
    if (pct >= 50) return { bar: "bg-amber-500", text: "text-amber-600 dark:text-amber-400" };
    return { bar: "bg-red-400", text: "text-red-500 dark:text-red-400" };
}

/**
 * Renders the rich detail of a GradeResult: eligibility banner, a section scorecard,
 * the participant summary, a "where points were lost" recap, the collapsible
 * per-criterion breakdown, and the agent log. Everything is derived from the
 * GradeResult data, so it renders identically for any rubric (BYUMS or general).
 * Shared by the single-plan grader and the screening dashboard drill-down.
 *
 * `businessName` heads the feedback card so a reader always knows whose plan the
 * feedback belongs to (it mirrors the heading of the downloadable PDF report).
 */
export default function GradeBreakdown({ result, businessName = "" }: { result: GradeResult; businessName?: string }) {
    // Detail sections collapse by default — the scorecard is the at-a-glance entry
    // point, so we no longer auto-expand weak sections (that was the "overwhelming" view).
    const [openSections, setOpenSections] = useState<Record<string, boolean>>({});
    useEffect(() => { setOpenSections({}); }, [result]);

    const eligibility = result.eligibility_status || "eligible";
    const eligStyle =
        eligibility === "eligible"
            ? "bg-emerald-50 dark:bg-emerald-900/20 border-emerald-200 dark:border-emerald-800 text-emerald-700 dark:text-emerald-300"
            : eligibility === "ineligible"
                ? "bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800 text-red-700 dark:text-red-300"
                : "bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800 text-amber-700 dark:text-amber-300";

    const assessments = result.assessments || [];
    const sections = assessments.reduce<Record<string, CriterionAssessment[]>>((acc, a) => {
        (acc[sectionOf(a.criteria_name)] ||= []).push(a);
        return acc;
    }, {});
    const sectionEntries = Object.entries(sections);

    // Factual recap: every criterion that did not earn full marks, worst gap first.
    // Surfaces only the grader's existing rationale — no generated advice.
    const weak = assessments
        .filter((a) => a.awarded_points < a.max_points)
        .sort((a, b) => (b.max_points - b.awarded_points) - (a.max_points - a.awarded_points));

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

            {/* Scorecard — at-a-glance section totals (the "cover letter" overview) */}
            {sectionEntries.length > 0 && (
                <div className="border border-slate-200 dark:border-slate-800 rounded-xl p-4">
                    <h4 className="font-bold text-slate-900 dark:text-white mb-3 text-sm">Scorecard</h4>
                    <div className="grid sm:grid-cols-2 gap-x-6 gap-y-2.5">
                        {sectionEntries.map(([section, items]) => {
                            const awarded = items.reduce((s, a) => s + a.awarded_points, 0);
                            const max = items.reduce((s, a) => s + a.max_points, 0);
                            const pct = max > 0 ? (awarded / max) * 100 : 0;
                            const c = pctClasses(pct);
                            return (
                                <div key={section} className="space-y-1">
                                    <div className="flex items-center justify-between gap-2 text-sm">
                                        <span className="text-slate-700 dark:text-slate-300 truncate">{section}</span>
                                        <span className={`font-mono font-semibold shrink-0 ${c.text}`}>{fmt(awarded)} / {fmt(max)}</span>
                                    </div>
                                    <div className="h-1.5 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                                        <div className={`h-full ${c.bar}`} style={{ width: `${Math.min(100, pct)}%` }} />
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}

            {/* Participant summary — moved up to sit under the scorecard as the cover letter.
                Headed by the business name; "Participant feedback" drops to the eyebrow. */}
            {result.feedback && (
                <div className="bg-slate-50 dark:bg-slate-800/40 border border-slate-100 dark:border-slate-800 rounded-xl p-4">
                    <div className="mb-3">
                        <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500">
                            Participant feedback
                        </p>
                        <h4 className="font-bold text-slate-900 dark:text-white text-base leading-snug break-words">
                            {businessName || "Business plan"}
                        </h4>
                    </div>
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

            {/* Where points were lost — factual recap, worst gap first */}
            {weak.length > 0 && (
                <div className="border border-slate-200 dark:border-slate-800 rounded-xl p-4">
                    <h4 className="font-bold text-slate-900 dark:text-white mb-3 text-sm">Where points were lost</h4>
                    <div className="space-y-3">
                        {weak.map((a, i) => (
                            <div key={i} className="flex items-start gap-2.5">
                                <span className="mt-0.5"><StatusIcon a={a} /></span>
                                <div className="min-w-0 flex-1">
                                    <div className="flex items-center justify-between gap-3">
                                        <span className={`text-sm font-medium ${awardColor(a)}`}>{a.criteria_name}</span>
                                        <span className={`text-sm font-mono font-semibold shrink-0 ${awardColor(a)}`}>{fmt(a.awarded_points)} / {fmt(a.max_points)}</span>
                                    </div>
                                    {a.reason && <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">{a.reason}</p>}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Full per-criterion breakdown — collapsed by default */}
            {sectionEntries.length > 0 && (
                <div className="border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden divide-y divide-slate-100 dark:divide-slate-800">
                    {sectionEntries.map(([section, items]) => {
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
                                    <span className="text-sm font-mono text-slate-500">{fmt(awarded)} / {fmt(max)}</span>
                                </button>
                                <AnimatePresence>
                                    {open && (
                                        <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden">
                                            <div className="px-3 pb-3 space-y-3">
                                                {items.map((a, i) => (
                                                    <div key={i} className="pl-6">
                                                        <div className="flex items-center justify-between gap-3">
                                                            <span className={`flex items-center gap-1.5 text-sm font-medium ${awardColor(a)}`}>
                                                                <StatusIcon a={a} /> {labelOf(a.criteria_name)}
                                                            </span>
                                                            <span className={`text-sm font-mono font-semibold shrink-0 ${awardColor(a)}`}>{fmt(a.awarded_points)} / {fmt(a.max_points)}</span>
                                                        </div>
                                                        <div className={`mt-1 h-1.5 rounded-full overflow-hidden ${trackClass(a)}`}>
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
