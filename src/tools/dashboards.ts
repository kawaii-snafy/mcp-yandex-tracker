/** Dashboards and their widgets — https://yandex.ru/support/tracker/en/api/dashboards/create-dashboard.md */

import { z } from "zod";
import { given } from "../client.ts";
import { tool } from "../tool.ts";

export const dashboardTools = [
  tool({
    name: "tracker_create_dashboard",
    description: `Create a dashboard.

POST /v3/dashboards/
https://yandex.ru/support/tracker/en/api/dashboards/create-dashboard.md

Add the Cycle time widget to it with tracker_create_cycle_time_widget.`,
    input: {
      name: z.string().min(1).describe("Dashboard name."),
      layout: z
        .string()
        .optional()
        .describe(
          "Widget layout: `one-column` (default), `two-columns`, `three-columns`, `narrow-left-wide-right` or `one-top-two-bottom`.",
        ),
      owner: z
        .union([z.string(), z.number().int(), z.record(z.string(), z.unknown())])
        .optional()
        .describe("Username or ID of the dashboard owner. Defaults to the user creating it."),
    },
    run: (tracker, a) =>
      tracker.request("POST", "/dashboards/", {
        body: given({ name: a.name, layout: a.layout, owner: a.owner }),
      }),
  }),

  tool({
    name: "tracker_create_cycle_time_widget",
    description: `Add a "Cycle time" chart widget to an existing dashboard.

POST /v3/dashboards/{dashboardId}/widgets/cycleTime
https://yandex.ru/support/tracker/en/api/dashboards/create-widget.md`,
    input: {
      dashboardId: z.union([z.string(), z.number().int()]).describe("Dashboard ID."),
      description: z.string().min(1).describe("Widget name."),
      query: z.string().optional().describe("Issue filter in the query language."),
      filter: z
        .record(z.string(), z.unknown())
        .optional()
        .describe('Issue filter in `{"<field>": "<value>"}` format.'),
      filterId: z
        .union([z.string(), z.number().int()])
        .optional()
        .describe("ID of a saved filter."),
      fromStatuses: z
        .array(z.unknown())
        .optional()
        .describe(
          "Statuses the measurement starts from, as objects with `key`. Time in them is not counted. Defaults to the first status in the issue history.",
        ),
      toStatuses: z
        .array(z.unknown())
        .optional()
        .describe(
          "Statuses the measurement ends at, as objects with `key`. With several, the last one the issue moved to wins. Defaults to the last status in the issue history.",
        ),
      excludedStatuses: z
        .array(z.unknown())
        .optional()
        .describe("Statuses whose time is excluded from the calculation."),
      includedStatuses: z
        .array(z.unknown())
        .optional()
        .describe("Statuses whose time is included in the calculation."),
      bucket: z
        .record(z.string(), z.unknown())
        .optional()
        .describe(
          "Step of the chart: `unit` (`Days`, `Weeks`, `Months`, `Sprints`), `count` (always 1 for sprints) and `boardId` for sprints. Default 7 days.",
        ),
      calendar: z
        .number()
        .int()
        .optional()
        .describe("ID of the calendar to count working hours by. Defaults to the standard one."),
      lines: z
        .record(z.string(), z.unknown())
        .optional()
        .describe(
          "Lines on the time axis: `movingAverage`, `standardDeviation`, `percentile` (array) and `cakePercentile` (number).",
        ),
      start: z
        .string()
        .optional()
        .describe("Formula the calculation starts at, for example `now() - 2w`. Default 2 years."),
      end: z
        .string()
        .optional()
        .describe("Formula the calculation ends at, for example `now() - 2d`. Default `now()`."),
      mode: z
        .string()
        .optional()
        .describe(
          "Display mode: `common-lines`, `common-lines-and-points` or `status-lines` (a chart per status).",
        ),
      autoUpdatable: z.boolean().optional().describe("Refresh the chart automatically."),
    },
    run: (tracker, a) =>
      tracker.request("POST", `/dashboards/${a.dashboardId}/widgets/cycleTime`, {
        body: given({
          description: a.description,
          query: a.query,
          filter: a.filter,
          filterId: a.filterId,
          fromStatuses: a.fromStatuses,
          toStatuses: a.toStatuses,
          excludedStatuses: a.excludedStatuses,
          includedStatuses: a.includedStatuses,
          bucket: a.bucket,
          calendar: a.calendar,
          lines: a.lines,
          start: a.start,
          end: a.end,
          mode: a.mode,
          autoUpdatable: a.autoUpdatable,
        }),
      }),
  }),
];
