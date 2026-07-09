"use client";

import { useCallback, useRef, useState } from "react";

import {
  applyEvent,
  initialStreamState,
  type StageEvent,
  type StreamState,
} from "@/lib/gradingStages";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export interface StartPayload {
  rubric: unknown[];
  submission_files?: { filename: string; content: string }[];
  submission_text?: string;
  student_id?: string;
  guideline?: string;
  use_evidence?: boolean;
  ensemble_n?: number;
  [k: string]: unknown;
}

/**
 * Drives the Live Grading Theater from the backend SSE stream (Phase 3, A1).
 *
 * Handshake: POST /grade/stream/start -> { job_id }, then open an EventSource
 * GET on /grade/stream/{job_id} (EventSource can't POST the payload). Each
 * "stage" frame is folded into StreamState via the pure applyEvent reducer; a
 * "done"/"grade_error" frame ends the stream. A start failure or connection
 * drop before completion surfaces as the "error" stage, so a caller can fall
 * back to a plain loader instead of hanging.
 */
export function useGradingStream() {
  const [state, setState] = useState<StreamState>(initialStreamState);
  const [active, setActive] = useState(false);
  const esRef = useRef<EventSource | null>(null);

  const close = useCallback(() => {
    esRef.current?.close();
    esRef.current = null;
    setActive(false);
  }, []);

  const reset = useCallback(() => {
    close();
    setState(initialStreamState);
  }, [close]);

  const start = useCallback(
    async (payload: StartPayload) => {
      reset();
      setActive(true);

      let jobId: string;
      try {
        const res = await fetch(`${API_URL}/grade/stream/start`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ student_id: "web", ...payload }),
        });
        if (!res.ok) throw new Error(`Could not start grading (HTTP ${res.status}).`);
        jobId = (await res.json()).job_id;
      } catch (e) {
        setState((s) => ({ ...s, stage: "error", error: (e as Error).message }));
        setActive(false);
        return;
      }

      const es = new EventSource(`${API_URL}/grade/stream/${jobId}`);
      esRef.current = es;

      const fold = (e: MessageEvent) => {
        try {
          setState((s) => applyEvent(s, JSON.parse(e.data) as StageEvent));
        } catch {
          /* ignore a malformed frame rather than break the stream */
        }
      };

      es.addEventListener("stage", fold as EventListener);
      es.addEventListener("done", ((e: MessageEvent) => {
        fold(e);
        close();
      }) as EventListener);
      es.addEventListener("grade_error", ((e: MessageEvent) => {
        fold(e);
        close();
      }) as EventListener);
      es.onerror = () => {
        // Connection-level error (carries no data). Only surface it if we did
        // not already finish — a normal close after "done" also fires here.
        setState((s) =>
          s.stage === "done"
            ? s
            : { ...s, stage: "error", error: s.error ?? "The grading stream disconnected." },
        );
        close();
      };
    },
    [reset, close],
  );

  return { state, active, start, reset };
}
