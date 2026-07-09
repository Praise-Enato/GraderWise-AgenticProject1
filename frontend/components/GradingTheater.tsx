"use client";

import { useEffect, useState, type CSSProperties, type PointerEvent } from "react";
import { motion, AnimatePresence, useReducedMotion, useMotionValue, useSpring } from "framer-motion";

import { STAGE_ORDER, stageIndex, type Stage, type StreamState } from "@/lib/gradingStages";

// The Live Grading Theater (eng review Phase 3). Every scene advances only on a
// real backend event, and each stage shows the actual pipeline data streaming
// in. The signature beat is the judge "bounce-back" — the self-correction that
// was previously invisible. Scenes are hand-built layered SVG (no Lottie dep),
// animated with framer-motion; prefers-reduced-motion drops to calm static art.

const SCENE_COPY: Record<string, { title: string; sub: (s: StreamState) => string }> = {
  idle: { title: "Ready to grade", sub: () => "Upload a plan and start grading." },
  screening: {
    title: "Screening the gate",
    sub: (s) =>
      s.screening
        ? s.screening.eligibility_status === "eligible"
          ? "Eligible — through the gate."
          : `${s.screening.eligibility_status.replace("_", " ")} — flagged for a human.`
        : "Checking eligibility…",
  },
  reading: {
    title: "Reading the plan",
    sub: (s) =>
      `Scored ${s.criteriaScored} criteria` + (s.score != null ? ` · running ${s.score} pts` : "…"),
  },
  judging: { title: "Second opinion", sub: () => "Checking the grade is consistent and complete." },
  retrying: {
    title: "Re-scoring",
    sub: (s) => (s.judge?.reason ? `Judge sent it back: ${s.judge.reason}` : "Judge sent it back — re-scoring."),
  },
  coaching: { title: "Coaching the team", sub: () => "Writing specific, encouraging feedback." },
  done: {
    title: "Verdict",
    sub: (s) => {
      const r = s.result as { score?: number } | null;
      return r && typeof r.score === "number" ? `Final score: ${r.score}` : "Grading complete.";
    },
  },
  error: { title: "Grading hit a problem", sub: (s) => s.error ?? "Something went wrong." },
};

const ELIGIBILITY_HEX: Record<string, string> = {
  eligible: "#10b981",
  needs_review: "#f59e0b",
  ineligible: "#ef4444",
};

