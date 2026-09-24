/** Queue macros — https://yandex.ru/support/tracker/en/api/get-macroses.md */

import { z } from "zod";
import { given, path } from "../client.ts";
import { tool } from "../tool.ts";

const queueId = z.string().min(1).describe("Queue ID or key. The key is case-sensitive.");
const macroId = z.string().min(1).describe("Macro ID.");

const body = z
  .string()
  .describe(
    'Message the macro creates when it runs. Use `{"unset": 1}` to delete the message instead.',
  );

const issueUpdate = z
  .record(z.string(), z.unknown())
  .describe(
    "Issue fields the macro changes, keyed by field ID. `null` clears a field; the `set`, `add` and `remove` operators apply here too.",
  );

export const macroTools = [
  tool({
    name: "tracker_get_macros",
    description: `Get every macro defined in a queue.

GET /v3/queues/{queueId}/macros
https://yandex.ru/support/tracker/en/api/get-macroses.md`,
    input: { queueId },
    run: (tracker, a) => tracker.request("GET", path`/queues/${a.queueId}/macros`),
  }),

  tool({
    name: "tracker_get_macro",
    description: `Get one macro of a queue.

GET /v3/queues/{queueId}/macros/{macroId}
https://yandex.ru/support/tracker/en/api/get-macros.md`,
    input: { queueId, macroId },
    run: (tracker, a) => tracker.request("GET", path`/queues/${a.queueId}/macros/${a.macroId}`),
  }),

  tool({
    name: "tracker_create_macro",
    description: `Create a macro in a queue.

POST /v3/queues/{queueId}/macros
https://yandex.ru/support/tracker/en/api/post-macros.md`,
    input: {
      queueId,
      name: z.string().min(1).describe("Macro name."),
      body: body.optional(),
      issueUpdate: issueUpdate.optional(),
    },
    run: (tracker, a) =>
      tracker.request("POST", path`/queues/${a.queueId}/macros`, {
        body: given({ name: a.name, body: a.body, issueUpdate: a.issueUpdate }),
      }),
  }),

  tool({
    name: "tracker_patch_macro",
    description: `Edit a macro of a queue.

PATCH /v3/queues/{queueId}/macros/{macroId}
https://yandex.ru/support/tracker/en/api/patch-macros.md`,
    input: {
      queueId,
      macroId,
      name: z.string().min(1).describe("Macro name."),
      body: body.optional(),
      issueUpdate: issueUpdate.optional(),
    },
    run: (tracker, a) =>
      tracker.request("PATCH", path`/queues/${a.queueId}/macros/${a.macroId}`, {
        body: given({ name: a.name, body: a.body, issueUpdate: a.issueUpdate }),
      }),
  }),

  tool({
    name: "tracker_delete_macro",
    description: `Delete a macro of a queue.

DELETE /v3/queues/{queueId}/macros/{macroId}
https://yandex.ru/support/tracker/en/api/delete-macros.md`,
    input: { queueId, macroId },
    run: (tracker, a) => tracker.request("DELETE", path`/queues/${a.queueId}/macros/${a.macroId}`),
  }),
];
