"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import {
  ArrowRight, Check, Quote, Scale, Trophy, ShieldCheck, Images, Clapperboard,
  Sparkles, FileSpreadsheet, Gavel,
} from "lucide-react";
import { ModeToggle } from "@/components/ModeToggle";
import { Logo } from "@/components/Logo";

const FEATURES = [
  {
    icon: Clapperboard,
    title: "Live Grading Theater",
    body: "Watch the real pipeline judge each plan, stage by stage — screening, reading, the second-opinion re-score, the verdict. Not a spinner: the actual work, streamed.",
  },
  {
    icon: Quote,
    title: "Evidence-linked scoring",
    body: "Every point is cited to the exact passage in the plan. A quote that isn't in the submission is rejected, so a score is never hand-wavy — and disputes are resolvable.",
  },
  {
    icon: Scale,
    title: "Real calibration & confidence",
    body: "Each plan is graded several times and the spread becomes an honest confidence — measured against your human panel's own agreement, never a number we invented.",
  },
  {
    icon: Trophy,
    title: "Defensible leaderboard",
    body: "Rank the whole field with a tie band at the shortlist cutoff, so a sub-point gap inside the noise never decides a prize. Flagged plans go to a review queue, not the bin.",
  },
  {
    icon: ShieldCheck,
    title: "Fairness & integrity",
    body: "Eligibility and AI-content screening on every submission, plus disparate-impact checks across language and region — surfaced to a human, never an automatic disqualification.",
  },
  {
    icon: Images,
    title: "Reads the whole plan",
    body: "Text, slides, and the figures inside images — financial tables, licences, bank letters. Parses your rubric straight from CSV, PDF, or DOCX.",
  },
];

const STAGES = [
  { n: "01", title: "Screen the gate", body: "Eligibility, disqualifiers, and AI-content flags before a plan is ever ranked." },
  { n: "02", title: "Read the plan", body: "Score each rubric criterion on the evidence actually present — no credit for a heading with nothing under it." },
  { n: "03", title: "Second opinion", body: "A Judge checks the grade for consistency and completeness, and sends it back to re-score if it's off." },
  { n: "04", title: "Coach the team", body: "Specific, encouraging feedback written to the founders in plain language." },
  { n: "05", title: "Verdict", body: "A defensible score plus a pinned grade-of-record — the exact inputs, re-derivable in an appeal." },
];

