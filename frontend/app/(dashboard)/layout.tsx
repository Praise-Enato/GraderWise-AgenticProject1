"use client";

import { useState } from "react";
import Link from "next/link";
import Sidebar from "@/components/Sidebar";
import { BackGuard } from "@/components/BackGuard";
import { Menu, Lock, ArrowRight } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { Logo } from "@/components/Logo";

// Keep in sync with app/select/page.tsx — the educator workspace is disabled in the demo deploy.
const EDUCATOR_ENABLED = process.env.NEXT_PUBLIC_EDUCATOR_ENABLED !== "false";

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    const [collapsed, setCollapsed] = useState(false);
    const [mobileOpen, setMobileOpen] = useState(false);

    // Block direct-URL access to any educator page when the workspace is disabled.
    // Rendering this instead of {children} means the educator pages never mount and
    // never call the backend.
    if (!EDUCATOR_ENABLED) {
        return (
            <div className="min-h-screen w-full flex flex-col items-center justify-center px-4 text-center bg-white dark:bg-slate-950">
                <div className="inline-flex w-14 h-14 items-center justify-center rounded-2xl bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 mb-6">
                    <Lock className="w-7 h-7" />
                </div>
                <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
                    Educator grading is unavailable in this demo
                </h1>
                <p className="text-slate-500 dark:text-slate-400 mt-2 mb-8 max-w-md">
                    This deployment showcases the Business Plan grader. The Educator workspace is
                    disabled here.
                </p>
                <Link
                    href="/business"
                    className="inline-flex items-center justify-center gap-2 py-3 px-6 rounded-xl text-white font-semibold shadow-lg bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-700 hover:to-violet-700 transition-all"
                >
                    Go to Business Plan grader
                    <ArrowRight className="w-4 h-4" />
                </Link>
            </div>
        );
    }

    return (
        <div className="flex h-screen overflow-hidden bg-slate-50 dark:bg-slate-950">
            <BackGuard />
            
            {/* Desktop Sidebar */}
            <div className="hidden md:flex h-full z-30">
                <Sidebar collapsed={collapsed} setCollapsed={setCollapsed} />
            </div>

            {/* Mobile Sidebar Overlay */}
            <AnimatePresence>
                {mobileOpen && (
                    <>
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            onClick={() => setMobileOpen(false)}
                            className="fixed inset-0 bg-black/50 z-40 md:hidden backdrop-blur-sm"
                        />
                        <motion.div
                            initial={{ x: "-100%" }}
                            animate={{ x: 0 }}
                            exit={{ x: "-100%" }}
                            transition={{ type: "spring", bounce: 0, duration: 0.4 }}
                            className="fixed inset-y-0 left-0 z-50 w-72 md:hidden"
                        >
                            <Sidebar isMobile onClose={() => setMobileOpen(false)} />
                        </motion.div>
                    </>
                )}
            </AnimatePresence>

            {/* Main content area */}
            <div className="flex-1 flex flex-col h-screen overflow-hidden relative transition-all duration-300">
                {/* Mobile Header */}
                <div className="md:hidden flex items-center justify-between p-4 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 shrink-0 z-20">
                    <div className="flex items-center gap-3">
                        <button 
                            onClick={() => setMobileOpen(true)}
                            className="p-2 -ml-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                        >
                            <Menu className="w-6 h-6 text-slate-600 dark:text-slate-300" />
                        </button>
                        <div className="flex items-center gap-2">
                             {/* Reusing Logo component for brand consistency */}
                             <Logo className="w-8 h-8" showText={false} />
                             <span className="font-bold text-lg text-slate-800 dark:text-white">GradeWise</span>
                        </div>
                    </div>
                </div>

                <div className="flex-1 overflow-y-auto">
                    {children}
                </div>
            </div>
        </div>
    );
}
