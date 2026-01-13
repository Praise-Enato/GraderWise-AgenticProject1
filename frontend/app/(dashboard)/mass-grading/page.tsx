"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Layers, Play, CheckCircle, AlertCircle, Loader2, FileText } from "lucide-react";

export default function MassGradingPage() {
    const [pendingCount, setPendingCount] = useState(0);
    const [isGrading, setIsGrading] = useState(false);
    const [progress, setProgress] = useState(0);
    const [logs, setLogs] = useState<string[]>([]);
    const [complete, setComplete] = useState(false);

    useEffect(() => {
        fetchStats();
    }, []);

    const fetchStats = async () => {
        const res = await fetch('/api/student/submissions');
        const data = await res.json();
        const pending = data.filter((s: any) => s.status === 'pending');
        setPendingCount(pending.length);
    };

    const handleMassGrade = async () => {
        setIsGrading(true);
        setLogs(prev => [...prev, "Initializing Mass Grading protocols..."]);
        setProgress(10);

        try {
            setLogs(prev => [...prev, `Found ${pendingCount} pending submissions. Sending to AI Agent...`]);
            setProgress(30);

            const res = await fetch('/api/educator/mass-grade', {
                method: 'POST'
            });
            const result = await res.json();

            if (res.ok) {
                setProgress(100);
                setLogs(prev => [...prev, ...result.results.map((r: any) => `Submission ${r.id}: ${r.status.toUpperCase()}`)]);
                setLogs(prev => [...prev, "Batch processing complete."]);
                setComplete(true);
                fetchStats(); // Refresh count
            } else {
                setLogs(prev => [...prev, "Error: " + result.error]);
            }

        } catch (e) {
            setLogs(prev => [...prev, "Critical Failure: " + String(e)]);
        } finally {
            setIsGrading(false);
        }
    };

    return (
        <div className="min-h-screen bg-slate-50 dark:bg-background p-8">
            <div className="max-w-4xl mx-auto space-y-8">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900 dark:text-white flex items-center gap-3">
                        <Layers className="w-8 h-8 text-indigo-500" />
                        Mass Grading Agent
                    </h1>
                    <p className="text-slate-500 dark:text-slate-400 mt-2">
                        Automate the assessment of multiple submissions using the configured rubric.
                    </p>
                </div>

                <div className="grid md:grid-cols-2 gap-8">
                    {/* Status Card */}
                    <div className="bg-white dark:bg-slate-900 p-8 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col items-center justify-center text-center">
                        <div className="w-24 h-24 rounded-full bg-indigo-50 dark:bg-indigo-900/20 flex items-center justify-center mb-6">
                            <FileText className="w-10 h-10 text-indigo-500" />
                        </div>
                        <h2 className="text-4xl font-black text-slate-900 dark:text-white mb-2">{pendingCount}</h2>
                        <p className="text-slate-500 font-medium uppercase tracking-wider text-sm">Pending Submissions</p>

                        <button
                            onClick={handleMassGrade}
                            disabled={pendingCount === 0 || isGrading}
                            className={`mt-8 w-full py-4 rounded-2xl font-bold text-lg flex items-center justify-center gap-3 transition-all ${pendingCount === 0
                                    ? 'bg-slate-100 dark:bg-slate-800 text-slate-400 cursor-not-allowed'
                                    : isGrading
                                        ? 'bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600'
                                        : 'bg-indigo-600 hover:bg-indigo-700 text-white shadow-xl shadow-indigo-500/20 hover:scale-[1.02]'
                                }`}
                        >
                            {isGrading ? <Loader2 className="w-6 h-6 animate-spin" /> : <Play className="w-6 h-6 fill-current" />}
                            {isGrading ? "Agent Working..." : "Run Mass Grading"}
                        </button>
                    </div>

                    {/* Terminal / Log */}
                    <div className="bg-slate-900 rounded-3xl p-6 font-mono text-sm text-slate-300 overflow-hidden flex flex-col h-[400px]">
                        <div className="flex items-center gap-2 mb-4 text-slate-500 border-b border-white/10 pb-4">
                            <div className="w-3 h-3 rounded-full bg-red-500" />
                            <div className="w-3 h-3 rounded-full bg-yellow-500" />
                            <div className="w-3 h-3 rounded-full bg-green-500" />
                            <span className="ml-2 text-xs">agent_logs.log</span>
                        </div>
                        <div className="flex-1 overflow-y-auto space-y-2">
                            {logs.length === 0 && <span className="text-slate-600 italic">// Ready to process...</span>}
                            {logs.map((log, i) => (
                                <motion.div
                                    key={i}
                                    initial={{ opacity: 0, x: -10 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    className="border-l-2 border-indigo-500 pl-3 py-1"
                                >
                                    <span className="text-indigo-400 mr-2">➜</span>
                                    {log}
                                </motion.div>
                            ))}
                            {complete && (
                                <motion.div
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    className="text-emerald-400 font-bold mt-4 pt-4 border-t border-white/10"
                                >
                                    Work Session Complete. All items graded.
                                </motion.div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Rubric Preview (Brief) */}
                <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800">
                    <h3 className="font-bold text-slate-900 dark:text-white mb-4">Active Global Rubric</h3>
                    <div className="grid md:grid-cols-3 gap-4">
                        {['Thesis & Argument', 'Evidence & Analysis', 'Structure & Clarity'].map((c, i) => (
                            <div key={i} className="p-3 bg-slate-50 dark:bg-slate-800 rounded-lg text-sm border border-slate-100 dark:border-slate-700">
                                <span className="font-semibold block text-slate-700 dark:text-slate-300">{c}</span>
                                <span className="text-slate-400 text-xs">Weighted Criteria</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}
