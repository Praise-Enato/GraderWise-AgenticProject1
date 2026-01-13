import { User } from "lucide-react";

export default function ProfilePage() {
    return (
        <div className="space-y-8">
            <div className="flex items-center gap-4">
                <div className="w-16 h-16 bg-indigo-100 rounded-full flex items-center justify-center text-indigo-600">
                    <User className="w-8 h-8" />
                </div>
                <div>
                    <h1 className="text-3xl font-bold text-slate-900 dark:text-white">My Profile</h1>
                    <p className="text-slate-500">Manage your personal information.</p>
                </div>
            </div>

            <div className="bg-white dark:bg-slate-900 p-8 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm">
                <p className="text-slate-500 italic">Profile details coming soon...</p>
            </div>
        </div>
    );
}
