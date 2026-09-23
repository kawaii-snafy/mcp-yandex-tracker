/**
 * Rewrite the generated half of docs/TOOLS.md from the tool registry.
 *
 * The preamble above the marker is written by hand — calling convention, the
 * places the wrapper is not literal. Everything between the markers is derived
 * from the tools themselves, so the index cannot drift from the code.
 */

import { spawnSync } from "node:child_process";
import { readFile, writeFile } from "node:fs/promises";
import { parseEndpoint } from "../src/tool.ts";
import { sections } from "../src/tools/index.ts";

const DOC = new URL("../docs/TOOLS.md", import.meta.url);
const START = "<!-- tools:start -->";
const END = "<!-- tools:end -->";

// Nothing else checks the description contract, so this is where a tool that
// breaks it is refused — with its name, rather than as a crash on `undefined`.
const DOC_URL = /^(https:\/\/yandex\.ru\/support\/tracker\/en\/api\/([\w/-]+)\.md)$/m;

function render(): string {
  const lines: string[] = [];
  for (const { title, blurb, tools } of sections) {
    lines.push(`### ${title} — ${tools.length} endpoints\n`, `${blurb}\n`);
    lines.push("| Name | Endpoint | Effect | Documentation |", "| --- | --- | --- | --- |");
    for (const def of tools) {
      const endpoint = parseEndpoint(def.description);
      const [, url, page] = DOC_URL.exec(def.description) ?? [];
      if (!endpoint || !url) {
        throw new Error(
          `${def.name}: the description needs a "<METHOD> /v3/<path>" line and a page URL.`,
        );
      }
      lines.push(
        `| \`${def.name}\` | \`${endpoint.method} ${endpoint.path}\` | ${def.effect} | [${page}](${url}) |`,
      );
    }
    lines.push("");
  }
  return lines.join("\n");
}

const before = await readFile(DOC, "utf8");
const from = before.indexOf(START);
const to = before.indexOf(END);
if (from === -1 || to === -1 || to < from) {
  throw new Error(`docs/TOOLS.md must contain ${START} and ${END}, in that order`);
}

await writeFile(DOC, `${before.slice(0, from + START.length)}\n\n${render()}\n${before.slice(to)}`);

// The tables are emitted unaligned; prettier owns column widths, and the repo
// checks formatting in CI. Format here so a regenerated file is committable and
// so re-running this script is a genuine no-op.
const formatted = spawnSync(
  "npx",
  ["prettier", "--write", "--log-level", "warn", "docs/TOOLS.md"],
  { cwd: new URL("..", import.meta.url).pathname, shell: process.platform === "win32" },
);
if (formatted.status !== 0) {
  throw new Error(`prettier failed: ${formatted.stderr?.toString() ?? ""}`);
}

const total = sections.reduce((count, section) => count + section.tools.length, 0);
const changed = (await readFile(DOC, "utf8")) !== before;
console.error(
  changed
    ? `docs/TOOLS.md updated: ${total} tools`
    : `docs/TOOLS.md already up to date: ${total} tools`,
);
