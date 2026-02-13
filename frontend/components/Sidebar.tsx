"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
    LayoutDashboard, History, Settings, LogOut, ChevronLeft, ChevronRight, User,
    BookOpen, PenTool, BarChart3, Brain, Layers, X, Briefcase
} from "lucide-react";
import { Logo } from "@/components/Logo";
import { UnsavedChangesModal } from "@/components/UnsavedChangesModal";
import { motion, AnimatePresence } from "framer-motion";
import { useState, useEffect } from "react";

// Props definition
interface SidebarProps {
    collapsed?: boolean;
    setCollapsed?: (v: boolean) => void;
    isMobile?: boolean;      // New prop
    onClose?: () => void;    // New prop
}

export default function Sidebar({ collapsed, setCollapsed, isMobile = false, onClose }: SidebarProps) {
    const pathname = usePathname();
    const [isInternalCollapsed, setIsInternalCollapsed] = useState(false);
    const [isLogoutModalOpen, setIsLogoutModalOpen] = useState(false);

    // Force expanded on mobile
    const isCollapsed = isMobile ? false : (collapsed !== undefined ? collapsed : isInternalCollapsed);
    
    const toggleCollapse = () => {
        if (isMobile) return; // Disable toggle on mobile
        if (setCollapsed) {
            setCollapsed(!isCollapsed);
        } else {
            setIsInternalCollapsed(!isInternalCollapsed);
        }
    };

    const [user, setUser] = useState({ firstName: "Educator", lastName: "Admin", email: "educator@example.com" });

    useEffect(() => {
        const profile = localStorage.getItem('userProfile');
        if (profile) {
            const data = JSON.parse(profile);
            if (data.role === 'educator') setUser(data);
        }
    }, []);

    const navItems = [
        { icon: LayoutDashboard, label: "Dashboard", href: "/dashboard" },
        { icon: PenTool, label: "Grading Tool", href: "/grading" },
        { icon: Briefcase, label: "Business Grading", href: "/business-grading" },
        { icon: Layers, label: "Mass Grading", href: "/mass-grading" },
        { icon: BookOpen, label: "Grading Results", href: "/submissions" },
        { icon: BarChart3, label: "Analytics", href: "/analytics" },
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
                        <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Educator</p>
                    )}
                </div>
                {navItems.map((link) => {
                    const isActive = pathname === link.href;
                    return (
                        <Link
                            key={link.href}
                            href={link.href}
                            onClick={() => isMobile && onClose && onClose()} // Close on click for mobile
                            className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all group relative overflow-hidden ${isActive
                                ? "bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400 font-semibold"
                                : "text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-white"
                                }`}
                        >
                            <link.icon className={`w-5 h-5 flex-shrink-0 transition-colors ${isActive ? "text-emerald-600 dark:text-emerald-400" : "text-slate-500 dark:text-slate-400 group-hover:text-slate-900 dark:group-hover:text-white"}`} />
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
                                    layoutId="activeTab"
                                    className="absolute left-0 top-0 bottom-0 w-1 bg-emerald-600 rounded-r-full"
                                />
                            )}
                        </Link>
                    )
                })}
            </nav>

            <div className="p-4 border-t border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50 transition-colors">
                <div className={`flex items-center gap-3 ${isCollapsed ? 'justify-center' : ''} mb-4 overflow-hidden`}>
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center text-white font-bold text-sm shadow-md shrink-0">
                        {user.firstName[0]}{user.lastName[0]}
                    </div>
                    {!isCollapsed && (
                        <div className="overflow-hidden">
                            <motion.div
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                className="font-semibold text-sm text-slate-900 dark:text-white truncate"
                            >
                                {user.firstName} {user.lastName}
                            </motion.div>
                            <motion.div
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                className="text-xs text-slate-500 truncate w-32"
                            >
                                {user.email}
                            </motion.div>
                        </div>
                    )}
                </div>

                <div className="flex items-center gap-2">
                    {!isMobile && (
                        <button
                            onClick={toggleCollapse}
                            className="flex-1 flex items-center justify-center p-2 rounded-lg hover:bg-white dark:hover:bg-slate-800 text-slate-500 border border-transparent hover:border-slate-200 dark:hover:border-slate-700 transition-all shadow-sm"
                            title={isCollapsed ? "Expand" : "Collapse"}
                        >
                            {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
                        </button>
                    )}

                    <button
                        onClick={() => setIsLogoutModalOpen(true)}
                        className="flex-1 flex items-center justify-center p-2 rounded-lg text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-all border border-transparent hover:border-red-100 dark:hover:border-red-900/30"
                        title="Logout"
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
        </motion.aside >
    );
}
