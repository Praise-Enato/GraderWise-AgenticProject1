"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Layers, Play, CheckCircle, AlertCircle, Loader2, FileText, Upload, RefreshCw, BookOpen } from "lucide-react";
import { GradeWiseAPI, RubricItem } from "@/lib/api";

export default function MassGradingPage() {
    const [pendingCount, setPendingCount] = useState(0);
    const [isGrading, setIsGrading] = useState(false);
    const [progress, setProgress] = useState(0);
    const [logs, setLogs] = useState<string[]>([]);
    const [complete, setComplete] = useState(false);
    const [activeRubric, setActiveRubric] = useState<RubricItem[]>([]);
    const [courseMaterials, setCourseMaterials] = useState<string[]>([]);
    const [isUploading, setIsUploading] = useState(false);
    const [isUploadingContext, setIsUploadingContext] = useState(false);
    const [isUploadingRubric, setIsUploadingRubric] = useState(false);

    useEffect(() => {
        fetchStats();
        loadRubric();
        loadCourseMaterials();
    }, []);

    const loadRubric = () => {
        const stored = localStorage.getItem('importedRubric');
        if (stored) {
            try {
                const parsed = JSON.parse(stored);
                if (Array.isArray(parsed)) setActiveRubric(parsed);
            } catch (e) {
                console.error("Failed to load rubric", e);
            }
        }
    };

    const loadCourseMaterials = () => {
        const stored = localStorage.getItem('courseMaterials');
        if (stored) {
            try {
                const parsed = JSON.parse(stored);
                if (Array.isArray(parsed)) setCourseMaterials(parsed);
            } catch (e) {
                console.error("Failed to load course materials", e);
            }
        }
    };

    const fetchStats = async () => {
        try {
            const res = await fetch('/api/submissions');
            if (res.ok) {
                const data = await res.json();
                const pending = data.filter((s: any) => s.status === 'pending');
                setPendingCount(pending.length);
            }
        } catch (e) {
            console.error("Failed to fetch stats", e);
        }
    };

    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        if (!e.target.files?.length) return;
        
        setIsUploading(true);
        setLogs(prev => [...prev, `Uploading ${e.target.files?.length} files...`]);
        
        try {
            const files = Array.from(e.target.files);
            let uploadedCount = 0;
    
            for (const file of files) {
                try {
                    // 1. Extract text using the shared API
                    const { text } = await GradeWiseAPI.extractText(file);
                    
                    // 2. Create submission via internal API
                    await fetch('/api/submissions', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            title: file.name,
                            fileName: file.name,
                            content: text // Send extracted text to backend
                        })
                    });
                    uploadedCount++;
                    setLogs(prev => [...prev, `Uploaded: ${file.name}`]);
                } catch (err) {
                     console.error(err);
                     setLogs(prev => [...prev, `Failed to upload ${file.name}`]);
                }
            }
            
            setLogs(prev => [...prev, `Upload complete. ${uploadedCount} new submissions ready.`]);
            await fetchStats();
        } catch (globalError) {
             console.error("Critical upload error related to generic crash", globalError);
             setLogs(prev => [...prev, "Upload process crashed unexpectedly."]);
        } finally {
            setIsUploading(false);
            // Reset input
            e.target.value = "";
        }
    };

    const handleMassGrade = async () => {
        setIsGrading(true);
        setLogs(prev => [...prev, "Initializing Mass Grading protocols..."]);
        setProgress(10);

        try {
            setLogs(prev => [...prev, `Found ${pendingCount} pending submissions. Sending to AI Agent...`]);
            setProgress(30);

            const res = await fetch('/api/educator/mass-grade', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ rubric: activeRubric })
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
            console.error(e);
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
                        <div className="w-24 h-24 rounded-full bg-indigo-50 dark:bg-indigo-900/20 flex items-center justify-center mb-6 relative">
                            <FileText className="w-10 h-10 text-indigo-500" />
                            {isUploading && (
                                <div className="absolute inset-0 rounded-full border-4 border-indigo-500 border-t-transparent animate-spin" />
                            )}
                        </div>
                        <h2 className="text-4xl font-black text-slate-900 dark:text-white mb-2">{pendingCount}</h2>
                        <p className="text-slate-500 font-medium uppercase tracking-wider text-sm">Pending Submissions</p>

                        <div className="flex flex-col w-full gap-3 mt-8">
                            <label className={`w-full py-3 rounded-2xl font-bold text-sm flex items-center justify-center gap-2 transition-all cursor-pointer border border-dashed border-indigo-200 dark:border-indigo-800 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 text-indigo-600 ${isGrading ? 'opacity-50 pointer-events-none' : ''}`}>
                                <Upload className="w-4 h-4" />
                                {isUploading ? "Uploading..." : "Upload New Submissions"}
                                <input 
                                    type="file" 
                                    multiple 
                                    className="hidden" 
                                    accept=".txt,.pdf,.docx,.md"
                                    onChange={handleFileUpload}
                                    disabled={isUploading || isGrading}
                                />
                            </label>

                            <button
                                onClick={handleMassGrade}
                                disabled={pendingCount === 0 || isGrading || isUploading}
                                className={`w-full py-4 rounded-2xl font-bold text-lg flex items-center justify-center gap-3 transition-all ${pendingCount === 0
                                        ? 'bg-slate-100 dark:bg-slate-800 text-slate-400 cursor-not-allowed'
                                        : isGrading
                                            ? 'bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600'
                                            : 'bg-indigo-600 hover:bg-indigo-700 text-white shadow-xl shadow-indigo-500/20 hover:scale-[1.02]'
                                    }`}
                            >
                                {isGrading ? <Loader2 className="w-6 h-6 animate-spin" /> : <Play className="w-6 h-6 fill-current" />}
                                {isGrading ? "Gradewise is working..." : "Run Mass Grading"}
                            </button>
                        </div>
                    </div>

                    {/* Terminal / Log */}
                    <div className="bg-slate-900 rounded-3xl p-6 font-mono text-sm text-slate-300 overflow-hidden flex flex-col h-[450px]">
                        <div className="flex items-center gap-2 mb-4 text-slate-500 border-b border-white/10 pb-4">
                            <div className="w-3 h-3 rounded-full bg-red-500" />
                            <div className="w-3 h-3 rounded-full bg-yellow-500" />
                            <div className="w-3 h-3 rounded-full bg-green-500" />
                            <span className="ml-2 text-xs">agent_logs.log</span>
                        </div>
                        <div className="flex-1 overflow-y-auto space-y-2 scrollbar-thin scrollbar-thumb-slate-700">
                            {logs.length === 0 && <span className="text-slate-600 italic">// Ready to process...</span>}
                            {logs.map((log, i) => (
                                <motion.div
                                    key={i}
                                    initial={{ opacity: 0, x: -10 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    className="border-l-2 border-indigo-500 pl-3 py-1 break-words"
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

                {/* Configuration Section (Uploads) */}
                <div className="grid md:grid-cols-2 gap-8">
                    {/* Course Material Upload */}
                    <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800">
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="font-bold text-slate-900 dark:text-white flex items-center gap-2">
                                <BookOpen className="w-5 h-5 text-blue-500" /> Upload Course Context
                            </h3>
                        </div>
                        <div className="space-y-4">
                            <label className={`flex flex-col items-center justify-center w-full h-32 border-2 border-dashed rounded-xl cursor-pointer transition-colors ${isUploadingContext ? 'border-slate-200 bg-slate-50' : 'border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 hover:bg-slate-100 dark:hover:bg-slate-800'}`}>
                                {isUploadingContext ? (
                                     <div className="flex flex-col items-center justify-center">
                                        <Loader2 className="w-8 h-8 mb-2 text-blue-500 animate-spin" />
                                        <p className="text-sm text-slate-400">Ingesting material...</p>
                                     </div>
                                ) : (
                                    <div className="flex flex-col items-center justify-center pt-5 pb-6">
                                        <Upload className="w-8 h-8 mb-3 text-slate-400" />
                                        <p className="text-sm text-slate-500 dark:text-slate-400"><span className="font-semibold">Click to upload</span> PDF/DOCX</p>
                                    </div>
                                )}
                                <input type="file" className="hidden" multiple accept=".pdf,.docx,.txt" onChange={async (e) => {
                                    if (!e.target.files?.length) return;
                                    setIsUploadingContext(true);
                                    const formData = new FormData();
                                    Array.from(e.target.files).forEach(f => formData.append('files', f));
                                    try {
                                        const res = await fetch('http://127.0.0.1:8000/ingest', { method: 'POST', body: formData });
                                        if (res.ok) {
                                            const names = Array.from(e.target.files).map(f => f.name);
                                            setCourseMaterials(names);
                                            localStorage.setItem('courseMaterials', JSON.stringify(names));
                                            setLogs(prev => [...prev, `Ingested ${names.length} course materials.`]);
                                        }
                                    } catch (err) {
                                        console.error(err);
                                        setLogs(prev => [...prev, "Failed to upload course materials."]);
                                    } finally {
                                        setIsUploadingContext(false);
                                        e.target.value = ""; 
                                    }
                                }} disabled={isUploadingContext} />
                            </label>
                            {courseMaterials.length > 0 && (
                                <div className="flex flex-wrap gap-2">
                                    {courseMaterials.map((m, i) => (
                                        <span key={i} className="text-xs px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded">
                                            {m}
                                        </span>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Rubric Upload */}
                    <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800">
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="font-bold text-slate-900 dark:text-white flex items-center gap-2">
                                <CheckCircle className="w-5 h-5 text-indigo-500" /> Upload Grading Rubric
                            </h3>
                        </div>
                         <div className="space-y-4">
                            <label className={`flex flex-col items-center justify-center w-full h-32 border-2 border-dashed rounded-xl cursor-pointer transition-colors ${isUploadingRubric ? 'border-slate-200 bg-slate-50' : 'border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 hover:bg-slate-100 dark:hover:bg-slate-800'}`}>
                               {isUploadingRubric ? (
                                     <div className="flex flex-col items-center justify-center">
                                        <Loader2 className="w-8 h-8 mb-2 text-indigo-500 animate-spin" />
                                        <p className="text-sm text-slate-400">Parsing rubric...</p>
                                     </div>
                                ) : (
                                    <div className="flex flex-col items-center justify-center pt-5 pb-6">
                                        <Upload className="w-8 h-8 mb-3 text-slate-400" />
                                        <p className="text-sm text-slate-500 dark:text-slate-400"><span className="font-semibold">Click to upload</span> CSV/XLSX/PDF</p>
                                    </div>
                                )}
                                <input type="file" className="hidden" multiple accept=".csv,.xlsx,.pdf,.docx" onChange={async (e) => {
                                    if (!e.target.files?.length) return;
                                    setIsUploadingRubric(true);
                                    const formData = new FormData();
                                    Array.from(e.target.files).forEach(f => formData.append('files', f));
                                    try {
                                        const res = await fetch('http://127.0.0.1:8000/parse-rubric', { method: 'POST', body: formData });
                                        if (res.ok) {
                                            const rubric = await res.json();
                                            setActiveRubric(rubric);
                                            localStorage.setItem('importedRubric', JSON.stringify(rubric));
                                            setLogs(prev => [...prev, `Parsed rubric with ${rubric.length} criteria.`]);
                                        }
                                    } catch (err) {
                                        console.error(err);
                                        setLogs(prev => [...prev, "Failed to parse rubric."]);
                                    } finally {
                                        setIsUploadingRubric(false);
                                        e.target.value = "";
                                    }
                                }} disabled={isUploadingRubric} />
                            </label>
                        </div>
                    </div>
                </div>

                {/* Rubric Preview (Detailed) */}
                <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800">
                    <div className="flex justify-between items-center mb-4">
                        <h3 className="font-bold text-slate-900 dark:text-white">Active Global Rubric Configuration</h3>
                         <button onClick={loadRubric} className="text-xs text-indigo-500 hover:text-indigo-600 flex items-center gap-1">
                            <RefreshCw className="w-3 h-3" /> Sync
                        </button>
                    </div>
                    
                    {activeRubric.length > 0 ? (
                        <div className="space-y-4">
                            {activeRubric.map((c, i) => (
                                <div key={i} className="p-4 bg-slate-50 dark:bg-slate-800/50 rounded-xl border border-slate-100 dark:border-slate-700">
                                    <div className="flex justify-between items-start mb-2">
                                        <span className="font-bold text-slate-800 dark:text-slate-200">{c.criteria}</span>
                                        <span className="text-sm font-mono font-bold bg-indigo-100 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300 px-2 py-0.5 rounded">{c.max_points} pts</span>
                                    </div>
                                    <p className="text-sm text-slate-600 dark:text-slate-400 mb-3">{c.description}</p>
                                    
                                    {(c.developing_description || c.developing_points) && (
                                         <div className="mt-2 text-xs text-slate-500 border-t border-slate-200 dark:border-slate-700 pt-2 grid grid-cols-2 gap-4">
                                            <div>
                                                <span className="font-semibold block mb-1">Developing ({c.developing_points}pts)</span>
                                                {c.developing_description}
                                            </div>
                                             <div>
                                                <span className="font-semibold block mb-1">Zero ({c.zero_points}pts)</span>
                                                {c.zero_description || "Not present"}
                                            </div>
                                         </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="text-center py-8 text-slate-400 bg-slate-50 dark:bg-slate-800/50 rounded-xl border border-dashed border-slate-200 dark:border-slate-700">
                           <AlertCircle className="w-6 h-6 mx-auto mb-2 opacity-50" />
                           <p>No active rubric configured.</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
