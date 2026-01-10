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
  ArrowRight,
  X,
  File as FileIcon,
  Loader2
} from 'lucide-react';
import Link from 'next/link';
import { motion, AnimatePresence } from "framer-motion";
import { ModeToggle } from "@/components/ModeToggle";
import { NotificationDropdown } from "@/components/NotificationDropdown";
import { useState, useEffect } from "react";
import { GradeWiseAPI } from "@/lib/api";
import { GradeDetailsModal } from "@/components/GradeDetailsModal";
import { InfoTooltip } from "@/components/InfoTooltip";

interface HistoryItem {
  id: string;
  date: string;
  studentName: string;
  studentId: string;
  subject: string;
  score: number;
  maxScore?: number;
}

export default function Dashboard() {
  const [recentActivity, setRecentActivity] = useState<HistoryItem[]>([]);
  const [mounted, setMounted] = useState(false);
  const [selectedActivity, setSelectedActivity] = useState<any>(null); // State for modal

  // Ingestion Modal State
  const [showIngestModal, setShowIngestModal] = useState(false);
  const [ingestFiles, setIngestFiles] = useState<File[]>([]);
  const [ingestStatus, setIngestStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
  const [ingestMessage, setIngestMessage] = useState('');

  // Rubric Import Modal State
  const [showRubricModal, setShowRubricModal] = useState(false);
  const [rubricFiles, setRubricFiles] = useState<File[]>([]);
  const [rubricStatus, setRubricStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
  const [rubricMessage, setRubricMessage] = useState('');

  const [savedMaterials, setSavedMaterials] = useState<string[]>([]);

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

    // Load saved materials
    const materials = localStorage.getItem('courseMaterials');
    if (materials) {
      try {
        setSavedMaterials(JSON.parse(materials));
      } catch (e) {
        console.error("Failed to parse course materials", e);
      }
    }
  }, []);

  const handleIngest = async () => {
    if (ingestFiles.length === 0) return;

    setIngestStatus('uploading');
    try {
      const result = await GradeWiseAPI.ingestFiles(ingestFiles);
      setIngestStatus('success');
      setIngestMessage(`Successfully processed ${result.files_processed} files.`);

      // Save file names to localStorage
      const fileNames = ingestFiles.map(f => f.name);
      localStorage.setItem('courseMaterials', JSON.stringify(fileNames));
      // Trigger local state update if I add one, or force reload/event
      // For now, I'll update a local state to show it immediately
      setSavedMaterials(fileNames);

      setTimeout(() => {
        setShowIngestModal(false);
        setIngestFiles([]);
        setIngestStatus('idle');
      }, 2000);
    } catch (error: any) {
      setIngestStatus('error');
      setIngestMessage(error.message || "Failed to upload files");
    }
  };

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setIngestFiles(Array.from(e.target.files));
    }
  };

  const handleRubricImport = async () => {
    if (rubricFiles.length === 0) return;

    setRubricStatus('uploading');
    try {
      const result = await GradeWiseAPI.parseRubric(rubricFiles);
      setRubricStatus('success');
      setRubricMessage(`Successfully parsed rubric with ${result.length} criteria.`);

      // Save to localStorage
      localStorage.setItem('importedRubric', JSON.stringify(result));

      setTimeout(() => {
        setShowRubricModal(false);
        setRubricFiles([]);
        setRubricStatus('idle');
      }, 2000);
    } catch (error: any) {
      setRubricStatus('error');
      setRubricMessage(error.message || "Failed to parse rubric");
    }
  };

  const onRubricFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setRubricFiles(Array.from(e.target.files));
    }
  };

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
              label={<span className="flex items-center gap-1">Avg. Grading Time <InfoTooltip content="Average time taken by the AI to grade one submission." /></span>}
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
                      desc="Upload PDF or Table"
                      onClick={() => setShowRubricModal(true)}
                    />
                    <ActionButton
                      icon={<FolderOpen className="w-5 h-5" />}
                      title="Course Materials"
                      desc="Manage resources"
                      onClick={() => setShowIngestModal(true)}
                    />
                  </div>

                  {savedMaterials.length > 0 && (
                    <div className="mt-6 pt-6 border-t border-slate-100 dark:border-slate-800">
                      <div className="flex justify-between items-center mb-2">
                        <h3 className="text-xs font-bold uppercase text-slate-500">Active Context</h3>
                        <button onClick={() => { localStorage.removeItem('courseMaterials'); setSavedMaterials([]) }} className="text-xs text-red-400 hover:text-red-500">Clear</button>
                      </div>
                      <div className="space-y-2">
                        {savedMaterials.map((name, i) => (
                          <div key={i} className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
                            <CheckCircle className="w-3 h-3 text-green-500" />
                            <span className="truncate">{name}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
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
                            score={item.maxScore ? `${item.score}/${item.maxScore}` : item.score + "%"}
                            onClick={() => setSelectedActivity({
                              ...item,
                              feedback: "Detailed feedback would be loaded here from the backend..."
                            })}
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


      {/* Ingestion Modal */}
      <AnimatePresence>
        {showIngestModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-white dark:bg-slate-900 w-full max-w-lg rounded-2xl shadow-xl overflow-hidden border border-slate-200 dark:border-slate-800"
            >
              <div className="p-6 border-b border-slate-100 dark:border-slate-800 flex justify-between items-center">
                <h3 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <FolderOpen className="w-5 h-5 text-blue-500" /> Upload Course Materials
                </h3>
                <button onClick={() => setShowIngestModal(false)} className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200">
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="p-6 space-y-4">
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  Upload PDF textbooks, lecture slides, or reading materials. The agent will use these to fact-check grading.
                </p>

                <div className="border-2 border-dashed border-slate-200 dark:border-slate-700 rounded-xl p-8 text-center hover:border-blue-500 transition-colors bg-slate-50/50 dark:bg-slate-800/30">
                  <input
                    type="file"
                    id="file-upload"
                    multiple
                    accept=".pdf,.docx,.txt"
                    className="hidden"
                    onChange={onFileChange}
                  />
                  <label htmlFor="file-upload" className="cursor-pointer flex flex-col items-center gap-3">
                    <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-full text-blue-600 dark:text-blue-400">
                      <Upload className="w-6 h-6" />
                    </div>
                    <div>
                      <span className="font-semibold text-primary hover:underline">Click to upload</span> or drag and drop
                    </div>
                    <span className="text-xs text-slate-400">PDF, DOCX, TXT (max 10MB)</span>
                  </label>
                </div>

                {/* File List */}
                {ingestFiles.length > 0 && (
                  <div className="space-y-2 max-h-40 overflow-y-auto">
                    {ingestFiles.map((file, idx) => (
                      <div key={idx} className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800 rounded-lg text-sm">
                        <div className="flex items-center gap-3 text-slate-700 dark:text-slate-300 truncate">
                          <FileIcon className="w-4 h-4 text-slate-400" />
                          <span className="truncate max-w-[200px]">{file.name}</span>
                        </div>
                        <span className="text-xs text-slate-400">{(file.size / 1024 / 1024).toFixed(2)} MB</span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Status Message */}
                {ingestStatus === 'success' && (
                  <div className="p-3 bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400 text-sm rounded-lg flex items-center gap-2">
                    <CheckCircle className="w-4 h-4" /> {ingestMessage}
                  </div>
                )}
                {ingestStatus === 'error' && (
                  <div className="p-3 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm rounded-lg flex items-center gap-2">
                    <CheckCircle className="w-4 h-4" /> {ingestMessage}
                  </div>
                )}
              </div>

              <div className="p-6 bg-slate-50 dark:bg-slate-800/50 border-t border-slate-100 dark:border-slate-800 flex justify-end gap-3">
                <button onClick={() => setShowIngestModal(false)} className="px-4 py-2 text-slate-600 dark:text-slate-300 font-medium hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors">
                  Cancel
                </button>
                <button
                  onClick={handleIngest}
                  disabled={ingestFiles.length === 0 || ingestStatus === 'uploading'}
                  className="px-4 py-2 bg-primary hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg font-medium shadow-lg shadow-blue-500/20 flex items-center gap-2"
                >
                  {ingestStatus === 'uploading' && <Loader2 className="w-4 h-4 animate-spin" />}
                  {ingestStatus === 'uploading' ? 'Processing...' : 'Ingest Materials'}
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Rubric Import Modal */}
      <AnimatePresence>
        {showRubricModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-white dark:bg-slate-900 w-full max-w-lg rounded-2xl shadow-xl overflow-hidden border border-slate-200 dark:border-slate-800"
            >
              <div className="p-6 border-b border-slate-100 dark:border-slate-800 flex justify-between items-center">
                <h3 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <Upload className="w-5 h-5 text-blue-500" /> Import Grading Rubric
                </h3>
                <button onClick={() => setShowRubricModal(false)} className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200">
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="p-6 space-y-4">
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  Upload your rubric (PDF, DOCX, TXT, CSV, or Excel). The system will auto-parse criteria and points.
                </p>

                <div className="border-2 border-dashed border-slate-200 dark:border-slate-700 rounded-xl p-8 text-center hover:border-blue-500 transition-colors bg-slate-50/50 dark:bg-slate-800/30">
                  <input
                    type="file"
                    id="rubric-upload"
                    accept=".pdf,.docx,.txt,.csv,.xlsx,.xls"
                    className="hidden"
                    onChange={onRubricFileChange}
                  />
                  <label htmlFor="rubric-upload" className="cursor-pointer flex flex-col items-center gap-3">
                    <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-full text-blue-600 dark:text-blue-400">
                      <Upload className="w-6 h-6" />
                    </div>
                    <div>
                      <span className="font-semibold text-primary hover:underline">Click to upload</span> or drag and drop
                    </div>
                    <span className="text-xs text-slate-400">Supports PDF, DOCX, TXT, CSV, Excel</span>
                  </label>
                </div>

                {/* File List */}
                {rubricFiles.length > 0 && (
                  <div className="space-y-2 max-h-40 overflow-y-auto">
                    {rubricFiles.map((file, idx) => (
                      <div key={idx} className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800 rounded-lg text-sm">
                        <div className="flex items-center gap-3 text-slate-700 dark:text-slate-300 truncate">
                          <FileIcon className="w-4 h-4 text-slate-400" />
                          <span className="truncate max-w-[200px]">{file.name}</span>
                        </div>
                        <span className="text-xs text-slate-400">{(file.size / 1024 / 1024).toFixed(2)} MB</span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Status Message */}
                {rubricStatus === 'success' && (
                  <div className="p-3 bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400 text-sm rounded-lg flex items-center gap-2">
                    <CheckCircle className="w-4 h-4" /> {rubricMessage}
                  </div>
                )}
                {rubricStatus === 'error' && (
                  <div className="p-3 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm rounded-lg flex items-center gap-2">
                    <CheckCircle className="w-4 h-4" /> {rubricMessage}
                  </div>
                )}
              </div>

              <div className="p-6 bg-slate-50 dark:bg-slate-800/50 border-t border-slate-100 dark:border-slate-800 flex justify-end gap-3">
                <button onClick={() => setShowRubricModal(false)} className="px-4 py-2 text-slate-600 dark:text-slate-300 font-medium hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors">
                  Cancel
                </button>
                <button
                  onClick={handleRubricImport}
                  disabled={rubricFiles.length === 0 || rubricStatus === 'uploading'}
                  className="px-4 py-2 bg-primary hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg font-medium shadow-lg shadow-blue-500/20 flex items-center gap-2"
                >
                  {rubricStatus === 'uploading' && <Loader2 className="w-4 h-4 animate-spin" />}
                  {rubricStatus === 'uploading' ? 'Scanning...' : 'Parse Rubric'}
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <GradeDetailsModal
        isOpen={!!selectedActivity}
        onClose={() => setSelectedActivity(null)}
        item={selectedActivity}
      />
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

function ActionButton({ icon, title, desc, onClick }: any) {
  return (
    <button onClick={onClick} className="w-full flex items-center gap-4 p-4 rounded-xl border border-slate-100 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/30 hover:bg-white dark:hover:bg-slate-800 hover:border-slate-200 dark:hover:border-slate-600 hover:shadow-md transition-all text-left group">
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

function TableRow({ initials, color, name, assignment, status, statusColor, score, processing, onClick }: any) {
  const statusConfig: Record<string, string> = {
    green: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
    amber: "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400",
    slate: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-400",
  };

  return (
    <tr onClick={onClick} className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors group cursor-pointer">
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
