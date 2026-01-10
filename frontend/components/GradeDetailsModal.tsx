
"use client";

import { motion, AnimatePresence } from "framer-motion";
import { X, FileText, CheckCircle, AlertTriangle, Calendar, User, Hash, BookOpen, Brain, Sparkles } from "lucide-react";

interface GradeDetailsModalProps {
    isOpen: boolean;
    onClose: () => void;
    item: any; // Using any for flexibility with both HistoryItem and potentially diff structure from Dashboard
}

export function GradeDetailsModal({ isOpen, onClose, item }: GradeDetailsModalProps) {
    if (!item) return null;

    // Helper to determine badge color
    const getScoreColor = (score: number) => {
        if (score >= 90) return "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 border-green-200 dark:border-green-800";
        if (score >= 80) return "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400 border-blue-200 dark:border-blue-800";
        if (score >= 70) return "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400 border-amber-200 dark:border-amber-800";
        return "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400 border-red-200 dark:border-red-800";
    };

    return (
        <AnimatePresence>
            {isOpen && (
                <>
                    {/* Backdrop */}
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={onClose}
                        className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center p-4"
                    />

                    {/* Modal */}
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95, y: 20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95, y: 20 }}
                        className="fixed z-50 w-full max-w-2xl bg-white dark:bg-slate-900 rounded-3xl shadow-2xl border border-slate-200 dark:border-slate-800 overflow-hidden max-h-[90vh] flex flex-col top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2"
                    >
                        {/* Header */}
                        <div className="p-6 border-b border-slate-100 dark:border-slate-800 flex justify-between items-start bg-slate-50/50 dark:bg-slate-800/30">
                            <div>
                                <div className="flex items-center gap-2 mb-2">
                                    <span className="text-xs font-bold uppercase tracking-wider text-slate-500 bg-white dark:bg-slate-800 px-2 py-1 rounded border border-slate-200 dark:border-slate-700">
                                        {item.subject || "Subject"}
                                    </span>
                                    <span className="text-xs text-slate-400 flex items-center gap-1">
                                        <Calendar className="w-3 h-3" />
                                        {item.date ? new Date(item.date).toLocaleDateString() : 'Just now'}
                                    </span>
                                </div>
                                <h2 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
                                    {item.studentName}
                                </h2>
                                <p className="text-sm text-slate-500 flex items-center gap-1 mt-1">
                                    <Hash className="w-3 h-3" /> ID: {item.studentId}
                                </p>
                            </div>
                            <button
                                onClick={onClose}
                                className="p-2 hover:bg-slate-200 dark:hover:bg-slate-800 rounded-full transition-colors text-slate-500"
                            >
                                <X className="w-5 h-5" />
                            </button>
                        </div>

                        {/* Content Scrollable */}
                        <div className="flex-1 overflow-y-auto p-6 space-y-6">

                            {/* Score Stats */}
                            <div className="flex gap-4">
                                <div className={`flex-1 p-4 rounded-xl border ${getScoreColor(item.score)} flex flex-col items-center justify-center text-center`}>
                                    <span className="text-sm font-semibold uppercase tracking-wide opacity-80">Final Score</span>
                                    <span className="text-4xl font-bold mt-1">{item.score}%</span>
                                </div>

                                {item.confidence_score !== undefined && (
                                    <div className="flex-1 p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50 flex flex-col items-center justify-center text-center">
                                        <div className="flex items-center gap-1.5 text-slate-500 text-sm font-semibold uppercase tracking-wide mb-1">
                                            <Brain className="w-4 h-4" /> AI Confidence
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <span className={`text-2xl font-bold ${item.confidence_score >= 0.9 ? 'text-green-600' : 'text-amber-500'}`}>
                                                {Math.round(item.confidence_score * 100)}%
                                            </span>
                                            {item.confidence_score >= 0.9 && <CheckCircle className="w-5 h-5 text-green-500" />}
                                        </div>
                                    </div>
                                )}
                            </div>

                            {/* Detailed Feedback */}
                            <div>
                                <h3 className="text-sm font-bold uppercase text-slate-500 mb-3 flex items-center gap-2">
                                    <Sparkles className="w-4 h-4 text-blue-500" />
                                    Detailed Feedback
                                </h3>
                                <div className="p-5 bg-slate-50 dark:bg-slate-800/50 rounded-2xl border border-slate-100 dark:border-slate-800 text-slate-700 dark:text-slate-300 leading-relaxed whitespace-pre-wrap">
                                    {item.feedback}
                                </div>
                            </div>

                        </div>

                        {/* Footer */}
                        <div className="p-4 border-t border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 flex justify-end">
                            <button onClick={onClose} className="px-6 py-2.5 bg-slate-900 dark:bg-white text-white dark:text-slate-900 font-medium rounded-xl hover:opacity-90 transition-opacity">
                                Close Report
                            </button>
                        </div>
                    </motion.div>
                </>
            )}
        </AnimatePresence>
    );
}
