import { describe, it, expect } from "vitest";

import { sectionOf, labelOf } from "@/components/GradeBreakdown";

// GradeBreakdown groups per-criterion results by rubric section, splitting the
// criterion name on " - ". These pure helpers drive that grouping in the app's
// strongest result view, so their edge cases are worth locking down.
describe("rubric criterion name split", () => {
  it("sectionOf extracts the section before ' - '", () => {
    expect(sectionOf("Financials - Detailed Breakdown")).toBe("Financials");
  });

  it("labelOf extracts the label after ' - '", () => {
    expect(labelOf("Financials - Detailed Breakdown")).toBe("Detailed Breakdown");
  });

  it("sectionOf falls back to 'Other' when there is no delimiter", () => {
    expect(sectionOf("Market")).toBe("Other");
  });

  it("labelOf returns the whole name when there is no delimiter", () => {
    expect(labelOf("Market")).toBe("Market");
  });

  it("labelOf preserves a further ' - ' inside the label", () => {
    expect(labelOf("A - B - C")).toBe("B - C");
  });
});
