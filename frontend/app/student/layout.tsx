"use client";

import { useState } from "react";
import { BackGuard } from "@/components/BackGuard";
import { TrainLinesBackground } from "@/components/TrainLinesBackground";
import { StudentSidebar } from "@/components/StudentSidebar";
import { ModeToggle } from "@/components/ModeToggle";
import { Logo } from "@/components/Logo";

export default function StudentLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    const [collapsed, setCollapsed] = useState(false);

    return (
        <div className="min-h-screen bg-slate-50 dark:bg-slate-950 transition-colors duration-500 relative flex">
            <BackGuard />

            {/* Background for the whole student area */}
            <div className="fixed inset-0 z-0 opacity-20 pointer-events-none">
                <TrainLinesBackground />
            </div>

            {/* Sidebar (Desktop) */}
            <StudentSidebar collapsed={collapsed} setCollapsed={setCollapsed} />

            {/* Main Content Area */}
            <div
                className={`flex-1 flex flex-col transition-all duration-300 ${collapsed ? "md:pl-20" : "md:pl-64"
                    }`}
            >
                {/* Mobile/Tablet Top Nav (simplified since Sidebar handles desktop) */}
                <nav className="sticky top-0 z-30 w-full bg-white/80 dark:bg-slate-950/80 backdrop-blur-md border-b border-slate-200 dark:border-white/10 md:hidden px-4 h-16 flex items-center justify-between">
                    <Logo className="w-8 h-8" />
                    <ModeToggle />
                </nav>

                {/* Desktop Top Right Actions (Theme Toggle mainly) */}
                <div className="hidden md:flex justify-end p-6 fixed top-0 right-0 z-30 pointer-events-none">
                    <div className="pointer-events-auto">
                        <ModeToggle />
                    </div>
                </div>

                <main className="relative z-10 p-4 md:p-8 max-w-7xl mx-auto w-full">
                    {children}
                </main>
            </div>
        </div>
    );
}
