"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { ArrowRight, Github, Mail, Lock, User, Loader2, CheckCircle } from "lucide-react";
import { Logo } from "@/components/Logo";
import { ModeToggle } from "@/components/ModeToggle";
import { TrainLinesBackground } from "@/components/TrainLinesBackground";

export default function SignupPage() {
    const router = useRouter();
    const [isLogin, setIsLogin] = useState(false);
    
    // Role is now always educator
    const [formData, setFormData] = useState({ name: "", email: "", password: "" });
    const [isLoading, setIsLoading] = useState(false);
    const [isSuccess, setIsSuccess] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Auth Guard
    useEffect(() => {
        const profile = localStorage.getItem('userProfile');
        if (profile) {
            router.replace('/select');
        }
    }, [router]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setError(null);

        // Mock API call
        await new Promise(resolve => setTimeout(resolve, 1500));

        if (!isLogin) {
            // Register Logic
            const nameParts = formData.name.split(" ");
            const firstName = nameParts[0] || "User";
            const lastName = nameParts.length > 1 ? nameParts.slice(1).join(" ") : "";

            localStorage.setItem('userProfile', JSON.stringify({
                firstName,
                lastName,
                email: formData.email,
                role: 'educator',
                plan: 'Pro'
            }));
        } else {
            // Login Logic - Mock
            const existingProfile = localStorage.getItem('userProfile');
            if (!existingProfile) {
                // Auto-create for demo if not found
                localStorage.setItem('userProfile', JSON.stringify({
                    firstName: "Demo",
                    lastName: "Educator",
                    email: formData.email,
                    role: 'educator',
                    plan: 'Pro'
                }));
            }
        }

        setIsLoading(false);
        setIsSuccess(true);

        // Redirect to the workspace chooser (one login → either workspace)
        setTimeout(() => {
            router.push('/select');
        }, 1500);
    };

    return (
        <div className="min-h-screen w-full flex items-center justify-center relative overflow-hidden bg-slate-950">

            {/* Animated Background */}
            <TrainLinesBackground />

            {/* Theme Toggle */}
            <div className="absolute top-4 right-4 z-50">
                <ModeToggle />
            </div>

            <div className="w-full max-w-2xl relative z-10 px-4">

                {/* Logo Header */}
                <div className="text-center mb-8">
                    <Link href="/" className="inline-flex items-center gap-3 mb-4 group justify-center">
                        <Logo className="w-12 h-12" showText={false} />
                        <span className="text-3xl font-bold text-white tracking-tight">GradeWise</span>
                    </Link>
                    <h1 className="text-2xl font-bold text-white mb-2">
                        {isLogin ? "Welcome Back" : "Educator Access"}
                    </h1>
                    <p className="text-indigo-200 text-sm">
                        {isLogin
                            ? "Access your dashboard to continue."
                            : "Create your account to start grading."}
                    </p>
                </div>

                {/* Card */}
                <div className="bg-white/95 dark:bg-slate-900/90 backdrop-blur-xl rounded-2xl shadow-2xl overflow-hidden border border-white/10">
                    <div className="p-8">

                        {/* Login/Signup Toggle */}
                        <div className="flex bg-slate-100 dark:bg-slate-800 p-1 rounded-xl mb-6 relative">
                            <motion.div
                                className="absolute top-1 bottom-1 w-[calc(50%-4px)] bg-white dark:bg-slate-700 rounded-lg shadow-sm"
                                animate={{ x: isLogin ? "100%" : "0%" }}
                                transition={{ type: "spring", stiffness: 300, damping: 30 }}
                            />
                            <button onClick={() => setIsLogin(false)} className={`flex-1 relative z-10 py-2 text-sm font-semibold transition-colors text-center ${!isLogin ? "text-indigo-600 dark:text-indigo-400" : "text-slate-500 dark:text-slate-400"}`}>
                                Sign Up
                            </button>
                            <button onClick={() => setIsLogin(true)} className={`flex-1 relative z-10 py-2 text-sm font-semibold transition-colors text-center ${isLogin ? "text-indigo-600 dark:text-indigo-400" : "text-slate-500 dark:text-slate-400"}`}>
                                Sign In
                            </button>
                        </div>

                        <form onSubmit={handleSubmit} className="space-y-4">
                            {!isLogin && (
                                <div>
                                    <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase mb-1.5 ml-1">Full Name</label>
                                    <div className="relative">
                                        <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                                        <input
                                            type="text"
                                            required={!isLogin}
                                            className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-10 py-3 text-slate-900 dark:text-white outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all font-medium"
                                            placeholder="John Doe"
                                            value={formData.name}
                                            onChange={e => setFormData({ ...formData, name: e.target.value })}
                                        />
                                    </div>
                                </div>
                            )}

                            <div>
                                <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase mb-1.5 ml-1">Email</label>
                                <div className="relative">
                                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                                    <input
                                        type="email"
                                        required
                                        className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-10 py-3 text-slate-900 dark:text-white outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all font-medium"
                                        placeholder="name@example.com"
                                        value={formData.email}
                                        onChange={e => setFormData({ ...formData, email: e.target.value })}
                                    />
                                </div>
                            </div>

                            <div>
                                <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase mb-1.5 ml-1">Password</label>
                                <div className="relative">
                                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                                    <input
                                        type="password"
                                        required
                                        className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-10 py-3 text-slate-900 dark:text-white outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all font-medium"
                                        placeholder="••••••••"
                                        value={formData.password}
                                        onChange={e => setFormData({ ...formData, password: e.target.value })}
                                    />
                                </div>
                            </div>

                            <button
                                type="submit"
                                disabled={isLoading || isSuccess}
                                className={`w-full py-3.5 rounded-xl font-bold text-white shadow-lg shadow-emerald-500/20 hover:shadow-emerald-500/30 transition-all flex items-center justify-center gap-2 mt-6 ${isSuccess ? "bg-green-500" :
                                    "bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700"
                                    }`}
                            >
                                {isLoading ? (
                                    <Loader2 className="w-5 h-5 animate-spin" />
                                ) : isSuccess ? (
                                    <><CheckCircle className="w-5 h-5" /> Success</>
                                ) : (
                                    <>{isLogin ? "Sign In" : "Get Started"} <ArrowRight className="w-4 h-4" /></>
                                )}
                            </button>
                        </form>

                        <div className="mt-6 flex items-center justify-center gap-4">
                            <button className="p-2 rounded-full bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors">
                                <svg className="w-5 h-5" viewBox="0 0 24 24"><path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" /><path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" /><path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" /><path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" /></svg>
                            </button>
                            <button className="p-2 rounded-full bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors">
                                <Github className="w-5 h-5 text-slate-800 dark:text-white" />
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
