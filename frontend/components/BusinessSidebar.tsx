"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
    LayoutDashboard, LogOut, ChevronLeft, ChevronRight,
    Briefcase, Trophy, Swords, X, LayoutGrid
} from "lucide-react";
import { Logo } from "@/components/Logo";
import { UnsavedChangesModal } from "@/components/UnsavedChangesModal";
import { motion, AnimatePresence } from "framer-motion";
import { useState, useEffect } from "react";

interface SidebarProps {
    collapsed?: boolean;
    setCollapsed?: (v: boolean) => void;
    isMobile?: boolean;
    onClose?: () => void;
}

// Business Plan workspace sidebar. Mirrors the educator Sidebar structure but
// carries only the competition-suite nav and an indigo/violet accent so the two
// workspaces read as distinct products. "Switch workspace" returns to /select.
export default function BusinessSidebar({ collapsed, setCollapsed, isMobile = false, onClose }: SidebarProps) {
    const pathname = usePathname();
    const [isInternalCollapsed, setIsInternalCollapsed] = useState(false);
    const [isLogoutModalOpen, setIsLogoutModalOpen] = useState(false);

    const isCollapsed = isMobile ? false : (collapsed !== undefined ? collapsed : isInternalCollapsed);

    const toggleCollapse = () => {
        if (isMobile) return;
        if (setCollapsed) setCollapsed(!isCollapsed);
        else setIsInternalCollapsed(!isInternalCollapsed);
    };

    const [user, setUser] = useState({ firstName: "Business", lastName: "User", email: "user@example.com" });

    useEffect(() => {
        const profile = localStorage.getItem('userProfile');
        if (profile) {
            try { setUser(JSON.parse(profile)); } catch { /* ignore */ }
        }
    }, []);

    const navItems = [
        { icon: LayoutDashboard, label: "Dashboard", href: "/business" },
        { icon: Briefcase, label: "Business Plan Grader", href: "/business/grading" },
        { icon: Trophy, label: "Competition Screening", href: "/business/screening" },
        { icon: Swords, label: "AI vs Human", href: "/business/ai-vs-human" },
    ];

    return (
        <motion.aside
            initial={false}
            animate={isMobile ? undefined : { width: isCollapsed ? 80 : 256 }}
            transition={{ duration: 0.3, ease: "easeInOut" }}
            className={`h-full bg-white dark:bg-slate-900 border-r border-slate-100 dark:border-white/5 flex flex-col shadow-xl z-20 ${isMobile ? 'w-72' : 'relative'}`}
        >
            <div className="h-16 flex items-center justify-between px-6 border-b border-slate-100 dark:border-white/5 shrink-0 bg-white dark:bg-slate-900 transition-colors">
                <Link href="/" className="flex items-center gap-3 overflow-hidden hover:opacity-80 transition-opacity">
                    <Logo className="w-8 h-8" showText={false} />
                    <AnimatePresence>
                        {!isCollapsed && (
                            <motion.span
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                exit={{ opacity: 0 }}
                                className="font-bold text-lg text-slate-800 dark:text-white tracking-tight whitespace-nowrap"
                            >
                                GradeWise
                            </motion.span>
                        )}
                    </AnimatePresence>
                </Link>

                {isMobile && onClose && (
                    <button
                        onClick={onClose}
                        className="p-1 -mr-2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full transition-colors"
                        aria-label="Close menu"
                    >
                        <X className="w-5 h-5" />
                    </button>
                )}
            </div>

            <nav className="flex-1 p-4 space-y-2 overflow-y-auto overflow-x-hidden">
                <div className="mb-6 px-2">
                    {!isCollapsed && (
                        <p className="text-xs font-semibold text-indigo-400 uppercase tracking-wider mb-2">Business Plan</p>
                    )}
                </div>
                {navItems.map((link) => {
                    const isActive = pathname === link.href;
                    return (
                        <Link
                            key={link.href}
                            href={link.href}
                            onClick={() => isMobile && onClose && onClose()}
                            className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all group relative overflow-hidden ${isActive
                                ? "bg-indigo-50 dark:bg-indigo-900/20 text-indigo-600 dark:text-indigo-400 font-semibold"
                                : "text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-white"
                                }`}
                        >
                            <link.icon className={`w-5 h-5 flex-shrink-0 transition-colors ${isActive ? "text-indigo-600 dark:text-indigo-400" : "text-slate-500 dark:text-slate-400 group-hover:text-slate-900 dark:group-hover:text-white"}`} />
                            {!isCollapsed && (
                                <motion.span
                                    initial={{ opacity: 0, x: -10 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ delay: 0.1 }}
                                    className="whitespace-nowrap"
                                >
                                    {link.label}
                                </motion.span>
                            )}
                            {isActive && (
                                <motion.div
                                    layoutId="activeTabBiz"
                                    className="absolute left-0 top-0 bottom-0 w-1 bg-indigo-600 rounded-r-full"
                                />
                            )}
                        </Link>
                    );
                })}

                {/* Switch workspace — same login, different product */}
                <Link
                    href="/select"
                    onClick={() => isMobile && onClose && onClose()}
                    className="flex items-center gap-3 px-4 py-3 mt-4 rounded-xl border border-dashed border-slate-200 dark:border-slate-700 text-slate-500 dark:text-slate-400 hover:text-indigo-600 dark:hover:text-indigo-400 hover:border-indigo-300 dark:hover:border-indigo-700 hover:bg-indigo-50/50 dark:hover:bg-indigo-900/10 transition-all group"
                >
                    <LayoutGrid className="w-5 h-5 flex-shrink-0" />
                    {!isCollapsed && <span className="whitespace-nowrap text-sm font-medium">Switch workspace</span>}
                </Link>
            </nav>

            <div className="p-4 border-t border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50 transition-colors">
                <div className={`flex items-center gap-3 ${isCollapsed ? 'justify-center' : ''} mb-4 overflow-hidden`}>
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center text-white font-bold text-sm shadow-md shrink-0">
                        {(user.firstName?.[0] || "B")}{(user.lastName?.[0] || "U")}
                    </div>
                    {!isCollapsed && (
                        <div className="overflow-hidden">
                            <div className="font-semibold text-sm text-slate-900 dark:text-white truncate">
                                {user.firstName} {user.lastName}
                            </div>
                            <div className="text-xs text-slate-500 truncate w-32">{user.email}</div>
                        </div>
                    )}
                </div>

                {/* Stack vertically when collapsed so the expand button always fits
                    the narrow rail (side-by-side would overflow 80px and hide it). */}
                <div className={`flex gap-2 ${isCollapsed ? "flex-col" : "items-center"}`}>
                    {!isMobile && (
                        <button
                            onClick={toggleCollapse}
                            className="flex-1 w-full flex items-center justify-center p-2 rounded-lg hover:bg-white dark:hover:bg-slate-800 text-slate-500 border border-transparent hover:border-slate-200 dark:hover:border-slate-700 transition-all shadow-sm"
                            title={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
                            aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
                        >
                            {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
                        </button>
                    )}
                    <button
                        onClick={() => setIsLogoutModalOpen(true)}
                        className="flex-1 w-full flex items-center justify-center p-2 rounded-lg text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-all border border-transparent hover:border-red-100 dark:hover:border-red-900/30"
                        title="Logout"
                        aria-label="Logout"
                    >
                        <LogOut className="w-4 h-4" />
                    </button>
                </div>
            </div>

            <UnsavedChangesModal
                isOpen={isLogoutModalOpen}
                onClose={() => setIsLogoutModalOpen(false)}
                onConfirm={() => {
                    localStorage.removeItem('userProfile');
                    window.location.replace('/signup');
                }}
            />
        </motion.aside>
    );
}
