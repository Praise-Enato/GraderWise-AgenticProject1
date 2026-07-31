"use client";

import { useCallback, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";

import { GradingTheater } from "@/components/GradingTheater";
import { applyEvent, initialStreamState, type StageEvent, type StreamState } from "@/lib/gradingStages";

// A standalone preview for the Live Grading Theater: it replays a realistic
// event sequence (including a judge rejection + re-score) through the real
// component, so the scenes can be reviewed without a live model. Not part of a
// grading flow — a design/QA harness.
const SCRIPT: StageEvent[] = [
  { stage: "screening", eligibility_status: "needs_review", dq_reasons: ["No business licence attached"], ai_content_flag: true },
  { stage: "reading", criteria_scored: 3, score: 16 },
  { stage: "reading", criteria_scored: 8, score: 44 },
  { stage: "judging", is_valid: false, reason: "2 of 12 criteria were not scored", revision_number: 1 },
  { stage: "reading", criteria_scored: 12, score: 71 },
  { stage: "judging", is_valid: true, revision_number: 1 },
  { stage: "coaching" },
  { stage: "done", grade_result: { score: 71 } },
];

export default function TheaterPreview() {
  const router = useRouter();
  const goBack = useCallback(() => {
    // Return to wherever they came from; fall back to home on a direct visit.
    if (typeof window !== "undefined" && window.history.length > 1) router.back();
    else router.push("/");
  }, [router]);

  const [state, setState] = useState<StreamState>(initialStreamState);
  const [step, setStep] = useState(0);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);
  const idx = useRef(0); // authoritative index; a state updater must not read a moving closure var

  const play = useCallback(() => {
    if (timer.current) clearInterval(timer.current);
    idx.current = 0;
    setState(initialStreamState);
    setStep(0);
    timer.current = setInterval(() => {
      const ev = SCRIPT[idx.current]; // capture BEFORE scheduling so the updater closes over a stable value
      if (!ev) {
        if (timer.current) clearInterval(timer.current);
        timer.current = null;
        return;
      }
      setState((s) => applyEvent(s, ev));
      idx.current += 1;
      setStep(idx.current);
    }, 1400);
  }, []);

  // Deterministic single-step advance (used for design QA / screenshots).
  const next = useCallback(() => {
    if (idx.current >= SCRIPT.length) {
      idx.current = 0;
      setState(initialStreamState);
      setStep(0);
      return;
    }
    const ev = SCRIPT[idx.current];
    setState((s) => applyEvent(s, ev));
    idx.current += 1;
    setStep(idx.current);
  }, []);

  return (
    <main className="mx-auto flex min-h-screen max-w-xl flex-col items-center justify-center gap-8 p-8">
      <button
        onClick={goBack}
        aria-label="Go back"
        className="fixed left-4 top-4 z-10 inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white/80 px-3 py-2 text-sm font-medium text-slate-700 shadow-sm backdrop-blur transition-colors hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900/80 dark:text-slate-200 dark:hover:bg-slate-800"
      >
        <ArrowLeft className="h-4 w-4" /> Back
      </button>
      <div className="w-full rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <GradingTheater state={state} />
      </div>
      <div className="flex gap-3">
        <button
          onClick={play}
          className="rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-blue-700"
        >
          Play grading sequence
        </button>
        <button
          onClick={next}
          data-testid="step"
          className="rounded-lg border border-slate-300 px-5 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
        >
          Step ({step}/{SCRIPT.length})
        </button>
      </div>
      <p className="text-xs text-slate-400">Preview harness · replays a scripted stream (incl. a judge re-score)</p>
    </main>
  );
}
