"use client";

import { useState, useRef, useEffect } from "react";
import { GradeWiseAPI, RubricItem, GradeResult } from "@/lib/api";
import {
    Upload, FileText, Plus, Trash2, ArrowRight, CheckCircle,
    AlertCircle, Sparkles, BookOpen, ChevronRight, Calculator
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { GradingLoader } from "@/components/GradingLoader"; // Import


export default function GradingPage() {
    // State: Submission
    const [studentName, setStudentName] = useState("John Doe");
    const [submissionText, setSubmissionText] = useState("");
    const [fileName, setFileName] = useState<string | null>(null);
    const [rubricLoaded, setRubricLoaded] = useState(false);

    // State: Rubric
    const [rubric, setRubric] = useState<RubricItem[]>([
        { criteria: "Clarity", max_points: 10, description: "Is the argument clear?" }
    ]);

    const [courseMaterials, setCourseMaterials] = useState<string[]>([]);

    useEffect(() => {
        const imported = localStorage.getItem('importedRubric');
        if (imported) {
            try {
                const parsed = JSON.parse(imported);
                if (Array.isArray(parsed) && parsed.length > 0) {
                    setRubric(parsed);
                    setRubricLoaded(true);
                }
            } catch (e) {
                console.error("Failed to load imported rubric", e);
            }
        }

        const materials = localStorage.getItem('courseMaterials');
        if (materials) {
            try {
                setCourseMaterials(JSON.parse(materials));
            } catch (e) {
                console.error("Failed to load course materials", e);
            }
        }
    }, []);

    // State: Grading
    const [isGrading, setIsGrading] = useState(false);
    const [result, setResult] = useState<GradeResult | null>(null);
    const [error, setError] = useState<string | null>(null);

    // State: Save Meta
    const [saveMeta, setSaveMeta] = useState({ studentName: "", studentId: "", subject: "English 101" });
    const [isSaved, setIsSaved] = useState(false);

    const handleSave = () => {
        const totalPoints = rubric.reduce((sum, item) => sum + item.max_points, 0);
        const historyItem = {
            id: Date.now().toString(),
            date: new Date().toISOString(),
            ...saveMeta,
            score: result?.score,
            maxScore: totalPoints,
            feedback: result?.feedback,
            citations: result?.citations
        };

        const existing = JSON.parse(localStorage.getItem('gradingHistory') || '[]');
        localStorage.setItem('gradingHistory', JSON.stringify([historyItem, ...existing]));

        setIsSaved(true);
        setTimeout(() => setResult(null), 1500); // Close after success
    };

    // Handlers
    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        setFileName(file.name);
        setSubmissionText("Extracting text..."); // Loading state

        try {
            const result = await GradeWiseAPI.extractText(file);
            setSubmissionText(result.text);
        } catch (err: any) {
            setSubmissionText("");
            setError(err.message || "Failed to extract text from file");
            setFileName(null);
        }
    };

    const handleRubricUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        // Optimistic UI update or loading state could go here
        try {
            const parsedRubric = await GradeWiseAPI.parseRubric([file]);
            if (parsedRubric && parsedRubric.length > 0) {
                setRubric(parsedRubric);
                setRubricLoaded(true);
            }
        } catch (err: any) {
            setError(err.message || "Failed to parse rubric file");
        }
    };

    const addRubricItem = () => {
        setRubric([...rubric, { criteria: "", max_points: 10, description: "" }]);
    };

    const updateRubricItem = (index: number, field: keyof RubricItem, value: string | number) => {
        const newRubric = [...rubric];
        newRubric[index] = { ...newRubric[index], [field]: value };
        setRubric(newRubric);
    };

    const removeRubricItem = (index: number) => {
        setRubric(rubric.filter((_, i) => i !== index));
    };

    const handleAutoFillRubric = () => {
        setRubric([
            { criteria: "Thesis Statement", max_points: 20, description: "Clear, arguable thesis present in intro." },
            { criteria: "Evidence", max_points: 30, description: "Claims supported by relevant text citations." },
            { criteria: "Analysis", max_points: 30, description: "Deep analysis of evidence, not just summary." },
            { criteria: "Grammar & Style", max_points: 20, description: "Professional tone, few errors." }
        ]);
    };

    // State: Grading Status
    const [gradingStatusIndex, setGradingStatusIndex] = useState(0);
    const GRADING_MESSAGES = [
        "Analyzing submission context...",
        "Analyzing submission context...",
        "Checking rubric criteria...",
        "Checking rubric criteria...",
        "Checking rubric criteria...",
        "Validating initial score...",
        "Validating initial score...",
        "Generating constructive feedback...",
        "Generating constructive feedback...",
        "Finalizing assessment..."
    ];

    const handleGrade = async () => {
        if (!submissionText) {
            setError("Please enter submission text first.");
            return;
        }
        setIsGrading(true);
        setError(null);
        setGradingStatusIndex(0);

        // Cycle status messages
        const intervalId = setInterval(() => {
            setGradingStatusIndex(prev => (prev + 1) % GRADING_MESSAGES.length);
        }, 3000);

        try {
            const data = await GradeWiseAPI.gradeSubmission(submissionText, "student-123", rubric);
            setResult(data);
        } catch (err: any) {
            setError(err.message || "Grading failed");
        } finally {
            clearInterval(intervalId);
            setIsGrading(false);
            setGradingStatusIndex(0);
        }
    };



    return (
        <div className="h-screen overflow-y-auto bg-slate-50 dark:bg-background p-8 transition-colors duration-300">
            {/* Same Header/Layout code... I will only replace the modal part mostly, but for replace_file I need context. 
               Actually, I'll rewrite the Modal section. */ }

            <div className="max-w-7xl mx-auto pb-20 space-y-8">
                {/* Header */}
                <header className="flex justify-between items-center">
                    <div>
                        <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Grading Interface</h1>
                        <p className="text-slate-500 dark:text-slate-400 mt-1">AI-powered assessment</p>
                    </div>
                </header>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 h-[calc(100vh-200px)] min-h-[600px]">
                    {rubricLoaded && (
                        <div className="lg:col-span-2 mb-4 p-4 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 rounded-xl flex items-center justify-between">
                            <span className="flex items-center gap-2"><CheckCircle className="w-5 h-5" /> Imported rubric loaded successfully.</span>
                            <button onClick={() => { localStorage.removeItem('importedRubric'); setRubricLoaded(false); }} className="text-sm underline hover:text-blue-800">Clear</button>
                        </div>
                    )}
                    {/* INPUT and RUBRIC sections remain same. I will assume they are unchanged if I use replace_file carefully. 
                        Wait, I must provide StartLine/EndLine. 
                        I'll use a large chunk replacement for the Modal logic.
                     */}
                    {/* For brevity in this tool call, I will include the unmodified lines in my thought process but in the tool call I must act on the Modal section. */}

                    {/* LEFT COLUMN: Input */}
                    <section className="flex flex-col gap-6">
                        {courseMaterials.length > 0 && (
                            <div className="flex justify-end">
                                <span className="text-xs font-medium text-slate-500 bg-white dark:bg-slate-800 px-3 py-1.5 rounded-full shadow-sm border border-slate-100 dark:border-slate-700 flex items-center gap-2">
                                    <BookOpen className="w-3 h-3 text-blue-500" />
                                    Context: {courseMaterials.join(", ")}
                                </span>
                            </div>
                        )}
                        {/* 1. Student Submission Card */}
                        <div className="flex-1 bg-white dark:bg-slate-900/50 backdrop-blur-sm border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm flex flex-col overflow-hidden">
                            <div className="p-4 border-b border-slate-100 dark:border-slate-800 flex justify-between items-center bg-slate-50/50 dark:bg-slate-900/50">
                                <h3 className="font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                                    <FileText className="w-4 h-4 text-blue-500" /> Student Submission
                                </h3>
                                <label className="cursor-pointer px-3 py-1.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-xs font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors flex items-center gap-2">
                                    <Upload className="w-3 h-3" />
                                    {fileName ? "Change File" : "Upload File"}
                                    <input type="file" className="hidden" accept=".txt,.pdf,.docx,.csv,.xlsx,.py,.js,.ts,.jsx,.tsx,.java,.cpp,.c,.h,.cs,.go,.rs,.php,.rb,.swift,.kt,.scala,.html,.css,.sql,.sh,.bat,.json,.xml,.yaml,.yml,.md" onChange={handleFileUpload} />
                                </label>
                            </div>
                            <div className="flex-1 p-0 relative">
                                <textarea
                                    className="w-full h-full p-4 resize-none bg-transparent outline-none text-slate-700 dark:text-slate-300 font-mono text-sm leading-relaxed"
                                    placeholder="Paste student text here or upload a file..."
                                    value={submissionText}
                                    onChange={(e) => setSubmissionText(e.target.value)}
                                ></textarea>
                                {!submissionText && !fileName && (
                                    <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                                        <div className="text-center text-slate-400">
                                            <Upload className="w-8 h-8 mx-auto mb-2 opacity-50" />
                                            <p className="text-sm">Drop file here (PDF, DOCX, Code, TXT)</p>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    </section>

                    {/* RIGHT COLUMN: Rubric ... SAME ... */}
                    <section className="flex flex-col gap-6">
                        <div className="flex-1 bg-white dark:bg-slate-900/50 backdrop-blur-sm border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm flex flex-col overflow-hidden">
                            <div className="p-4 border-b border-slate-100 dark:border-slate-800 flex justify-between items-center bg-slate-50/50 dark:bg-slate-900/50">
                                <h3 className="font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                                    <BookOpen className="w-4 h-4 text-indigo-500" /> Grading Rubric
                                </h3>
                                <div className="flex items-center gap-3">
                                    <label className="cursor-pointer text-xs text-slate-500 hover:text-indigo-600 font-medium transition-colors flex items-center gap-1">
                                        <Upload className="w-3 h-3" /> Upload
                                        <input type="file" className="hidden" accept=".txt,.pdf,.docx,.csv,.xlsx,.md" onChange={handleRubricUpload} />
                                    </label>
                                    <button className="text-xs text-primary font-medium hover:text-blue-600 transition-colors" onClick={handleAutoFillRubric}>Auto-fill</button>
                                </div>
                            </div>

                            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                                {rubric.map((item, index) => (
                                    <div key={index} className="p-4 rounded-xl border border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/30 group hover:border-blue-200 dark:hover:border-blue-800 transition-colors">
                                        <div className="flex gap-3 mb-2">
                                            <input type="text" placeholder="Criteria Name" className="flex-1 bg-transparent border-none p-0 font-semibold text-slate-900 dark:text-white placeholder-slate-400 focus:ring-0" value={item.criteria} onChange={(e) => updateRubricItem(index, 'criteria', e.target.value)} />
                                            <div className="flex items-center gap-1 bg-white dark:bg-slate-900 px-2 rounded border border-slate-200 dark:border-slate-700">
                                                <span className="text-xs text-slate-400">Pts</span>
                                                <input type="number" className="w-10 bg-transparent border-none p-0 text-right font-mono text-sm focus:ring-0" value={item.max_points} onChange={(e) => updateRubricItem(index, 'max_points', parseInt(e.target.value) || 0)} />
                                            </div>
                                            <button onClick={() => removeRubricItem(index)} className="text-slate-400 hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100"><Trash2 className="w-4 h-4" /></button>
                                        </div>
                                        <input type="text" placeholder="Description of criteria..." className="w-full bg-transparent border-none p-0 text-sm text-slate-500 dark:text-slate-400 placeholder-slate-400/50 focus:ring-0" value={item.description} onChange={(e) => updateRubricItem(index, 'description', e.target.value)} />
                                    </div>
                                ))}
                                <button onClick={addRubricItem} className="w-full py-3 border border-dashed border-slate-300 dark:border-slate-700 rounded-xl text-slate-500 dark:text-slate-400 hover:text-primary hover:border-primary/50 hover:bg-blue-50/50 dark:hover:bg-blue-900/10 transition-all flex items-center justify-center gap-2 text-sm font-medium"><Plus className="w-4 h-4" /> Add Criteria</button>
                            </div>

                            <div className="p-4 border-t border-slate-100 dark:border-slate-800 bg-white dark:bg-slate-900">
                                {error && <div className="mb-3 p-3 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm rounded-lg flex items-center gap-2"><AlertCircle className="w-4 h-4" /> {error}</div>}

                                <AnimatePresence mode="wait">
                                    {isGrading ? (
                                        <motion.div
                                            initial={{ opacity: 0, height: 0 }}
                                            animate={{ opacity: 1, height: "auto" }}
                                            exit={{ opacity: 0, height: 0 }}
                                            className="py-4"
                                        >
                                            <GradingLoader />
                                        </motion.div>
                                    ) : (
                                        <motion.button
                                            initial={{ opacity: 0 }}
                                            animate={{ opacity: 1 }}
                                            onClick={handleGrade}
                                            disabled={isGrading}
                                            className="w-full py-3 bg-slate-900 dark:bg-white text-white dark:text-slate-900 rounded-xl font-bold hover:shadow-lg transform active:scale-[0.98] transition-all flex items-center justify-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed"
                                        >
                                            <Sparkles className="w-4 h-4" /> Run Grading Agent
                                        </motion.button>
                                    )}
                                </AnimatePresence>
                            </div>
                        </div>
                    </section>
                </div>


                {/* RESULT MODAL - UPDATED */}
                <AnimatePresence>
                    {result && (
                        <motion.div
                            initial={{ opacity: 0, y: 100 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: 100 }}
                            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
                        >
                            <div className="bg-white dark:bg-slate-900 w-full max-w-3xl max-h-[90vh] overflow-y-auto rounded-3xl shadow-2xl relative">
                                <button
                                    onClick={() => setResult(null)}
                                    className="absolute top-4 right-4 p-2 rounded-full hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                                >
                                    <ArrowRight className="w-5 h-5 rotate-45" />
                                </button>

                                <div className="p-8">
                                    <div className="flex items-center gap-4 mb-6">
                                        <div className="p-4 bg-green-100 dark:bg-green-900/30 rounded-2xl">
                                            <Calculator className="w-8 h-8 text-green-600 dark:text-green-400" />
                                        </div>
                                        <div>
                                            <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Grading Complete</h2>
                                            <div className="flex items-center gap-2 mt-1">
                                                <p className="text-slate-500 text-sm">Calculated Score</p>
                                                {result.confidence_score && (
                                                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${result.confidence_score >= 0.9 ? 'bg-green-100 text-green-700 border-green-200 dark:bg-green-900/30 dark:text-green-400 dark:border-green-800' :
                                                        result.confidence_score >= 0.75 ? 'bg-yellow-100 text-yellow-700 border-yellow-200 dark:bg-yellow-900/30 dark:text-yellow-400 dark:border-yellow-800' :
                                                            'bg-red-100 text-red-700 border-red-200 dark:bg-red-900/30 dark:text-red-400 dark:border-red-800'
                                                        }`}>
                                                        {Math.round((result.confidence_score || 0) * 100)}% Confidence
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                        <div className="ml-auto text-right">
                                            <div className="text-4xl font-black text-slate-900 dark:text-white">
                                                {result.score} <span className="text-2xl text-slate-400">/ {rubric.reduce((sum, item) => sum + item.max_points, 0)}</span>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="space-y-6">
                                        {/* Agent Thinking Process Log */}
                                        {result.thinking_process && result.thinking_process.length > 0 && (
                                            <div className="bg-slate-50 dark:bg-slate-800/50 rounded-xl border border-slate-100 dark:border-slate-800 overflow-hidden">
                                                <details className="group">
                                                    <summary className="flex items-center justify-between p-4 cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors">
                                                        <div className="flex items-center gap-2 font-semibold text-sm text-slate-700 dark:text-slate-300">
                                                            <Sparkles className="w-4 h-4 text-purple-500" />
                                                            Agent Thinking Process
                                                        </div>
                                                        <ChevronRight className="w-4 h-4 text-slate-400 group-open:rotate-90 transition-transform" />
                                                    </summary>
                                                    <div className="px-4 pb-4 border-t border-slate-100 dark:border-slate-800 bg-white dark:bg-slate-900/50">
                                                        <div className="mt-3 space-y-2">
                                                            {result.thinking_process.map((log, i) => (
                                                                <div key={i} className="flex items-start gap-2 text-xs font-mono text-slate-600 dark:text-slate-400">
                                                                    <span className="text-slate-300 select-none">{(i + 1).toString().padStart(2, '0')}</span>
                                                                    <span>{log}</span>
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </div>
                                                </details>
                                            </div>
                                        )}

                                        <div className="bg-slate-50 dark:bg-slate-800/50 p-6 rounded-2xl border border-slate-100 dark:border-slate-800">
                                            <h3 className="font-bold text-slate-900 dark:text-white mb-3">Feedback</h3>
                                            <p className="text-slate-700 dark:text-slate-300 leading-relaxed whitespace-pre-wrap">
                                                {result.feedback}
                                            </p>
                                        </div>
                                    </div>

                                    {/* Save Grade Details Form */}
                                    <div className="mt-8 pt-8 border-t border-slate-100 dark:border-slate-800">
                                        <h3 className="font-bold text-slate-900 dark:text-white mb-4">Save to History</h3>
                                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                            <div>
                                                <label className="text-xs font-semibold text-slate-500 uppercase">Student Name</label>
                                                <input
                                                    type="text"
                                                    placeholder="e.g. John Doe"
                                                    className="w-full mt-1 px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white focus:ring-2 focus:ring-primary/20 outline-none"
                                                    value={saveMeta.studentName}
                                                    onChange={e => setSaveMeta({ ...saveMeta, studentName: e.target.value })}
                                                />
                                            </div>
                                            <div>
                                                <label className="text-xs font-semibold text-slate-500 uppercase">Student ID</label>
                                                <input
                                                    type="text"
                                                    placeholder="e.g. S-10234"
                                                    className="w-full mt-1 px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white focus:ring-2 focus:ring-primary/20 outline-none"
                                                    value={saveMeta.studentId}
                                                    onChange={e => setSaveMeta({ ...saveMeta, studentId: e.target.value })}
                                                />
                                            </div>
                                            <div>
                                                <label className="text-xs font-semibold text-slate-500 uppercase">Subject</label>
                                                <input
                                                    type="text"
                                                    placeholder="e.g. History 101"
                                                    className="w-full mt-1 px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white focus:ring-2 focus:ring-primary/20 outline-none"
                                                    value={saveMeta.subject}
                                                    onChange={e => setSaveMeta({ ...saveMeta, subject: e.target.value })}
                                                />
                                            </div>
                                        </div>

                                        <div className="mt-6 flex justify-end gap-3">
                                            <button onClick={() => setResult(null)} className="px-6 py-2.5 border border-slate-200 dark:border-slate-700 rounded-xl font-medium hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors">
                                                Cancel
                                            </button>
                                            <button
                                                onClick={handleSave}
                                                disabled={isSaved || !saveMeta.studentName}
                                                className={`px-6 py-2.5 text-white rounded-xl font-medium shadow-lg transition-all flex items-center gap-2 ${isSaved ? 'bg-green-500 hover:bg-green-600' : 'bg-primary hover:bg-blue-600'}`}
                                            >
                                                {isSaved ? <><CheckCircle className="w-5 h-5" /> Saved!</> : "Save Grade Record"}
                                            </button>
                                        </div>
                                    </div>

                                </div>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </div>
    );
}
