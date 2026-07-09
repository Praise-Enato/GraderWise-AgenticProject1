// Adds jest-dom matchers (toBeInTheDocument, etc.) for component tests.
import "@testing-library/jest-dom/vitest";

// jsdom has no matchMedia; framer-motion's useReducedMotion() calls it.
if (typeof window !== "undefined" && !window.matchMedia) {
  window.matchMedia = ((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  })) as unknown as typeof window.matchMedia;
}