const VOICES = [
  {
    quote: "For the first time the shortlist held up under questioning. Every score pointed to a line in the plan — the panel debated substance, not the tool.",
    name: "Amara Okonkwo",
    role: "Lead Judge · Africa Business Plan Competition",
  },
  {
    quote: "We screened three hundred plans in an afternoon and still hand-reviewed every flagged one. The tie band at the cutoff saved us a genuinely unfair call.",
    name: "Kwabena Mensah",
    role: "Programme Director",
  },
  {
    quote: "The feedback was specific and kind. Finalists felt judged fairly even when they didn't advance — that's rare.",
    name: "Zainab Bello",
    role: "Mentor & Past Finalist",
  },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Nav */}
      <nav className="fixed inset-x-0 top-0 z-50 border-b border-black/5 bg-background/80 backdrop-blur-md dark:border-white/10">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <Logo className="h-9 w-9" />
          <div className="hidden items-center gap-8 text-sm font-medium text-slate-600 dark:text-slate-300 md:flex">
            <a href="#features" className="hover:text-emerald-700 dark:hover:text-emerald-400">Features</a>
            <a href="#how" className="hover:text-emerald-700 dark:hover:text-emerald-400">How it works</a>
            <a href="#judges" className="hover:text-emerald-700 dark:hover:text-emerald-400">For judges</a>
          </div>
          <div className="flex items-center gap-3">
            <ModeToggle />
            <Link href="/signin" className="text-sm font-medium text-slate-600 hover:text-emerald-700 dark:text-slate-300 dark:hover:text-emerald-400">
              Sign in
            </Link>
            <Link href="/signup" className="rounded-full bg-emerald-600 px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-emerald-600/20 transition hover:bg-emerald-700">
              Get started
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative overflow-hidden pt-32 pb-24">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(60%_50%_at_70%_0%,rgba(16,185,129,0.10),transparent_60%),radial-gradient(40%_40%_at_10%_10%,rgba(224,169,46,0.08),transparent_55%)]" />
        <div className="mx-auto grid max-w-7xl grid-cols-1 items-center gap-14 px-4 sm:px-6 lg:grid-cols-2 lg:px-8">
          <div>
            <motion.span
              initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}
              className="inline-flex items-center gap-2 rounded-full border border-gold-500/30 bg-gold-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-gold-600 dark:text-gold-400"
            >
              <Gavel className="h-3.5 w-3.5" /> Built for business-plan competitions
            </motion.span>
            <motion.h1
              initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.05 }}
              className="font-display mt-6 text-5xl font-semibold leading-[1.05] tracking-tight text-ink-900 dark:text-white md:text-6xl"
            >
              Judge every plan like your <span className="text-emerald-600 dark:text-emerald-400">fairest human judge</span> — at the scale of the whole field.
            </motion.h1>
            <motion.p
              initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.1 }}
              className="mt-6 max-w-xl text-lg leading-relaxed text-slate-600 dark:text-slate-300"
            >
              GradeWise screens, scores, and ranks hundreds of business plans against your rubric.
              Every point is cited to the plan, graded several times for a real confidence, and
              calibrated against your own judges — with a shortlist you can defend.
            </motion.p>
            <motion.div
              initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.15 }}
              className="mt-9 flex flex-col gap-3 sm:flex-row"
            >
              <Link href="/signup" className="group inline-flex items-center justify-center gap-2 rounded-full bg-emerald-600 px-7 py-3.5 font-semibold text-white shadow-xl shadow-emerald-600/20 transition hover:bg-emerald-700">
                Start judging <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
              </Link>
              <Link href="/theater-preview" className="inline-flex items-center justify-center gap-2 rounded-full border border-slate-300 px-7 py-3.5 font-semibold text-slate-700 transition hover:border-emerald-500 hover:text-emerald-700 dark:border-slate-700 dark:text-slate-200 dark:hover:text-emerald-400">
                <Sparkles className="h-4 w-4" /> Watch it grade
              </Link>
            </motion.div>
            <div className="mt-8 flex flex-wrap gap-x-6 gap-y-2 text-sm text-slate-500 dark:text-slate-400">
              {["Every point cited to the plan", "Graded 5× for real confidence", "A shortlist you can defend"].map((t) => (
                <span key={t} className="inline-flex items-center gap-2"><Check className="h-4 w-4 text-emerald-500" />{t}</span>
              ))}
            </div>
          </div>

          {/* Signature: a live judge scorecard */}
          <ScorecardHero />
        </div>
      </section>

      {/* Capability strip */}
      <section className="border-y border-black/5 bg-white/60 py-10 dark:border-white/10 dark:bg-white/[0.02]">
        <div className="mx-auto grid max-w-7xl grid-cols-2 gap-6 px-4 sm:px-6 md:grid-cols-4 lg:px-8">
          {[
            { k: "Every point", v: "cited" },
            { k: "Graded", v: "5× / plan" },
            { k: "Rubric in", v: "CSV·PDF·DOCX" },
            { k: "Reads", v: "slides + figures" },
          ].map((s) => (
            <div key={s.k} className="text-center">
              <div className="font-display text-2xl font-semibold text-ink-900 dark:text-white">{s.v}</div>
              <div className="mt-1 text-xs font-medium uppercase tracking-wide text-slate-500">{s.k}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-24">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="max-w-2xl">
            <h2 className="font-display text-4xl font-semibold tracking-tight text-ink-900 dark:text-white">A judge that shows its work</h2>
            <p className="mt-4 text-lg text-slate-600 dark:text-slate-300">Everything a competition needs to score a field quickly and defend the result afterwards.</p>
          </div>
          <div className="mt-14 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map((f, i) => (
              <motion.div
                key={f.title}
                initial={{ opacity: 0, y: 18 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, margin: "-60px" }}
                transition={{ duration: 0.4, delay: (i % 3) * 0.06 }}
                className="rounded-2xl border border-black/5 bg-white p-7 shadow-sm transition hover:shadow-lg hover:shadow-emerald-900/5 dark:border-white/10 dark:bg-white/[0.03]"
              >
                <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-emerald-600/10 text-emerald-700 dark:text-emerald-400">
                  <f.icon className="h-5 w-5" />
                </div>
                <h3 className="mt-5 text-lg font-semibold text-ink-900 dark:text-white">{f.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-slate-600 dark:text-slate-400">{f.body}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* How it works — the real pipeline, a genuine sequence */}
      <section id="how" className="border-y border-black/5 bg-white/60 py-24 dark:border-white/10 dark:bg-white/[0.02]">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="max-w-2xl">
            <h2 className="font-display text-4xl font-semibold tracking-tight text-ink-900 dark:text-white">Five stages, out loud</h2>
            <p className="mt-4 text-lg text-slate-600 dark:text-slate-300">The same pipeline you watch in the Grading Theater. Each plan moves through it in order.</p>
          </div>
          <ol className="mt-14 grid gap-6 md:grid-cols-5">
            {STAGES.map((s) => (
              <li key={s.n} className="relative rounded-2xl border border-black/5 bg-white p-6 dark:border-white/10 dark:bg-white/[0.03]">
                <span className="font-display text-3xl font-semibold text-emerald-600/30 dark:text-emerald-400/30">{s.n}</span>
                <h3 className="mt-3 font-semibold text-ink-900 dark:text-white">{s.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-slate-600 dark:text-slate-400">{s.body}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      {/* For judges — leaderboard mock */}
      <section id="judges" className="py-24">
        <div className="mx-auto grid max-w-7xl items-center gap-14 px-4 sm:px-6 lg:grid-cols-2 lg:px-8">
          <div>
            <span className="inline-flex items-center gap-2 rounded-full bg-emerald-600/10 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-emerald-700 dark:text-emerald-400">For judges</span>
            <h2 className="font-display mt-5 text-4xl font-semibold tracking-tight text-ink-900 dark:text-white">Screen the field. Defend the shortlist.</h2>
            <p className="mt-4 text-lg leading-relaxed text-slate-600 dark:text-slate-300">
              Grade the whole competition in one run and watch the ranking form live. Plans clustered
              at the cutoff are flagged as a statistical tie for a human to break; ineligible or
              AI-flagged plans go to a review queue. Export a committee-ready report when you're done.
            </p>
            <ul className="mt-6 space-y-3 text-slate-700 dark:text-slate-300">
              {["Animated leaderboard with a moving shortlist line", "Tie band so noise never decides a prize", "Needs-review queue for flagged plans", "One-click committee report pack"].map((t) => (
                <li key={t} className="flex items-center gap-3"><Check className="h-5 w-5 shrink-0 text-emerald-500" />{t}</li>
              ))}
            </ul>
          </div>
          <LeaderboardMock />
        </div>
      </section>

      {/* Voices */}
      <section className="bg-ink-950 py-24 text-white">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <h2 className="font-display max-w-2xl text-4xl font-semibold tracking-tight">Trusted with the hard calls</h2>
          <div className="mt-14 grid gap-6 md:grid-cols-3">
            {VOICES.map((v) => (
              <figure key={v.name} className="flex flex-col rounded-2xl border border-white/10 bg-white/[0.04] p-7">
                <Quote className="h-6 w-6 text-gold-400" />
                <blockquote className="mt-4 flex-1 text-[15px] leading-relaxed text-slate-200">{v.quote}</blockquote>
                <figcaption className="mt-6">
                  <div className="font-semibold text-white">{v.name}</div>
                  <div className="text-sm text-slate-400">{v.role}</div>
                </figcaption>
              </figure>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24">
        <div className="mx-auto max-w-4xl px-4 text-center sm:px-6 lg:px-8">
          <h2 className="font-display text-4xl font-semibold tracking-tight text-ink-900 dark:text-white md:text-5xl">Run your next competition on evidence.</h2>
          <p className="mx-auto mt-5 max-w-xl text-lg text-slate-600 dark:text-slate-300">Set your rubric, upload the field, and let GradeWise do the first pass — while your judges keep the final word.</p>
          <div className="mt-9 flex flex-col justify-center gap-3 sm:flex-row">
            <Link href="/signup" className="group inline-flex items-center justify-center gap-2 rounded-full bg-emerald-600 px-8 py-4 font-semibold text-white shadow-xl shadow-emerald-600/20 transition hover:bg-emerald-700">
              Create your judging workspace <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
            </Link>
            <Link href="/theater-preview" className="inline-flex items-center justify-center gap-2 rounded-full border border-slate-300 px-8 py-4 font-semibold text-slate-700 transition hover:border-emerald-500 hover:text-emerald-700 dark:border-slate-700 dark:text-slate-200">
              Watch a plan get graded
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-black/5 bg-white/60 pt-16 pb-8 dark:border-white/10 dark:bg-white/[0.02]">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="grid gap-12 md:grid-cols-4">
            <div className="md:col-span-2">
              <Logo className="h-8 w-8" textClassName="ml-2 text-xl font-bold text-ink-900 dark:text-white" />
              <p className="mt-4 max-w-sm text-slate-500 dark:text-slate-400">An AI judge for business-plan competitions — evidence-linked scores, real calibration, and a shortlist your panel can stand behind.</p>
            </div>
            <div>
              <h4 className="font-semibold text-ink-900 dark:text-white">Product</h4>
              <ul className="mt-4 space-y-2 text-sm text-slate-500 dark:text-slate-400">
                <li><a href="#features" className="hover:text-emerald-700 dark:hover:text-emerald-400">Features</a></li>
                <li><a href="#how" className="hover:text-emerald-700 dark:hover:text-emerald-400">How it works</a></li>
                <li><Link href="/theater-preview" className="hover:text-emerald-700 dark:hover:text-emerald-400">Grading Theater</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-ink-900 dark:text-white">Contact</h4>
              <ul className="mt-4 space-y-3 text-sm text-slate-500 dark:text-slate-400">
                <li>
                  <div className="font-medium text-slate-700 dark:text-slate-300">Praise Enato</div>
                  <a href="mailto:praisenato@gmail.com" className="hover:text-emerald-700 dark:hover:text-emerald-400">praisenato@gmail.com</a>
                </li>
                <li>
                  <div className="font-medium text-slate-700 dark:text-slate-300">Felix Gbedemah</div>
                  <a href="mailto:afrogbede09@gmail.com" className="hover:text-emerald-700 dark:hover:text-emerald-400">afrogbede09@gmail.com</a>
                </li>
              </ul>
            </div>
          </div>
          <div className="mt-12 flex flex-col items-center justify-between gap-2 border-t border-black/5 pt-8 text-sm text-slate-400 dark:border-white/10 md:flex-row">
            <p>© 2026 GradeWise. All rights reserved.</p>
            <p>Judge the field. Defend the shortlist.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}

// --- Signature hero: a judge scorecard scoring a plan --------------------- //
function ScorecardHero() {
  const rows = [
    { name: "Problem & pain", score: 8, max: 8 },
    { name: "Market sizing", score: 6, max: 8, evidence: "“2.3 million smallholder farmers in the northern corridor…”" },
    { name: "Financials", score: 4, max: 6 },
    { name: "Team", score: 5, max: 6 },
  ];
  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.1 }}
      className="relative"
    >
      <div className="absolute -inset-6 -z-10 rounded-[2rem] bg-gradient-to-tr from-emerald-500/10 to-gold-500/10 blur-2xl" />
      <div className="rounded-2xl border border-black/5 bg-white shadow-2xl shadow-ink-950/10 dark:border-white/10 dark:bg-ink-900">
        <div className="flex items-center justify-between border-b border-black/5 px-6 py-4 dark:border-white/10">
          <div>
            <div className="text-sm font-semibold text-ink-900 dark:text-white">AgriConnect — Business Plan</div>
            <div className="text-xs text-slate-500">Scored against the 80-pt rubric</div>
          </div>
          <span className="rounded-full bg-emerald-600/10 px-2.5 py-1 text-xs font-semibold text-emerald-700 dark:text-emerald-400">Eligible</span>
        </div>
        <div className="space-y-4 px-6 py-5">
          {rows.map((r, i) => (
            <div key={r.name}>
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-700 dark:text-slate-200">{r.name}</span>
                <span className="font-semibold tabular-nums text-ink-900 dark:text-white">{r.score}/{r.max}</span>
              </div>
              <div className="mt-1.5 h-2 overflow-hidden rounded-full bg-slate-100 dark:bg-white/10">
                <motion.div
                  className="h-full rounded-full bg-emerald-500"
                  initial={{ width: 0 }} animate={{ width: `${(r.score / r.max) * 100}%` }}
                  transition={{ duration: 0.7, delay: 0.3 + i * 0.12, ease: "easeOut" }}
                />
              </div>
              {r.evidence && (
                <motion.p
                  initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.1 }}
                  className="mt-2 rounded-lg border-l-2 border-gold-500 bg-gold-500/5 px-3 py-2 text-xs italic text-slate-600 dark:text-slate-300"
                >
                  {r.evidence}
                </motion.p>
              )}
            </div>
          ))}
        </div>
        <div className="flex items-center justify-between border-t border-black/5 px-6 py-4 dark:border-white/10">
          <span className="inline-flex items-center gap-2 text-xs font-medium text-slate-500">
            <Scale className="h-4 w-4 text-emerald-500" /> Agrees with the human panel · graded 5×
          </span>
          <span className="font-display text-2xl font-semibold text-ink-900 dark:text-white tabular-nums">71<span className="text-base text-slate-400">/80</span></span>
        </div>
      </div>
    </motion.div>
  );
}

// --- For-judges: a leaderboard with a tie zone at the cutoff -------------- //
function LeaderboardMock() {
  const rows = [
    { rank: 1, team: "Okavango Solar", score: 88 },
    { rank: 2, team: "MamaMarket", score: 82 },
    { rank: 3, team: "AgriConnect", score: 71, tie: true },
    { rank: 4, team: "ClinicLink", score: 70.5, tie: true },
    { rank: 5, team: "PayGrid", score: 63, flagged: true },
  ];
  return (
    <div className="relative">
      <div className="absolute -inset-6 -z-10 rounded-[2rem] bg-gradient-to-tl from-gold-500/10 to-emerald-500/10 blur-2xl" />
      <div className="rounded-2xl border border-black/5 bg-white shadow-2xl shadow-ink-950/10 dark:border-white/10 dark:bg-ink-900">
        <div className="flex items-center justify-between border-b border-black/5 px-6 py-4 dark:border-white/10">
          <span className="text-sm font-semibold text-ink-900 dark:text-white">Leaderboard · 300 plans</span>
          <span className="rounded-full bg-gold-500/15 px-2.5 py-1 text-xs font-semibold text-gold-600 dark:text-gold-400">Top 3 advance</span>
        </div>
        <div className="divide-y divide-black/5 dark:divide-white/10">
          {rows.map((r) => (
            <div key={r.rank} className={"flex items-center gap-4 px-6 py-3 " + (r.tie ? "bg-gold-500/[0.06]" : "")}>
              <span className="w-6 font-display text-lg font-semibold text-slate-400 tabular-nums">{r.rank}</span>
              <span className="flex-1 text-sm font-medium text-ink-900 dark:text-white">{r.team}</span>
              {r.flagged && <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-semibold text-amber-700 dark:bg-amber-900/40 dark:text-amber-300">needs review</span>}
              <span className="font-semibold tabular-nums text-ink-900 dark:text-white">{r.score}</span>
            </div>
          ))}
        </div>
        <div className="border-t border-black/5 px-6 py-3 text-xs text-slate-500 dark:border-white/10">
          <span className="inline-flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-gold-500" /> Tie band at the cutoff — ranks 3 & 4 are within the noise; a human decides.</span>
        </div>
      </div>
    </div>
  );
}
