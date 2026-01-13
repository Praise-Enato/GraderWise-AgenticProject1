"use client";

import { motion, AnimatePresence } from "framer-motion";
import { AlertTriangle, LogOut } from "lucide-react";

interface UnsavedChangesModalProps {
    isOpen: boolean;
    onClose: () => void;
    onConfirm: () => void;
}

export function UnsavedChangesModal({ isOpen, onClose, onConfirm }: UnsavedChangesModalProps) {
    return (
        <AnimatePresence>
            {isOpen && (
                <>
                    {/* Backdrop */}
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[9999] flex items-center justify-center p-4"
                        onClick={onClose}
                    />

                    {/* Modal */}
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95, y: 20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95, y: 20 }}
                        className="fixed z-[10000] w-full max-w-sm bg-white dark:bg-slate-900 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-800 overflow-hidden top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2"
                    >
                        <div className="p-6 text-center">
                            <div className="w-12 h-12 bg-amber-100 dark:bg-amber-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
                                <AlertTriangle className="w-6 h-6 text-amber-600 dark:text-amber-500" />
                            </div>
                            <h2 className="text-lg font-bold text-slate-900 dark:text-white mb-2">
                                Unsaved Progress Warning
                            </h2>
                            <p className="text-sm text-slate-500 dark:text-slate-400 mb-6 leading-relaxed">
                                You are about to leave the secure session. Any unfinished grading jobs or unsaved data will be lost.
                            </p>

                            <div className="flex flex-col gap-3">
                                <button
                                    onClick={onConfirm}
                                    className="w-full py-2.5 bg-red-500 hover:bg-red-600 text-white rounded-xl font-medium transition-colors flex items-center justify-center gap-2"
                                >
                                    <LogOut className="w-4 h-4" />
                                    Logout & Exit
                                </button>
                                <button
                                    onClick={onClose}
                                    className="w-full py-2.5 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-xl font-medium transition-colors"
                                >
                                    Stay Signed In
                                </button>
                            </div>
                        </div>
                    </motion.div>
                </>
            )}
        </AnimatePresence>
    );
}
