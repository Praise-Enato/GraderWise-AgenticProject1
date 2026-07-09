"use client";

import { motion, AnimatePresence, useReducedMotion } from "framer-motion";

import { STAGE_ORDER, stageIndex, type Stage, type StreamState } from "@/lib/gradingStages";

// The Live Grading Theater (eng review Phase 3). Unlike the old timer-driven
// loader, every scene here advances only on a real backend event, and each
// stage shows the actual pipeline data streaming in. The signature beat is the
// judge "bounce-back": the self-correction that was previously invisible.

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

// The scene shown for each stage (retrying reuses the judging scene, bouncing).
function sceneKey(stage: Stage): string {
  return stage;
}

export function GradingTheater({ state }: { state: StreamState }) {
  const reduce = useReducedMotion();
  const stage = state.stage;
  const copy = SCENE_COPY[stage] ?? SCENE_COPY.idle;
  const activeIndex = stageIndex(stage === "retrying" ? "judging" : stage);

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
              <span
                className={
                  "h-2.5 w-2.5 rounded-full transition-colors " +
                  (done
                    ? "bg-emerald-500"
                    : current
                      ? "bg-blue-500"
                      : "bg-slate-300 dark:bg-slate-600")
                }
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

      {/* Scene */}
      <div className="relative flex h-40 w-40 items-center justify-center">
        <AnimatePresence mode="wait">
          <motion.div
            key={sceneKey(stage)}
            initial={reduce ? { opacity: 0 } : { opacity: 0, scale: 0.9, y: 8 }}
            animate={reduce ? { opacity: 1 } : { opacity: 1, scale: 1, y: 0 }}
            exit={reduce ? { opacity: 0 } : { opacity: 0, scale: 0.95, y: -8 }}
            transition={{ type: "spring", bounce: 0.4, duration: 0.5 }}
            className="absolute inset-0 flex items-center justify-center"
          >
            <Scene stage={stage} state={state} reduce={!!reduce} />
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Copy + live data */}
      <div className="min-h-[4.5rem] max-w-sm text-center">
        <AnimatePresence mode="wait">
          <motion.div
            key={copy.title}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
          >
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
              <span
                key={r}
                className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600 dark:bg-slate-800 dark:text-slate-300"
              >
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

