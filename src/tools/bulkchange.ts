/** Bulk issue operations — https://yandex.ru/support/tracker/en/api/bulkchange/bulk-update-issues.md */

import { z } from "zod";
import { given } from "../client.ts";
import { tool } from "../tool.ts";

/**
 * The issue selector every bulk operation takes: a list of keys, or a filter in
 * the query language that Tracker resolves to one.
 */
const issues = z
  .union([z.array(z.unknown()), z.string()])
  .describe(
    "Issues to change: an array of issue keys, or a filter in the query language. Up to 10,000 issues per operation.",
  );

const notify = z
  .boolean()
  .optional()
  .describe(
    "Notify the users named in the issue fields about the change. Default `false`, unlike most other endpoints.",
  );

const values = z
  .record(z.string(), z.unknown())
  .describe(
    "Issue parameters to update, in the same format as when editing an issue. The `set`, `add` and `remove` operators apply here too.",
  );

export const bulkchangeTools = [
  tool({
    name: "tracker_bulk_update_issues",
    description: `Apply the same edit to many issues at once.

POST /v3/bulkchange/_update
https://yandex.ru/support/tracker/en/api/bulkchange/bulk-update-issues.md

Returns the bulk operation, not the issues: poll it with
tracker_get_bulkchange and list its failures with tracker_get_bulkchange_issues.`,
    effect: "modify",
    input: {
      issues,
      values,
      notify,
    },
    run: (tracker, a) =>
      tracker.request("POST", "/bulkchange/_update", {
        params: given({ notify: a.notify }),
        body: given({ issues: a.issues, values: a.values }),
      }),
  }),

  tool({
    name: "tracker_bulk_move_issues",
    description: `Move many issues to another queue at once.

POST /v3/bulkchange/_move
https://yandex.ru/support/tracker/en/api/bulkchange/bulk-move-issues.md

Returns the bulk operation, not the issues: poll it with
tracker_get_bulkchange and list its failures with tracker_get_bulkchange_issues.`,
    effect: "modify",
    input: {
      queue: z.string().min(1).describe("Key of the queue to move the issues to."),
      issues,
      values: values.optional(),
      moveAllFields: z
        .boolean()
        .optional()
        .describe(
          "Move the issues' versions, components and projects when the target queue has matching ones. Default `false`, which clears them.",
        ),
      initialStatus: z
        .boolean()
        .optional()
        .describe(
          "Reset each issue to the initial status of the target queue's workflow. Default `false`, which keeps the current status.",
        ),
      notify,
    },
    run: (tracker, a) =>
      tracker.request("POST", "/bulkchange/_move", {
        params: given({ notify: a.notify }),
        body: given({
          queue: a.queue,
          issues: a.issues,
          values: a.values,
          moveAllFields: a.moveAllFields,
          initialStatus: a.initialStatus,
        }),
      }),
  }),

  tool({
    name: "tracker_bulk_transition_issues",
    description: `Run the same workflow transition on many issues at once.

POST /v3/bulkchange/_transition
https://yandex.ru/support/tracker/en/api/bulkchange/bulk-transition.md

Transitions available for an issue come from tracker_get_transitions. A
transition into a status such as Closed needs the resolution in \`values\`.`,
    effect: "modify",
    input: {
      transition: z.string().min(1).describe("ID of the transition to execute."),
      issues,
      values: values.optional(),
      notify,
    },
    run: (tracker, a) =>
      tracker.request("POST", "/bulkchange/_transition", {
        params: given({ notify: a.notify }),
        body: given({ transition: a.transition, issues: a.issues, values: a.values }),
      }),
  }),

  tool({
    name: "tracker_get_bulkchange",
    description: `Get the status and progress of a bulk operation.

GET /v3/bulkchange/{bulkchangeId}
https://yandex.ru/support/tracker/en/api/bulkchange/bulk-move-info.md`,
    input: {
      bulkchangeId: z
        .string()
        .min(1)
        .describe("ID of the bulk operation, as returned when it was started."),
    },
    run: (tracker, a) => tracker.request("GET", `/bulkchange/${a.bulkchangeId}`),
  }),

  tool({
    name: "tracker_get_bulkchange_issues",
    description: `List the issues a bulk operation failed on, with the reason for each.

GET /v3/bulkchange/{bulkchangeId}/issues
https://yandex.ru/support/tracker/en/api/bulkchange/bulk-move-info.md`,
    input: {
      bulkchangeId: z
        .string()
        .min(1)
        .describe("ID of the bulk operation, as returned when it was started."),
    },
    run: (tracker, a) => tracker.request("GET", `/bulkchange/${a.bulkchangeId}/issues`),
  }),
];
