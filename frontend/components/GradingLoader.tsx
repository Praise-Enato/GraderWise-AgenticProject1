
"use client";

import { motion, AnimatePresence } from "framer-motion";
import { useState, useEffect } from "react";
import { Search, PenTool, Scale, RefreshCw, CheckCircle, Brain } from "lucide-react";

const LOADING_PHASES = [
    {
        id: "analyze",
        text: "Analyzing Structure...",
        subtext: "DeepSeek V3 is reading the student's submission.",
        icon: Search,
        color: "text-blue-500",
        bg: "bg-blue-100 dark:bg-blue-900/30"
    },
    {
        id: "context",
        text: "Retrieving Context...",
        subtext: "Fetching relevant knowledge from RAG vector db.",
        icon: Brain,
        color: "text-purple-500",
        bg: "bg-purple-100 dark:bg-purple-900/30"
    },
    {
        id: "grade",
        text: "Applying Rubric...",
        subtext: "Checking criteria matches against evidence.",
        icon: PenTool,
        color: "text-amber-500",
        bg: "bg-amber-100 dark:bg-amber-900/30"
    },
    {
        id: "judge",
        text: "Judge Validating...",
        subtext: "Self-correcting loop: Ensuring fairness & accuracy.",
        icon: Scale,
        color: "text-red-500",
        bg: "bg-red-100 dark:bg-red-900/30"
    },
    {
        id: "refine",
        text: "Refining Feedback...",
        subtext: "Polishing socratic guidance for the student.",
        icon: RefreshCw,
        color: "text-emerald-500",
        bg: "bg-emerald-100 dark:bg-emerald-900/30"
    }
];

export function GradingLoader() {
    const [phaseIndex, setPhaseIndex] = useState(0);

    useEffect(() => {
        // Cycle through phases every 1.5 seconds to simulate progress
        const interval = setInterval(() => {
            setPhaseIndex((prev) => (prev + 1) % LOADING_PHASES.length);
        }, 1800);
        return () => clearInterval(interval);
    }, []);

    const currentPhase = LOADING_PHASES[phaseIndex];
    const Icon = currentPhase.icon;

    return (
        <div className="flex flex-col items-center justify-center p-8 w-full">
            <div className="relative w-24 h-24 mb-6 flex items-center justify-center">
                {/* Ripples */}
                <motion.div
                    animate={{ scale: [1, 1.5, 1], opacity: [0.5, 0, 0.5] }}
                    transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                    className={`absolute inset-0 rounded-full ${currentPhase.bg}`}
                />

                {/* Main Icon Circle */}
                <motion.div
                    key={currentPhase.id}
                    initial={{ scale: 0.8, rotate: -20, opacity: 0 }}
                    animate={{ scale: 1, rotate: 0, opacity: 1 }}
                    exit={{ scale: 0.8, rotate: 20, opacity: 0 }}
                    transition={{ type: "spring", bounce: 0.5 }}
                    className={`relative z-10 w-20 h-20 rounded-full bg-white dark:bg-slate-800 shadow-xl flex items-center justify-center border-4 border-slate-50 dark:border-slate-700`}
                >
                    <Icon className={`w-10 h-10 ${currentPhase.color}`} />
                </motion.div>

                {/* Orbiting particle */}
                <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
                    className="absolute inset-[-10px]"
                >
                    <div className={`w-3 h-3 rounded-full ${currentPhase.bg.replace('/30', '')} shadow-sm`} />
                </motion.div>
            </div>

            <AnimatePresence mode="wait">
                <motion.div
                    key={currentPhase.id}
                    initial={{ y: 10, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    exit={{ y: -10, opacity: 0 }}
                    className="text-center space-y-2"
                >
                    <h3 className="text-xl font-bold text-slate-900 dark:text-white">
                        {currentPhase.text}
                    </h3>
                    <p className="text-sm text-slate-500 dark:text-slate-400 max-w-xs mx-auto">
                        {currentPhase.subtext}
                    </p>
                </motion.div>
            </AnimatePresence>

            {/* Progress Bar */}
            <div className="w-64 h-1.5 bg-slate-100 dark:bg-slate-800 rounded-full mt-6 overflow-hidden">
                <motion.div
                    className="h-full bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500"
                    animate={{ x: ["-100%", "100%"] }}
                    transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                />
            </div>
        </div>
    );
}