// --- Scenes: small SVG motifs, animated only when motion is allowed --------- //
function Scene({ stage, state, reduce }: { stage: Stage; state: StreamState; reduce: boolean }) {
  const loop = reduce ? {} : { repeat: Infinity, ease: "easeInOut" as const };
  const stroke = "currentColor";

  if (stage === "screening") {
    // A document sliding through a checkpoint gate.
    return (
      <svg viewBox="0 0 120 120" className="h-32 w-32 text-blue-500">
        <line x1="30" y1="20" x2="30" y2="100" stroke={stroke} strokeWidth="3" opacity="0.3" />
        <line x1="90" y1="20" x2="90" y2="100" stroke={stroke} strokeWidth="3" opacity="0.3" />
        <motion.rect
          x="20" y="46" width="28" height="34" rx="3" fill={stroke}
          animate={reduce ? { x: 46 } : { x: [10, 46, 46] }}
          transition={reduce ? {} : { duration: 2.4, times: [0, 0.6, 1], ...loop }}
        />
        <motion.circle
          cx="90" cy="63" r="10" fill="none" stroke={stroke} strokeWidth="3"
          animate={reduce ? { opacity: 1 } : { opacity: [0, 0, 1], scale: [0.6, 0.6, 1] }}
          transition={reduce ? {} : { duration: 2.4, times: [0, 0.6, 0.8], ...loop }}
        />
      </svg>
    );
  }

  if (stage === "reading") {
    // Text lines scanning in.
    return (
      <svg viewBox="0 0 120 120" className="h-32 w-32 text-emerald-500">
        <rect x="24" y="20" width="72" height="84" rx="6" fill="none" stroke={stroke} strokeWidth="3" opacity="0.4" />
        {[0, 1, 2, 3, 4].map((i) => (
          <motion.line
            key={i}
            x1="34" y1={38 + i * 13} x2="86" y2={38 + i * 13}
            stroke={stroke} strokeWidth="4" strokeLinecap="round"
            animate={reduce ? { pathLength: 1, opacity: 1 } : { pathLength: [0, 1], opacity: [0.3, 1] }}
            transition={reduce ? {} : { duration: 0.8, delay: i * 0.18, repeat: Infinity, repeatDelay: 1 }}
          />
        ))}
      </svg>
    );
  }

  if (stage === "judging" || stage === "retrying") {
    // A balance scale. Level while judging; a visible bounce when the judge rejects.
    const beam = stage === "retrying"
      ? (reduce ? { rotate: -8 } : { rotate: [0, -12, 10, -6, 0] })
      : (reduce ? { rotate: 0 } : { rotate: [-4, 4, -4] });
    return (
      <svg viewBox="0 0 120 120" className={stage === "retrying" ? "h-32 w-32 text-amber-500" : "h-32 w-32 text-purple-500"}>
        <line x1="60" y1="24" x2="60" y2="96" stroke={stroke} strokeWidth="3" />
        <circle cx="60" cy="22" r="4" fill={stroke} />
        <motion.g
          style={{ originX: "60px", originY: "30px" }}
          animate={beam}
          transition={reduce ? {} : { duration: stage === "retrying" ? 0.9 : 2.2, ...(stage === "retrying" ? {} : loop) }}
        >
          <line x1="30" y1="30" x2="90" y2="30" stroke={stroke} strokeWidth="3" />
          <path d="M30 30 L22 50 L38 50 Z" fill="none" stroke={stroke} strokeWidth="2.5" />
          <path d="M90 30 L82 50 L98 50 Z" fill="none" stroke={stroke} strokeWidth="2.5" />
        </motion.g>
      </svg>
    );
  }

  if (stage === "coaching") {
    // A pen drawing a line of feedback.
    return (
      <svg viewBox="0 0 120 120" className="h-32 w-32 text-emerald-500">
        <motion.path
          d="M28 78 C 44 60, 60 92, 76 70 S 100 56, 100 56"
          fill="none" stroke={stroke} strokeWidth="4" strokeLinecap="round"
          animate={reduce ? { pathLength: 1 } : { pathLength: [0, 1] }}
          transition={reduce ? {} : { duration: 1.6, repeat: Infinity, repeatDelay: 0.4 }}
        />
        <motion.circle
          cx="0" cy="0" r="4" fill={stroke}
          animate={reduce ? { opacity: 0 } : { offsetDistance: ["0%", "100%"] }}
        />
      </svg>
    );
  }

  if (stage === "done") {
    const r = state.result as { score?: number } | null;
    const score = r && typeof r.score === "number" ? Math.round(r.score) : null;
    return (
      <svg viewBox="0 0 120 120" className="h-32 w-32 text-emerald-500">
        <motion.circle
          cx="60" cy="60" r="46" fill="none" stroke={stroke} strokeWidth="5"
          initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ duration: 0.8 }}
        />
        <text x="60" y="70" textAnchor="middle" className="fill-slate-900 dark:fill-white" fontSize="30" fontWeight="700">
          {score != null ? score : "✓"}
        </text>
      </svg>
    );
  }

  if (stage === "error") {
    return (
      <svg viewBox="0 0 120 120" className="h-32 w-32 text-red-500">
        <circle cx="60" cy="60" r="46" fill="none" stroke={stroke} strokeWidth="5" opacity="0.5" />
        <line x1="60" y1="38" x2="60" y2="68" stroke={stroke} strokeWidth="6" strokeLinecap="round" />
        <circle cx="60" cy="82" r="3.5" fill={stroke} />
      </svg>
    );
  }

  // idle
  return (
    <svg viewBox="0 0 120 120" className="h-32 w-32 text-slate-400">
      <rect x="34" y="24" width="52" height="72" rx="6" fill="none" stroke={stroke} strokeWidth="3" />
    </svg>
  );
}
