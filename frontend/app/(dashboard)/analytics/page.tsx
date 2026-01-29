"use client";

import { useEffect, useState } from "react";
import { BarChart3, TrendingUp, Users, Award, Calendar } from "lucide-react";
import { motion } from "framer-motion";

export default function AnalyticsPage() {
    const [stats, setStats] = useState({
        total: 0,
        average: 0,
        highest: 0,
        lowest: 0,
        distribution: { A: 0, B: 0, C: 0, D: 0, F: 0 }
    });
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function fetchAnalytics() {
            try {
                const res = await fetch('/api/submissions', { cache: 'no-store' });
                const data = await res.json();
                
                if (Array.isArray(data)) {
                    const graded = data.filter((s: any) => s.status === 'graded' && s.grade);
                    
                    if (graded.length === 0) {
                        setStats(prev => ({ ...prev, total: data.length }));
                        return;
                    }

                    // Parse grades (handling "45 / 50" format)
                    const scores = graded.map((s: any) => {
                        const parts = s.grade.split('/');
                        if (parts.length === 2) {
                            const score = parseFloat(parts[0].trim());
                            const max = parseFloat(parts[1].trim());
                            return (score / max) * 100; // Normalize to percentage
                        }
                        return 0;
                    });

                    const total = data.length;
                    const avg = scores.reduce((a: number, b: number) => a + b, 0) / scores.length;
                    const max = Math.max(...scores);
                    const min = Math.min(...scores);

                    // Calculate distribution
                    const dist = { A: 0, B: 0, C: 0, D: 0, F: 0 };
                    scores.forEach((s: number) => {
                        if (s >= 90) dist.A++;
                        else if (s >= 80) dist.B++;
                        else if (s >= 70) dist.C++;
                        else if (s >= 60) dist.D++;
                        else dist.F++;
                    });

                    setStats({
                        total,
                        average: Math.round(avg),
                        highest: Math.round(max),
                        lowest: Math.round(min),
                        distribution: dist
                    });
                }
            } catch (e) {
                console.error("Failed to load analytics", e);
            } finally {
                setLoading(false);
            }
        }

        fetchAnalytics();
    }, []);

    const cards = [
        { label: "Class Average", value: `${stats.average}%`, icon: TrendingUp, color: "text-emerald-500", bg: "bg-emerald-50 dark:bg-emerald-900/20" },
        { label: "Total Submissions", value: stats.total, icon: Users, color: "text-blue-500", bg: "bg-blue-50 dark:bg-blue-900/20" },
        { label: "Highest Score", value: `${stats.highest}%`, icon: Award, color: "text-amber-500", bg: "bg-amber-50 dark:bg-amber-900/20" },
        { label: "Recent Activity", value: "Today", icon: Calendar, color: "text-purple-500", bg: "bg-purple-50 dark:bg-purple-900/20" },
    ];

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
            </div>
        );
    }

    return (
        <div className="p-8 max-w-7xl mx-auto space-y-8">
            <div>
                <h1 className="text-3xl font-bold text-slate-900 dark:text-white flex items-center gap-3">
                    <BarChart3 className="w-8 h-8 text-indigo-600" />
                    Analytics Dashboard
                </h1>
                <p className="text-slate-500 dark:text-slate-400 mt-2">Performance insights and grade distribution overview.</p>
            </div>

            {/* Key Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {cards.map((card, idx) => (
                    <motion.div 
                        key={idx}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: idx * 0.1 }}
                        className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm"
                    >
                        <div className="flex items-start justify-between">
                            <div>
                                <p className="text-sm font-medium text-slate-500 dark:text-slate-400">{card.label}</p>
                                <h3 className="text-3xl font-bold text-slate-900 dark:text-white mt-2">{card.value}</h3>
                            </div>
                            <div className={`p-3 rounded-xl ${card.bg}`}>
                                <card.icon className={`w-6 h-6 ${card.color}`} />
                            </div>
                        </div>
                    </motion.div>
                ))}
            </div>

            {/* Charts Section */}
            <div className="grid md:grid-cols-2 gap-8">
                {/* Grade Distribution */}
                <motion.div 
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.4 }}
                    className="bg-white dark:bg-slate-900 p-8 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm"
                >
                    <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-6">Grade Distribution</h3>
                    <div className="flex items-end gap-4 h-64 border-b border-slate-200 dark:border-slate-700 pb-4">
                        {Object.entries(stats.distribution).map(([grade, count], i) => {
                            const max = 10; // arbitrary scale max for demo
                            const height = Math.min((count / (stats.total || 1)) * 100, 100); 
                            
                            return (
                                <div key={grade} className="flex-1 flex flex-col items-center justify-end h-full gap-2 group">
                                     <div className="text-xs font-bold text-slate-500 opacity-0 group-hover:opacity-100 transition-opacity mb-1 uppercase tracking-wider">{count} students</div>
                                    <div 
                                        className="w-full bg-indigo-500 dark:bg-indigo-600 rounded-t-lg transition-all duration-500 hover:bg-indigo-400"
                                        style={{ height: `${count > 0 ? (count / (stats.total || 1)) * 100 : 2}%` }}
                                    />
                                    <span className="font-bold text-slate-600 dark:text-slate-400">{grade}</span>
                                </div>
                            );
                        })}
                    </div>
                </motion.div>

                {/* Performance Summary */}
                <motion.div 
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.5 }}
                    className="bg-white dark:bg-slate-900 p-8 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col justify-center items-center text-center"
                >
                    <div className="w-32 h-32 rounded-full border-8 border-emerald-100 dark:border-emerald-900/30 flex items-center justify-center mb-6">
                        <span className="text-3xl font-black text-emerald-600 dark:text-emerald-400">{stats.average || 0}%</span>
                    </div>
                    <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-2">Class Performance</h3>
                    <p className="text-slate-500 dark:text-slate-400 text-sm max-w-xs">
                        The class average is currently <strong className="text-slate-700 dark:text-slate-200">{stats.average > 70 ? 'strong' : 'needs improvement'}</strong>. 
                        Most students are falling within the <strong>{Object.entries(stats.distribution).sort((a,b) => b[1] - a[1])[0]?.[0]} range</strong>.
                    </p>
                </motion.div>
            </div>
        </div>
    );
}
