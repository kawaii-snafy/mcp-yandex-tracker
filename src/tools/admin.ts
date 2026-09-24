/** Reference dictionaries — https://yandex.ru/support/tracker/en/api/admin/get-statuses.md */

import { z } from "zod";
import { given, path } from "../client.ts";
import { tool } from "../tool.ts";

export const adminTools = [
  tool({
    name: "tracker_get_issuetypes",
    description: `Get the list of available issue types.

GET /v3/issuetypes
https://yandex.ru/support/tracker/en/api/admin/get-issue-types.md`,
    input: {},
    run: (tracker) => tracker.request("GET", "/issuetypes"),
  }),

  tool({
    name: "tracker_create_issuetype",
    description: `Create a new issue type.

POST /v3/issuetypes/
https://yandex.ru/support/tracker/en/api/admin/create-issue-type.md

Requires Administrator rights in the organization.`,
    input: {
      key: z.string().min(1).describe("Key of the issue type."),
      name: z
        .record(z.string(), z.unknown())
        .describe('Issue type name per language: {"ru": "Клиент", "en": "Customer"}.'),
    },
    run: (tracker, a) =>
      tracker.request("POST", "/issuetypes/", { body: given({ key: a.key, name: a.name }) }),
  }),

  tool({
    name: "tracker_patch_issuetype",
    description: `Modify an existing issue type.

PATCH /v3/issuetypes/{issueTypeId}
https://yandex.ru/support/tracker/en/api/admin/patch-issue-type.md

Requires Administrator rights. Call tracker_get_issuetypes to read the
current \`version\`.`,
    input: {
      issueTypeId: z
        .string()
        .min(1)
        .describe("Unique ID of the issue type in Yandex Tracker, or the issue type key."),
      version: z
        .number()
        .int()
        .optional()
        .describe(
          "Version of the issue type. Changes apply only to the current version of the issue type.",
        ),
      name: z
        .record(z.string(), z.unknown())
        .optional()
        .describe('Issue type name per language: {"ru": "Покупатель", "en": "Customer"}.'),
    },
    run: (tracker, a) =>
      tracker.request("PATCH", path`/issuetypes/${a.issueTypeId}`, {
        params: given({ version: a.version }),
        body: given({ name: a.name }),
      }),
  }),

  tool({
    name: "tracker_get_statuses",
    description: `Get the list of issue statuses.

GET /v3/statuses
https://yandex.ru/support/tracker/en/api/admin/get-statuses.md`,
    input: {},
    run: (tracker) => tracker.request("GET", "/statuses"),
  }),

  tool({
    name: "tracker_create_status",
    description: `Create a new issue status.

POST /v3/statuses/
https://yandex.ru/support/tracker/en/api/admin/create-status.md

Requires Administrator rights in the organization.`,
    input: {
      key: z
        .string()
        .min(1)
        .describe("Status key (ID). Use Latin characters only, starting with a lowercase letter."),
      name: z
        .record(z.string(), z.unknown())
        .describe('Status name per language: {"ru": "Мой статус", "en": "My status"}.'),
      type: z
        .string()
        .min(1)
        .describe(
          "Status type. Acceptable values include: `new`, `inProgress`, `paused`, `done`, `cancelled`.",
        ),
    },
    run: (tracker, a) =>
      tracker.request("POST", "/statuses/", {
        body: given({ key: a.key, name: a.name, type: a.type }),
      }),
  }),

  tool({
    name: "tracker_patch_status",
    description: `Change an existing issue status.

PATCH /v3/statuses/{statusId}
https://yandex.ru/support/tracker/en/api/admin/patch-status.md

Requires Administrator rights. Call tracker_get_statuses to read the
current \`version\`.`,
    input: {
      statusId: z
        .string()
        .min(1)
        .describe("Unique ID of the issue status in Yandex Tracker, or the status key."),
      version: z
        .number()
        .int()
        .optional()
        .describe("Version of the issue status. Changes are only made to the current version."),
      name: z
        .record(z.string(), z.unknown())
        .optional()
        .describe('Status name per language: {"ru": "Мой статус", "en": "My status"}.'),
      description: z.string().optional().describe("Status description."),
      order: z
        .number()
        .int()
        .optional()
        .describe(
          "Status weight. This parameter affects the order of status display in the interface.",
        ),
      type: z
        .string()
        .optional()
        .describe(
          "Status type. Acceptable values include: `new`, `inProgress`, `paused`, `done`, `cancelled`.",
        ),
    },
    run: (tracker, a) =>
      tracker.request("PATCH", path`/statuses/${a.statusId}`, {
        params: given({ version: a.version }),
        body: given({
          name: a.name,
          description: a.description,
          order: a.order,
          type: a.type,
        }),
      }),
  }),

  tool({
    name: "tracker_get_resolutions",
    description: `Get the list of resolutions.

GET /v3/resolutions
https://yandex.ru/support/tracker/en/api/admin/get-resolutions.md`,
    input: {},
    run: (tracker) => tracker.request("GET", "/resolutions"),
  }),

  tool({
    name: "tracker_create_resolution",
    description: `Create a new resolution.

POST /v3/resolutions/
https://yandex.ru/support/tracker/en/api/admin/create-resolution.md

Requires Administrator rights in the organization.`,
    input: {
      key: z
        .string()
        .min(1)
        .describe(
          "Resolution key (ID). Use Latin characters only, starting with a lowercase letter.",
        ),
      name: z
        .record(z.string(), z.unknown())
        .describe('Resolution name per language: {"ru": "Моя резолюция", "en": "My resolution"}.'),
    },
    run: (tracker, a) =>
      tracker.request("POST", "/resolutions/", { body: given({ key: a.key, name: a.name }) }),
  }),

  tool({
    name: "tracker_patch_resolution",
    description: `Make changes to a resolution.

PATCH /v3/resolutions/{resolutionId}
https://yandex.ru/support/tracker/en/api/admin/patch-resolution.md

Requires Administrator rights. Call tracker_get_resolutions to read the
current \`version\`.`,
    input: {
      resolutionId: z
        .string()
        .min(1)
        .describe("Unique ID of the resolution in Yandex Tracker, or the resolution key."),
      version: z
        .number()
        .int()
        .optional()
        .describe("Resolution version. Changes only apply to the current resolution version."),
      name: z
        .record(z.string(), z.unknown())
        .optional()
        .describe('Resolution name per language: {"ru": "Моя резолюция", "en": "My resolution"}.'),
      description: z.string().optional().describe("Resolution description."),
      order: z
        .number()
        .int()
        .optional()
        .describe(
          "Resolution weight. This parameter affects the order of resolution display in the interface.",
        ),
    },
    run: (tracker, a) =>
      tracker.request("PATCH", path`/resolutions/${a.resolutionId}`, {
        params: given({ version: a.version }),
        body: given({ name: a.name, description: a.description, order: a.order }),
      }),
  }),

  tool({
    name: "tracker_get_priorities",
    description: `Get the list of priorities for an issue.

GET /v3/priorities
https://yandex.ru/support/tracker/en/api/admin/get-priorities.md`,
    input: {
      localized: z
        .boolean()
        .optional()
        .describe(
          "Shows if the response contains translations. `true`: the response only contains priority descriptions in the user's language (default). `false`: the response contains priority descriptions in all supported languages.",
        ),
    },
    run: (tracker, a) =>
      tracker.request("GET", "/priorities", { params: given({ localized: a.localized }) }),
  }),

  tool({
    name: "tracker_create_priority",
    description: `Create a new priority for issues.

POST /v3/priorities/
https://yandex.ru/support/tracker/en/api/admin/create-priority.md

Requires Administrator rights in the organization.`,
    input: {
      name: z
        .record(z.string(), z.unknown())
        .describe(
          'Priority name per language: {"en": "English name", "ru": "Название на русском"}.',
        ),
      key: z.string().min(1).describe("Priority key."),
      order: z
        .number()
        .int()
        .describe(
          "Priority weight. This parameter affects the order in which the priority is displayed in the interface.",
        ),
      description: z.string().describe("Priority description."),
    },
    run: (tracker, a) =>
      tracker.request("POST", "/priorities/", {
        body: given({
          name: a.name,
          key: a.key,
          order: a.order,
          description: a.description,
        }),
      }),
  }),

  tool({
    name: "tracker_patch_priority",
    description: `Update a priority.

PATCH /v3/priorities/{priorityId}
https://yandex.ru/support/tracker/en/api/admin/patch-priority.md

Requires Administrator rights. This request cannot change a priority icon in
the Tracker interface. Call tracker_get_priorities to read the current
\`version\`.`,
    input: {
      priorityId: z
        .string()
        .min(1)
        .describe("The unique ID of the priority in Tracker, or the priority key."),
      version: z
        .number()
        .int()
        .optional()
        .describe(
          "The priority version. Changes are only applied to the current priority version.",
        ),
      name: z
        .record(z.string(), z.unknown())
        .optional()
        .describe(
          'Priority name per language: {"en": "English name", "ru": "Название на русском"}.',
        ),
      description: z.string().optional().describe("Priority description."),
    },
    run: (tracker, a) =>
      tracker.request("PATCH", path`/priorities/${a.priorityId}`, {
        params: given({ version: a.version }),
        body: given({ name: a.name, description: a.description }),
      }),
  }),
];
