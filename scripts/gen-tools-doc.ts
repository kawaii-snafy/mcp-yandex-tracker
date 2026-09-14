/**
 * Rewrite the generated half of docs/TOOLS.md from the tool registry.
 *
 * The preamble above the marker is written by hand — calling convention, the
 * places the wrapper is not literal. Everything between the markers is derived
 * from the tools themselves, so the index cannot drift from the code.
 */

import { spawnSync } from "node:child_process";
import { readFile, writeFile } from "node:fs/promises";
import { adminTools } from "../src/tools/admin.ts";
import { boardTools } from "../src/tools/boards.ts";
import { bulkchangeTools } from "../src/tools/bulkchange.ts";
import { dashboardTools } from "../src/tools/dashboards.ts";
import { entityTools } from "../src/tools/entities.ts";
import { filterTools } from "../src/tools/filters.ts";
import { gapTools } from "../src/tools/gaps.ts";
import { importTools } from "../src/tools/imports.ts";
import { issueTools } from "../src/tools/issues.ts";
import { macroTools } from "../src/tools/macros.ts";
import { projectTools } from "../src/tools/projects.ts";
import { queueTools } from "../src/tools/queues.ts";
import { userTools } from "../src/tools/users.ts";
import type { ToolDef } from "../src/tool.ts";

const DOC = new URL("../docs/TOOLS.md", import.meta.url);
const START = "<!-- tools:start -->";
const END = "<!-- tools:end -->";

// Both are guaranteed by tests/tools.test.ts, which fails if a description
// lacks them or names an endpoint the tool does not call.
const ENDPOINT = /^(GET|POST|PUT|PATCH|DELETE) (\/v3\/\S*)$/m;
const DOC_URL = /^(https:\/\/yandex\.ru\/support\/tracker\/en\/api\/([\w/-]+)\.md)$/m;

const SECTIONS: [readonly ToolDef[], string, string][] = [
  [
    issueTools,
    "Issues",
    "Issues, comments, checklists, attachments, worklog, links, transitions and the field dictionary.",
  ],
  [
    queueTools,
    "Queues",
    "Queues, versions, tags, permissions, local fields, workflows, triggers, autoactions and components.",
  ],
  [
    bulkchangeTools,
    "Bulk operations",
    "The same edit, move or transition applied to up to 10,000 issues, and the status of the operation.",
  ],
  [
    importTools,
    "Import",
    "Issues, comments, links, worklog records and files brought in from another tracker with their original authors and dates.",
  ],
  [filterTools, "Saved filters", "The issue filters saved in the Tracker interface."],
  [macroTools, "Queue macros", "The macros a queue offers when working on an issue."],
  [boardTools, "Boards & sprints", "Boards, their columns, and sprints."],
  [
    entityTools,
    "Projects, portfolios & goals",
    "The `entities` API, with their comments, checklists, attachments, links and permissions.",
  ],
  [
    projectTools,
    "Projects (older API)",
    "The projects API that predates `entities`; every page recommends its entity counterpart.",
  ],
  [dashboardTools, "Dashboards", "Dashboards and the Cycle time widget."],
  [gapTools, "Absences", "Employee absences: vacations, sick leaves and duty shifts."],
  [adminTools, "Reference dictionaries", "Issue types, statuses, resolutions and priorities."],
  [userTools, "Users", "The organization's users and the token owner."],
];

function render(): string {
  const lines: string[] = [];
  for (const [tools, title, blurb] of SECTIONS) {
    lines.push(`### ${title} — ${tools.length} tools\n`, `${blurb}\n`);
    lines.push("| Tool | Endpoint | Effect | Documentation |", "| --- | --- | --- | --- |");
    for (const def of tools) {
      const [, method, path] = ENDPOINT.exec(def.description)!;
      const [, url, page] = DOC_URL.exec(def.description)!;
      lines.push(`| \`${def.name}\` | \`${method} ${path}\` | ${def.effect} | [${page}](${url}) |`);
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

const total = SECTIONS.reduce((count, [tools]) => count + tools.length, 0);
const changed = (await readFile(DOC, "utf8")) !== before;
console.error(
  changed
    ? `docs/TOOLS.md updated: ${total} tools`
    : `docs/TOOLS.md already up to date: ${total} tools`,
);