export function GradingTheater({ state }: { state: StreamState }) {
  const reduce = !!useReducedMotion();
  const stage = state.stage;
  const copy = SCENE_COPY[stage] ?? SCENE_COPY.idle;
  const activeIndex = stageIndex(stage === "retrying" ? "judging" : stage);

  // Pointer-parallax tilt: the scene turns toward the cursor in 3D (springed).
  const tiltX = useSpring(useMotionValue(0), { stiffness: 150, damping: 15 });
  const tiltY = useSpring(useMotionValue(0), { stiffness: 150, damping: 15 });
  const onMove = (e: PointerEvent<HTMLDivElement>) => {
    const r = e.currentTarget.getBoundingClientRect();
    const px = (e.clientX - r.left) / r.width - 0.5;
    const py = (e.clientY - r.top) / r.height - 0.5;
    tiltY.set(px * 28);
    tiltX.set(-py * 28);
  };
  const onLeave = () => {
    tiltX.set(0);
    tiltY.set(0);
  };

  return (
    <div
      className="flex w-full flex-col items-center gap-6 p-8"
      role="status"
      aria-live="polite"
      aria-label={`Grading stage: ${copy.title}`}
    >
      {/* Progress rail — encodes the real pipeline order, not decoration */}
      <ol className="flex items-center gap-2" aria-hidden={stage === "error"}>
        {STAGE_ORDER.map((st, i) => {
          const done = activeIndex > i || stage === "done";
          const current = activeIndex === i && stage !== "done";
          return (
            <li key={st} className="flex items-center gap-2">
              <motion.span
                className={
                  "h-2.5 w-2.5 rounded-full " +
                  (done ? "bg-emerald-500" : current ? "bg-blue-500" : "bg-slate-300 dark:bg-slate-600")
                }
                animate={current && !reduce ? { scale: [1, 1.5, 1] } : { scale: 1 }}
                transition={current && !reduce ? { duration: 1.4, repeat: Infinity } : {}}
              />
              {i < STAGE_ORDER.length - 1 && (
                <span
                  className={
                    "h-px w-8 transition-colors " +
                    (activeIndex > i ? "bg-emerald-500" : "bg-slate-200 dark:bg-slate-700")
                  }
                />
              )}
            </li>
          );
        })}
      </ol>

      {/* Scene — a 3D stage: perspective + pointer-parallax tilt + depth layers */}
      <div
        data-testid="theater-stage"
        className="relative flex h-52 w-52 items-center justify-center"
        style={{ perspective: 900 }}
        onPointerMove={reduce ? undefined : onMove}
        onPointerLeave={reduce ? undefined : onLeave}
      >
        <AnimatePresence mode="wait">
          <motion.div
            key={stage}
            initial={reduce ? { opacity: 0 } : { opacity: 0, rotateX: -45, y: 26 }}
            animate={reduce ? { opacity: 1 } : { opacity: 1, rotateX: 0, y: 0 }}
            exit={reduce ? { opacity: 0 } : { opacity: 0, rotateX: 32, y: -22 }}
            transition={{ type: "spring", bounce: 0.3, duration: 0.6 }}
            style={reduce ? undefined : { rotateX: tiltX, rotateY: tiltY, transformStyle: "preserve-3d" }}
            className="absolute inset-0 flex items-center justify-center"
          >
            {/* receding back panel (parallax depth) */}
            {!reduce && (
              <div
                aria-hidden
                className="absolute h-36 w-36 rounded-3xl bg-gradient-to-br from-slate-100 to-slate-200 shadow-inner dark:from-slate-800 dark:to-slate-900"
                style={{ transform: "translateZ(-60px)" }}
              />
            )}
            {/* the motif, lifted toward the viewer */}
            <div
              className="drop-shadow-xl"
              style={reduce ? undefined : { transform: "translateZ(45px)", transformStyle: "preserve-3d" }}
            >
              <Scene stage={stage} state={state} reduce={reduce} />
            </div>
            {/* floor shadow grounds the motif */}
            {!reduce && (
              <div
                aria-hidden
                className="absolute -bottom-1 h-4 w-28 rounded-[50%] bg-black/25 blur-md dark:bg-black/50"
                style={{ transform: "translateZ(-30px)" }}
              />
            )}
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Copy + live data */}
      <div className="min-h-[4.5rem] max-w-sm text-center">
        <AnimatePresence mode="wait">
          <motion.div key={copy.title} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -6 }}>
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white">{copy.title}</h3>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{copy.sub(state)}</p>
          </motion.div>
        </AnimatePresence>

        {stage === "screening" && state.screening && (
          <div className="mt-3 flex flex-wrap justify-center gap-2">
            <EligibilityPill status={state.screening.eligibility_status} />
            {state.screening.ai_content_flag && (
              <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-700 dark:bg-amber-900/40 dark:text-amber-300">
                AI-content flag
              </span>
            )}
            {state.screening.dq_reasons.map((r) => (
              <span key={r} className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600 dark:bg-slate-800 dark:text-slate-300">
                {r}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function EligibilityPill({ status }: { status: string }) {
  const styles: Record<string, string> = {
    eligible: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300",
    needs_review: "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300",
    ineligible: "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300",
  };
  return (
    <span className={"rounded-full px-2 py-0.5 text-xs font-medium " + (styles[status] ?? styles.eligible)}>
      {status.replace("_", " ")}
    </span>
  );
}

// A count-up number for the verdict (respects reduced motion).
function useCountUp(target: number, active: boolean, reduce: boolean): number {
  const [n, setN] = useState(0);
  useEffect(() => {
    if (!active) return;
    if (reduce || typeof requestAnimationFrame === "undefined") {
      setN(target);
      return;
    }
    let raf = 0;
    const start = performance.now();
    const dur = 900;
    const tick = (t: number) => {
      const p = Math.min(1, (t - start) / dur);
      setN(Math.round(target * (1 - Math.pow(1 - p, 3)))); // easeOutCubic
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [target, active, reduce]);
  return n;
}

const SPRING = { type: "spring" as const, stiffness: 120, damping: 8 };

// --- Scenes: layered SVG motifs on a 160x160 canvas ------------------------- //
function Scene({ stage, state, reduce }: { stage: Stage; state: StreamState; reduce: boolean }) {
  if (stage === "screening") return <ScreeningScene state={state} reduce={reduce} />;
  if (stage === "reading") return <ReadingScene reduce={reduce} />;
  if (stage === "judging" || stage === "retrying")
    return <JudgingScene retrying={stage === "retrying"} reduce={reduce} />;
  if (stage === "coaching") return <CoachingScene reduce={reduce} />;
  if (stage === "done") return <VerdictScene state={state} reduce={reduce} />;
  if (stage === "error") return <ErrorScene reduce={reduce} />;
  return <IdleScene />;
}

function Paper({ x = 46, y = 40, w = 68, h = 84, lines = 5 }: { x?: number; y?: number; w?: number; h?: number; lines?: number }) {
  return (
    <g>
      <rect x={x} y={y} width={w} height={h} rx="6" fill="white" stroke="#cbd5e1" strokeWidth="1.5" className="dark:[fill:#0f172a] dark:[stroke:#334155]" />
      <rect x={x + 10} y={y + 12} width={w * 0.5} height="6" rx="3" fill="#94a3b8" />
      {Array.from({ length: lines }).map((_, i) => (
        <rect key={i} x={x + 10} y={y + 28 + i * 12} width={w - 20 - (i % 2) * 10} height="4" rx="2" fill="#e2e8f0" className="dark:[fill:#1e293b]" />
      ))}
    </g>
  );
}

function ScreeningScene({ state, reduce }: { state: StreamState; reduce: boolean }) {
  const status = state.screening?.eligibility_status ?? "eligible";
  const color = ELIGIBILITY_HEX[status] ?? ELIGIBILITY_HEX.eligible;
  const mark = status === "eligible" ? "✓" : status === "ineligible" ? "✕" : "!";
  return (
    <svg viewBox="0 0 160 160" className="h-40 w-40">
      {/* checkpoint posts + light */}
      <rect x="24" y="34" width="10" height="96" rx="3" fill="#94a3b8" opacity="0.5" />
      <rect x="126" y="34" width="10" height="96" rx="3" fill="#94a3b8" opacity="0.5" />
      <rect x="24" y="28" width="112" height="10" rx="4" fill="#94a3b8" opacity="0.5" />
      <motion.circle cx="80" cy="33" r="4" fill={color}
        animate={reduce ? { opacity: 1 } : { opacity: [0.4, 1, 0.4] }} transition={{ duration: 1.6, repeat: Infinity }} />

      {/* document slides through the gate */}
      <motion.g
        animate={reduce ? { x: 0 } : { x: [-46, 0, 0] }}
        transition={reduce ? {} : { duration: 2.6, times: [0, 0.55, 1], repeat: Infinity, ease: "easeInOut" }}
      >
        <Paper x={46} y={44} w={68} h={80} lines={4} />
        {/* scan beam sweeping down the doc */}
        {!reduce && (
          <motion.rect x="46" width="68" height="4" rx="2" fill={color}
            animate={{ y: [48, 116, 48], opacity: [0, 0.9, 0] }}
            transition={{ duration: 2.6, repeat: Infinity, ease: "easeInOut" }} />
        )}
      </motion.g>

      {/* eligibility stamp thuds in */}
      <motion.g
        initial={reduce ? { opacity: 1, scale: 1 } : { opacity: 0, scale: 2.4, rotate: -18 }}
        animate={reduce ? { opacity: 1, scale: 1 } : { opacity: [0, 0, 1], scale: [2.4, 2.4, 1], rotate: [-18, -18, -10] }}
        transition={reduce ? {} : { duration: 2.6, times: [0, 0.6, 0.72], repeat: Infinity }}
        style={{ originX: "104px", originY: "104px" }}
      >
        <rect x="82" y="92" width="44" height="26" rx="5" fill="none" stroke={color} strokeWidth="3" />
        <text x="104" y="110" textAnchor="middle" fontSize="15" fontWeight="800" fill={color}>{mark}</text>
      </motion.g>
    </svg>
  );
}

function ReadingScene({ reduce }: { reduce: boolean }) {
  return (
    <svg viewBox="0 0 160 160" className="h-40 w-40">
      <Paper x={40} y={26} w={80} h={108} lines={0} />
      <rect x="52" y="40" width="42" height="7" rx="3.5" fill="#94a3b8" />
      {Array.from({ length: 6 }).map((_, i) => {
        const y = 58 + i * 13;
        return (
          <g key={i}>
            <rect x="52" y={y} width={56 - (i % 3) * 8} height="5" rx="2.5" fill="#e2e8f0" className="dark:[fill:#1e293b]" />
            {!reduce && (
              <motion.rect x="52" y={y} width={56 - (i % 3) * 8} height="5" rx="2.5" fill="#10b981"
                initial={{ scaleX: 0 }} animate={{ scaleX: [0, 1, 1, 0] }} style={{ originX: "52px" }}
                transition={{ duration: 3, times: [0, 0.4, 0.8, 1], delay: i * 0.22, repeat: Infinity }} />
            )}
          </g>
        );
      })}
      {/* scanner bar */}
      {!reduce && (
        <motion.g animate={{ y: [50, 130, 50] }} transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}>
          <rect x="44" y="0" width="72" height="10" rx="5" fill="#10b981" opacity="0.18" />
          <rect x="44" y="4" width="72" height="2" fill="#10b981" opacity="0.8" />
        </motion.g>
      )}
    </svg>
  );
}

function JudgingScene({ retrying, reduce }: { retrying: boolean; reduce: boolean }) {
  const color = retrying ? "#f59e0b" : "#8b5cf6";
  const beam = retrying
    ? (reduce ? { rotate: -9 } : { rotate: [0, -16, 12, -7, 4, 0] })
    : (reduce ? { rotate: 0 } : { rotate: [-6, 6, -6] });
  return (
    <svg viewBox="0 0 160 160" className="h-40 w-40" style={{ color }}>
      {/* stand */}
      <rect x="76" y="34" width="8" height="86" rx="3" fill="currentColor" />
      <path d="M56 128 L104 128 L96 120 L64 120 Z" fill="currentColor" />
      <circle cx="80" cy="32" r="5" fill="currentColor" />
      {/* pivoting beam + pans */}
      <motion.g
        style={{ originX: "80px", originY: "40px" }}
        animate={beam}
        transition={reduce ? {} : retrying ? { duration: 1.1, ease: "easeInOut" } : { duration: 2.4, repeat: Infinity, ease: "easeInOut" }}
      >
        <rect x="34" y="37" width="92" height="6" rx="3" fill="currentColor" />
        {[38, 122].map((cx) => (
          <g key={cx}>
            <line x1={cx} y1="40" x2={cx - 14} y2="66" stroke="currentColor" strokeWidth="1.5" />
            <line x1={cx} y1="40" x2={cx + 14} y2="66" stroke="currentColor" strokeWidth="1.5" />
            <path d={`M${cx - 16} 66 A 16 10 0 0 0 ${cx + 16} 66 Z`} fill="currentColor" opacity="0.25" />
            <path d={`M${cx - 16} 66 A 16 10 0 0 0 ${cx + 16} 66`} fill="none" stroke="currentColor" strokeWidth="2" />
          </g>
        ))}
      </motion.g>
      {/* verdict glyph: check settles (valid) or a return-arrow (retry) */}
      {retrying ? (
        <motion.path
          d="M96 96 a 16 16 0 1 0 6 12" fill="none" stroke={color} strokeWidth="4" strokeLinecap="round"
          initial={{ opacity: 0 }} animate={{ opacity: [0, 1] }} transition={{ delay: 0.5, duration: 0.4 }} />
      ) : (
        <motion.path
          d="M70 100 l 8 8 l 16 -18" fill="none" stroke="#10b981" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round"
          initial={reduce ? { pathLength: 1, opacity: 1 } : { pathLength: 0, opacity: 0 }}
          animate={{ pathLength: 1, opacity: 1 }} transition={{ delay: 0.6, duration: 0.5 }} />
      )}
    </svg>
  );
}

function CoachingScene({ reduce }: { reduce: boolean }) {
  const d = "M40 96 C 56 74, 70 108, 86 86 S 116 70, 120 74";
  return (
    <svg viewBox="0 0 160 160" className="h-40 w-40 text-emerald-500">
      <Paper x={34} y={30} w={92} h={100} lines={2} />
      {/* handwriting stroke draws in */}
      <motion.path d={d} fill="none" stroke="currentColor" strokeWidth="3.5" strokeLinecap="round"
        initial={reduce ? { pathLength: 1 } : { pathLength: 0 }}
        animate={reduce ? { pathLength: 1 } : { pathLength: [0, 1] }}
        transition={reduce ? {} : { duration: 1.8, repeat: Infinity, repeatDelay: 0.5, ease: "easeInOut" }} />
      {/* pen nib follows the same path */}
      {!reduce && (
        <motion.g animate={{ offsetDistance: ["0%", "100%"] }}
          transition={{ duration: 1.8, repeat: Infinity, repeatDelay: 0.5, ease: "easeInOut" }}
          style={{ offsetPath: `path('${d}')`, offsetRotate: "auto" } as CSSProperties}>
          <path d="M0 0 l 10 3 l -8 4 Z" fill="#1e293b" className="dark:[fill:#e2e8f0]" />
          <rect x="4" y="-9" width="4" height="12" rx="1.5" fill="currentColor" transform="rotate(35)" />
        </motion.g>
      )}
    </svg>
  );
}

function VerdictScene({ state, reduce }: { state: StreamState; reduce: boolean }) {
  const r = state.result as { score?: number; assessments?: { max_points?: number }[] } | null;
  const score = r && typeof r.score === "number" ? Math.round(r.score) : null;
  const total = r?.assessments?.reduce((sum, a) => sum + (a.max_points ?? 0), 0) || 0;
  const pct = score != null && total > 0 ? Math.min(1, score / total) : 1;
  const n = useCountUp(score ?? 0, score != null, reduce);
  const R = 54;
  const C = 2 * Math.PI * R;
  return (
    <svg viewBox="0 0 160 160" className="h-40 w-40 text-emerald-500">
      <circle cx="80" cy="80" r={R} fill="none" stroke="#e2e8f0" strokeWidth="10" className="dark:[stroke:#1e293b]" />
      <motion.circle
        cx="80" cy="80" r={R} fill="none" stroke="currentColor" strokeWidth="10" strokeLinecap="round"
        transform="rotate(-90 80 80)" strokeDasharray={C}
        initial={{ strokeDashoffset: C }}
        animate={{ strokeDashoffset: C * (1 - pct) }}
        transition={reduce ? { duration: 0 } : { duration: 1, ease: "easeOut" }}
      />
      <text x="80" y="82" textAnchor="middle" fontSize="34" fontWeight="800" className="fill-slate-900 dark:fill-white">
        {score != null ? n : "✓"}
      </text>
      {score != null && total > 0 && (
        <text x="80" y="104" textAnchor="middle" fontSize="12" className="fill-slate-400">of {total}</text>
      )}
    </svg>
  );
}

function ErrorScene({ reduce }: { reduce: boolean }) {
  return (
    <svg viewBox="0 0 160 160" className="h-40 w-40 text-red-500">
      <motion.circle cx="80" cy="80" r="52" fill="none" stroke="currentColor" strokeWidth="6" opacity="0.4"
        animate={reduce ? {} : { scale: [1, 1.05, 1] }} transition={{ duration: 1.6, repeat: Infinity }} style={{ originX: "80px", originY: "80px" }} />
      <line x1="80" y1="52" x2="80" y2="90" stroke="currentColor" strokeWidth="8" strokeLinecap="round" />
      <circle cx="80" cy="108" r="4.5" fill="currentColor" />
    </svg>
  );
}

function IdleScene() {
  return (
    <svg viewBox="0 0 160 160" className="h-40 w-40 text-slate-400">
      <Paper x={44} y={30} w={72} h={100} lines={4} />
    </svg>
  );
}
