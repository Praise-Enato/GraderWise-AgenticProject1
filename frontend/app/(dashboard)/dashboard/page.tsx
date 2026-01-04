"use client";

import {
  Bell,
  Plus,
  CheckCircle,
  Clock,
  Star,
  Zap,
  Upload,
  FolderOpen,
  ArrowRight
} from 'lucide-react';
import Link from 'next/link';
import { motion } from "framer-motion";
import { ModeToggle } from "@/components/ModeToggle";
import { NotificationDropdown } from "@/components/NotificationDropdown";
import { useState, useEffect } from "react";

interface HistoryItem {
  id: string;
  date: string;
  studentName: string;
  studentId: string;
  subject: string;
  score: number;
}

export default function Dashboard() {
  const [recentActivity, setRecentActivity] = useState<HistoryItem[]>([]);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const stored = localStorage.getItem('gradingHistory');
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        setRecentActivity(parsed.slice(0, 5));
      } catch (e) {
        console.error("Failed to parse history", e);
      }
    }
  }, []);

  const container = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  const getInitials = (name: string) => {
    return name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
  };

  const colors = ["bg-pink-500", "bg-purple-500", "bg-blue-500", "bg-emerald-500", "bg-orange-500"];

  return (
    <div className="flex h-screen overflow-hidden bg-background transition-colors duration-300">
      <main className="flex-1 overflow-y-auto relative p-8">

        {/* Subtle Background Elements */}
        <div className="absolute top-0 left-0 w-full h-96 overflow-hidden pointer-events-none opacity-40 dark:opacity-20 z-0">
          <div className="absolute -top-20 -right-20 w-[600px] h-[600px] bg-blue-50 dark:bg-blue-900/20 rounded-full blur-3xl"></div>
          <div className="absolute top-40 -left-20 w-[400px] h-[400px] bg-indigo-50 dark:bg-indigo-900/20 rounded-full blur-3xl"></div>
        </div>

        <motion.div
          className="max-w-7xl mx-auto relative z-10 space-y-8"
          variants={container}
          initial="hidden"
          animate="show"
        >
          {/* Header */}
          <header className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div>
              <h1 className="text-3xl font-bold text-slate-900 dark:text-white tracking-tight">Dashboard</h1>
              <p className="text-slate-500 dark:text-slate-400 mt-1 text-sm md:text-base">Welcome back, Prof. Anderson. Here's what's happening in your classes.</p>
            </div>
            <div className="flex items-center gap-3">
              <ModeToggle />
              <NotificationDropdown />
              <Link href="/grading">
                <button className="bg-primary hover:bg-blue-600 text-white px-5 py-2.5 rounded-xl shadow-lg shadow-blue-500/25 flex items-center gap-2 transition-all transform hover:-translate-y-0.5 active:translate-y-0 font-medium text-sm">
                  <Plus className="w-4 h-4" />
                  <span>Create Assessment</span>
                </button>
              </Link>
            </div>
          </header>

          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <StatsCard
              icon={<CheckCircle className="w-6 h-6 text-white" />}
              iconBg="bg-blue-500"
              badge="+12% from last week"
              badgeColor="text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20"
              value={recentActivity.length.toString()}
              label="Total Submissions"
              subtext="Recorded in local history"
            />
            <StatsCard
              icon={<Clock className="w-6 h-6 text-white" />}
              iconBg="bg-indigo-500"
              badge="-5% avg. time"
              badgeColor="text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20"
              value="4.2m"
              label="Avg. Grading Time"
              subtext="Per Submission"
            />
            <StatsCard
              icon={<Star className="w-6 h-6 text-white" />}
              iconBg="bg-amber-500"
              badge="Top 10% performance"
              badgeColor="text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20"
              value="88%"
              label="Class Average"
              subtext="Physics 101"
            />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Quick Actions - TeachFlow Style */}
            <div className="lg:col-span-1 space-y-6">
              <section className="bg-white dark:bg-slate-800/50 backdrop-blur-sm border border-slate-200 dark:border-slate-700 rounded-2xl p-6 shadow-sm h-full flex flex-col justify-between">
                <div>
                  <div className="flex items-center gap-2 mb-6">
                    <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg text-primary">
                      <Zap className="w-5 h-5" />
                    </div>
                    <h2 className="text-lg font-bold text-slate-900 dark:text-white">Quick Actions</h2>
                  </div>

                  <div className="space-y-3">
                    <ActionButton
                      icon={<Upload className="w-5 h-5" />}
                      title="Import Rubric"
                      desc="Upload PDF guide"
                    />
                    <ActionButton
                      icon={<FolderOpen className="w-5 h-5" />}
                      title="Course Materials"
                      desc="Manage resources"
                    />
                  </div>
                </div>

                <Link href="/grading" className="mt-6 w-full">
                  <button className="w-full py-3 bg-slate-900 dark:bg-black text-white rounded-xl font-medium shadow-lg shadow-slate-900/10 hover:shadow-slate-900/20 transition-all flex items-center justify-center gap-2 group">
                    Start New Grading Job <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                  </button>
                </Link>
              </section>
            </div>

            {/* Recent Assessments Table */}
            <div className="lg:col-span-2">
              <div className="bg-white dark:bg-slate-800/50 backdrop-blur-sm border border-slate-200 dark:border-slate-700 rounded-2xl shadow-sm overflow-hidden min-h-[400px]">
                <div className="p-6 border-b border-slate-100 dark:border-slate-700 flex justify-between items-center">
                  <h2 className="text-lg font-bold text-slate-900 dark:text-white">Recent Activity</h2>
                  <Link href="/history" className="text-sm font-medium text-primary hover:text-blue-700 transition-colors">View All</Link>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse">
                    <thead className="bg-slate-50 dark:bg-slate-800/80">
                      <tr>
                        <th className="px-6 py-4 text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400 font-semibold">Student</th>
                        <th className="px-6 py-4 text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400 font-semibold">Assessment</th>
                        <th className="px-6 py-4 text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400 font-semibold">Status</th>
                        <th className="px-6 py-4 text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400 font-semibold text-right">Grade</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                      {!mounted ? (
                        <tr>
                          <td colSpan={4} className="px-6 py-12 text-center text-slate-500">Loading activity...</td>
                        </tr>
                      ) : recentActivity.length === 0 ? (
                        <tr>
                          <td colSpan={4} className="px-6 py-12 text-center text-slate-500">
                            <p className="mb-2">No recent grading activity found.</p>
                            <Link href="/grading" className="text-primary hover:underline text-sm">Grade your first student</Link>
                          </td>
                        </tr>
                      ) : (
                        recentActivity.map((item, index) => (
                          <TableRow
                            key={item.id}
                            initials={getInitials(item.studentName)}
                            color={colors[index % colors.length]}
                            name={item.studentName}
                            assignment={item.subject} // Using subject as assignment for now
                            status="Graded"
                            statusColor="green"
                            score={item.score + "%"}
                          />
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>

        </motion.div>
      </main>
    </div>
  );
}

// Components
function StatsCard({ icon, iconBg, badge, badgeColor, value, label, subtext }: any) {
  return (
    <div className="bg-white dark:bg-slate-800/50 backdrop-blur-sm p-6 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm hover:shadow-md transition-shadow group">
      <div className="flex justify-between items-start mb-4">
        <div className={`p-3 ${iconBg} rounded-xl shadow-lg shadow-blue-500/20 group-hover:scale-110 transition-transform duration-300`}>
          {icon}
        </div>
        <span className={`px-2.5 py-1 rounded-full text-xs font-semibold ${badgeColor}`}>
          {badge}
        </span>
      </div>
      <div>
        <h3 className="text-3xl font-bold text-slate-900 dark:text-white mb-1">{value}</h3>
        <p className="text-sm font-medium text-slate-600 dark:text-slate-300">{label}</p>
        <p className="text-xs text-slate-400 mt-1">{subtext}</p>
      </div>
    </div>
  );
}

function ActionButton({ icon, title, desc }: any) {
  return (
    <button className="w-full flex items-center gap-4 p-4 rounded-xl border border-slate-100 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/30 hover:bg-white dark:hover:bg-slate-800 hover:border-slate-200 dark:hover:border-slate-600 hover:shadow-md transition-all text-left group">
      <div className="p-2.5 bg-white dark:bg-slate-700 rounded-lg text-slate-600 dark:text-slate-300 group-hover:text-primary group-hover:bg-blue-50 dark:group-hover:bg-blue-900/20 transition-colors shadow-sm">
        {icon}
      </div>
      <div>
        <h4 className="font-semibold text-slate-900 dark:text-white text-sm group-hover:text-primary transition-colors">{title}</h4>
        <p className="text-xs text-slate-500 dark:text-slate-400">{desc}</p>
      </div>
      <ArrowRight className="w-4 h-4 text-slate-300 ml-auto group-hover:text-primary group-hover:translate-x-1 transition-all" />
    </button>
  )
}

function TableRow({ initials, color, name, assignment, status, statusColor, score, processing }: any) {
  const statusConfig: Record<string, string> = {
    green: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
    amber: "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400",
    slate: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-400",
  };

  return (
    <tr className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors group">
      <td className="px-6 py-4">
        <div className="flex items-center gap-3">
          <div className={`w-9 h-9 rounded-full ${color} flex items-center justify-center text-white text-xs font-bold shadow-sm ring-2 ring-white dark:ring-slate-800`}>
            {initials}
          </div>
          <span className="font-semibold text-slate-900 dark:text-white group-hover:text-primary transition-colors">{name}</span>
        </div>
      </td>
      <td className="px-6 py-4 text-sm text-slate-600 dark:text-slate-400">{assignment}</td>
      <td className="px-6 py-4">
        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${statusConfig[statusColor]}`}>
          {processing && <span className="w-1.5 h-1.5 bg-current rounded-full animate-pulse"></span>}
          {status}
        </span>
      </td>
      <td className="px-6 py-4 text-right font-bold text-slate-900 dark:text-white">{score}</td>
    </tr>
  );
}
