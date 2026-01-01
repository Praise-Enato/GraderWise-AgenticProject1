'use client';

import Link from 'next/link';
import {
    LayoutDashboard,
    PlusCircle,
    History,
    Users,
    Settings,
    HelpCircle,
    GraduationCap
} from 'lucide-react';
import { usePathname } from 'next/navigation';
import { useState, useEffect } from 'react';

export default function Sidebar() {
    const pathname = usePathname();
    const [userName, setUserName] = useState("Instructor");

    // Hydrate user profile from local storage
    if (typeof window !== 'undefined') {
        // Simple client-side only check to avoid hydration mismatch is usually better done with useEffect
    }

    // We need useEffect to avoid hydration error
    const [mounted, setMounted] = useState(false);
    useEffect(() => {
        setMounted(true);
        const stored = localStorage.getItem('userProfile');
        if (stored) {
            const { firstName, lastName } = JSON.parse(stored);
            setUserName(`${firstName} ${lastName}`);
        }
    }, []);

    return (
        <aside className="w-64 flex-shrink-0 border-r border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 flex flex-col transition-colors duration-300 h-screen">
            {/* Header */}
            <div className="h-20 flex items-center px-6 border-b border-slate-200 dark:border-slate-700">
                <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-blue-400 flex items-center justify-center text-white shadow-lg shadow-blue-500/30">
                        <GraduationCap className="w-5 h-5" />
                    </div>
                    <span className="font-bold text-xl tracking-tight text-slate-900 dark:text-white">GradeWise</span>
                </div>
            </div>

            {/* Navigation */}
            <nav className="flex-1 overflow-y-auto py-6 px-3 space-y-1">
                {[
                    { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
                    { label: "New Grading Job", href: "/grading", icon: PlusCircle },
                    { label: "Class History", href: "/history", icon: History },
                    { label: "Students", href: "/students", icon: Users },
                ].map((link) => {
                    const isActive = pathname === link.href;
                    const Icon = link.icon;
                    return (
                        <Link
                            key={link.href}
                            href={link.href}
                            className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 group ${isActive
                                ? "bg-primary text-white shadow-lg shadow-blue-500/30"
                                : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-white"
                                }`}
                        >
                            <Icon className={`w-5 h-5 transition-colors ${isActive
                                ? "text-white"
                                : "text-slate-400 group-hover:text-slate-600 dark:group-hover:text-slate-200"
                                }`} />
                            <span className="font-medium">{link.label}</span>
                        </Link>
                    );
                })}

                <div className="pt-4 mt-4 border-t border-slate-200 dark:border-slate-700">
                    <p className="px-3 text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">System</p>

                    {[
                        { label: "Settings", href: "/settings", icon: Settings },
                        { label: "Support", href: "/support", icon: HelpCircle },
                    ].map((link) => {
                        const isActive = pathname === link.href;
                        const Icon = link.icon;
                        return (
                            <Link
                                key={link.href}
                                href={link.href}
                                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 group ${isActive
                                    ? "bg-primary text-white shadow-lg shadow-blue-500/30"
                                    : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-white"
                                    }`}
                            >
                                <Icon className={`w-5 h-5 transition-colors ${isActive
                                    ? "text-white"
                                    : "text-slate-400 group-hover:text-slate-600 dark:group-hover:text-slate-200"
                                    }`} />
                                <span className="font-medium">{link.label}</span>
                            </Link>
                        );
                    })}
                </div>
            </nav>

            <div className="p-4 border-t border-slate-200 dark:border-slate-700 space-y-4">
                {/* System Status - Professional & Dynamic */}
                <div className="flex items-center justify-between px-2">
                    <div className="flex items-center gap-2">
                        <span className="relative flex h-2.5 w-2.5">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
                        </span>
                        <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">System Online</span>
                    </div>
                    <span className="text-xs font-mono text-slate-400 dark:text-slate-500">v2.4.0</span>
                </div>

                <Link href="/settings" className="flex items-center gap-3 p-2 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors cursor-pointer group">
                    <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-primary font-bold shadow-sm group-hover:bg-primary group-hover:text-white transition-all text-xs">
                        {mounted && userName ? (
                            userName.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase()
                        ) : (
                            <Users className="w-5 h-5" />
                        )}
                    </div>
                    <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-slate-900 dark:text-white truncate">{mounted ? userName : "Instructor"}</p>
                        <p className="text-xs text-slate-500 dark:text-slate-400 truncate">Pro Plan • Unlimited</p>
                    </div>
                    <Settings className="w-4 h-4 text-slate-400 group-hover:text-primary transition-colors" />
                </Link>
            </div>
        </aside>
    );
}

