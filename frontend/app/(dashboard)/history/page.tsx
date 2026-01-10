"use client";

import { useState, useEffect } from "react";
import { History, Search, FileText, Calendar, ChevronRight, User, Hash, BookOpen } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface HistoryItem {
    id: string;
    date: string;
    studentName: string;
    studentId: string;
    subject: string;
    score: number;
    feedback: string;
    citations: string[];
}

import { GradeDetailsModal } from "@/components/GradeDetailsModal"; // Import

export default function HistoryPage() {
    const [history, setHistory] = useState<HistoryItem[]>([]);
    const [searchTerm, setSearchTerm] = useState("");
    const [selectedItem, setSelectedItem] = useState<HistoryItem | null>(null); // State
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        setMounted(true);
        const stored = localStorage.getItem('gradingHistory');
        if (stored) {
            try {
                setHistory(JSON.parse(stored));
            } catch (e) {
                console.error("Failed to parse history", e);
            }
        }
    }, []);

    const filteredHistory = history.filter(item =>
        item.studentName.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.studentId.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.subject.toLowerCase().includes(searchTerm.toLowerCase())
    );

    if (!mounted) return null;

    return (
        <div className="h-screen overflow-y-auto bg-slate-50 dark:bg-background p-8 transition-colors duration-300">
            <div className="max-w-7xl mx-auto pb-20 space-y-8">

                {/* Header */}
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                        <h1 className="text-3xl font-bold text-slate-900 dark:text-white flex items-center gap-3">
                            <History className="w-8 h-8 text-primary" /> Class History
                        </h1>
                        <p className="text-slate-500 dark:text-slate-400 mt-1">Archive of all graded assessments.</p>
                    </div>

                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                        <input
                            type="text"
                            placeholder="Search students or subjects..."
                            className="pl-10 pr-4 py-2.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl focus:ring-2 focus:ring-primary/20 outline-none w-full md:w-80 transition-all text-slate-900 dark:text-white"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                        />
                    </div>
                </div>

                {/* Content */}
                {history.length === 0 ? (
                    <div className="flex flex-col items-center justify-center p-20 bg-white dark:bg-slate-900/50 rounded-3xl border border-dashed border-slate-300 dark:border-slate-800 text-center">
                        <div className="w-16 h-16 bg-slate-100 dark:bg-slate-800 rounded-full flex items-center justify-center mb-6">
                            <FileText className="w-8 h-8 text-slate-400" />
                        </div>
                        <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-2">No History Yet</h3>
                        <p className="text-slate-500 max-w-sm mb-6">Start by grading a student submission in the "New Grading Job" section.</p>
                        <a href="/grading" className="px-6 py-2.5 bg-primary text-white rounded-xl font-medium hover:bg-blue-600 transition-colors">
                            Go to Grading
                        </a>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        <AnimatePresence>
                            {filteredHistory.map((item, index) => (
                                <motion.div
                                    key={item.id}
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ delay: index * 0.05 }}
                                    onClick={() => setSelectedItem(item)}
                                    className="bg-white dark:bg-slate-900/50 backdrop-blur-sm border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm hover:shadow-lg hover:border-blue-200 dark:hover:border-blue-800 transition-all group cursor-pointer overflow-hidden flex flex-col scale-[1] active:scale-[0.98]"
                                >
                                    <div className="p-6 flex-1">
                                        <div className="flex justify-between items-start mb-4">
                                            <div className="flex flex-col">
                                                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">{item.subject}</span>
                                                <h3 className="font-bold text-lg text-slate-900 dark:text-white">{item.studentName}</h3>
                                            </div>
                                            <div className={`px-3 py-1 rounded-full text-sm font-bold ${item.score >= 90 ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' :
                                                item.score >= 80 ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' :
                                                    item.score >= 70 ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400' :
                                                        'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                                                }`}>
                                                {item.score}%
                                            </div>
                                        </div>

                                        <div className="space-y-3 mb-6">
                                            <div className="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
                                                <Hash className="w-4 h-4" /> ID: {item.studentId}
                                            </div>
                                            <div className="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
                                                <Calendar className="w-4 h-4" /> {new Date(item.date).toLocaleDateString()}
                                            </div>
                                        </div>

                                        <p className="text-sm text-slate-600 dark:text-slate-300 line-clamp-3">
                                            {item.feedback}
                                        </p>
                                    </div>

                                    <div className="p-4 border-t border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/30 flex justify-between items-center group-hover:bg-blue-50/50 dark:group-hover:bg-blue-900/10 transition-colors">
                                        <span className="text-xs font-medium text-slate-500">View Full Report</span>
                                        <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-primary transition-colors" />
                                    </div>
                                </motion.div>
                            ))}
                        </AnimatePresence>
                    </div>
                )}
            </div>

            <GradeDetailsModal
                isOpen={!!selectedItem}
                onClose={() => setSelectedItem(null)}
                item={selectedItem}
            />
        </div>
    );
}
