"use client";

import React, { useId } from "react";
import { motion } from "framer-motion";

interface LogoProps {
  className?: string;
  showText?: boolean;
  textClassName?: string;
  status?: "idle" | "loading" | "success" | "error";
}

/**
 * GradeWise mark: a standalone graduation cap (no container). The board carries
 * a blue→emerald gradient (bridging the two modes), the head is a darker teal
 * for separation, and the tassel is gold — so the mark reads on light or dark.
 * The favicon (app/icon.tsx) uses the same shape.
 */
export const Logo: React.FC<LogoProps> = ({
  className = "w-10 h-10",
  showText = true,
  textClassName = "text-xl font-bold text-slate-900 dark:text-white",
}) => {
  const id = useId();
  const board = `board-${id}`;

  return (
    <div className="flex items-center gap-2.5 group">
      <motion.div
        className={`relative ${className}`}
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4 }}
        whileHover={{ y: -1, rotate: -2 }}
      >
        <svg viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg" className="h-full w-full drop-shadow-sm">
          <defs>
            <linearGradient id={board} x1="6" y1="20" x2="94" y2="60" gradientUnits="userSpaceOnUse">
              <stop offset="0%" stopColor="#3b82f6" />
              <stop offset="100%" stopColor="#10b981" />
            </linearGradient>
          </defs>

          {/* head / cap base (darker, sits under the board) */}
          <path d="M32 50 L50 58 L68 50 L68 66 C68 72 60 75.5 50 75.5 C40 75.5 32 72 32 66 Z" fill="#0f766e" />
          {/* mortarboard */}
          <path d="M50 20 L94 40 L50 60 L6 40 Z" fill={`url(#${board})`} />
          {/* button */}
          <circle cx="50" cy="40" r="3" fill="#e0a92e" />
          {/* tassel */}
          <path d="M50 40 C 70 40, 79 48, 79 62" stroke="#e0a92e" strokeWidth="2.6" strokeLinecap="round" fill="none" />
          <circle cx="79" cy="64" r="3.8" fill="#f5c451" />
        </svg>
      </motion.div>

      {showText && (
        <div className="flex flex-col leading-none">
          <span className={`tracking-tight ${textClassName}`}>GradeWise</span>
          <span className="mt-0.5 text-[0.58rem] font-bold uppercase tracking-[0.22em] text-emerald-600 dark:text-emerald-400">
            AI Grader
          </span>
        </div>
      )}
    </div>
  );
};
