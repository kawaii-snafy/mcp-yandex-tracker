/**
 * Every documented Yandex Tracker v3 endpoint, one tool each.
 *
 * Modules mirror the sections of the official documentation, so a doc page maps
 * to exactly one code file, and `sections` below names each of them. That list
 * is the registry's table of contents: the `tracker_api` catalogue, the
 * `tracker://api` resource and `docs/TOOLS.md` are all rendered from it, so a
 * new module has to be added here exactly once to appear in all three.
 */

import type { ToolDef } from "../tool.ts";
import { adminTools } from "./admin.ts";
import { boardTools } from "./boards.ts";
import { bulkchangeTools } from "./bulkchange.ts";
import { dashboardTools } from "./dashboards.ts";
import { entityTools } from "./entities.ts";
import { filterTools } from "./filters.ts";
import { gapTools } from "./gaps.ts";
import { importTools } from "./imports.ts";
import { issueTools } from "./issues.ts";
import { macroTools } from "./macros.ts";
import { projectTools } from "./projects.ts";
import { queueTools } from "./queues.ts";
import { userTools } from "./users.ts";

export type ToolSection = {
  /** Slug the catalogue and the `tracker://api/{section}` resource address it by. */
  readonly id: string;
  /** Heading for `docs/TOOLS.md`. */
  readonly title: string;
  /** The one line that has to tell an agent whether the section is the one it wants. */
  readonly blurb: string;
  readonly tools: readonly ToolDef[];
};

export const sections: readonly ToolSection[] = [
  {
    id: "issues",
    title: "Issues",
    blurb:
      "Issues, comments, checklists, attachments, worklog, links, transitions and the field dictionary.",
    tools: issueTools,
  },
  {
    id: "queues",
    title: "Queues",
    blurb:
      "Queues, versions, tags, permissions, local fields, workflows, triggers, autoactions and components.",
    tools: queueTools,
  },
  {
    id: "bulkchange",
    title: "Bulk operations",
    blurb:
      "The same edit, move or transition applied to up to 10,000 issues, and the status of the operation.",
    tools: bulkchangeTools,
  },
  {
    id: "imports",
    title: "Import",
    blurb:
      "Issues, comments, links, worklog records and files brought in from another tracker with their original authors and dates.",
    tools: importTools,
  },
  {
    id: "filters",
    title: "Saved filters",
    blurb: "The issue filters saved in the Tracker interface.",
    tools: filterTools,
  },
  {
    id: "macros",
    title: "Queue macros",
    blurb: "The macros a queue offers when working on an issue.",
    tools: macroTools,
  },
  {
    id: "boards",
    title: "Boards & sprints",
    blurb: "Boards, their columns, and sprints.",
    tools: boardTools,
  },
  {
    id: "entities",
    title: "Projects, portfolios & goals",
    blurb:
      "The `entities` API, with their comments, checklists, attachments, links and permissions.",
    tools: entityTools,
  },
  {
    id: "projects",
    title: "Projects (older API)",
    blurb:
      "The projects API that predates `entities`; every page recommends its entity counterpart.",
    tools: projectTools,
  },
  {
    id: "dashboards",
    title: "Dashboards",
    blurb: "Dashboards and the Cycle time widget.",
    tools: dashboardTools,
  },
  {
    id: "gaps",
    title: "Absences",
    blurb: "Employee absences: vacations, sick leaves and duty shifts.",
    tools: gapTools,
  },
  {
    id: "admin",
    title: "Reference dictionaries",
    blurb: "Issue types, statuses, resolutions and priorities.",
    tools: adminTools,
  },
  {
    id: "users",
    title: "Users",
    blurb: "The organization's users and the token owner.",
    tools: userTools,
  },
];

export const allTools: readonly ToolDef[] = sections.flatMap((section) => section.tools);

/** The registry keyed the way `tracker_api`, `tracker_read` and `tracker_call` look it up. */
export const toolsByName: ReadonlyMap<string, ToolDef> = new Map(
  allTools.map((def) => [def.name, def]),
);
