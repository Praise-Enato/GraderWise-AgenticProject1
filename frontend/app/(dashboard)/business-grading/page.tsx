"use client";

import { useState, useEffect } from "react";
import { GradeWiseAPI, RubricItem, GradeResult } from "@/lib/api";
import {
    Upload, FileText, Plus, Trash2, ArrowRight, CheckCircle,
    AlertCircle, Sparkles, BookOpen, ChevronRight, Calculator, Loader2,
    Presentation, FileCheck, Briefcase
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { GradingLoader } from "@/components/GradingLoader";
import ReactMarkdown from 'react-markdown';

// PPTX metadata after extraction
interface PPTXMeta {
    filename: string;
    markdown_content: string;
    slide_count: number;
    has_tables: boolean;
    has_images: boolean;
    text_length: number;
}

const BUSINESS_TYPES = [
    { key: "startup", label: "Startup", desc: "Seed/Series A pitch deck" },
    { key: "enterprise", label: "Enterprise", desc: "Strategic business plan" },
    { key: "nonprofit", label: "Nonprofit", desc: "Grant proposal / social enterprise" },
    { key: "general", label: "General", desc: "Universal business plan" },
] as const;

type BusinessType = typeof BUSINESS_TYPES[number]["key"];

export default function BusinessGradingPage() {
    // --- Submission state ---
    const [pptxMeta, setPptxMeta] = useState<PPTXMeta | null>(null);
    const [pptxFile, setPptxFile] = useState<File | null>(null);
    const [isExtractingPptx, setIsExtractingPptx] = useState(false);

    const [documentFiles, setDocumentFiles] = useState<{ filename: string; content: string }[]>([]);
    const [docRawFiles, setDocRawFiles] = useState<File[]>([]);
    const [isExtractingDocs, setIsExtractingDocs] = useState(false);

    // --- Config state ---
    const [businessType, setBusinessType] = useState<BusinessType>("startup");
    const [rubric, setRubric] = useState<RubricItem[]>([]);
    const [rubricLoaded, setRubricLoaded] = useState(false);

    // --- Grading state ---
    const [isGrading, setIsGrading] = useState(false);
    const [result, setResult] = useState<GradeResult | null>(null);
    const [error, setError] = useState<string | null>(null);

    // --- Save state ---
    const [saveMeta, setSaveMeta] = useState({ teamName: "", teamId: "", course: "Business Plan" });
    const [isSaved, setIsSaved] = useState(false);

    // Load rubric template when business type changes
    useEffect(() => {
        const loadTemplate = async () => {
            try {
                const template = await GradeWiseAPI.getBusinessRubricTemplate(businessType);
                setRubric(template);
                setRubricLoaded(true);
            } catch (err) {
                console.error("Failed to load rubric template", err);
            }
        };
        loadTemplate();
    }, [businessType]);

    // Load imported rubric from localStorage (if user uploaded via Dashboard)
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
    }, []);

    // --- Handlers ---

    const handlePptxUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        setIsExtractingPptx(true);
        setError(null);
        try {
            const meta = await GradeWiseAPI.extractPPTX(file);
            setPptxMeta({ filename: file.name, ...meta });
            setPptxFile(file);
        } catch (err: any) {
            setError(err?.response?.data?.detail || err.message || "Failed to extract PPTX");
        } finally {
            setIsExtractingPptx(false);
            e.target.value = '';
        }
    };

    const handleDocUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const files = e.target.files;
        if (!files || files.length === 0) return;

        setIsExtractingDocs(true);
        setError(null);
        try {
            const fileArray = Array.from(files);
            const extracted = await GradeWiseAPI.extractFilesContent(fileArray);
            setDocumentFiles(prev => [...prev, ...extracted]);
            setDocRawFiles(prev => [...prev, ...fileArray]);
        } catch (err: any) {
            setError(err?.response?.data?.detail || err.message || "Failed to extract documents");
        } finally {
            setIsExtractingDocs(false);
            e.target.value = '';
        }
    };

    const removePptx = () => {
        setPptxMeta(null);
        setPptxFile(null);
    };

    const removeDoc = (index: number) => {
        setDocumentFiles(prev => prev.filter((_, i) => i !== index));
        setDocRawFiles(prev => prev.filter((_, i) => i !== index));
    };

    const handleRubricUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;
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

    const handleGrade = async () => {
        if (!pptxFile && documentFiles.length === 0) {
            setError("Please upload at least a pitch deck (PPTX) or a business plan document.");
            return;
        }
        if (rubric.length === 0) {
            setError("Rubric is empty. Select a business type or add criteria manually.");
            return;
        }

        setIsGrading(true);
        setError(null);

        try {
            const pptxArr = pptxFile ? [pptxFile] : [];
            const data = await GradeWiseAPI.gradeBusinessPlan(
                pptxArr,
                docRawFiles,
                rubric,
                saveMeta.teamId || "team-001",
                businessType
            );
            setResult(data);
        } catch (err: any) {
            setError(err?.response?.data?.detail || err.message || "Grading failed");
        } finally {
            setIsGrading(false);
        }
    };

    const handleSave = async () => {
        if (!result) return;
        try {
            const totalPoints = rubric.reduce((sum, item) => sum + item.max_points, 0);

            // Step 1: Create a new submission entry
            const createRes = await fetch('/api/submissions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    title: saveMeta.teamName || "Business Plan",
                    fileName: pptxMeta?.filename || documentFiles[0]?.filename || "business_plan",
                    student_id: saveMeta.teamId || "team-001",
                    subject: saveMeta.course || "Business Plan",
                })
            });
            if (!createRes.ok) throw new Error("Failed to create submission entry");
            const submissionData = await createRes.json();

            // Step 2: Update it with the grade
            const gradeRes = await fetch('/api/grade', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    id: submissionData.id,
                    manualGrade: {
                        score: `${result.score} / ${totalPoints}`,
                        feedback: result.feedback,
                        thinkingProcess: result.thinking_process
                    }
                })
            });
            if (!gradeRes.ok) throw new Error("Failed to save grade");

            setIsSaved(true);
            setTimeout(() => {
                setResult(null);
                window.location.href = '/submissions';
            }, 1000);
        } catch (e) {
            console.error("Failed to save grade", e);
            setError("Failed to save grade. Please try again.");
        }
    };

    const totalPoints = rubric.reduce((sum, item) => sum + item.max_points, 0);

    return (
        <div className="h-screen overflow-y-auto bg-slate-50 dark:bg-background p-8 transition-colors duration-300">
            <div className="max-w-7xl mx-auto pb-20 space-y-8">
                {/* Header */}
                <header className="flex justify-between items-center">
                    <div>
                        <h1 className="text-3xl font-bold text-slate-900 dark:text-white flex items-center gap-3">
                            <Briefcase className="w-8 h-8 text-emerald-600" />
                            Business Plan Grading
                        </h1>
                        <p className="text-slate-500 dark:text-slate-400 mt-1">AI-powered business plan & pitch deck assessment</p>
                    </div>
                </header>

                {/* Business Type Selector */}
                <div className="flex gap-3">
                    {BUSINESS_TYPES.map((bt) => (
                        <button
                            key={bt.key}
                            onClick={() => setBusinessType(bt.key)}
                            className={`flex-1 p-4 rounded-xl border-2 transition-all text-left ${
                                businessType === bt.key
                                    ? "border-emerald-500 bg-emerald-50 dark:bg-emerald-900/20 shadow-sm"
                                    : "border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900/50 hover:border-slate-300 dark:hover:border-slate-600"
                            }`}
                        >
                            <div className={`text-sm font-bold ${businessType === bt.key ? "text-emerald-700 dark:text-emerald-400" : "text-slate-700 dark:text-slate-300"}`}>
                                {bt.label}
                            </div>
                            <div className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">{bt.desc}</div>
                        </button>
                    ))}
                </div>

                {rubricLoaded && (
                    <div className="p-4 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 rounded-xl flex items-center justify-between">
                        <span className="flex items-center gap-2"><CheckCircle className="w-5 h-5" /> Rubric loaded for {businessType} ({rubric.length} criteria, {totalPoints} pts)</span>
                        <button onClick={() => { localStorage.removeItem('importedRubric'); setRubricLoaded(false); }} className="text-sm underline hover:text-blue-800">Reset</button>
                    </div>
                )}

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 min-h-[600px]">
                    {/* LEFT COLUMN: Submissions */}
                    <section className="flex flex-col gap-6">
                        {/* Pitch Deck (PPTX) Card */}
                        <div className="bg-white dark:bg-slate-900/50 backdrop-blur-sm border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm flex flex-col overflow-hidden">
                            <div className="p-4 border-b border-slate-100 dark:border-slate-800 flex justify-between items-center bg-slate-50/50 dark:bg-slate-900/50">
                                <h3 className="font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                                    <Presentation className="w-4 h-4 text-orange-500" /> Pitch Deck (PPTX)
                                </h3>
                                <label className="cursor-pointer px-3 py-1.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-xs font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors flex items-center gap-2">
                                    {isExtractingPptx ? <Loader2 className="w-3 h-3 animate-spin" /> : <Upload className="w-3 h-3" />}
                                    Upload PPTX
                                    <input type="file" className="hidden" accept=".pptx" onChange={handlePptxUpload} />
                                </label>
                            </div>
                            <div className="p-4 min-h-[140px] flex items-center justify-center">
                                {pptxMeta ? (
                                    <div className="w-full flex items-center justify-between p-3 bg-orange-50 dark:bg-orange-900/10 rounded-xl border border-orange-100 dark:border-orange-900/30 group">
                                        <div className="flex items-center gap-3">
                                            <div className="p-2 bg-white dark:bg-slate-800 rounded-lg border border-orange-200 dark:border-orange-800 text-orange-500">
                                                <Presentation className="w-4 h-4" />
                                            </div>
                                            <div>
                                                <div className="text-sm font-medium text-slate-900 dark:text-white truncate max-w-[200px]">{pptxMeta.filename}</div>
                                                <div className="flex items-center gap-2 mt-1">
                                                    <span className="text-xs bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 px-2 py-0.5 rounded-full text-slate-600 dark:text-slate-400">{pptxMeta.slide_count} slides</span>
                                                    {pptxMeta.has_tables && <span className="text-xs bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 px-2 py-0.5 rounded-full">Tables</span>}
                                                    {pptxMeta.has_images && <span className="text-xs bg-purple-50 dark:bg-purple-900/20 text-purple-600 dark:text-purple-400 px-2 py-0.5 rounded-full">Images</span>}
                                                    <span className="text-xs text-slate-400">{pptxMeta.text_length.toLocaleString()} chars</span>
                                                </div>
                                            </div>
                                        </div>
                                        <button onClick={removePptx} className="p-2 text-slate-400 hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100">
                                            <Trash2 className="w-4 h-4" />
                                        </button>
                                    </div>
                                ) : (
                                    <div className="text-center text-slate-400">
                                        <Presentation className="w-8 h-8 mx-auto mb-2 opacity-50" />
                                        <p className="text-sm">Upload your pitch deck (.pptx)</p>
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Business Plan Document Card */}
                        <div className="flex-1 bg-white dark:bg-slate-900/50 backdrop-blur-sm border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm flex flex-col overflow-hidden">
                            <div className="p-4 border-b border-slate-100 dark:border-slate-800 flex justify-between items-center bg-slate-50/50 dark:bg-slate-900/50">
                                <h3 className="font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                                    <FileCheck className="w-4 h-4 text-blue-500" /> Business Plan Report
                                </h3>
                                <label className="cursor-pointer px-3 py-1.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-xs font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors flex items-center gap-2">
                                    {isExtractingDocs ? <Loader2 className="w-3 h-3 animate-spin" /> : <Upload className="w-3 h-3" />}
                                    Add Files
                                    <input type="file" className="hidden" multiple accept=".pdf,.docx,.txt" onChange={handleDocUpload} />
                                </label>
                            </div>
                            <div className="flex-1 p-0 relative flex flex-col min-h-[200px]">
                                {documentFiles.length > 0 ? (
                                    <div className="flex-1 overflow-y-auto p-4 space-y-3">
                                        {documentFiles.map((file, index) => (
                                            <div key={index} className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800/50 rounded-xl border border-slate-100 dark:border-slate-800 group">
                                                <div className="flex items-center gap-3">
                                                    <div className="p-2 bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 text-blue-500">
                                                        <FileText className="w-4 h-4" />
                                                    </div>
                                                    <div>
                                                        <div className="text-sm font-medium text-slate-900 dark:text-white truncate max-w-[200px]">{file.filename}</div>
                                                        <div className="text-xs text-slate-500">{file.content.length.toLocaleString()} chars</div>
                                                    </div>
                                                </div>
                                                <button onClick={() => removeDoc(index)} className="p-2 text-slate-400 hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100">
                                                    <Trash2 className="w-4 h-4" />
                                                </button>
                                            </div>
                                        ))}
                                    </div>
                                ) : (
                                    <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                                        <div className="text-center text-slate-400">
                                            <FileCheck className="w-8 h-8 mx-auto mb-2 opacity-50" />
                                            <p className="text-sm">Upload business plan report<br />(PDF, DOCX, or TXT)</p>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    </section>

                    {/* RIGHT COLUMN: Rubric & Grade Button */}
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
                                    <span className="text-xs text-slate-400 font-mono">{totalPoints} pts</span>
                                </div>
                            </div>

                            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                                {rubric.map((item, index) => (
                                    <div key={index} className="p-4 rounded-xl border border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/30 group hover:border-emerald-200 dark:hover:border-emerald-800 transition-colors">
                                        <div className="flex gap-3 mb-2">
                                            <input type="text" placeholder="Criteria Name" className="flex-1 bg-transparent border-none p-0 font-semibold text-slate-900 dark:text-white placeholder-slate-400 focus:ring-0" value={item.criteria} onChange={(e) => updateRubricItem(index, 'criteria', e.target.value)} />
                                            <div className="flex items-center gap-1 bg-white dark:bg-slate-900 px-2 rounded border border-slate-200 dark:border-slate-700">
                                                <span className="text-xs text-slate-400">Pts</span>
                                                <input
                                                    type="number"
                                                    step="0.1"
                                                    className="w-10 bg-transparent border-none p-0 text-right font-mono text-sm focus:ring-0"
                                                    value={item.max_points}
                                                    onChange={(e) => updateRubricItem(index, 'max_points', parseFloat(e.target.value) || 0)}
                                                />
                                            </div>
                                            <button onClick={() => removeRubricItem(index)} className="text-slate-400 hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100"><Trash2 className="w-4 h-4" /></button>
                                        </div>
                                        <input type="text" placeholder="Description of criteria..." className="w-full bg-transparent border-none p-0 text-sm text-slate-500 dark:text-slate-400 placeholder-slate-400/50 focus:ring-0" value={item.description} onChange={(e) => updateRubricItem(index, 'description', e.target.value)} />
                                    </div>
                                ))}
                                <button onClick={addRubricItem} className="w-full py-3 border border-dashed border-slate-300 dark:border-slate-700 rounded-xl text-slate-500 dark:text-slate-400 hover:text-emerald-600 hover:border-emerald-400/50 hover:bg-emerald-50/50 dark:hover:bg-emerald-900/10 transition-all flex items-center justify-center gap-2 text-sm font-medium"><Plus className="w-4 h-4" /> Add Criteria</button>
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
                                            className="w-full py-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-bold hover:shadow-lg transform active:scale-[0.98] transition-all flex items-center justify-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed"
                                        >
                                            <Sparkles className="w-4 h-4" /> Grade Business Plan
                                        </motion.button>
                                    )}
                                </AnimatePresence>
                            </div>
                        </div>
                    </section>
                </div>

                {/* RESULT MODAL */}
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
                                        <div className="p-4 bg-emerald-100 dark:bg-emerald-900/30 rounded-2xl">
                                            <Calculator className="w-8 h-8 text-emerald-600 dark:text-emerald-400" />
                                        </div>
                                        <div>
                                            <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Business Plan Assessment</h2>
                                            <div className="flex items-center gap-2 mt-1">
                                                <p className="text-slate-500 text-sm capitalize">{businessType} Plan</p>
                                                {result.confidence_score != null && (
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
                                                {result.score} <span className="text-2xl text-slate-400">/ {totalPoints}</span>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="space-y-6">
                                        {/* Agent Thinking Process */}
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

                                        {/* Feedback */}
                                        <div className="bg-slate-50 dark:bg-slate-800/50 p-6 rounded-2xl border border-slate-100 dark:border-slate-800">
                                            <h3 className="font-bold text-slate-900 dark:text-white mb-3">Investor-Style Feedback</h3>
                                            <div className="text-slate-700 dark:text-slate-300 leading-relaxed text-sm">
                                                <ReactMarkdown components={{
                                                    p: ({ node, ...props }) => <p className="mb-4 leading-loose" {...props} />,
                                                    h1: ({ node, ...props }) => <h1 className="text-xl font-bold mt-6 mb-3 text-slate-900 dark:text-white" {...props} />,
                                                    h2: ({ node, ...props }) => <h2 className="text-lg font-bold mt-5 mb-2 text-slate-900 dark:text-white" {...props} />,
                                                    h3: ({ node, ...props }) => <h3 className="text-base font-bold mt-4 mb-2 text-slate-900 dark:text-white" {...props} />,
                                                    ul: ({ node, ...props }) => <ul className="list-disc pl-5 mb-4 space-y-2" {...props} />,
                                                    ol: ({ node, ...props }) => <ol className="list-decimal pl-5 mb-4 space-y-2" {...props} />,
                                                    li: ({ node, ...props }) => <li className="pl-1" {...props} />,
                                                    strong: ({ node, ...props }) => <strong className="font-semibold text-slate-900 dark:text-white" {...props} />,
                                                }}>
                                                    {result.feedback}
                                                </ReactMarkdown>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Save to History */}
                                    <div className="mt-8 pt-8 border-t border-slate-100 dark:border-slate-800">
                                        <h3 className="font-bold text-slate-900 dark:text-white mb-4">Save to History</h3>
                                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                            <div>
                                                <label className="text-xs font-semibold text-slate-500 uppercase">Team / Student Name</label>
                                                <input
                                                    type="text"
                                                    placeholder="e.g. Team Alpha"
                                                    className="w-full mt-1 px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white focus:ring-2 focus:ring-emerald-500/20 outline-none"
                                                    value={saveMeta.teamName}
                                                    onChange={e => setSaveMeta({ ...saveMeta, teamName: e.target.value })}
                                                />
                                            </div>
                                            <div>
                                                <label className="text-xs font-semibold text-slate-500 uppercase">Team / Student ID</label>
                                                <input
                                                    type="text"
                                                    placeholder="e.g. T-001"
                                                    className="w-full mt-1 px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white focus:ring-2 focus:ring-emerald-500/20 outline-none"
                                                    value={saveMeta.teamId}
                                                    onChange={e => setSaveMeta({ ...saveMeta, teamId: e.target.value })}
                                                />
                                            </div>
                                            <div>
                                                <label className="text-xs font-semibold text-slate-500 uppercase">Course</label>
                                                <input
                                                    type="text"
                                                    placeholder="e.g. Entrepreneurship 101"
                                                    className="w-full mt-1 px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white focus:ring-2 focus:ring-emerald-500/20 outline-none"
                                                    value={saveMeta.course}
                                                    onChange={e => setSaveMeta({ ...saveMeta, course: e.target.value })}
                                                />
                                            </div>
                                        </div>

                                        <div className="mt-6 flex justify-end gap-3">
                                            <button onClick={() => setResult(null)} className="px-6 py-2.5 border border-slate-200 dark:border-slate-700 rounded-xl font-medium hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors">
                                                Cancel
                                            </button>
                                            <button
                                                onClick={handleSave}
                                                disabled={isSaved || !saveMeta.teamName}
                                                className={`px-6 py-2.5 text-white rounded-xl font-medium shadow-lg transition-all flex items-center gap-2 ${isSaved ? 'bg-green-500 hover:bg-green-600' : 'bg-emerald-600 hover:bg-emerald-700'}`}
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
