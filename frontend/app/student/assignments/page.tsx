"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { FileText, CheckCircle, Loader2, MessageSquare, Sparkles, X, Send } from "lucide-react";
import ReactMarkdown from "react-markdown";
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

// Mock Feedback Chatbot Component (Reused)
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
            const { response } = await GradeWiseAPI.chatWithFeedback(userMsg, feedback);
            setMessages(prev => [...prev, { role: 'assistant', content: response }]);
        } catch (e) {
            console.error(e);
            setMessages(prev => [...prev, { role: 'assistant', content: "System Error: Unable to reach feedback agent." }]);
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

export default function AssignmentsPage() {
    const [submissions, setSubmissions] = useState<Submission[]>([]);
    const [activeFeedback, setActiveFeedback] = useState<Submission | null>(null);
    const [isChatOpen, setIsChatOpen] = useState(false);

    const studentId = "student-123"; // Retrieve from auth context in real app

    useEffect(() => {
        fetch(`/api/student/submissions?studentId=${studentId}`)
            .then(res => res.json())
            .then(data => setSubmissions(data))
            .catch(err => console.error(err));
    }, []);

    return (
        <div className="w-full max-w-[1920px] mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="mb-8">
                <h1 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-3">
                    <FileText className="w-8 h-8 text-indigo-500" />
                    My Assignments & History
                </h1>
                <p className="text-slate-500 dark:text-slate-400 mt-2">View your past submissions, grades, and AI feedback.</p>
            </div>

            <div className="grid gap-6">
                {submissions.length === 0 && (
                    <div className="text-center py-12 bg-white dark:bg-slate-900 rounded-3xl border border-dashed border-slate-300 dark:border-slate-700">
                        <p className="text-slate-500">No assignments submitted yet.</p>
                    </div>
                )}
                {submissions.map((sub) => (
                    <motion.div
                        key={sub.id}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className={`bg-white dark:bg-slate-900 rounded-3xl border p-6 shadow-sm transition-all ${activeFeedback?.id === sub.id
                            ? 'border-indigo-500 ring-1 ring-indigo-500/50'
                            : 'border-slate-200 dark:border-slate-800 hover:border-indigo-300'
                            }`}
                    >
                        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                            <div className="flex items-center gap-4">
                                <div className={`p-3 rounded-2xl ${sub.status === 'graded'
                                    ? 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600'
                                    : 'bg-slate-100 dark:bg-slate-800 text-slate-500'
                                    }`}>
                                    {sub.status === 'graded' ? <CheckCircle className="w-6 h-6" /> : <Loader2 className="w-6 h-6 animate-spin" />}
                                </div>
                                <div>
                                    <h3 className="text-lg font-bold text-slate-900 dark:text-white">{sub.title}</h3>
                                    <div className="flex items-center gap-3 text-sm text-slate-500 mt-1">
                                        <span>{sub.date}</span>
                                        {sub.fileName && <span className="bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded text-xs font-mono">{sub.fileName}</span>}
                                    </div>
                                </div>
                            </div>

                            {sub.status === 'graded' && (
                                <div className="flex items-center gap-6">
                                    <div className="text-right">
                                        <div className="text-3xl font-black text-slate-900 dark:text-white">{sub.grade}</div>
                                        <div className="text-[10px] font-bold uppercase text-emerald-500 tracking-wider">Final Grade</div>
                                    </div>
                                    <div className="flex gap-2">
                                        <button
                                            onClick={() => setActiveFeedback(activeFeedback?.id === sub.id ? null : sub)}
                                            className="px-4 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 font-medium text-sm transition-colors"
                                        >
                                            {activeFeedback?.id === sub.id ? "Hide Feedback" : "View Feedback"}
                                        </button>
                                        <button
                                            onClick={() => { setActiveFeedback(sub); setIsChatOpen(true); }}
                                            className="px-4 py-2 rounded-xl bg-indigo-600 text-white hover:bg-indigo-700 font-medium text-sm transition-colors flex items-center gap-2"
                                        >
                                            <MessageSquare className="w-4 h-4" /> Chat
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>

                        <AnimatePresence>
                            {activeFeedback?.id === sub.id && sub.feedback && (
                                <motion.div
                                    initial={{ opacity: 0, height: 0 }}
                                    animate={{ opacity: 1, height: 'auto' }}
                                    exit={{ opacity: 0, height: 0 }}
                                    className="mt-6 pt-6 border-t border-slate-100 dark:border-slate-800"
                                >
                                    <div className="prose prose-slate dark:prose-invert max-w-none">
                                        <ReactMarkdown>{sub.feedback}</ReactMarkdown>
                                    </div>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </motion.div>
                ))}
            </div>

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
