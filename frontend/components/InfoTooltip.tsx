
"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Info } from "lucide-react";

interface InfoTooltipProps {
    content: string;
    children?: React.ReactNode;
    width?: string;
    side?: "top" | "bottom" | "left" | "right";
}

export function InfoTooltip({ content, children, width = "max-w-xs", side = "top" }: InfoTooltipProps) {
    const [isVisible, setIsVisible] = useState(false);

    return (
        <span
            className="relative inline-flex items-center"
            onMouseEnter={() => setIsVisible(true)}
            onMouseLeave={() => setIsVisible(false)}
        >
            {children ? children : <Info className="w-4 h-4 text-slate-400 hover:text-blue-500 transition-colors cursor-help" />}

            <AnimatePresence>
                {isVisible && (
                    <motion.div
                        initial={{ opacity: 0, scale: 0.9, y: 5 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.9, y: 5 }}
                        transition={{ duration: 0.15 }}
                        className={`absolute z-50 ${width} p-3 bg-slate-900 dark:bg-slate-800 text-white text-xs rounded-xl shadow-xl border border-slate-700/50 backdrop-blur-md pointer-events-none transform -translate-x-1/2 left-1/2 ${side === "top" ? "-top-2 -translate-y-[100%]" :
                            side === "bottom" ? "top-full mt-2" : "" // simplified positioning
                            }`}
                        style={{
                            boxShadow: "0 10px 38px -10px rgba(22, 23, 24, 0.35), 0 10px 20px -15px rgba(22, 23, 24, 0.2)"
                        }}
                    >
                        {content}
                        {/* Arrow */}
                        <div className="absolute left-1/2 -translate-x-1/2 bottom-[-4px] w-2 h-2 bg-slate-900 dark:bg-slate-800 rotate-45 border-b border-r border-slate-700/50"></div>
                    </motion.div>
                )}
            </AnimatePresence>
        </span>
    );
}
