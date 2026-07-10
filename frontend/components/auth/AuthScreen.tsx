"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { ArrowRight, Github, Mail, Lock, User, Loader2, CheckCircle, Eye, EyeOff, Scale, Quote } from "lucide-react";
import { Logo } from "@/components/Logo";
import { ModeToggle } from "@/components/ModeToggle";

type Mode = "signup" | "signin";

const COPY: Record<Mode, { title: string; sub: string; cta: string; alt: string; altHref: string; altLabel: string }> = {
  signup: {
    title: "Create your judging workspace",
    sub: "Set a rubric, upload the field, and start scoring in minutes.",
    cta: "Create account",
    alt: "Already judging with GradeWise?",
    altHref: "/signin",
    altLabel: "Sign in",
  },
  signin: {
    title: "Welcome back",
    sub: "Pick up where your panel left off.",
    cta: "Sign in",
    alt: "New to GradeWise?",
    altHref: "/signup",
    altLabel: "Create an account",
  },
};

export function AuthScreen({ mode }: { mode: Mode }) {
  const router = useRouter();
  const isLogin = mode === "signin";
  const copy = COPY[mode];

  const [formData, setFormData] = useState({ name: "", email: "", password: "" });
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  // If already "signed in" (localStorage mock), go straight to the dashboard.
  useEffect(() => {
    if (localStorage.getItem("userProfile")) router.replace("/dashboard");
  }, [router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    await new Promise((r) => setTimeout(r, 1200)); // mock auth

    const [firstName, ...rest] = (formData.name || "Demo Judge").split(" ");
    const existing = localStorage.getItem("userProfile");
    if (!isLogin || !existing) {
      localStorage.setItem("userProfile", JSON.stringify({
        firstName: firstName || "Demo",
        lastName: rest.join(" "),
        email: formData.email,
        role: "judge",
        plan: "Pro",
      }));
    }
    setIsLoading(false);
    setIsSuccess(true);
    setTimeout(() => router.push("/dashboard"), 900);
  };

  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      {/* Branded panel */}
      <aside className="relative hidden overflow-hidden p-12 text-white lg:flex lg:flex-col lg:justify-between bg-[linear-gradient(135deg,#065f46_0%,#0f766e_32%,#1d4ed8_68%,#0b1220_100%)]">
        {/* colorful glows for depth */}
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(60%_45%_at_15%_5%,rgba(52,211,153,0.45),transparent_60%),radial-gradient(55%_45%_at_95%_15%,rgba(56,189,248,0.30),transparent_60%),radial-gradient(60%_50%_at_80%_100%,rgba(224,169,46,0.22),transparent_60%)]" />
        <div className="pointer-events-none absolute -left-24 top-1/3 h-72 w-72 rounded-full bg-emerald-400/20 blur-3xl" />
        <div className="pointer-events-none absolute -right-16 bottom-10 h-64 w-64 rounded-full bg-gold-500/20 blur-3xl" />
        <div className="relative">
          <Link href="/" className="inline-flex items-center gap-3">
            <Logo className="h-9 w-9" showText={false} />
            <span className="text-xl font-bold tracking-tight">GradeWise</span>
          </Link>
        </div>

        <div className="relative">
          <h2 className="font-display text-4xl font-semibold leading-tight">
            Judge the field.<br />Defend the shortlist.
          </h2>
          <ul className="mt-8 space-y-3 text-slate-300">
            {["Every point cited to the plan", "Graded 5× for a real confidence", "A shortlist your panel can stand behind"].map((t) => (
              <li key={t} className="flex items-center gap-3">
                <CheckCircle className="h-5 w-5 text-emerald-400" /> {t}
              </li>
            ))}
          </ul>

          <figure className="mt-10 max-w-md rounded-2xl border border-white/10 bg-white/[0.04] p-6">
            <Quote className="h-5 w-5 text-gold-400" />
            <blockquote className="mt-3 text-sm leading-relaxed text-slate-200">
              For the first time the shortlist held up under questioning. Every score pointed to a line in the plan.
            </blockquote>
            <figcaption className="mt-4 text-sm">
              <span className="font-semibold text-white">Amara Okonkwo</span>
              <span className="text-slate-400"> · Lead Judge</span>
            </figcaption>
          </figure>
        </div>

        <div className="relative inline-flex items-center gap-2 text-xs text-slate-400">
          <Scale className="h-4 w-4 text-emerald-400" /> Calibrated against your human panel
        </div>
      </aside>

      {/* Form */}
      <main className="relative flex items-center justify-center bg-background px-6 py-12">
        <div className="absolute right-4 top-4"><ModeToggle /></div>

        <div className="w-full max-w-sm">
          {/* mobile logo */}
          <Link href="/" className="mb-8 inline-flex items-center gap-2 lg:hidden">
            <Logo className="h-8 w-8" showText={false} />
            <span className="text-lg font-bold text-ink-900 dark:text-white">GradeWise</span>
          </Link>

          <h1 className="font-display text-3xl font-semibold text-ink-900 dark:text-white">{copy.title}</h1>
          <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">{copy.sub}</p>

          {/* social */}
          <div className="mt-8 grid grid-cols-2 gap-3">
            <button type="button" className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50 dark:border-white/10 dark:bg-white/5 dark:text-slate-200 dark:hover:bg-white/10">
              <svg className="h-4 w-4" viewBox="0 0 24 24"><path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" /><path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" /><path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93z" fill="#FBBC05" /><path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" /></svg>
              Google
            </button>
            <button type="button" className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50 dark:border-white/10 dark:bg-white/5 dark:text-slate-200 dark:hover:bg-white/10">
              <Github className="h-4 w-4" /> GitHub
            </button>
          </div>

          <div className="my-6 flex items-center gap-3 text-xs text-slate-400">
            <span className="h-px flex-1 bg-slate-200 dark:bg-white/10" /> or with email <span className="h-px flex-1 bg-slate-200 dark:bg-white/10" />
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {!isLogin && (
              <Field icon={User} label="Full name" type="text" placeholder="Amara Okonkwo"
                value={formData.name} onChange={(v) => setFormData({ ...formData, name: v })} required />
            )}
            <Field icon={Mail} label="Email" type="email" placeholder="you@competition.org"
              value={formData.email} onChange={(v) => setFormData({ ...formData, email: v })} required />
            <div>
              <label className="mb-1.5 ml-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" />
                <input
                  type={showPassword ? "text" : "password"} required placeholder="••••••••"
                  value={formData.password} onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  className="w-full rounded-xl border border-slate-200 bg-white px-10 py-3 font-medium text-slate-900 outline-none transition focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 dark:border-white/10 dark:bg-white/5 dark:text-white"
                />
                <button type="button" onClick={() => setShowPassword((s) => !s)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200" aria-label={showPassword ? "Hide password" : "Show password"}>
                  {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                </button>
              </div>
            </div>

            {isLogin && (
              <div className="text-right">
                <a href="#" className="text-xs font-medium text-emerald-700 hover:underline dark:text-emerald-400">Forgot password?</a>
              </div>
            )}

            <motion.button
              type="submit" disabled={isLoading || isSuccess} whileTap={{ scale: 0.99 }}
              className={"mt-2 flex w-full items-center justify-center gap-2 rounded-xl py-3.5 font-semibold text-white shadow-lg shadow-emerald-600/20 transition " +
                (isSuccess ? "bg-emerald-500" : "bg-emerald-600 hover:bg-emerald-700")}
            >
              {isLoading ? <Loader2 className="h-5 w-5 animate-spin" />
                : isSuccess ? <><CheckCircle className="h-5 w-5" /> Success</>
                : <>{copy.cta} <ArrowRight className="h-4 w-4" /></>}
            </motion.button>
          </form>

          <p className="mt-6 text-center text-sm text-slate-500 dark:text-slate-400">
            {copy.alt}{" "}
            <Link href={copy.altHref} className="font-semibold text-emerald-700 hover:underline dark:text-emerald-400">{copy.altLabel}</Link>
          </p>
        </div>
      </main>
    </div>
  );
}

function Field({
  icon: Icon, label, type, placeholder, value, onChange, required,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string; type: string; placeholder: string; value: string;
  onChange: (v: string) => void; required?: boolean;
}) {
  return (
    <div>
      <label className="mb-1.5 ml-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</label>
      <div className="relative">
        <Icon className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" />
        <input
          type={type} required={required} placeholder={placeholder} value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-full rounded-xl border border-slate-200 bg-white px-10 py-3 font-medium text-slate-900 outline-none transition focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 dark:border-white/10 dark:bg-white/5 dark:text-white"
        />
      </div>
    </div>
  );
}
