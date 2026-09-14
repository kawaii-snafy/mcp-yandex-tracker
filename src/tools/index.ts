/**
 * Every documented Yandex Tracker v3 endpoint, one tool each.
 *
 * Modules mirror the sections of the official documentation, so a doc page maps
 * to exactly one code file.
 */

import type { ToolDef } from "../tool.ts";
import { adminTools } from "./admin.ts";
import { boardTools } from "./boards.ts";
import { entityTools } from "./entities.ts";
import { issueTools } from "./issues.ts";
import { queueTools } from "./queues.ts";
import { userTools } from "./users.ts";

export const allTools: readonly ToolDef[] = [
  ...issueTools,
  ...queueTools,
  ...boardTools,
  ...entityTools,
  ...adminTools,
  ...userTools,
];
