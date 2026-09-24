/** Employee absences — https://yandex.ru/support/tracker/en/api/gaps/post-gaps.md */

import { z } from "zod";
import { given } from "../client.ts";
import { tool } from "../tool.ts";

export const gapTools = [
  tool({
    name: "tracker_create_gaps",
    description: `Record employee absences: vacations, sick leaves, duty shifts and the like.

POST /v3/gaps
https://yandex.ru/support/tracker/en/api/gaps/post-gaps.md

Requires Administrator rights in the organization.`,
    input: {
      gaps: z
        .array(z.unknown())
        .describe(
          "Absence records, at most 100. Each has `user` (login or ID), `workflow` (`vacation`, `paid_day_off`, `illness`, `absence`, `trip`, `conference_trip`, `conference`, `learning`, `maternity`, `duty`), `from` and `to` in ISO 8601, and optionally `id`, `fullDay` and `workInAbsence`.",
        ),
    },
    run: (tracker, a) => tracker.request("POST", "/gaps", { body: { gaps: a.gaps } }),
  }),

  tool({
    name: "tracker_search_gaps",
    description: `Find the absences of given users that overlap a time window.

POST /v3/gaps/_search
https://yandex.ru/support/tracker/en/api/gaps/search-gaps.md

Requires Administrator rights in the organization. Results are grouped by user;
a user with no absences in the window comes back with an empty list.`,
    effect: "read",
    input: {
      users: z
        .array(z.unknown())
        .describe("Logins or IDs of the users to get absences for, at most 100."),
      from: z
        .string()
        .optional()
        .describe("Start of the search window in ISO 8601 format. Defaults to the current time."),
      to: z
        .string()
        .optional()
        .describe("End of the search window in ISO 8601 format. Must be later than `from`."),
      perPage: z.number().int().optional().describe("Users per response page. Default 50."),
      page: z.number().int().optional().describe("Page number of the paginated output. Default 1."),
    },
    run: (tracker, a) =>
      tracker.request("POST", "/gaps/_search", {
        params: given({ perPage: a.perPage, page: a.page }),
        body: given({ users: a.users, from: a.from, to: a.to }),
      }),
  }),

  tool({
    name: "tracker_delete_gaps",
    description: `Delete absence records by ID.

DELETE /v3/gaps
https://yandex.ru/support/tracker/en/api/gaps/delete-gaps.md

Requires Administrator rights in the organization. An ID that does not exist is
ignored rather than reported.`,
    input: {
      gapIds: z
        .array(z.string())
        .describe(
          "IDs of the absence records to delete, at most 100 and each at most 128 characters.",
        ),
    },
    // The page spells this parameter as one comma-separated value rather than a
    // repeated key, which is what the array would otherwise become.
    run: (tracker, a) =>
      tracker.request("DELETE", "/gaps", { params: { gapIds: a.gapIds.join(",") } }),
  }),
];
