import Sidebar from "@/components/Sidebar";
import BackGuard from "@/components/BackGuard";

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <div className="flex h-screen overflow-hidden">
            <BackGuard />
            <Sidebar />
            <div className="flex-1 flex flex-col h-screen overflow-hidden">
                {children}
            </div>
        </div>
    );
}
