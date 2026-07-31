// TEMPORARY DEV SHIM — not the permanent fix.
// On this WSL2 kernel (6.18.33.2-microsoft-standard-WSL2) the native lightningcss
// `.node` binary crashes with SIGBUS on load, which kills Next.js/Turbopack's
// Tailwind PostCSS worker. The WASM build works fine, so intercept `require('lightningcss')`
// and substitute the synchronous WASM build. Injected via NODE_OPTIONS so it also
// reaches the CSS worker Turbopack spawns. Remove once the kernel issue is resolved.
const Module = require('module');
const path = require('path');
// Absolute path bypasses lightningcss-wasm's restrictive "exports" field.
const WASM_ENTRY = path.join(__dirname, 'node_modules', 'lightningcss-wasm', 'wasm-node.cjs');
const originalLoad = Module._load;
let wasmCache = null;
Module._load = function (request, parent, isMain) {
  if (request === 'lightningcss') {
    if (!wasmCache) {
      wasmCache = require(WASM_ENTRY);
    }
    return wasmCache;
  }
  return originalLoad.apply(this, arguments);
};
