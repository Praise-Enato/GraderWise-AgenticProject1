export default function StudentsPage() {
    return (
        <div className="flex flex-col items-center justify-center h-full p-8 text-center">
            <div className="bg-primary/10 p-6 rounded-full mb-4">
                <span className="text-4xl">👥</span>
            </div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">Student Management</h1>
            <p className="text-slate-500 dark:text-slate-400 max-w-md">
                Manage your class roster and view student profiles here. Feature coming soon.
            </p>
        </div>
    );
}
