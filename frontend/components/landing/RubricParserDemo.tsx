
"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { FileText, ArrowRight, Check, Loader2, Upload } from "lucide-react";

export function RubricParserDemo() {
    const [status, setStatus] = useState<"idle" | "parsing" | "done">("idle");
    const [demoRubric, setDemoRubric] = useState<any[]>([]);

    const handleSimulatedUpload = () => {
        setStatus("parsing");
        // Simulate API delay
        setTimeout(() => {
            setDemoRubric([
                { criteria: "Thesis Statement", max_points: 20, description: "Clear argument presented in introduction." },
                { criteria: "Evidence", max_points: 30, description: "Claims supported by textual evidence." },
                { criteria: "Analysis", max_points: 30, description: "Original analysis connecting evidence to thesis." },
                { criteria: "Mechanics", max_points: 20, description: "Grammar, spelling, and citation formatting." }
            ]);
            setStatus("done");
        }, 2000);
    };

    return (
        <section className="py-24 bg-slate-50 dark:bg-slate-900/50 transition-colors">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex flex-col lg:flex-row items-center gap-16">
                    <div className="flex-1 space-y-8">
                        <h2 className="text-3xl md:text-4xl font-bold text-slate-900 dark:text-white">
                            Don't Build Rubrics. <br />
                            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-violet-600">Just Upload Them.</span>
                        </h2>
                        <p className="text-lg text-slate-600 dark:text-slate-300 leading-relaxed">
                            Stop wasting hours manually entering grading criteria. GradeWise parses your existing Word, PDF, or Excel rubrics and instantly converts them into an active AI grading agent.
                        </p>

                        <div className="flex items-center gap-4 text-sm font-medium text-slate-500">
                            <div className="flex items-center gap-2">
                                <span className="p-1 bg-blue-100 dark:bg-blue-900/30 rounded text-blue-600 dark:text-blue-400"><FileText className="w-4 h-4" /></span>
                                .DOCX
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="p-1 bg-red-100 dark:bg-red-900/30 rounded text-red-600 dark:text-red-400"><FileText className="w-4 h-4" /></span>
                                .PDF
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="p-1 bg-green-100 dark:bg-green-900/30 rounded text-green-600 dark:text-green-400"><FileText className="w-4 h-4" /></span>
                                .XLSX
                            </div>
                        </div>

                        <button
                            onClick={handleSimulatedUpload}
                            disabled={status !== "idle"}
                            className="inline-flex items-center gap-2 px-6 py-3 bg-slate-900 dark:bg-white text-white dark:text-slate-900 rounded-xl font-bold hover:opacity-90 transition-opacity disabled:opacity-50"
                        >
                            {status === "idle" ? <>Try Live Demo <ArrowRight className="w-4 h-4" /></> : "Processing Demo..."}
                        </button>
                    </div>

                    {/* Interactive Demo Card */}
                    <div className="flex-1 w-full max-w-lg">
                        <div className="relative bg-white dark:bg-slate-950 rounded-2xl shadow-xl border border-slate-200 dark:border-slate-800 overflow-hidden min-h-[400px] flex flex-col">
                            {/* Window Header */}
                            <div className="h-10 bg-slate-100 dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 flex items-center px-4 gap-2">
                                <div className="w-3 h-3 rounded-full bg-red-400" />
                                <div className="w-3 h-3 rounded-full bg-yellow-400" />
                                <div className="w-3 h-3 rounded-full bg-green-400" />
                                <div className="text-xs text-slate-400 ml-2 font-mono">rubric_parser.exe</div>
                            </div>

                            {/* Content */}
                            <div className="p-6 flex-1 flex flex-col relative">
                                <AnimatePresence mode="wait">
                                    {status === "idle" && (
                                        <motion.div
                                            key="idle"
                                            initial={{ opacity: 0 }}
                                            animate={{ opacity: 1 }}
                                            exit={{ opacity: 0 }}
                                            className="flex-1 flex flex-col items-center justify-center text-center border-2 border-dashed border-slate-200 dark:border-slate-800 rounded-xl m-4"
                                        >
                                            <div className="w-16 h-16 bg-blue-50 dark:bg-blue-900/20 rounded-full flex items-center justify-center mb-4 text-blue-500">
                                                <Upload className="w-8 h-8" />
                                            </div>
                                            <p className="text-sm font-medium text-slate-900 dark:text-white">Drop your rubric file here</p>
                                            <p className="text-xs text-slate-500 mt-1">or click "Try Live Demo" to simulate</p>
                                        </motion.div>
                                    )}

                                    {status === "parsing" && (
                                        <motion.div
                                            key="parsing"
                                            initial={{ opacity: 0 }}
                                            animate={{ opacity: 1 }}
                                            exit={{ opacity: 0 }}
                                            className="flex-1 flex flex-col items-center justify-center"
                                        >
                                            <Loader2 className="w-12 h-12 text-blue-600 animate-spin mb-4" />
                                            <p className="text-sm font-semibold text-slate-900 dark:text-white">AI Agent Analysis</p>
                                            <p className="text-xs text-slate-500 mt-2">Extracting criteria and point values...</p>
                                            <div className="mt-8 w-48 space-y-2">
                                                <div className="h-2 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                                                    <motion.div
                                                        className="h-full bg-blue-600"
                                                        initial={{ width: "0%" }}
                                                        animate={{ width: "100%" }}
                                                        transition={{ duration: 2 }}
                                                    />
                                                </div>
                                            </div>
                                        </motion.div>
                                    )}

                                    {status === "done" && (
                                        <motion.div
                                            key="done"
                                            initial={{ opacity: 0, y: 10 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            className="space-y-3"
                                        >
                                            <div className="flex items-center justify-between mb-4">
                                                <span className="text-sm font-bold text-green-600 flex items-center gap-2"><Check className="w-4 h-4" /> Parsing Complete</span>
                                                <button onClick={() => setStatus('idle')} className="text-xs text-slate-400 hover:text-slate-600">Reset</button>
                                            </div>

                                            {demoRubric.map((item, i) => (
                                                <motion.div
                                                    key={i}
                                                    initial={{ opacity: 0, x: -10 }}
                                                    animate={{ opacity: 1, x: 0 }}
                                                    transition={{ delay: i * 0.1 }}
                                                    className="p-3 bg-slate-50 dark:bg-slate-900 rounded-lg border border-slate-100 dark:border-slate-800 text-xs"
                                                >
                                                    <div className="flex justify-between font-bold text-slate-700 dark:text-slate-200">
                                                        <span>{item.criteria}</span>
                                                        <span>{item.max_points} pts</span>
                                                    </div>
                                                    <p className="text-slate-500 mt-1 truncate">{item.description}</p>
                                                </motion.div>
                                            ))}
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    );
}
