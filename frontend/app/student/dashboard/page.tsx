"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { UploadCloud, FileText, CheckCircle, Brain, Sparkles, MessageSquare, X, Send, Loader2, Copy, User } from "lucide-react";
import { InfoTooltip } from "@/components/InfoTooltip";
import ReactMarkdown from "react-markdown";
import { GradingLoader } from "@/components/GradingLoader";
import { GradeWiseAPI } from "@/lib/api";

type Submission = {
    id: string;
    title: string;
    status: 'pending' | 'graded';
    grade?: string;
    feedback?: string;
    date: string;
    fileName?: string;
};

// Mock Feedback Chatbot Component
function FeedbackChatbot({ feedback, onClose }: { feedback: string; onClose: () => void }) {
    const [messages, setMessages] = useState<{ role: 'user' | 'assistant', content: string }[]>([
        { role: 'assistant', content: "Hi! I'm your feedback assistant. Ask me anything about your grade or how to improve based on the feedback you received." }
    ]);
    const [input, setInput] = useState("");
    const [isThinking, setIsThinking] = useState(false);
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }, [messages]);

    const handleSend = async () => {
        if (!input.trim()) return;
        const userMsg = input;
        setInput("");
        setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
        setIsThinking(true);

        try {
            // Call Real RAG Agent
            // Note: We might not have the full submission text here unless stored. 
            // For now, we pass empty string or rely on feedback context.
            // Ideally, we fetch the text using the submission ID if stored.
            const { response } = await GradeWiseAPI.chatWithFeedback(userMsg, feedback);

            setMessages(prev => [...prev, { role: 'assistant', content: response }]);
        } catch (e) {
            console.error(e);
            setMessages(prev => [...prev, { role: 'assistant', content: "I'm having trouble connecting to the Knowledge Base right now." }]);
        } finally {
            setIsThinking(false);
        }
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            className="fixed bottom-8 right-8 w-96 h-[500px] bg-white dark:bg-slate-900 rounded-2xl shadow-2xl border border-indigo-200 dark:border-indigo-900 flex flex-col z-50 overflow-hidden"
        >
            <div className="p-4 bg-gradient-to-r from-indigo-600 to-violet-600 flex items-center justify-between text-white">
                <div className="flex items-center gap-2">
                    <Sparkles className="w-5 h-5" />
                    <span className="font-bold">Feedback Coach</span>
                </div>
                <button onClick={onClose} className="p-1 hover:bg-white/20 rounded-lg transition-colors">
                    <X className="w-5 h-5" />
                </button>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-4" ref={scrollRef}>
                {messages.map((m, i) => (
                    <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-[80%] p-3 rounded-2xl text-sm ${m.role === 'user'
                            ? 'bg-indigo-600 text-white rounded-br-none'
                            : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 rounded-bl-none'
                            }`}>
                            {m.content}
                        </div>
                    </div>
                ))}
                {isThinking && (
                    <div className="flex justify-start">
                        <div className="bg-slate-100 dark:bg-slate-800 p-3 rounded-2xl rounded-bl-none">
                            <Loader2 className="w-4 h-4 animate-spin text-indigo-500" />
                        </div>
                    </div>
                )}
            </div>

            <div className="p-4 border-t border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/50">
                <div className="flex gap-2">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                        placeholder="Ask about your feedback..."
                        className="flex-1 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-2 text-sm outline-none focus:border-indigo-500"
                    />
                    <button onClick={handleSend} className="p-2 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition-colors">
                        <Send className="w-4 h-4" />
                    </button>
                </div>
            </div>
        </motion.div>
    );
}

// Mock user for demo isolation
const MOCK_USER = { studentId: "student-123" };

export default function StudentDashboard() {
    const [activeTab, setActiveTab] = useState<'upload' | 'paste'>('upload');
    const [dragActive, setDragActive] = useState(false);
    const [submissions, setSubmissions] = useState<Submission[]>([]);
    const [activeFeedback, setActiveFeedback] = useState<Submission | null>(null);
    const [isChatOpen, setIsChatOpen] = useState(false);
    const [loading, setLoading] = useState(true);
    const [isProcessing, setIsProcessing] = useState(false); // For grading animation

    // Fetch initial data filtered by user
    useEffect(() => {
        fetch(`/api/student/submissions?studentId=${MOCK_USER.studentId}`)
            .then(res => res.json())
            .then(data => {
                setSubmissions(data);
                setLoading(false);
            })
            .catch(err => console.error("Failed to load submissions", err));
    }, [MOCK_USER.studentId]);

    const handleDrag = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === "dragenter" || e.type === "dragover") {
            setDragActive(true);
        } else if (e.type === "dragleave") {
            setDragActive(false);
        }
    };

    const handleDrop = async (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            const file = e.dataTransfer.files[0];
            await handleFileUpload(file);
        }
    };

    const handleFileUpload = async (file: File) => {
        // 1. Upload File
        const formData = new FormData();
        formData.append('file', file);

        try {
            await fetch('/api/student/upload', { method: 'POST', body: formData });

            // 2. Create Submission (Pending)
            const res = await fetch('/api/student/submissions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title: file.name, fileName: file.name })
            });
            const newSub = await res.json();
            setSubmissions(prev => [newSub, ...prev]);

            // 3. Trigger Gradient Agent (Animation)
            setIsProcessing(true);

            // Simulate processing time then update grade
            setTimeout(async () => {
                const gradeRes = await fetch('/api/student/grade', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ id: newSub.id })
                });
                const gradedSub = await gradeRes.json();

                setSubmissions(prev => prev.map(s => s.id === gradedSub.id ? gradedSub : s));
                setIsProcessing(false);
            }, 5000); // 5 seconds of animation

        } catch (e) {
            console.error(e);
            setIsProcessing(false);
        }
    };

    const addSubmission = async (name: string) => {
        // Only for text input mock currently
        const res = await fetch('/api/student/submissions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title: "Text Submission", fileName: "essay.txt" })
        });
        const newSub = await res.json();
        setSubmissions(prev => [newSub, ...prev]);
    };

    return (
        <div className="w-full max-w-[1920px] mx-auto px-4 sm:px-6 lg:px-8 transition-all duration-300">
            <div className="grid lg:grid-cols-2 gap-8">

                {/* 1. Submission Container */}
                <motion.div
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.1 }}
                    className="bg-white dark:bg-slate-900/80 backdrop-blur-xl rounded-3xl border border-slate-200 dark:border-white/10 shadow-2xl overflow-hidden flex flex-col h-[600px]"
                >
                    <div className="p-6 border-b border-slate-100 dark:border-white/5 bg-slate-50/50 dark:bg-slate-900/50 flex items-center justify-between">
                        <div>
                            <h2 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
                                <UploadCloud className="w-5 h-5 text-indigo-500" />
                                New Submission
                            </h2>
                            <p className="text-sm text-slate-500 dark:text-slate-400">Upload your work for instant AI analysis.</p>
                        </div>
                        <div className="flex bg-slate-200 dark:bg-slate-800 p-1 rounded-xl">
                            <button
                                onClick={() => setActiveTab('upload')}
                                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${activeTab === 'upload' ? 'bg-white dark:bg-slate-700 shadow-sm text-indigo-600 dark:text-indigo-400' : 'text-slate-500'}`}
                            >
                                File Upload
                            </button>
                            <button
                                onClick={() => setActiveTab('paste')}
                                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${activeTab === 'paste' ? 'bg-white dark:bg-slate-700 shadow-sm text-indigo-600 dark:text-indigo-400' : 'text-slate-500'}`}
                            >
                                Text Input
                            </button>
                        </div>
                    </div>

                    <div className="flex-1 p-6 flex flex-col relative">
                        <AnimatePresence>
                            {isProcessing && (
                                <motion.div
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    exit={{ opacity: 0 }}
                                    className="absolute inset-0 z-10 bg-white/90 dark:bg-slate-900/90 backdrop-blur-sm flex items-center justify-center rounded-b-3xl"
                                >
                                    <GradingLoader />
                                </motion.div>
                            )}
                        </AnimatePresence>
                        {activeTab === 'upload' ? (
                            <div
                                className={`flex-1 border-3 border-dashed rounded-2xl transition-all flex flex-col items-center justify-center text-center p-8 group cursor-pointer ${dragActive ? "border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20 scale-[0.99]" : "border-slate-200 dark:border-slate-700 hover:border-indigo-400 dark:hover:border-indigo-600 hover:bg-slate-50 dark:hover:bg-slate-800/50"
                                    }`}
                                onDragEnter={handleDrag}
                                onDragLeave={handleDrag}
                                onDragOver={handleDrag}
                                onDrop={handleDrop}
                            >
                                <div className="w-20 h-20 rounded-full bg-indigo-50 dark:bg-slate-800 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform shadow-lg shadow-indigo-500/10">
                                    <FileText className="w-10 h-10 text-indigo-500 dark:text-indigo-400" />
                                </div>
                                <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-2">Drag & Drop Assignment</h3>
                                <p className="text-slate-500 dark:text-slate-400 text-sm max-w-xs mb-6">Support for PDF, DOCX, TXT. <br />Max file size 10MB.</p>
                                <button className="px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold shadow-lg shadow-indigo-500/20 transition-all">
                                    Browse Files
                                </button>
                            </div>
                        ) : (
                            <div className="flex-1 flex flex-col">
                                <textarea
                                    className="flex-1 w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-4 text-sm resize-none outline-none focus:border-indigo-500 transition-colors dark:text-slate-200"
                                    placeholder="Paste your essay or assignment text here..."
                                />
                                <button className="mt-4 w-full py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-xl shadow-lg shadow-indigo-500/20 transition-all flex items-center justify-center gap-2">
                                    <Send className="w-4 h-4" /> Submit Text
                                </button>
                            </div>
                        )}
                    </div>
                </motion.div>

                {/* 2. Feedback Container */}
                <motion.div
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.2 }}
                    className="bg-white dark:bg-slate-900/80 backdrop-blur-xl rounded-3xl border border-slate-200 dark:border-white/10 shadow-2xl overflow-hidden flex flex-col h-[600px]"
                >
                    <div className="p-6 border-b border-slate-100 dark:border-white/5 bg-slate-50/50 dark:bg-slate-900/50">
                        <h2 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
                            <Brain className="w-5 h-5 text-emerald-500" />
                            Results & Feedback
                        </h2>
                        <p className="text-sm text-slate-500 dark:text-slate-400">View your grades and ask the AI for clarifications.</p>
                    </div>

                    <div className="flex-1 overflow-y-auto p-6 space-y-4">
                        {submissions.map((sub, i) => (
                            <motion.div
                                key={sub.id}
                                layout
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                className={`border rounded-2xl p-5 transition-all ${activeFeedback?.id === sub.id ? 'border-indigo-500 ring-2 ring-indigo-500/10 bg-indigo-50/50 dark:bg-indigo-900/10' : 'border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-800 hover:border-indigo-300 dark:hover:border-indigo-700'
                                    }`}
                            >
                                <div className="flex items-start justify-between mb-4">
                                    <div className="flex items-center gap-3">
                                        <div className={`p-2 rounded-lg ${sub.status === 'graded' ? 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600' : 'bg-slate-100 dark:bg-slate-700 text-slate-500'}`}>
                                            {sub.status === 'graded' ? <CheckCircle className="w-5 h-5" /> : <Loader2 className="w-5 h-5 animate-spin" />}
                                        </div>
                                        <div>
                                            <h3 className="font-bold text-slate-900 dark:text-white">{sub.title}</h3>
                                            <div className="text-xs text-slate-500 flex items-center gap-2">
                                                <span>{sub.date}</span>
                                                {sub.fileName && <span className="px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-700 font-mono text-[10px]">{sub.fileName}</span>}
                                            </div>
                                        </div>
                                    </div>
                                    {sub.status === 'graded' && (
                                        <div className="flex flex-col items-end">
                                            <span className="text-2xl font-black text-slate-900 dark:text-white">{sub.grade}</span>
                                            <span className="text-[10px] font-bold uppercase text-emerald-500 tracking-wider">Graded</span>
                                        </div>
                                    )}
                                </div>

                                {sub.status === 'graded' && sub.feedback && (
                                    <div className="mt-4 pt-4 border-t border-slate-100 dark:border-slate-700/50">
                                        <p className="text-sm text-slate-600 dark:text-slate-300 line-clamp-2 mb-3 leading-relaxed">
                                            {sub.feedback}
                                        </p>
                                        <div className="flex gap-2">
                                            <button
                                                onClick={() => {
                                                    setActiveFeedback(activeFeedback?.id === sub.id ? null : sub);
                                                }}
                                                className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 flex items-center gap-1"
                                            >
                                                {activeFeedback?.id === sub.id ? "Hide Feedback" : "Read Full Feedback"}
                                            </button>
                                            <button
                                                onClick={() => {
                                                    setActiveFeedback(sub);
                                                    setIsChatOpen(true);
                                                }}
                                                className="text-xs font-semibold px-2 py-1 rounded bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 hover:bg-indigo-100 dark:hover:bg-indigo-900/50 flex items-center gap-1 ml-auto"
                                            >
                                                <MessageSquare className="w-3 h-3" /> Discuss with AI
                                            </button>
                                        </div>
                                    </div>
                                )}

                                <AnimatePresence>
                                    {activeFeedback?.id === sub.id && (
                                        <motion.div
                                            initial={{ opacity: 0, height: 0 }}
                                            animate={{ opacity: 1, height: 'auto' }}
                                            exit={{ opacity: 0, height: 0 }}
                                            className="mt-4 p-4 bg-slate-50 dark:bg-slate-900/50 rounded-xl text-sm text-slate-700 dark:text-slate-300 leading-relaxed border border-slate-100 dark:border-slate-800"
                                        >
                                            <div className="prose prose-sm dark:prose-invert">
                                                <ReactMarkdown>
                                                    {sub.feedback || ""}
                                                </ReactMarkdown>
                                            </div>
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                            </motion.div>
                        ))}
                    </div>
                </motion.div>
            </div>

            {/* AI Chatbot Overlay */}
            <AnimatePresence>
                {isChatOpen && activeFeedback && (
                    <FeedbackChatbot
                        feedback={activeFeedback.feedback || ""}
                        onClose={() => setIsChatOpen(false)}
                    />
                )}
            </AnimatePresence>

        </div>
    );
}
