import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";

import { useGradingStream } from "@/lib/useGradingStream";

// Fake EventSource so the hook's SSE wiring is testable in jsdom.
class FakeEventSource {
  static instances: FakeEventSource[] = [];
  url: string;
  onerror: (() => void) | null = null;
  closed = false;
  private listeners: Record<string, ((e: { data: string }) => void)[]> = {};
  constructor(url: string) {
    this.url = url;
    FakeEventSource.instances.push(this);
  }
  addEventListener(type: string, cb: (e: { data: string }) => void) {
    (this.listeners[type] ||= []).push(cb);
  }
  close() {
    this.closed = true;
  }
  emit(type: string, data: unknown) {
    (this.listeners[type] || []).forEach((cb) => cb({ data: JSON.stringify(data) }));
  }
}

beforeEach(() => {
  FakeEventSource.instances = [];
  (globalThis as unknown as { EventSource: unknown }).EventSource = FakeEventSource;
});

describe("useGradingStream", () => {
  it("opens the stream after the start handshake and folds events into state", async () => {
    (globalThis as unknown as { fetch: unknown }).fetch = vi.fn(async () => ({
      ok: true,
      json: async () => ({ job_id: "job-1" }),
    }));

    const { result } = renderHook(() => useGradingStream());
    await act(async () => {
      await result.current.start({ rubric: [] });
    });

    const es = FakeEventSource.instances.at(-1)!;
    expect(es.url).toContain("/grade/stream/job-1");

    act(() => es.emit("stage", { stage: "screening", eligibility_status: "eligible" }));
    expect(result.current.state.stage).toBe("screening");

    act(() => es.emit("stage", { stage: "reading", criteria_scored: 3, score: 20 }));
    expect(result.current.state.criteriaScored).toBe(3);

    act(() => es.emit("done", { stage: "done", grade_result: { score: 20 } }));
    expect(result.current.state.stage).toBe("done");
    expect(result.current.state.result).toEqual({ score: 20 });
    expect(es.closed).toBe(true);
  });

  it("surfaces the error stage when the start handshake fails", async () => {
    (globalThis as unknown as { fetch: unknown }).fetch = vi.fn(async () => ({ ok: false, status: 500 }));
    const { result } = renderHook(() => useGradingStream());
    await act(async () => {
      await result.current.start({ rubric: [] });
    });
    await waitFor(() => expect(result.current.state.stage).toBe("error"));
    expect(result.current.state.error).toContain("500");
  });
});
