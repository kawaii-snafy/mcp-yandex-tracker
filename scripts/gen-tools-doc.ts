/**
 * Rewrite the generated half of docs/TOOLS.md from the tool registry.
 *
 * The preamble above the marker is written by hand — calling convention, the
 * places the wrapper is not literal. Everything between the markers is derived
 * from the tools themselves, so the index cannot drift from the code.
 */

import { adminTools } from "../src/tools/admin.ts";
import { boardTools } from "../src/tools/boards.ts";
import { entityTools } from "../src/tools/entities.ts";
import { issueTools } from "../src/tools/issues.ts";
import { queueTools } from "../src/tools/queues.ts";
import { userTools } from "../src/tools/users.ts";
import type { ToolDef } from "../src/tool.ts";

const DOC = new URL("../docs/TOOLS.md", import.meta.url);
const START = "<!-- tools:start -->";
const END = "<!-- tools:end -->";

// Both are guaranteed by tests/tools.test.ts, which fails if a description
// lacks them or names an endpoint the tool does not call.
const ENDPOINT = /^(GET|POST|PATCH|DELETE) (\/v3\/\S*)$/m;
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
  [boardTools, "Boards & sprints", "Boards, their columns, and sprints."],
  [
    entityTools,
    "Projects, portfolios & goals",
    "The `entities` API, with their comments, checklists, attachments, links and permissions.",
  ],
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

const before = await Bun.file(DOC).text();
const from = before.indexOf(START);
const to = before.indexOf(END);
if (from === -1 || to === -1 || to < from) {
  throw new Error(`docs/TOOLS.md must contain ${START} and ${END}, in that order`);
}

await Bun.write(DOC, `${before.slice(0, from + START.length)}\n\n${render()}\n${before.slice(to)}`);

// The tables are emitted unaligned; prettier owns column widths, and the repo
// checks formatting in CI. Format here so a regenerated file is committable and
// so re-running this script is a genuine no-op.
const formatted = Bun.spawnSync(
  ["bunx", "prettier", "--write", "--log-level", "warn", "docs/TOOLS.md"],
  {
    cwd: new URL("..", import.meta.url).pathname,
  },
);
if (formatted.exitCode !== 0) {
  throw new Error(`prettier failed: ${formatted.stderr.toString()}`);
}

const total = SECTIONS.reduce((count, [tools]) => count + tools.length, 0);
const changed = (await Bun.file(DOC).text()) !== before;
console.error(
  changed
    ? `docs/TOOLS.md updated: ${total} tools`
    : `docs/TOOLS.md already up to date: ${total} tools`,
);
