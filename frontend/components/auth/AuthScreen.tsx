"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion, useReducedMotion, type Variants } from "framer-motion";
import {
  ArrowRight, Github, Mail, Lock, User, Loader2, CheckCircle, Eye, EyeOff,
  Scale, Quote, AlertTriangle,
} from "lucide-react";
import { Logo } from "@/components/Logo";
import { ModeToggle } from "@/components/ModeToggle";

type Mode = "signup" | "signin";
type Social = "google" | "github";

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

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function passwordStrength(pw: string): { score: number; label: string; color: string } {
  let score = 0;
  if (pw.length >= 8) score++;
  if (/[a-z]/.test(pw) && /[A-Z]/.test(pw)) score++;
  if (/\d/.test(pw)) score++;
  if (/[^A-Za-z0-9]/.test(pw)) score++;
  const label = ["Too short", "Weak", "Fair", "Good", "Strong"][score];
  const color = ["bg-red-500", "bg-red-500", "bg-amber-500", "bg-emerald-500", "bg-emerald-500"][score];
  return { score, label, color };
}

export function AuthScreen({ mode }: { mode: Mode }) {
  const router = useRouter();
  const isLogin = mode === "signin";
  const copy = COPY[mode];
  const reduce = useReducedMotion();

  const [formData, setFormData] = useState({ name: "", email: "", password: "" });
  const [showPassword, setShowPassword] = useState(false);
  const [capsOn, setCapsOn] = useState(false);
  const [remember, setRemember] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [social, setSocial] = useState<Social | null>(null);

  useEffect(() => {
    if (localStorage.getItem("userProfile")) router.replace("/dashboard");
  }, [router]);

  const emailValid = EMAIL_RE.test(formData.email);
  const emailError = formData.email.length > 0 && !emailValid;
  const strength = passwordStrength(formData.password);
  const busy = isLoading || isSuccess || social !== null;

  const finishAuth = () => {
    const [firstName, ...rest] = (formData.name || "Demo Judge").split(" ");
    const existing = localStorage.getItem("userProfile");
    if (!isLogin || !existing) {
      localStorage.setItem("userProfile", JSON.stringify({
        firstName: firstName || "Demo", lastName: rest.join(" "),
        email: formData.email, role: "judge", plan: "Pro",
      }));
    }
    setIsSuccess(true);
    setTimeout(() => router.push("/dashboard"), 900);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    await new Promise((r) => setTimeout(r, 1100));
    setIsLoading(false);
    finishAuth();
  };

  const handleSocial = async (provider: Social) => {
    setSocial(provider);
    await new Promise((r) => setTimeout(r, 1100));
    setSocial(null);
    finishAuth();
  };

  // Staggered entrance (respects reduced motion).
  const container: Variants = { hidden: {}, show: { transition: { staggerChildren: reduce ? 0 : 0.08, delayChildren: reduce ? 0 : 0.05 } } };
  const item: Variants = reduce
    ? { hidden: { opacity: 1 }, show: { opacity: 1 } }
    : { hidden: { opacity: 0, y: 12 }, show: { opacity: 1, y: 0, transition: { duration: 0.4 } } };
  const formV: Variants = reduce
    ? { hidden: { opacity: 1 }, show: { opacity: 1 } }
    : { hidden: { opacity: 0, y: 12 }, show: { opacity: 1, y: 0, transition: { when: "beforeChildren", staggerChildren: 0.07 } } };

  const inputBase = "w-full rounded-xl border bg-white px-10 py-3 font-medium text-slate-900 outline-none transition focus:ring-2 dark:bg-white/5 dark:text-white";

  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      {/* Branded panel (left) */}
      <aside className="relative hidden overflow-hidden p-12 text-white lg:flex lg:flex-col lg:justify-between bg-[linear-gradient(145deg,#064e3b_0%,#0f766e_34%,#155e75_66%,#0b1220_100%)]">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(55%_45%_at_12%_8%,rgba(52,211,153,0.40),transparent_60%),radial-gradient(50%_40%_at_92%_12%,rgba(56,189,248,0.22),transparent_60%),radial-gradient(55%_50%_at_82%_100%,rgba(224,169,46,0.18),transparent_60%)]" />
        <div className="pointer-events-none absolute inset-0 opacity-[0.06]" style={{ backgroundImage: "linear-gradient(to right, #fff 1px, transparent 1px), linear-gradient(to bottom, #fff 1px, transparent 1px)", backgroundSize: "40px 40px" }} />
        <div className="pointer-events-none absolute -left-24 top-1/3 h-72 w-72 rounded-full bg-emerald-400/20 blur-3xl" />
        <div className="pointer-events-none absolute -right-16 bottom-10 h-64 w-64 rounded-full bg-gold-500/20 blur-3xl" />
        <div className="relative">
          <Link href="/" className="inline-flex items-center gap-3">
            <Logo className="h-9 w-9" showText={false} />
            <span className="text-xl font-bold tracking-tight">GradeWise</span>
          </Link>
        </div>
        <div className="relative">
          <h2 className="font-display text-4xl font-semibold leading-tight">Judge the field.<br />Defend the shortlist.</h2>
          <ul className="mt-8 space-y-3 text-slate-300">
            {["Every point cited to the plan", "Graded 5× for a real confidence", "A shortlist your panel can stand behind"].map((t) => (
              <li key={t} className="flex items-center gap-3"><CheckCircle className="h-5 w-5 text-emerald-400" /> {t}</li>
            ))}
          </ul>
          <figure className="mt-10 max-w-md rounded-2xl border border-white/10 bg-white/[0.04] p-6">
            <Quote className="h-5 w-5 text-gold-400" />
            <blockquote className="mt-3 text-sm leading-relaxed text-slate-200">For the first time the shortlist held up under questioning. Every score pointed to a line in the plan.</blockquote>
            <figcaption className="mt-4 text-sm"><span className="font-semibold text-white">Amara Okonkwo</span><span className="text-slate-400"> · Lead Judge</span></figcaption>
          </figure>
        </div>
        <div className="relative inline-flex items-center gap-2 text-xs text-slate-400"><Scale className="h-4 w-4 text-emerald-400" /> Calibrated against your human panel</div>
      </aside>

      {/* Form (right) */}
      <main className="relative flex items-center justify-center overflow-hidden bg-background px-6 py-12">
        {/* hairline top accent */}
        <div className="absolute inset-x-0 top-0 h-0.5 bg-gradient-to-r from-emerald-500 via-blue-500 to-emerald-500" />
        {/* ambient aurora blobs + corner glow */}
        <motion.div aria-hidden className="pointer-events-none absolute -right-20 -top-24 h-80 w-80 rounded-full bg-emerald-400/25 blur-3xl dark:bg-emerald-500/15"
          animate={reduce ? undefined : { x: [0, 22, 0], y: [0, 18, 0] }} transition={{ duration: 15, repeat: Infinity, ease: "easeInOut" }} />
        <motion.div aria-hidden className="pointer-events-none absolute -bottom-24 -left-20 h-72 w-72 rounded-full bg-blue-400/20 blur-3xl dark:bg-blue-500/12"
          animate={reduce ? undefined : { x: [0, -18, 0], y: [0, -16, 0] }} transition={{ duration: 18, repeat: Infinity, ease: "easeInOut" }} />
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(40%_35%_at_92%_8%,rgba(16,185,129,0.10),transparent_60%)]" />
        {/* faint brand watermark */}
        <svg aria-hidden viewBox="0 0 100 100" className="pointer-events-none absolute left-1/2 top-1/2 h-[460px] w-[460px] -translate-x-1/2 -translate-y-1/2 text-emerald-500/[0.05] dark:text-emerald-400/[0.05]">
          <path d="M32 50 L50 58 L68 50 L68 66 C68 72 60 75.5 50 75.5 C40 75.5 32 72 32 66 Z" fill="currentColor" />
          <path d="M50 20 L94 40 L50 60 L6 40 Z" fill="currentColor" />
        </svg>

        <div className="absolute right-4 top-4 z-20"><ModeToggle /></div>

        <motion.div variants={container} initial="hidden" animate="show" className="relative z-10 w-full max-w-sm">
          {/* mobile logo */}
          <motion.div variants={item}>
            <Link href="/" className="mb-8 inline-flex items-center gap-2 lg:hidden">
              <Logo className="h-8 w-8" showText={false} />
              <span className="text-lg font-bold text-ink-900 dark:text-white">GradeWise</span>
            </Link>
          </motion.div>

          <motion.h1 variants={item} className="bg-gradient-to-r from-emerald-600 to-blue-600 bg-clip-text font-display text-3xl font-semibold text-transparent dark:from-emerald-400 dark:to-blue-400">
            {copy.title}
          </motion.h1>
          <motion.p variants={item} className="mt-2 text-sm text-slate-500 dark:text-slate-400">{copy.sub}</motion.p>

          {/* social */}
          <motion.div variants={item} className="mt-8 grid grid-cols-2 gap-3">
            <button type="button" onClick={() => handleSocial("google")} disabled={busy}
              className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50 disabled:opacity-60 dark:border-white/10 dark:bg-white/5 dark:text-slate-200 dark:hover:bg-white/10">
              {social === "google" ? <Loader2 className="h-4 w-4 animate-spin" /> : (
                <svg className="h-4 w-4" viewBox="0 0 24 24"><path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" /><path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" /><path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93z" fill="#FBBC05" /><path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" /></svg>
              )}
              Google
            </button>
            <button type="button" onClick={() => handleSocial("github")} disabled={busy}
              className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50 disabled:opacity-60 dark:border-white/10 dark:bg-white/5 dark:text-slate-200 dark:hover:bg-white/10">
              {social === "github" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Github className="h-4 w-4" />} GitHub
            </button>
          </motion.div>

          {/* shimmer divider */}
          <motion.div variants={item} className="relative my-6 flex items-center justify-center">
            <span className="absolute inset-x-0 top-1/2 h-px -translate-y-1/2 bg-gradient-to-r from-transparent via-slate-200 to-transparent dark:via-white/10" />
            {!reduce && (
              <motion.span className="absolute top-1/2 h-px w-24 -translate-y-1/2 bg-gradient-to-r from-transparent via-emerald-400/70 to-transparent"
                animate={{ left: ["-15%", "115%"] }} transition={{ duration: 3.6, repeat: Infinity, ease: "easeInOut" }} />
            )}
            <span className="relative bg-background px-3 text-xs text-slate-400">or with email</span>
          </motion.div>

          <motion.form variants={formV} onSubmit={handleSubmit} className="space-y-4">
            {!isLogin && (
              <motion.div variants={item}>
                <label className="mb-1.5 ml-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">Full name</label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" />
                  <input type="text" required placeholder="Amara Okonkwo" value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className={inputBase + " border-slate-200 focus:border-emerald-500 focus:ring-emerald-500/20 dark:border-white/10"} />
                </div>
              </motion.div>
            )}

            {/* email + inline validation */}
            <motion.div variants={item}>
              <label className="mb-1.5 ml-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">Email</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" />
                <input type="email" required placeholder="you@competition.org" value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className={inputBase + " " + (emailError
                    ? "border-red-400 focus:border-red-500 focus:ring-red-500/20"
                    : "border-slate-200 focus:border-emerald-500 focus:ring-emerald-500/20 dark:border-white/10")} />
                {emailValid && <CheckCircle className="absolute right-3 top-1/2 h-5 w-5 -translate-y-1/2 text-emerald-500" />}
              </div>
              {emailError && <p className="mt-1 ml-1 text-xs text-red-500">Enter a valid email address.</p>}
            </motion.div>

            {/* password + caps-lock warning + strength */}
            <motion.div variants={item}>
              <label className="mb-1.5 ml-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" />
                <input type={showPassword ? "text" : "password"} required placeholder="••••••••" value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  onKeyUp={(e) => setCapsOn(e.getModifierState("CapsLock"))}
                  onKeyDown={(e) => setCapsOn(e.getModifierState("CapsLock"))}
                  className={inputBase + " border-slate-200 focus:border-emerald-500 focus:ring-emerald-500/20 dark:border-white/10"} />
                <button type="button" onClick={() => setShowPassword((s) => !s)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                  aria-label={showPassword ? "Hide password" : "Show password"}>
                  {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                </button>
              </div>
              {capsOn && (
                <p className="mt-1 ml-1 flex items-center gap-1 text-xs text-amber-600 dark:text-amber-400">
                  <AlertTriangle className="h-3.5 w-3.5" /> Caps Lock is on
                </p>
              )}
              {!isLogin && formData.password.length > 0 && (
                <div className="mt-2">
                  <div className="flex gap-1">
                    {[0, 1, 2, 3].map((i) => (
                      <span key={i} className={"h-1 flex-1 rounded-full transition-colors " + (i < strength.score ? strength.color : "bg-slate-200 dark:bg-white/10")} />
                    ))}
                  </div>
                  <p className="mt-1 text-xs text-slate-400">Password strength: {strength.label}</p>
                </div>
              )}
            </motion.div>

            {/* remember me + forgot (sign-in) */}
            {isLogin && (
              <motion.div variants={item} className="flex items-center justify-between">
                <label className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-300">
                  <input type="checkbox" checked={remember} onChange={(e) => setRemember(e.target.checked)}
                    className="h-4 w-4 rounded border-slate-300 text-emerald-600 focus:ring-emerald-500 dark:border-white/20 dark:bg-white/5" />
                  Remember me
                </label>
                <a href="#" className="text-xs font-medium text-emerald-700 hover:underline dark:text-emerald-400">Forgot password?</a>
              </motion.div>
            )}

            <motion.button variants={item} type="submit" disabled={busy} whileTap={{ scale: 0.99 }}
              className={"mt-2 flex w-full items-center justify-center gap-2 rounded-xl py-3.5 font-semibold text-white shadow-lg shadow-emerald-500/30 transition disabled:opacity-90 " +
                (isSuccess ? "bg-emerald-500" : "bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500")}>
              {isLoading ? <Loader2 className="h-5 w-5 animate-spin" />
                : isSuccess ? <><CheckCircle className="h-5 w-5" /> Success</>
                : <>{copy.cta} <ArrowRight className="h-4 w-4" /></>}
            </motion.button>
          </motion.form>

          <motion.p variants={item} className="mt-6 text-center text-sm text-slate-500 dark:text-slate-400">
            {copy.alt}{" "}
            <Link href={copy.altHref} className="font-semibold text-emerald-700 hover:underline dark:text-emerald-400">{copy.altLabel}</Link>
          </motion.p>
        </motion.div>
      </main>
    </div>
  );
}
