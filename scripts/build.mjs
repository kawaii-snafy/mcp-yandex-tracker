/**
 * Bundle src/cli.ts into the single artifact that gets published.
 *
 * One Node-compatible ESM file with the dependencies inlined, so a cold
 * `npx -y mcp-yandex-tracker` has no dependency tree to install — which is
 * exactly how a host launches it. Plain JavaScript rather than TypeScript so
 * that every supported Node (>= 20) can run it without a TS loader.
 */

import { build } from "esbuild";

await build({
  entryPoints: ["src/cli.ts"],
  outfile: "dist/cli.js",
  bundle: true,
  platform: "node",
  format: "esm",
  target: "node20",
  sourcemap: "linked",
  banner: { js: "#!/usr/bin/env node" },
});
