import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "path";

// Test harness for the frontend (eng review T1: the app had zero tests).
// jsdom + Testing Library for component tests; the "@/" alias mirrors tsconfig
// so tests import app modules the same way the app does.
export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./vitest.setup.ts"],
    include: ["**/*.{test,spec}.{ts,tsx}"],
    exclude: ["node_modules", ".next", "e2e"],
  },
  resolve: {
    alias: { "@": path.resolve(__dirname, ".") },
  },
});
