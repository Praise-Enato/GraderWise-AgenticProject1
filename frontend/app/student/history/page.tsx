"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Clock, FileText, CheckCircle, Loader2, Calendar } from "lucide-react";

// Mock user for demo isolation
const MOCK_USER = { studentId: "student-123" };

type HistoryItem = {
    id: string;
    action: string;
    details: string;
    date: string;
    type: 'submission' | 'grade' | 'system';
};

export default function HistoryPage() {
    const [history, setHistory] = useState<HistoryItem[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Fetch submissions and transform into a history timeline
        fetch(`/api/student/submissions?studentId=${MOCK_USER.studentId}`)
            .then(res => res.json())
            .then((data: any[]) => {
                const events: HistoryItem[] = [];

                data.forEach(sub => {
                    // Event 1: Submission Created
                    events.push({
                        id: sub.id + "_submit",
                        action: "Submitted Assignment",
                        details: sub.title,
                        date: sub.date,
                        type: 'submission'
                    });

                    // Event 2: Graded (if status is graded)
                    if (sub.status === 'graded') {
                        events.push({
                            id: sub.id + "_grade",
                            action: "Received Grade",
                            details: `Scored ${sub.grade} on ${sub.title}`,
                            // Mocking a slightly later date/time or same date
                            date: sub.gradedAt ? new Date(sub.gradedAt).toLocaleDateString() : sub.date,
                            type: 'grade'
                        });
                    }
                });

                // Sort by date (mock sort as dates are strings like '1/13/2026')
                // For robust sorting in real app, backend should return ISO dates.
                // Here we just reverse to show latest first assuming data comes in order.
                setHistory(events.reverse());
                setLoading(false);
            })
            .catch(err => console.error(err));
    }, []);

    return (
        <div className="max-w-4xl mx-auto space-y-8">
            <div>
                <h1 className="text-3xl font-bold text-slate-900 dark:text-white flex items-center gap-3">
                    <Clock className="w-8 h-8 text-indigo-500" />
                    Activity History
                </h1>
                <p className="text-slate-500 dark:text-slate-400 mt-2">Track your academic journey and system activities.</p>
            </div>

            <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm p-8">
                {loading ? (
                    <div className="flex justify-center py-12">
                        <Loader2 className="w-8 h-8 animate-spin text-indigo-500" />
                    </div>
                ) : history.length === 0 ? (
                    <div className="text-center py-12 text-slate-500">No activity recorded yet.</div>
                ) : (
                    <div className="relative border-l-2 border-slate-100 dark:border-slate-800 ml-4 space-y-8 pl-8 py-2">
                        {history.map((item, i) => (
                            <motion.div
                                key={item.id}
                                initial={{ opacity: 0, x: -20 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ delay: i * 0.05 }}
                                className="relative"
                            >
                                <div className={`absolute -left-[41px] top-1 w-5 h-5 rounded-full border-4 border-white dark:border-slate-900 ${item.type === 'grade' ? 'bg-emerald-500' : 'bg-indigo-500'
                                    }`} />

                                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                                    <div>
                                        <h3 className="font-bold text-slate-900 dark:text-white text-lg">{item.action}</h3>
                                        <p className="text-slate-500 dark:text-slate-400">{item.details}</p>
                                    </div>
                                    <div className="flex items-center gap-2 text-xs font-mono text-slate-400 bg-slate-50 dark:bg-slate-800 px-3 py-1 rounded-full self-start sm:self-auto">
                                        <Calendar className="w-3 h-3" />
                                        {item.date}
                                    </div>
                                </div>
                            </motion.div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
