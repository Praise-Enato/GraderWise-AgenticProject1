import path from "path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  turbopack: {
    root: __dirname,
    resolveAlias: {
      tailwindcss: path.resolve(__dirname, "node_modules/tailwindcss"),
      "@tailwindcss/typography": path.resolve(
        __dirname,
        "node_modules/@tailwindcss/typography"
      ),
    },
  },
};

export default nextConfig;
