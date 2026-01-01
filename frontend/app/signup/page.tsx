"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { GraduationCap, ArrowRight, Github, Mail, Lock, User, Loader2, CheckCircle } from "lucide-react";

import { ModeToggle } from "@/components/ModeToggle";

export default function SignupPage() {
    const router = useRouter();
    const [isLogin, setIsLogin] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [isSuccess, setIsSuccess] = useState(false);

    // Form State
    const [formData, setFormData] = useState({
        name: "",
        email: "",
        password: ""
    });

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);

        // Mock API call
        await new Promise(resolve => setTimeout(resolve, 1500));

        setIsLoading(false);
        setIsSuccess(true);

        // Redirect after success animation
        setTimeout(() => {
            router.push("/dashboard");
        }, 1000);
    };

    return (
        <div className="min-h-screen w-full flex items-center justify-center bg-gradient-to-br from-indigo-900 via-violet-900 to-purple-900 p-4 transition-colors duration-500">

            {/* Theme Toggle */}
            <div className="absolute top-4 right-4 z-50">
                <ModeToggle />
            </div>

            {/* Background Decor */}
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
                <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-600/20 rounded-full blur-3xl animate-pulse"></div>
                <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-600/20 rounded-full blur-3xl animate-pulse delay-700"></div>
            </div>

            <div className="w-full max-w-md relative z-10">

                {/* Logo Header */}
                <div className="text-center mb-8">
                    <Link href="/" className="inline-flex items-center gap-2 mb-4 group">
                        <div className="w-10 h-10 rounded-xl flex items-center justify-center text-white bg-gradient-to-br from-blue-600 to-indigo-600 shadow-lg shadow-blue-600/20 group-hover:scale-110 transition-transform">
                            <GraduationCap className="w-6 h-6" />
                        </div>
                        <span className="text-2xl font-bold text-white tracking-tight">GradeWise</span>
                    </Link>
                    <h1 className="text-3xl font-bold text-white mb-2">
                        {isLogin ? "Welcome Back" : "Create Account"}
                    </h1>
                    <p className="text-indigo-200">
                        {isLogin
                            ? "Enter your credentials to access your workspace."
                            : "Join thousands of educators saving time with AI."}
                    </p>
                </div>

                {/* Card */}
                <div className="bg-white/95 dark:bg-slate-900/90 backdrop-blur-xl rounded-2xl shadow-2xl overflow-hidden transition-colors duration-300">
                    <div className="p-8">

                        {/* Toggle */}
                        <div className="flex bg-slate-100 dark:bg-slate-800 p-1 rounded-xl mb-8 relative transition-colors">
                            <motion.div
                                className="absolute top-1 bottom-1 w-[calc(50%-4px)] bg-white dark:bg-slate-700 rounded-lg shadow-sm"
                                animate={{ x: isLogin ? "100%" : "0%" }}
                                transition={{ type: "spring", stiffness: 300, damping: 30 }}
                            />
                            <button
                                onClick={() => setIsLogin(false)}
                                className={`flex-1 relative z-10 py-2 text-sm font-semibold transition-colors text-center ${!isLogin ? "text-indigo-600 dark:text-indigo-400" : "text-slate-500 dark:text-slate-400"}`}
                            >
                                Sign Up
                            </button>
                            <button
                                onClick={() => setIsLogin(true)}
                                className={`flex-1 relative z-10 py-2 text-sm font-semibold transition-colors text-center ${isLogin ? "text-indigo-600 dark:text-indigo-400" : "text-slate-500 dark:text-slate-400"}`}
                            >
                                Sign In
                            </button>
                        </div>

                        <form onSubmit={handleSubmit} className="space-y-4">
                            <AnimatePresence mode="popLayout">
                                {!isLogin && (
                                    <motion.div
                                        initial={{ opacity: 0, height: 0 }}
                                        animate={{ opacity: 1, height: "auto" }}
                                        exit={{ opacity: 0, height: 0 }}
                                        className="space-y-4 overflow-hidden"
                                    >
                                        <div>
                                            <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase mb-1.5 ml-1">Full Name</label>
                                            <div className="relative group">
                                                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 group-focus-within:text-indigo-500 transition-colors" />
                                                <input
                                                    type="text"
                                                    required={!isLogin}
                                                    className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-10 py-3 text-slate-900 dark:text-white placeholder:text-slate-400 outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all font-medium"
                                                    placeholder="John Doe"
                                                    value={formData.name}
                                                    onChange={e => setFormData({ ...formData, name: e.target.value })}
                                                />
                                            </div>
                                        </div>
                                    </motion.div>
                                )}
                            </AnimatePresence>

                            <div>
                                <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase mb-1.5 ml-1">Email Address</label>
                                <div className="relative group">
                                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 group-focus-within:text-indigo-500 transition-colors" />
                                    <input
                                        type="email"
                                        required
                                        className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-10 py-3 text-slate-900 dark:text-white placeholder:text-slate-400 outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all font-medium"
                                        placeholder="name@university.edu"
                                        value={formData.email}
                                        onChange={e => setFormData({ ...formData, email: e.target.value })}
                                    />
                                </div>
                            </div>

                            <div>
                                <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase mb-1.5 ml-1">Password</label>
                                <div className="relative group">
                                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 group-focus-within:text-indigo-500 transition-colors" />
                                    <input
                                        type="password"
                                        required
                                        className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-10 py-3 text-slate-900 dark:text-white placeholder:text-slate-400 outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all font-medium"
                                        placeholder="••••••••"
                                        value={formData.password}
                                        onChange={e => setFormData({ ...formData, password: e.target.value })}
                                    />
                                </div>
                            </div>

                            <button
                                type="submit"
                                disabled={isLoading || isSuccess}
                                className={`w-full py-3.5 rounded-xl font-bold text-white shadow-lg shadow-indigo-500/20 hover:shadow-indigo-500/30 transition-all flex items-center justify-center gap-2 mt-6 ${isSuccess ? "bg-green-500" : "bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-700 hover:to-violet-700"}`}
                            >
                                {isLoading ? (
                                    <Loader2 className="w-5 h-5 animate-spin" />
                                ) : isSuccess ? (
                                    <><CheckCircle className="w-5 h-5" /> Success</>
                                ) : (
                                    <>{isLogin ? "Sign In" : "Create Account"} <ArrowRight className="w-4 h-4" /></>
                                )}
                            </button>
                        </form>

                        <div className="mt-8 relative">
                            <div className="absolute inset-0 flex items-center">
                                <div className="w-full border-t border-slate-200 dark:border-slate-700"></div>
                            </div>
                            <div className="relative flex justify-center text-xs uppercase">
                                <span className="bg-white dark:bg-slate-900 px-2 text-slate-500 font-medium tracking-wide">Or continue with</span>
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4 mt-6">
                            <button type="button" className="flex items-center justify-center gap-2 px-4 py-2.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-slate-700 dark:text-white font-semibold hover:bg-slate-50 dark:hover:bg-slate-700 transition-all text-sm">
                                <svg className="w-5 h-5" viewBox="0 0 24 24"><path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" /><path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" /><path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" /><path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" /></svg>
                                Google
                            </button>
                            <button type="button" className="flex items-center justify-center gap-2 px-4 py-2.5 bg-slate-900 border border-slate-900 dark:bg-white dark:border-white dark:text-slate-900 rounded-xl text-white font-semibold hover:bg-slate-800 dark:hover:bg-slate-100 transition-all text-sm">
                                <Github className="w-5 h-5" />
                                GitHub
                            </button>
                        </div>
                    </div>

                    <div className="p-4 bg-slate-50 dark:bg-slate-800/50 border-t border-slate-100 dark:border-slate-800 text-center transition-colors">
                        <p className="text-xs text-slate-500 dark:text-slate-400">
                            By continuing, you agree to our <a href="#" className="text-indigo-600 dark:text-indigo-400 hover:underline">Terms of Service</a> and <a href="#" className="text-indigo-600 dark:text-indigo-400 hover:underline">Privacy Policy</a>.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
