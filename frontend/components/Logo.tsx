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
 * GradeWise mark: a graduation cap on a rounded gradient tile. The blue→emerald
 * gradient bridges the two modes (classroom + business). Clean enough to read at
 * favicon size; see app/icon.tsx for the matching favicon.
 */
export const Logo: React.FC<LogoProps> = ({
  className = "w-10 h-10",
  showText = true,
  textClassName = "text-xl font-bold text-slate-900 dark:text-white",
}) => {
  const id = useId();
  const tile = `tile-${id}`;
  const sheen = `sheen-${id}`;

  return (
    <div className="flex items-center gap-2.5 group">
      <motion.div
        className={`relative ${className}`}
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4 }}
        whileHover={{ y: -1 }}
      >
        <svg viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg" className="h-full w-full drop-shadow-md">
          <defs>
            <linearGradient id={tile} x1="0" y1="0" x2="100" y2="100" gradientUnits="userSpaceOnUse">
              <stop offset="0%" stopColor="#3b82f6" />
              <stop offset="55%" stopColor="#10b981" />
              <stop offset="100%" stopColor="#0d9488" />
            </linearGradient>
            <linearGradient id={sheen} x1="0" y1="0" x2="0" y2="100" gradientUnits="userSpaceOnUse">
              <stop offset="0%" stopColor="#ffffff" stopOpacity="0.28" />
              <stop offset="45%" stopColor="#ffffff" stopOpacity="0" />
            </linearGradient>
          </defs>

          {/* Rounded tile */}
          <rect x="6" y="6" width="88" height="88" rx="24" fill={`url(#${tile})`} />
          <rect x="6" y="6" width="88" height="88" rx="24" fill={`url(#${sheen})`} />

          {/* Graduation cap (white) */}
          <g fill="#ffffff">
            {/* mortarboard */}
            <path d="M50 28 L82 43 L50 58 L18 43 Z" />
            {/* head / cap base */}
            <path d="M35 50.5 L50 57.5 L65 50.5 V61 C65 66.5 56 69 50 69 C44 69 35 66.5 35 61 Z" fillOpacity="0.92" />
          </g>
          {/* tassel */}
          <path d="M72 46 V60" stroke="#ffffff" strokeWidth="2.4" strokeLinecap="round" />
          <circle cx="72" cy="63" r="3.2" fill="#fde68a" />
          <circle cx="50" cy="43" r="2.6" fill="#ffffff" />
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
