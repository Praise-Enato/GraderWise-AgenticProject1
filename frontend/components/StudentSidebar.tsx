"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, User, Settings, BookOpen, LogOut, ChevronLeft, ChevronRight, Calendar, FileText, GraduationCap, Clock } from "lucide-react";
import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Logo } from "@/components/Logo";
import { UnsavedChangesModal } from "@/components/UnsavedChangesModal";

export function StudentSidebar({
    collapsed,
    setCollapsed
}: {
    collapsed: boolean;
    setCollapsed: (v: boolean) => void
}) {
    const pathname = usePathname();
    const [showLogoutModal, setShowLogoutModal] = useState(false);
    const [user, setUser] = useState({ firstName: "Student", lastName: "User", email: "student@example.com" });

    useEffect(() => {
        const profile = localStorage.getItem('userProfile');
        if (profile) {
            setUser(JSON.parse(profile));
        }
    }, []);

    const navItems = [
        { href: "/student/dashboard", label: "Dashboard", icon: LayoutDashboard },
        { href: "/student/assignments", label: "Assignments", icon: FileText },
        { href: "/student/history", label: "History", icon: Clock },
        { href: "/student/settings", label: "Settings", icon: Settings },
    ];

    return (
        <>
            <motion.aside
                initial={false}
                animate={{ width: collapsed ? 80 : 256 }}
                transition={{ duration: 0.3, ease: "easeInOut" }}
                className="fixed left-0 top-0 h-full bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 z-40 hidden md:flex flex-col shadow-xl"
            >
                <div className="h-16 flex items-center gap-3 px-6 border-b border-slate-100 dark:border-slate-800 shrink-0 overflow-hidden">
                    <Logo className="w-8 h-8" showText={false} />
                    <AnimatePresence>
                        {!collapsed && (
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
                </div>

                <div className="flex-1 py-6 px-4 space-y-2 overflow-y-auto overflow-x-hidden">
                    <div className="mb-6 px-2">
                        {!collapsed && (
                            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Menu</p>
                        )}
                    </div>
                    <nav className="flex-1 space-y-2 p-4">
                        {navItems.map((link) => {
                            const Icon = link.icon;
                            const isActive = pathname === link.href;
                            return (
                                <Link
                                    key={link.href}
                                    href={link.href}
                                    className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all group relative overflow-hidden ${isActive
                                        ? "bg-indigo-50 dark:bg-indigo-900/20 text-indigo-600 dark:text-indigo-400 font-semibold"
                                        : "text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-white"
                                        }`}
                                >
                                    <link.icon className={`w-5 h-5 flex-shrink-0 transition-colors ${isActive ? "text-indigo-600 dark:text-indigo-400" : "text-slate-500 dark:text-slate-400 group-hover:text-slate-900 dark:group-hover:text-white"}`} />
                                    {!collapsed && (
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
                                            className="absolute left-0 top-0 bottom-0 w-1 bg-indigo-600 rounded-r-full"
                                        />
                                    )}
                                </Link>
                            );
                        })}
                    </nav>
                </div>

                <div className="p-4 border-t border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50 transition-colors">
                    <div className={`flex items-center gap-3 ${collapsed ? 'justify-center' : ''} mb-4 overflow-hidden`}>
                        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center text-white font-bold text-sm shadow-md shrink-0">
                            {user.firstName[0]}{user.lastName[0]}
                        </div>
                        {!collapsed && (
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
                        <button
                            onClick={() => setCollapsed(!collapsed)}
                            className="flex-1 flex items-center justify-center p-2 rounded-lg hover:bg-white dark:hover:bg-slate-800 text-slate-500 border border-transparent hover:border-slate-200 dark:hover:border-slate-700 transition-all shadow-sm"
                            title={collapsed ? "Expand" : "Collapse"}
                        >
                            {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
                        </button>

                        <button
                            onClick={() => setShowLogoutModal(true)}
                            className="flex-1 flex items-center justify-center p-2 rounded-lg text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-all border border-transparent hover:border-red-100 dark:hover:border-red-900/30"
                            title="Logout"
                        >
                            <LogOut className="w-4 h-4" />
                        </button>
                    </div>
                </div>
            </motion.aside>

            <UnsavedChangesModal
                isOpen={showLogoutModal}
                onClose={() => setShowLogoutModal(false)}
                onConfirm={() => {
                    localStorage.removeItem('userProfile');
                    window.location.href = '/signup';
                }}
            />
        </>
    );
}
