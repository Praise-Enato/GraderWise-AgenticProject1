"use client";

import { useState } from "react";
import Sidebar from "@/components/Sidebar";
import { BackGuard } from "@/components/BackGuard";

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    const [collapsed, setCollapsed] = useState(false);

    return (
        <div className="flex h-screen overflow-hidden bg-slate-50 dark:bg-slate-950">
            <BackGuard />
            <Sidebar collapsed={collapsed} setCollapsed={setCollapsed} />

            {/* Main content area that grows when sidebar shrinks */}
            <div className="flex-1 flex flex-col h-screen overflow-hidden transition-all duration-300 relative">
                {children}
            </div>
        </div>
    );
}
