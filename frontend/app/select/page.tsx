"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { GraduationCap, Briefcase, ArrowRight, Check } from "lucide-react";
import { Logo } from "@/components/Logo";
import { ModeToggle } from "@/components/ModeToggle";

export default function SelectWorkspace() {
    const [firstName, setFirstName] = useState<string | null>(null);

    useEffect(() => {
        const profile = localStorage.getItem("userProfile");
        if (profile) {
            try { setFirstName(JSON.parse(profile).firstName || null); } catch { /* ignore */ }
        }
    }, []);

    return (
        <div className="min-h-screen w-full relative overflow-hidden bg-white dark:bg-slate-950 transition-colors">
            {/* ambient gradient */}
            <div className="absolute inset-0 pointer-events-none overflow-hidden">
                <div className="absolute -top-40 -left-40 w-[500px] h-[500px] bg-emerald-100/50 dark:bg-emerald-900/10 rounded-full blur-3xl" />
                <div className="absolute -bottom-40 -right-40 w-[500px] h-[500px] bg-indigo-100/50 dark:bg-indigo-900/10 rounded-full blur-3xl" />
            </div>

            <div className="absolute top-4 right-4 z-20"><ModeToggle /></div>

            <div className="relative z-10 min-h-screen flex flex-col items-center justify-center px-4 py-16">
                <Link href="/" className="flex items-center gap-3 mb-8 hover:opacity-80 transition-opacity">
                    <Logo className="w-10 h-10" showText={false} />
                    <span className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">GradeWise</span>
                </Link>

                <motion.h1
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="text-3xl md:text-4xl font-bold text-slate-900 dark:text-white text-center tracking-tight"
                >
                    {firstName ? `Welcome, ${firstName}.` : "Choose your workspace"}
                </motion.h1>
                <motion.p
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.05 }}
                    className="text-slate-500 dark:text-slate-400 mt-2 mb-10 text-center max-w-xl"
                >
                    One account, two workspaces. Pick where you want to work — you can switch anytime.
                </motion.p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full max-w-4xl">
                    <WorkspaceCard
                        href="/dashboard"
                        accent="emerald"
                        icon={<GraduationCap className="w-7 h-7" />}
                        title="Educator"
                        tagline="Academic grading"
                        desc="Grade student submissions against your rubrics with course-material context and detailed feedback."
                        features={["Rubric-based grading", "Mass grading & results", "Analytics"]}
                        delay={0.1}
                    />
                    <WorkspaceCard
                        href="/business"
                        accent="indigo"
                        icon={<Briefcase className="w-7 h-7" />}
                        title="Business Plan"
                        tagline="Competition & general"
                        desc="Grade business plans (BYUMS or general rubric), screen a competition, and compare AI vs human scores."
                        features={["Vision grading (PDF / PPTX)", "Competition screening", "AI vs Human"]}
                        delay={0.15}
                    />
                </div>
            </div>
        </div>
    );
}

function WorkspaceCard({ href, accent, icon, title, tagline, desc, features, delay }: any) {
    const theme: Record<string, { ring: string; icon: string; btn: string; dot: string }> = {
        emerald: {
            ring: "hover:border-emerald-300 dark:hover:border-emerald-700 hover:shadow-emerald-500/10",
            icon: "bg-gradient-to-br from-emerald-500 to-teal-600",
            btn: "bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 shadow-emerald-500/25",
            dot: "text-emerald-500",
        },
        indigo: {
            ring: "hover:border-indigo-300 dark:hover:border-indigo-700 hover:shadow-indigo-500/10",
            icon: "bg-gradient-to-br from-indigo-500 to-violet-600",
            btn: "bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-700 hover:to-violet-700 shadow-indigo-500/25",
            dot: "text-indigo-500",
        },
    };
    const t = theme[accent];
    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay }}
        >
            <Link
                href={href}
                className={`group flex flex-col h-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-7 shadow-sm hover:shadow-xl transition-all hover:-translate-y-1 ${t.ring}`}
            >
                <div className={`inline-flex w-14 h-14 items-center justify-center rounded-2xl text-white shadow-lg mb-5 ${t.icon}`}>
                    {icon}
                </div>
                <h2 className="text-2xl font-bold text-slate-900 dark:text-white">{title}</h2>
                <p className="text-sm font-medium text-slate-400 mb-3">{tagline}</p>
                <p className="text-sm text-slate-600 dark:text-slate-400 mb-5 flex-1">{desc}</p>
                <ul className="space-y-2 mb-6">
                    {features.map((f: string, i: number) => (
                        <li key={i} className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-300">
                            <Check className={`w-4 h-4 ${t.dot}`} />
                            {f}
                        </li>
                    ))}
                </ul>
                <div className={`flex items-center justify-center gap-2 w-full py-3 rounded-xl text-white font-semibold shadow-lg transition-all ${t.btn}`}>
                    Enter {title}
                    <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </div>
            </Link>
        </motion.div>
    );
}
