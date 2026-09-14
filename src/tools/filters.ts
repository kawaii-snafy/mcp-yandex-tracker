/** Saved issue filters — https://yandex.ru/support/tracker/en/api/filters/get-filter.md */

import { z } from "zod";
import { given } from "../client.ts";
import { tool } from "../tool.ts";

const filter = z
  .record(z.string(), z.unknown())
  .describe(
    'Issue selection conditions, keyed by issue field: `{"assignee": "me()", "status": ["open", "inProgress"], "created": "2024-01-01..2024-12-31"}`. Not combinable with `query`.',
  );

const query = z
  .string()
  .describe("Issue selection conditions in the query language. Not combinable with `filter`.");

const fields = z
  .array(z.unknown())
  .describe(
    "Issue fields the Tracker UI shows for this filter. Affects the interface only, never an API response.",
  );

const sorts = z
  .array(z.unknown())
  .describe(
    "Sorting of the results: objects with `field` (issue field key) and `isAscending` (`true` ascending, `false` descending).",
  );

const groupBy = z
  .union([z.string(), z.record(z.string(), z.unknown())])
  .describe("Field the results are grouped by.");

const folder = z
  .union([z.string(), z.record(z.string(), z.unknown())])
  .describe("Folder the filter is saved in.");

export const filterTools = [
  tool({
    name: "tracker_get_filter",
    description: `Get the parameters of a saved issue filter.

GET /v3/filters/{filterId}
https://yandex.ru/support/tracker/en/api/filters/get-filter.md`,
    input: {
      filterId: z.union([z.string(), z.number().int()]).describe("Filter ID."),
    },
    run: (tracker, a) => tracker.request("GET", `/filters/${a.filterId}`),
  }),

  tool({
    name: "tracker_create_filter",
    description: `Create a saved issue filter.

POST /v3/filters/
https://yandex.ru/support/tracker/en/api/filters/create-filter.md`,
    input: {
      name: z.string().min(1).describe("Filter name."),
      filter: filter.optional(),
      query: query.optional(),
      fields: fields.optional(),
      sorts: sorts.optional(),
      groupBy: groupBy.optional(),
      folder: folder.optional(),
    },
    run: (tracker, a) =>
      tracker.request("POST", "/filters/", {
        body: given({
          name: a.name,
          filter: a.filter,
          query: a.query,
          fields: a.fields,
          sorts: a.sorts,
          groupBy: a.groupBy,
          folder: a.folder,
        }),
      }),
  }),

  tool({
    name: "tracker_update_filter",
    description: `Edit a saved issue filter.

PATCH /v3/filters/{filterId}
https://yandex.ru/support/tracker/en/api/filters/update-filter.md

\`filter\` is replaced whole rather than merged: send every condition the filter
should keep, not only the new ones.`,
    input: {
      filterId: z.union([z.string(), z.number().int()]).describe("Filter ID."),
      name: z.string().min(1).optional().describe("Filter name."),
      filter: filter.optional(),
      query: query.optional(),
      fields: fields.optional(),
      sorts: sorts.optional(),
      groupBy: groupBy.optional(),
      folder: folder.optional(),
    },
    run: (tracker, a) =>
      tracker.request("PATCH", `/filters/${a.filterId}`, {
        body: given({
          name: a.name,
          filter: a.filter,
          query: a.query,
          fields: a.fields,
          sorts: a.sorts,
          groupBy: a.groupBy,
          folder: a.folder,
        }),
      }),
  }),
];
