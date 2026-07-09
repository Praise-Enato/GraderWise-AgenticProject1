import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";

import { GradingTheater } from "@/components/GradingTheater";
import { initialStreamState, type StreamState } from "@/lib/gradingStages";

function stateWith(partial: Partial<StreamState>): StreamState {
  return { ...initialStreamState, ...partial };
}

describe("GradingTheater", () => {
  it("shows eligibility, AI flag, and DQ reasons in the screening scene", () => {
    render(
      <GradingTheater
        state={stateWith({
          stage: "screening",
          screening: { eligibility_status: "needs_review", dq_reasons: ["missing license"], ai_content_flag: true },
        })}
      />,
    );
    expect(screen.getByText("Screening the gate")).toBeInTheDocument();
    expect(screen.getByText("needs review")).toBeInTheDocument(); // eligibility pill (exact)
    expect(screen.getByText("AI-content flag")).toBeInTheDocument();
    expect(screen.getByText("missing license")).toBeInTheDocument();
  });

  it("shows criteria progress and running score while reading", () => {
    render(<GradingTheater state={stateWith({ stage: "reading", criteriaScored: 4, score: 22 })} />);
    expect(screen.getByText("Reading the plan")).toBeInTheDocument();
    expect(screen.getByText(/Scored 4 criteria/)).toBeInTheDocument();
    expect(screen.getByText(/running 22 pts/)).toBeInTheDocument();
  });

  it("surfaces the judge's rejection reason in the retry scene", () => {
    render(
      <GradingTheater
        state={stateWith({ stage: "retrying", judge: { is_valid: false, reason: "incomplete grade", revision_number: 1 } })}
      />,
    );
    expect(screen.getByText("Re-scoring")).toBeInTheDocument();
    expect(screen.getByText(/Judge sent it back: incomplete grade/)).toBeInTheDocument();
  });

  it("reveals the final score on the verdict scene", () => {
    render(<GradingTheater state={stateWith({ stage: "done", result: { score: 74 } })} />);
    expect(screen.getByText("Verdict")).toBeInTheDocument();
    expect(screen.getByText("Final score: 74")).toBeInTheDocument();
  });

  it("shows a clear error message, not a silent hang", () => {
    render(<GradingTheater state={stateWith({ stage: "error", error: "The grading stream disconnected." })} />);
    expect(screen.getByText("Grading hit a problem")).toBeInTheDocument();
    expect(screen.getByText("The grading stream disconnected.")).toBeInTheDocument();
  });
});
