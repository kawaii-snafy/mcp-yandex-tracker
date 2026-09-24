/** Boards, columns and sprints — https://yandex.ru/support/tracker/en/api/boards/get-boards.md */

import { z } from "zod";
import { given, ifMatch, path } from "../client.ts";
import { tool } from "../tool.ts";

export const boardTools = [
  tool({
    name: "tracker_get_boards",
    description: `Get the parameters of all issue boards created by the organization users.

GET /v3/boards
https://yandex.ru/support/tracker/en/api/boards/get-boards.md`,
    input: {},
    run: (tracker) => tracker.request("GET", "/boards"),
  }),

  tool({
    name: "tracker_get_boards_paginate",
    description: `Get the parameters of all boards with relative pagination support.

GET /v3/boards/_paginate
https://yandex.ru/support/tracker/en/api/boards/get-boards-paginate.md

Boards are sorted by ascending ID and no more than 500 records are
returned; pass the ID of the last board of a page as \`id\` to get the next.`,
    input: {
      perPage: z
        .number()
        .int()
        .optional()
        .describe("The number of items per page, no more than 500."),
      id: z
        .number()
        .int()
        .optional()
        .describe("The board ID to start the next page of results from."),
    },
    run: (tracker, a) =>
      tracker.request("GET", "/boards/_paginate", {
        params: given({ perPage: a.perPage, id: a.id }),
      }),
  }),

  tool({
    name: "tracker_get_board",
    description: `Get the parameters of an issue board.

GET /v3/boards/{boardId}
https://yandex.ru/support/tracker/en/api/boards/get-board.md`,
    input: {
      boardId: z.string().min(1).describe("Board ID."),
    },
    run: (tracker, a) => tracker.request("GET", path`/boards/${a.boardId}`),
  }),

  tool({
    name: "tracker_create_board",
    description: `Create an issue board.

POST /v3/boards/
https://yandex.ru/support/tracker/en/api/boards/post-board.md`,
    input: {
      name: z.string().min(1).describe("Board name."),
      defaultQueue: z
        .union([z.string(), z.number(), z.record(z.string(), z.unknown())])
        .describe(
          "Default queue for creating issues. An object with `id` and `key`, a string (queue key), or a number (queue ID).",
        ),
      boardType: z
        .string()
        .optional()
        .describe("Board type: `default` (basic), `scrum`, or `kanban`."),
      filter: z
        .record(z.string(), z.unknown())
        .optional()
        .describe(
          "Filter conditions for selecting board issues, as field key to value or array of values. Incompatible with `query`.",
        ),
      orderBy: z.string().optional().describe("Key of the field used to sort board issues."),
      orderAsc: z
        .boolean()
        .optional()
        .describe("Sort direction: `true` ascending, `false` descending."),
      query: z
        .string()
        .optional()
        .describe(
          "Filter for selecting board issues, in the query language. Incompatible with `filter`, `orderBy` and `orderAsc`.",
        ),
      useRanking: z
        .boolean()
        .optional()
        .describe("Whether the order of issues on the board can be changed."),
      country: z
        .record(z.string(), z.unknown())
        .optional()
        .describe(
          'Country whose business calendar the burndown chart uses, as {"id": "<ID>"}. Get the IDs with GET /v3/countries.',
        ),
    },
    run: (tracker, a) =>
      tracker.request("POST", "/boards/", {
        body: given({
          name: a.name,
          defaultQueue: a.defaultQueue,
          boardType: a.boardType,
          filter: a.filter,
          orderBy: a.orderBy,
          orderAsc: a.orderAsc,
          query: a.query,
          useRanking: a.useRanking,
          country: a.country,
        }),
      }),
  }),

  tool({
    name: "tracker_patch_board",
    description: `Edit the parameters of an issue board.

PATCH /v3/boards/{boardId}
https://yandex.ru/support/tracker/en/api/boards/patch-board.md

The current version is the \`version\` field returned by tracker_get_board.`,
    input: {
      boardId: z.string().min(1).describe("Board ID."),
      name: z.string().optional().describe("Board name."),
      columns: z
        .array(z.unknown())
        .optional()
        .describe(
          "New board columns, each with `id`, `name` and `statuses` (keys of the issue statuses shown in the column).",
        ),
      filter: z
        .record(z.string(), z.unknown())
        .optional()
        .describe(
          "Filter conditions for selecting board issues, as field key to value or array of values. Incompatible with `query`.",
        ),
      orderBy: z.string().optional().describe("Key of the field used to sort board issues."),
      orderAsc: z
        .boolean()
        .optional()
        .describe("Sort direction: `true` ascending, `false` descending."),
      query: z
        .string()
        .optional()
        .describe(
          "Filter for selecting board issues, in the query language. Incompatible with `filter`, `orderBy` and `orderAsc`.",
        ),
      useRanking: z
        .boolean()
        .optional()
        .describe("Whether the order of issues on the board can be changed."),
      country: z
        .record(z.string(), z.unknown())
        .optional()
        .describe(
          'Country whose business calendar the burndown chart uses, as {"id": "<ID>"}. Get the IDs with GET /v3/countries.',
        ),
      version: z
        .number()
        .int()
        .optional()
        .describe(
          "Current board version. The change is applied only if the board is still at this version.",
        ),
    },
    run: (tracker, a) =>
      tracker.request("PATCH", path`/boards/${a.boardId}`, {
        body: given({
          name: a.name,
          columns: a.columns,
          filter: a.filter,
          orderBy: a.orderBy,
          orderAsc: a.orderAsc,
          query: a.query,
          useRanking: a.useRanking,
          country: a.country,
        }),
        headers: ifMatch(a.version),
      }),
  }),

  tool({
    name: "tracker_delete_board",
    description: `Delete an issue board.

DELETE /v3/boards/{boardId}
https://yandex.ru/support/tracker/en/api/boards/delete-board.md`,
    input: {
      boardId: z.string().min(1).describe("Board ID."),
    },
    run: (tracker, a) => tracker.request("DELETE", path`/boards/${a.boardId}`),
  }),

  tool({
    name: "tracker_get_board_columns",
    description: `Get the parameters of all columns of a board.

GET /v3/boards/{boardId}/columns
https://yandex.ru/support/tracker/en/api/boards/get-columns.md`,
    input: {
      boardId: z.string().min(1).describe("Board ID."),
    },
    run: (tracker, a) => tracker.request("GET", path`/boards/${a.boardId}/columns`),
  }),

  tool({
    name: "tracker_get_board_column",
    description: `Get the parameters of one column of a board.

GET /v3/boards/{boardId}/columns/{columnId}
https://yandex.ru/support/tracker/en/api/boards/get-column.md`,
    input: {
      boardId: z.string().min(1).describe("Board ID."),
      columnId: z.string().min(1).describe("Column ID."),
    },
    run: (tracker, a) => tracker.request("GET", path`/boards/${a.boardId}/columns/${a.columnId}`),
  }),

  tool({
    name: "tracker_create_board_column",
    description: `Create a column on an issue board.

POST /v3/boards/{boardId}/columns/
https://yandex.ru/support/tracker/en/api/boards/post-column.md

The current version is the \`version\` field returned by tracker_get_board.`,
    input: {
      boardId: z.string().min(1).describe("Board ID."),
      name: z.string().min(1).describe("Column name."),
      statuses: z
        .array(z.unknown())
        .describe("Keys of the issue statuses to be included in the column."),
      version: z
        .number()
        .int()
        .optional()
        .describe(
          "Current board version. The change is applied only if the board is still at this version.",
        ),
    },
    run: (tracker, a) =>
      tracker.request("POST", path`/boards/${a.boardId}/columns/`, {
        body: given({ name: a.name, statuses: a.statuses }),
        headers: ifMatch(a.version),
      }),
  }),

  tool({
    name: "tracker_patch_board_column",
    description: `Edit the parameters of a board column.

PATCH /v3/boards/{boardId}/columns/{columnId}
https://yandex.ru/support/tracker/en/api/boards/patch-column.md

The current version is the \`version\` field returned by tracker_get_board.`,
    input: {
      boardId: z.string().min(1).describe("Board ID."),
      columnId: z.string().min(1).describe("Column ID."),
      name: z.string().optional().describe("Column name."),
      statuses: z
        .array(z.unknown())
        .optional()
        .describe("Keys of the issue statuses to be included in the column."),
      version: z
        .number()
        .int()
        .optional()
        .describe(
          "Current board version. The change is applied only if the board is still at this version.",
        ),
    },
    run: (tracker, a) =>
      tracker.request("PATCH", path`/boards/${a.boardId}/columns/${a.columnId}`, {
        body: given({ name: a.name, statuses: a.statuses }),
        headers: ifMatch(a.version),
      }),
  }),

  tool({
    name: "tracker_delete_board_column",
    description: `Delete a board column.

DELETE /v3/boards/{boardId}/columns/{columnId}
https://yandex.ru/support/tracker/en/api/boards/delete-column.md

The current version is the \`version\` field returned by tracker_get_board.`,
    input: {
      boardId: z.string().min(1).describe("Board ID."),
      columnId: z.string().min(1).describe("Column ID."),
      version: z
        .number()
        .int()
        .optional()
        .describe(
          "Current board version. The change is applied only if the board is still at this version.",
        ),
    },
    run: (tracker, a) =>
      tracker.request("DELETE", path`/boards/${a.boardId}/columns/${a.columnId}`, {
        headers: ifMatch(a.version),
      }),
  }),

  tool({
    name: "tracker_get_board_sprints",
    description: `Get the parameters of all sprints of a board.

GET /v3/boards/{boardId}/sprints
https://yandex.ru/support/tracker/en/api/boards/get-sprints.md

Each sprint carries a \`status\`: \`draft\` (open), \`in_progress\` (in
progress), \`released\` (resolved) or \`archived\`. The sprint currently
running is the one with \`status: in_progress\`.`,
    input: {
      boardId: z.string().min(1).describe("Board ID."),
    },
    run: (tracker, a) => tracker.request("GET", path`/boards/${a.boardId}/sprints`),
  }),

  tool({
    name: "tracker_get_sprint",
    description: `Get the parameters of a sprint.

GET /v3/sprints/{sprintId}
https://yandex.ru/support/tracker/en/api/boards/get-sprint.md`,
    input: {
      sprintId: z.string().min(1).describe("Sprint ID."),
    },
    run: (tracker, a) => tracker.request("GET", path`/sprints/${a.sprintId}`),
  }),

  tool({
    name: "tracker_create_sprint",
    description: `Create a sprint.

POST /v3/sprints
https://yandex.ru/support/tracker/en/api/boards/post-sprint.md`,
    input: {
      name: z.string().min(1).describe("Sprint name."),
      board: z
        .record(z.string(), z.unknown())
        .describe('Board whose issues the sprint refers to, as {"id": "<board_ID>"}.'),
      startDate: z.string().min(1).describe("Sprint start date in YYYY-MM-DD format."),
      endDate: z.string().min(1).describe("Sprint end date in YYYY-MM-DD format."),
    },
    run: (tracker, a) =>
      tracker.request("POST", "/sprints", {
        body: given({
          name: a.name,
          board: a.board,
          startDate: a.startDate,
          endDate: a.endDate,
        }),
      }),
  }),

  tool({
    name: "tracker_patch_sprint",
    description: `Edit the parameters of a sprint.

PATCH /v3/sprints/{sprintId}
https://yandex.ru/support/tracker/en/api/boards/patch-sprint.md

The current version is the \`version\` field returned by tracker_get_sprint.`,
    input: {
      sprintId: z.string().min(1).describe("Sprint ID."),
      name: z.string().optional().describe("Sprint name."),
      startDate: z.string().optional().describe("Sprint start date in YYYY-MM-DD format."),
      endDate: z.string().optional().describe("Sprint end date in YYYY-MM-DD format."),
      status: z
        .string()
        .optional()
        .describe(
          "Sprint status: `draft` (open), `in_progress` (in progress), `released` (released) or `archived` (archived).",
        ),
      version: z
        .number()
        .int()
        .optional()
        .describe(
          "Sprint version. Specify it to avoid losing changes during simultaneous editing.",
        ),
    },
    run: (tracker, a) =>
      tracker.request("PATCH", path`/sprints/${a.sprintId}`, {
        body: given({
          name: a.name,
          startDate: a.startDate,
          endDate: a.endDate,
          status: a.status,
        }),
        headers: ifMatch(a.version),
      }),
  }),

  tool({
    name: "tracker_start_sprint",
    description: `Start a sprint, changing its status to \`in_progress\`.

POST /v3/sprints/{sprintId}/_start
https://yandex.ru/support/tracker/en/api/boards/start-sprint.md

The current version is the \`version\` field returned by tracker_get_sprint.`,
    effect: "modify",
    input: {
      sprintId: z.string().min(1).describe("Sprint ID."),
      version: z
        .number()
        .int()
        .optional()
        .describe(
          "Sprint version. Specify it to avoid losing changes during simultaneous editing.",
        ),
    },
    run: (tracker, a) =>
      tracker.request("POST", path`/sprints/${a.sprintId}/_start`, {
        headers: ifMatch(a.version),
      }),
  }),

  tool({
    name: "tracker_archive_sprint",
    description: `Archive a sprint.

POST /v3/sprints/{sprintId}/_archive
https://yandex.ru/support/tracker/en/api/boards/archive-sprint.md

The current version is the \`version\` field returned by tracker_get_sprint.`,
    effect: "modify",
    input: {
      sprintId: z.string().min(1).describe("Sprint ID."),
      version: z
        .number()
        .int()
        .optional()
        .describe(
          "Sprint version. Specify it to avoid losing changes during simultaneous editing.",
        ),
    },
    run: (tracker, a) =>
      tracker.request("POST", path`/sprints/${a.sprintId}/_archive`, {
        headers: ifMatch(a.version),
      }),
  }),

  tool({
    name: "tracker_delete_sprint",
    description: `Delete a sprint.

DELETE /v3/sprints/{sprintId}
https://yandex.ru/support/tracker/en/api/boards/delete-sprint.md`,
    input: {
      sprintId: z.string().min(1).describe("Sprint ID."),
    },
    run: (tracker, a) => tracker.request("DELETE", path`/sprints/${a.sprintId}`),
  }),
];
