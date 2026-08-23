"use client";

import { useState, useEffect } from "react";
import { GradeWiseAPI, RubricItem, GradeResult, FewShotScore, friendlyApiError } from "@/lib/api";
import { Upload, Loader2, CheckCircle, AlertTriangle, Swords, Eye, FileText, Trash2 } from "lucide-react";
import { PdfTip } from "@/components/PdfTip";
import { motion } from "framer-motion";
import GradeBreakdown, { sectionOf } from "@/components/GradeBreakdown";
import { planBusinessName } from "@/lib/planName";

type SectionMap = Record<string, { awarded: number; max: number }>;

function bySection(items: { criteria: string; awarded: number; max_points: number }[]): SectionMap {
    const m: SectionMap = {};
    for (const it of items) {
        const s = sectionOf(it.criteria);
        (m[s] ||= { awarded: 0, max: 0 });
        m[s].awarded += it.awarded;
        m[s].max += it.max_points;
    }
    return m;
}

export default function BpcHeadToHeadPage() {
    const [rubric, setRubric] = useState<RubricItem[]>([]);
    const [guideline, setGuideline] = useState("");
    const [planTotal, setPlanTotal] = useState(0);
    const [refs, setRefs] = useState<FewShotScore[]>([]);
    const [rubricError, setRubricError] = useState<string | null>(null);

    const [file, setFile] = useState<File | null>(null);
    const [content, setContent] = useState("");
    const [extracting, setExtracting] = useState(false);
    const [vision, setVision] = useState(false);
    const [isGrading, setIsGrading] = useState(false);
    const [result, setResult] = useState<GradeResult | null>(null);
    const [gradedName, setGradedName] = useState("");
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        GradeWiseAPI.getBpcRubric()
            .then((d) => { setRubric(d.plan); setGuideline(d.guideline || ""); setPlanTotal(d.plan_total); })
            .catch((e) => setRubricError(friendlyApiError(e, "Could not load the BYUMS rubric.")));
        GradeWiseAPI.getFewShotScores().then(setRefs).catch(() => setRefs([]));
    }, []);

    const upload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const f = e.target.files?.[0];
        if (!f) return;
        setFile(f);
        setResult(null);
        setError(null);
        setContent("");          // clear stale text before re-extracting (avoid wrong-plan grade)
        setExtracting(true);
        try {
            const ex = await GradeWiseAPI.extractFilesContent([f]);
            setContent(ex[0]?.content || "");
        } catch {
            setContent("");
        } finally {
            setExtracting(false);
        }
        e.target.value = "";
    };

    const grade = async () => {
        if (!file) { setError("Upload a plan PDF first."); return; }
        if (rubric.length === 0) { setError("Rubric not loaded yet."); return; }
        setIsGrading(true); setError(null); setResult(null);
        try {
            const data = vision
                ? await GradeWiseAPI.gradeVision(file, file.name, rubric, guideline)
                : await GradeWiseAPI.gradeSubmission([{ filename: file.name, content }], file.name, rubric, { guideline, skip_rag: true, max_retries: 1 });
            setResult(data);
            setGradedName(file.name);
        } catch (e: any) {
            setError(e?.response?.data?.detail || e?.message || "Grading failed.");
        } finally {
            setIsGrading(false);
        }
    };

    const ref = refs.find((r) => r.filename === gradedName) || null;
    const aiSections = result ? bySection((result.assessments || []).map((a) => ({ criteria: a.criteria_name, awarded: a.awarded_points, max_points: a.max_points }))) : {};
    const humanSections = ref ? bySection(ref.items) : {};
    const allSections = Array.from(new Set([...Object.keys(aiSections), ...Object.keys(humanSections)]));

    return (
        <div className="h-screen overflow-y-auto bg-slate-50 dark:bg-background p-6 md:p-8 transition-colors">
            <div className="max-w-5xl mx-auto pb-20 space-y-6">
                <header className="flex flex-wrap justify-between items-start gap-4">
                    <div>
                        <h1 className="text-3xl font-bold text-slate-900 dark:text-white flex items-center gap-3">
                            <Swords className="w-7 h-7 text-emerald-600" /> AI vs Human — Head-to-Head
                        </h1>
                        <p className="text-slate-500 dark:text-slate-400 mt-1">
                            Grade a plan the judges already scored, and compare section by section.
                        </p>
                    </div>
                    {rubric.length > 0 ? (
                        <span className="text-xs font-medium text-emerald-700 dark:text-emerald-300 bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800 px-3 py-1.5 rounded-full flex items-center gap-2">
                            <CheckCircle className="w-3.5 h-3.5" /> {rubric.length} criteria / {planTotal} pts · {refs.length} human-scored reference{refs.length === 1 ? "" : "s"}
                        </span>
                    ) : rubricError ? <span className="text-xs text-red-600">{rubricError}</span>
                        : <span className="text-xs text-slate-400 flex items-center gap-2"><Loader2 className="w-3.5 h-3.5 animate-spin" /> loading…</span>}
                </header>

                <div className="bg-white dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm p-5 space-y-4">
                    <div className="flex flex-wrap items-center gap-3">
                        <label className="cursor-pointer px-3 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors flex items-center gap-2">
                            <Upload className="w-4 h-4" /> Upload a scored plan (PDF, PPTX, DOCX)
                            <input type="file" className="hidden" accept=".pdf,.pptx,.docx,.txt" onChange={upload} />
                        </label>
                        {file && (
                            <span className="inline-flex items-center gap-2 text-sm bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800 rounded-lg px-2.5 py-1.5">
                                <FileText className="w-4 h-4 text-emerald-600" /><span className="max-w-[280px] truncate">{file.name}</span>
                                <button onClick={() => { setFile(null); setResult(null); }} className="text-slate-400 hover:text-red-500"><Trash2 className="w-3.5 h-3.5" /></button>
                            </span>
                        )}
                        {refs.length > 0 && (
                            <span className="text-xs text-slate-400">reference on file: {refs.map((r) => r.filename).join(", ").slice(0, 60)}</span>
                        )}
                    </div>

                    <PdfTip />
                    <label className="flex items-start gap-2 text-sm text-slate-600 dark:text-slate-300 cursor-pointer select-none">
                        <input type="checkbox" checked={vision} onChange={(e) => setVision(e.target.checked)} className="mt-0.5 rounded accent-emerald-600" />
                        <span className="flex items-center gap-1.5"><Eye className="w-4 h-4 text-emerald-600" /><span><b>Vision mode</b> — read slide images with Gemini.</span></span>
                    </label>
                    {error && <div className="p-3 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm rounded-lg flex items-center gap-2"><AlertTriangle className="w-4 h-4" /> {error}</div>}
                    <button onClick={grade} disabled={isGrading || !file || rubric.length === 0 || extracting || (!vision && !content.trim())}
                        className="w-full py-3 bg-emerald-600 text-white rounded-xl font-bold hover:bg-emerald-700 active:scale-[0.99] transition-all flex items-center justify-center gap-2 disabled:opacity-60 disabled:cursor-not-allowed">
                        {isGrading ? <><Loader2 className="w-4 h-4 animate-spin" /> Grading…</>
                            : extracting ? <><Loader2 className="w-4 h-4 animate-spin" /> Reading PDF…</>
                                : <><Swords className="w-4 h-4" /> Grade & Compare</>}
                    </button>
                </div>

                {result && (
                    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-5">
                        {/* Totals */}
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                            <div className="bg-white dark:bg-slate-900/50 border border-emerald-200 dark:border-emerald-800 rounded-2xl shadow-sm p-6 text-center">
                                <p className="text-sm text-slate-500">AI (GradeWise)</p>
                                <div className="text-4xl font-black text-emerald-600 dark:text-emerald-400 mt-1">{result.score}<span className="text-2xl text-slate-400">/{planTotal}</span></div>
                            </div>
                            <div className="bg-white dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm p-6 text-center">
                                <p className="text-sm text-slate-500">Human judge</p>
                                {ref ? (
                                    <div className="text-4xl font-black text-slate-700 dark:text-slate-200 mt-1">{ref.human_total}<span className="text-2xl text-slate-400">/{planTotal}</span></div>
                                ) : (
                                    <div className="text-sm text-slate-400 mt-3">No human reference for this plan.<br />Upload one of: {refs.map((r) => r.filename).join(", ") || "—"}</div>
                                )}
                            </div>
                        </div>

                        {ref && (
                            <div className="bg-white dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm overflow-hidden">
                                <div className="p-4 border-b border-slate-100 dark:border-slate-800 font-semibold text-slate-900 dark:text-white flex items-center justify-between">
                                    <span>Section by section</span>
                                    <span className="text-sm font-normal text-slate-500">AI vs Human · gap {Math.abs(result.score - ref.human_total).toFixed(1)} pts</span>
                                </div>
                                <div className="divide-y divide-slate-100 dark:divide-slate-800">
                                    {allSections.map((s) => {
                                        const ai = aiSections[s] || { awarded: 0, max: 0 };
                                        const hu = humanSections[s] || { awarded: 0, max: 0 };
                                        const delta = ai.awarded - hu.awarded;
                                        return (
                                            <div key={s} className="p-3 flex items-center gap-4 text-sm">
                                                <span className="flex-1 min-w-0 truncate text-slate-700 dark:text-slate-300">{s}</span>
                                                <span className="w-20 text-right font-mono text-emerald-600 dark:text-emerald-400">{ai.awarded}/{ai.max}</span>
                                                <span className="w-20 text-right font-mono text-slate-500">{hu.awarded}/{hu.max}</span>
                                                <span className={`w-14 text-right font-mono ${delta > 0 ? "text-amber-600" : delta < 0 ? "text-blue-500" : "text-slate-400"}`}>
                                                    {delta > 0 ? "+" : ""}{delta.toFixed(1)}
                                                </span>
                                            </div>
                                        );
                                    })}
                                    <div className="p-3 flex items-center gap-4 text-sm font-bold bg-slate-50 dark:bg-slate-800/40">
                                        <span className="flex-1">Total</span>
                                        <span className="w-20 text-right font-mono text-emerald-600 dark:text-emerald-400">{result.score}/{planTotal}</span>
                                        <span className="w-20 text-right font-mono text-slate-600 dark:text-slate-300">{ref.human_total}/{planTotal}</span>
                                        <span className="w-14 text-right font-mono text-slate-400">{(result.score - ref.human_total > 0 ? "+" : "")}{(result.score - ref.human_total).toFixed(1)}</span>
                                    </div>
                                </div>
                                <div className="px-4 py-2 text-xs text-slate-400 flex gap-4">
                                    <span><span className="text-emerald-600 dark:text-emerald-400 font-mono">AI</span></span>
                                    <span><span className="text-slate-500 font-mono">Human</span></span>
                                    <span><span className="text-amber-600 font-mono">+</span> AI higher · <span className="text-blue-500 font-mono">−</span> AI lower</span>
                                </div>
                            </div>
                        )}

                        {/* AI detail */}
                        <div className="bg-white dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm p-6">
                            <h3 className="font-bold text-slate-900 dark:text-white mb-3">AI grade detail</h3>
                            <GradeBreakdown result={result} businessName={planBusinessName(ref?.business_name, result.business_name, gradedName)} />
                        </div>
                    </motion.div>
                )}
            </div>
        </div>
    );
}
