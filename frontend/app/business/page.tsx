"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import {
    Briefcase, Trophy, Swords, ArrowRight, Plus, Sparkles,
    ScrollText, ShieldCheck, Eye
} from "lucide-react";
import { ModeToggle } from "@/components/ModeToggle";

const container = {
    hidden: { opacity: 0 },
    show: { opacity: 1, transition: { staggerChildren: 0.08 } },
};
const item = {
    hidden: { opacity: 0, y: 16 },
    show: { opacity: 1, y: 0 },
};

export default function BusinessDashboard() {
    return (
        <div className="flex h-full overflow-hidden bg-background transition-colors duration-300">
            <main className="flex-1 overflow-y-auto relative p-8">
                {/* Subtle background */}
                <div className="absolute top-0 left-0 w-full h-96 overflow-hidden pointer-events-none opacity-40 dark:opacity-20 z-0">
                    <div className="absolute -top-20 -right-20 w-[600px] h-[600px] bg-indigo-100 dark:bg-indigo-900/20 rounded-full blur-3xl"></div>
                    <div className="absolute top-40 -left-20 w-[400px] h-[400px] bg-violet-100 dark:bg-violet-900/20 rounded-full blur-3xl"></div>
                </div>

                <motion.div
                    className="max-w-7xl mx-auto relative z-10 space-y-8"
                    variants={container}
                    initial="hidden"
                    animate="show"
                >
                    {/* Header */}
                    <motion.header variants={item} className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                        <div>
                            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-100 dark:border-indigo-800 text-indigo-600 dark:text-indigo-400 text-xs font-semibold uppercase tracking-wider mb-3">
                                <Sparkles className="w-3.5 h-3.5" />
                                Business Plan Competition Suite
                            </div>
                            <h1 className="text-3xl font-bold text-slate-900 dark:text-white tracking-tight">Business Plan Dashboard</h1>
                            <p className="text-slate-500 dark:text-slate-400 mt-1 text-sm md:text-base">
                                Grade, screen, and compare business plans — with vision grading and expert-calibrated scoring.
                            </p>
                        </div>
                        <div className="flex items-center gap-3">
                            <ModeToggle />
                            <Link href="/business/grading">
                                <button className="bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-700 hover:to-violet-700 text-white px-5 py-2.5 rounded-xl shadow-lg shadow-indigo-500/25 flex items-center gap-2 transition-all transform hover:-translate-y-0.5 active:translate-y-0 font-medium text-sm">
                                    <Plus className="w-4 h-4" />
                                    <span>Grade a Plan</span>
                                </button>
                            </Link>
                        </div>
                    </motion.header>

                    {/* Rubric modes */}
                    <motion.div variants={item} className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <ModeCard
                            badge="Competition mode"
                            badgeColor="text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/20"
                            title="BYUMS Competition"
                            points="80 pts"
                            desc="Africa Business Plan Competition rubric with eligibility/DQ screening, AI-content flagging, and few-shot calibration to an expert judge."
                            icon={<Trophy className="w-6 h-6 text-white" />}
                            iconBg="bg-amber-500"
                            features={["Eligibility & disqualifier screen", "Expert-calibrated severity", "Plan (80) + video (20) split"]}
                        />
                        <ModeCard
                            badge="General mode"
                            badgeColor="text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-900/20"
                            title="General Business"
                            points="100 pts"
                            desc="A universal 100-point rubric for any business plan — 30 criteria across 10 sections, no competition-specific gating."
                            icon={<ScrollText className="w-6 h-6 text-white" />}
                            iconBg="bg-indigo-500"
                            features={["Works for any plan", "Per-criterion guidance + tiers", "Financials weighted heaviest"]}
                        />
                    </motion.div>

                    {/* Tools */}
                    <motion.div variants={item}>
                        <h2 className="text-lg font-bold text-slate-900 dark:text-white mb-4">Tools</h2>
                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                            <ToolCard
                                href="/business/grading"
                                icon={<Briefcase className="w-6 h-6" />}
                                title="Business Plan Grader"
                                desc="Upload a plan (PDF, PPTX, or DOCX) and grade it against the BYUMS or general rubric — with vision grading for slides."
                                accent="indigo"
                            />
                            <ToolCard
                                href="/business/screening"
                                icon={<Trophy className="w-6 h-6" />}
                                title="Competition Screening"
                                desc="Bulk-grade a batch of submissions, rank them on a leaderboard, and produce a tie-aware shortlist."
                                accent="amber"
                            />
                            <ToolCard
                                href="/business/ai-vs-human"
                                icon={<Swords className="w-6 h-6" />}
                                title="AI vs Human"
                                desc="Compare the AI's section-by-section scores against a human judge's to spot disagreements."
                                accent="violet"
                            />
                        </div>
                    </motion.div>

                    {/* Capabilities strip */}
                    <motion.div variants={item} className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                        <Capability icon={<Eye className="w-5 h-5" />} label="Vision grading" value="Reads slides, tables & charts (Gemini)" />
                        <Capability icon={<ShieldCheck className="w-5 h-5" />} label="Self-correcting" value="Judge re-checks every grade for completeness" />
                        <Capability icon={<Sparkles className="w-5 h-5" />} label="Grounded" value="Optional financial / market reference corpus" />
                    </motion.div>
                </motion.div>
            </main>
        </div>
    );
}

