import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async redirects() {
    // The Business Plan suite moved out of the educator sidebar into its own
    // /business/* workspace. Keep old links working.
    return [
      { source: "/bpc-grading", destination: "/business/grading", permanent: false },
      { source: "/bpc-screening", destination: "/business/screening", permanent: false },
      { source: "/bpc-headtohead", destination: "/business/ai-vs-human", permanent: false },
    ];
  },
};

export default nextConfig;
