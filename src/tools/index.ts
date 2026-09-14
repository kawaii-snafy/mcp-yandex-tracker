/**
 * Every documented Yandex Tracker v3 endpoint, one tool each.
 *
 * Modules mirror the sections of the official documentation, so a doc page maps
 * to exactly one code file.
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

export const allTools: readonly ToolDef[] = [
  ...issueTools,
  ...bulkchangeTools,
  ...importTools,
  ...filterTools,
  ...queueTools,
  ...macroTools,
  ...boardTools,
  ...entityTools,
  ...projectTools,
  ...dashboardTools,
  ...gapTools,
  ...adminTools,
  ...userTools,
];
