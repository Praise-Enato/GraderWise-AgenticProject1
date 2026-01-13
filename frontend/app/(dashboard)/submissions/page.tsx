"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Search, Filter, BookOpen, Clock, ChevronRight, User, CheckCircle, AlertCircle } from "lucide-react";
import Link from "next/link";

type Submission = {
    id: string;
    title: string;
    studentName?: string; // We might need to mock this if not in current data
    status: 'pending' | 'graded';
    date: string;
    fileName?: string;
    grade?: string;
};

export default function SubmissionsPage() {
    const [submissions, setSubmissions] = useState<Submission[]>([]);
    const [filter, setFilter] = useState<'all' | 'pending' | 'graded'>('all');

    useEffect(() => {
        const fetchSubmissions = async () => {
            try {
                const res = await fetch('/api/student/submissions');
                const data = await res.json();
                // Add mock student names for demo if missing
                const enriched = data.map((s: any) => ({
                    ...s,
                    studentName: s.studentName || "Student User"
                }));
                setSubmissions(enriched);
            } catch (e) {
                console.error(e);
            }
        };
        fetchSubmissions();
    }, []);

    const filtered = submissions.filter(s => {
        if (filter === 'all') return true;
        return s.status === filter;
    });

    return (
        <div className="min-h-screen bg-slate-50 dark:bg-background p-8 transition-colors duration-300">
            <div className="max-w-7xl mx-auto space-y-8">
                {/* Header */}
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                        <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Student Submissions</h1>
                        <p className="text-slate-500 dark:text-slate-400 mt-1">Manage and grade incoming assignment work.</p>
                    </div>
                    <div className="flex items-center gap-2 bg-white dark:bg-slate-900 p-1.5 rounded-xl border border-slate-200 dark:border-slate-800">
                        <button
                            onClick={() => setFilter('all')}
                            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${filter === 'all' ? 'bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-white shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}
                        >
                            All
                        </button>
                        <button
                            onClick={() => setFilter('pending')}
                            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${filter === 'pending' ? 'bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}
                        >
                            Pending
                        </button>
                        <button
                            onClick={() => setFilter('graded')}
                            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${filter === 'graded' ? 'bg-emerald-50 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400 shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}
                        >
                            Graded
                        </button>
                    </div>
                </div>

                {/* List */}
                <div className="grid gap-4">
                    {filtered.length === 0 && (
                        <div className="text-center py-20 bg-white dark:bg-slate-900 rounded-2xl border border-dashed border-slate-200 dark:border-slate-800">
                            <BookOpen className="w-12 h-12 text-slate-300 mx-auto mb-4" />
                            <p className="text-slate-500">No submissions found.</p>
                        </div>
                    )}

                    {filtered.map((sub) => (
                        <motion.div
                            key={sub.id}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm hover:shadow-md transition-shadow group relative overflow-hidden"
                        >
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-6">
                                    <div className={`w-12 h-12 rounded-full flex items-center justify-center ${sub.status === 'graded' ? 'bg-emerald-100 dark:bg-emerald-900/20 text-emerald-500' : 'bg-amber-100 dark:bg-amber-900/20 text-amber-500'}`}>
                                        {sub.status === 'graded' ? <CheckCircle className="w-6 h-6" /> : <Clock className="w-6 h-6" />}
                                    </div>
                                    <div>
                                        <h3 className="text-lg font-bold text-slate-900 dark:text-white group-hover:text-primary transition-colors">{sub.title}</h3>
                                        <div className="flex items-center gap-4 text-sm text-slate-500 mt-1">
                                            <span className="flex items-center gap-1"><User className="w-3 h-3" /> {sub.studentName}</span>
                                            <span className="w-1 h-1 bg-slate-300 rounded-full" />
                                            <span>{sub.date}</span>
                                            {sub.fileName && (
                                                <>
                                                    <span className="w-1 h-1 bg-slate-300 rounded-full" />
                                                    <span className="font-mono bg-slate-100 dark:bg-slate-800 px-2 rounded text-xs">{sub.fileName}</span>
                                                </>
                                            )}
                                        </div>
                                    </div>
                                </div>

                                <div className="flex items-center gap-6">
                                    {sub.status === 'graded' ? (
                                        <div className="text-right">
                                            <span className="text-2xl font-black text-slate-900 dark:text-white">{sub.grade}</span>
                                            <p className="text-[10px] font-bold text-emerald-500 uppercase tracking-wider">Completed</p>
                                        </div>
                                    ) : (
                                        <div className="px-3 py-1 bg-amber-50 dark:bg-amber-900/20 text-amber-600 dark:text-amber-400 text-xs font-bold uppercase tracking-wider rounded-lg">
                                            Pending Review
                                        </div>
                                    )}

                                    <Link
                                        href={`/grading?id=${sub.id}`}
                                        className="w-10 h-10 rounded-full bg-slate-50 dark:bg-slate-800 flex items-center justify-center text-slate-400 hover:bg-primary hover:text-white transition-all"
                                    >
                                        <ChevronRight className="w-5 h-5" />
                                    </Link>
                                </div>
                            </div>
                        </motion.div>
                    ))}
                </div>
            </div>
        </div>
    );
}
