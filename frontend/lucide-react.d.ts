// lucide-react@0.562.0 ships type definitions but its package.json `exports` map
// omits a `types` condition, which `moduleResolution: "bundler"` requires — so
// `next build`'s typecheck fails with TS7016 across every file importing icons.
// This ambient declaration satisfies the resolver (icons are loosely typed) and
// unblocks the production build. Remove once lucide-react ships a fixed `exports`.
declare module "lucide-react";