function ModeCard({ badge, badgeColor, title, points, desc, icon, iconBg, features }: any) {
    return (
        <div className="bg-white dark:bg-slate-800/50 backdrop-blur-sm p-6 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm hover:shadow-md transition-shadow">
            <div className="flex justify-between items-start mb-4">
                <div className={`p-3 ${iconBg} rounded-xl shadow-lg shadow-black/5`}>{icon}</div>
                <span className={`px-2.5 py-1 rounded-full text-xs font-semibold ${badgeColor}`}>{badge}</span>
            </div>
            <div className="flex items-baseline gap-2 mb-1">
                <h3 className="text-xl font-bold text-slate-900 dark:text-white">{title}</h3>
                <span className="text-sm font-semibold text-slate-400">{points}</span>
            </div>
            <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">{desc}</p>
            <ul className="space-y-1.5">
                {features.map((f: string, i: number) => (
                    <li key={i} className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
                        <span className="w-1.5 h-1.5 rounded-full bg-indigo-400" />
                        {f}
                    </li>
                ))}
            </ul>
        </div>
    );
}

function ToolCard({ href, icon, title, desc, accent }: any) {
    const accents: Record<string, string> = {
        indigo: "text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-900/20 group-hover:bg-indigo-100 dark:group-hover:bg-indigo-900/30",
        amber: "text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/20 group-hover:bg-amber-100 dark:group-hover:bg-amber-900/30",
        violet: "text-violet-600 dark:text-violet-400 bg-violet-50 dark:bg-violet-900/20 group-hover:bg-violet-100 dark:group-hover:bg-violet-900/30",
    };
    return (
        <Link href={href} className="group block bg-white dark:bg-slate-800/50 backdrop-blur-sm border border-slate-200 dark:border-slate-700 rounded-2xl p-6 shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all">
            <div className={`inline-flex p-3 rounded-xl mb-4 transition-colors ${accents[accent]}`}>{icon}</div>
            <div className="flex items-center justify-between">
                <h3 className="font-bold text-slate-900 dark:text-white">{title}</h3>
                <ArrowRight className="w-4 h-4 text-slate-300 group-hover:text-slate-600 dark:group-hover:text-slate-200 group-hover:translate-x-1 transition-all" />
            </div>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-2">{desc}</p>
        </Link>
    );
}

function Capability({ icon, label, value }: any) {
    return (
        <div className="flex items-start gap-3 bg-white dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 rounded-xl p-4">
            <div className="p-2 rounded-lg bg-slate-100 dark:bg-slate-700 text-indigo-600 dark:text-indigo-400 shrink-0">{icon}</div>
            <div>
                <p className="text-sm font-semibold text-slate-900 dark:text-white">{label}</p>
                <p className="text-xs text-slate-500 dark:text-slate-400">{value}</p>
            </div>
        </div>
    );
}
