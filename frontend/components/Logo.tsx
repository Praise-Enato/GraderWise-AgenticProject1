
"use client";

import React from 'react';
import { motion } from "framer-motion";

interface LogoProps {
    className?: string;
    showText?: boolean;
    textClassName?: string;
    status?: "idle" | "loading" | "success" | "error";
}

export const Logo: React.FC<LogoProps> = ({
    className = "w-10 h-10",
    showText = true,
    textClassName = "text-xl font-bold text-slate-900 dark:text-white",
    status = "idle"
}) => {
    // Determine spark color and speed based on status
    const sparkColor = {
        idle: "#FDE047", // Yellow
        loading: "#F97316", // Orange
        success: "#22C55E", // Green
        error: "#EF4444"   // Red
    }[status];

    const orbitDuration = {
        idle: "4s",
        loading: "1s",
        success: "6s",
        error: "0.5s"
    }[status];
    return (
        <div className="flex items-center gap-3 group">
            <motion.div
                className={`relative flex items-center justify-center ${className}`}
                initial={{ opacity: 0, scale: 0.8, rotateY: -180 }}
                animate={{ opacity: 1, scale: 1, rotateY: 0 }}
                transition={{ duration: 0.8, type: "spring", bounce: 0.4 }}
                whileHover={{ scale: 1.1, rotateZ: 5 }}
            >
                <svg viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-full h-full drop-shadow-xl">
                    <defs>
                        {/* 3D Lighting Gradients */}
                        <linearGradient id="faceLight" x1="0" y1="0" x2="100%" y2="100%">
                            <stop offset="0%" stopColor="#60A5FA" stopOpacity="0.9" /> {/* bright blue */}
                            <stop offset="100%" stopColor="#2563EB" stopOpacity="1" />
                        </linearGradient>
                        <linearGradient id="faceDark" x1="100%" y1="0%" x2="0%" y2="100%">
                            <stop offset="0%" stopColor="#1E40AF" stopOpacity="1" /> {/* dark blue */}
                            <stop offset="100%" stopColor="#172554" stopOpacity="1" />
                        </linearGradient>
                        <linearGradient id="faceTop" x1="0" y1="0.5" x2="1" y2="0.5">
                            <stop offset="0%" stopColor="#93C5FD" />
                            <stop offset="100%" stopColor="#3B82F6" />
                        </linearGradient>

                        {/* Glow Filter */}
                        <filter id="glow3d" x="-50%" y="-50%" width="200%" height="200%">
                            <feGaussianBlur stdDeviation="4" result="blur" />
                            <feComposite in="SourceGraphic" in2="blur" operator="over" />
                        </filter>
                    </defs>

                    {/* ANIMATED LAYERS */}
                    <motion.g
                        animate={{ y: [0, -3, 0] }}
                        transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
                    >
                        {/* Isometric Cube Base - Bottom Face (Shadow) */}
                        <path d="M50 95 L15 75 L50 60 L85 75 Z" fill="#1e3a8a" opacity="0.4" filter="url(#blur)" />

                        {/* Right Face (Darker) */}
                        <path d="M50 55 L85 35 V75 L50 95 Z" fill="url(#faceDark)" stroke="#1e3a8a" strokeWidth="0.5" />

                        {/* Left Face (Mid) */}
                        <path d="M50 55 L15 35 V75 L50 95 Z" fill="url(#faceLight)" stroke="#2563EB" strokeWidth="0.5" />

                        {/* Top Face (Brightest) */}
                        <path d="M50 55 L15 35 L50 15 L85 35 Z" fill="url(#faceTop)" stroke="#93C5FD" strokeWidth="0.5" />

                        {/* Mortarboard / Cap Detail (Floating on top) */}
                        <motion.g
                            animate={{ y: [0, -2, 0] }}
                            transition={{ duration: 3, repeat: Infinity, ease: "easeInOut", delay: 0.5 }}
                        >
                            <path d="M50 25 L25 38 L50 50 L75 38 Z" fill="white" fillOpacity="0.9" />
                            {/* Tassel */}
                            <path d="M75 38 L75 55" stroke="#FDE047" strokeWidth="2" strokeLinecap="round" />
                            <circle cx="75" cy="55" r="2" fill="#FDE047" />
                        </motion.g>
                    </motion.g>

                    {/* Orbiting AI Spark */}
                    <motion.circle
                        cx="50" cy="50" r="3"
                        fill={sparkColor}
                        filter="url(#glow3d)"
                        animate={{
                            offsetDistance: "100%",
                            opacity: status === 'success' ? 1 : [0, 1, 1, 0]
                        }}
                    >
                        <animateMotion
                            dur={orbitDuration}
                            repeatCount="indefinite"
                            path="M50 15 Q 90 35 50 95 Q 10 35 50 15 Z"
                        />
                    </motion.circle>
                </svg>
            </motion.div>

            {showText && (
                <div className="flex flex-col">
                    <span className={`tracking-tight leading-none ${textClassName}`}>
                        GradeWise
                    </span>
                    <span className="text-[0.6rem] font-bold tracking-[0.2em] text-blue-500 uppercase ml-0.5">
                        Agentic AI
                    </span>
                </div>
            )}
        </div>
    );
};
