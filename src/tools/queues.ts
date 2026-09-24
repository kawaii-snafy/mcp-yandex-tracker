/** Queues, local fields, workflows, triggers and components — https://yandex.ru/support/tracker/en/api/queues/get-queues.md */

import { z } from "zod";
import { given, path } from "../client.ts";
import { tool } from "../tool.ts";

export const queueTools = [
  tool({
    name: "tracker_create_queue",
    description: `Create a queue.

POST /v3/queues/
https://yandex.ru/support/tracker/en/api/queues/create-queue.md`,
    input: {
      key: z.string().min(1).describe("Queue key."),
      name: z.string().min(1).describe("Queue name."),
      lead: z.string().min(1).describe("Username or ID of the queue owner."),
      defaultType: z.string().min(1).describe("ID or key of the default issue type."),
      defaultPriority: z.string().min(1).describe("ID or key of the default issue priority."),
      issueTypesConfig: z
        .array(z.unknown())
        .describe(
          "Settings of queue issue types, one object per issue type, each with `issueType` (issue type key), `workflow` (workflow ID, for example `hrPresetWorkflow`, `developmentPresetWorkflow` or `scrumDevelopmentPresetWorkflow`) and `resolutions` (array of resolution IDs or keys).",
        ),
    },
    run: (tracker, a) =>
      tracker.request("POST", "/queues/", {
        body: given({
          key: a.key,
          name: a.name,
          lead: a.lead,
          defaultType: a.defaultType,
          defaultPriority: a.defaultPriority,
          issueTypesConfig: a.issueTypesConfig,
        }),
      }),
  }),

  tool({
    name: "tracker_get_queues",
    description: `Get the list of available queues.

GET /v3/queues/
https://yandex.ru/support/tracker/en/api/queues/get-queues.md

With more than 50 queues the result is paginated: \`perPage\` and \`page\` are
the pagination parameters from common-format.md the endpoint page links to.`,
    input: {
      expand: z
        .string()
        .optional()
        .describe(
          "Additional fields to include in the response: `projects`, `components`, `versions`, `types`, `team`, `workflows`.",
        ),
      perPage: z
        .number()
        .int()
        .optional()
        .describe("Number of queues per response page. Default 50."),
      page: z.number().int().optional().describe("Page number. Default 1."),
    },
    run: (tracker, a) =>
      tracker.request("GET", "/queues/", {
        params: given({ expand: a.expand, perPage: a.perPage, page: a.page }),
      }),
  }),

  tool({
    name: "tracker_get_queue",
    description: `Get information about a queue.

GET /v3/queues/{queueId}
https://yandex.ru/support/tracker/en/api/queues/get-queue.md

This is also how you list the components of one queue: pass
\`expand=components\`. GET /v3/components returns every component of the
organization instead.`,
    input: {
      queueId: z.string().min(1).describe("Queue ID or key. The queue key is case-sensitive."),
      expand: z
        .string()
        .optional()
        .describe(
          "Additional fields to include in the response: `all`, `projects`, `components`, `versions`, `types`, `team`, `workflows`, `fields`, `issueTypesConfig`.",
        ),
    },
    run: (tracker, a) =>
      tracker.request("GET", path`/queues/${a.queueId}`, { params: given({ expand: a.expand }) }),
  }),

  tool({
    name: "tracker_delete_queue",
    description: `Delete a queue.

DELETE /v3/queues/{queueId}
https://yandex.ru/support/tracker/en/api/queues/delete-queue.md`,
    input: {
      queueId: z.string().min(1).describe("Queue ID or key. The queue key is case-sensitive."),
    },
    run: (tracker, a) => tracker.request("DELETE", path`/queues/${a.queueId}`),
  }),

  tool({
    name: "tracker_restore_queue",
    description: `Restore a deleted queue.

POST /v3/queues/{queueId}/_restore
https://yandex.ru/support/tracker/en/api/queues/restore-queue.md

Only an organization administrator can make this request.`,
    effect: "modify",
    input: {
      queueId: z.string().min(1).describe("Queue ID or key. The queue key is case-sensitive."),
    },
    run: (tracker, a) => tracker.request("POST", path`/queues/${a.queueId}/_restore`),
  }),

  tool({
    name: "tracker_get_queue_fields",
    description: `Get information about the required fields of a queue.

GET /v3/queues/{queueId}/fields
https://yandex.ru/support/tracker/en/api/queues/get-fields.md`,
    input: {
      queueId: z.string().min(1).describe("Queue ID or key. The queue key is case-sensitive."),
    },
    run: (tracker, a) => tracker.request("GET", path`/queues/${a.queueId}/fields`),
  }),

  tool({
    name: "tracker_get_queue_versions",
    description: `Get information about the versions of a queue.

GET /v3/queues/{queueId}/versions
https://yandex.ru/support/tracker/en/api/queues/get-versions.md`,
    input: {
      queueId: z.string().min(1).describe("Queue ID or key. The queue key is case-sensitive."),
    },
    run: (tracker, a) => tracker.request("GET", path`/queues/${a.queueId}/versions`),
  }),

  tool({
    name: "tracker_create_version",
    description: `Create a queue version.

POST /v3/versions/
https://yandex.ru/support/tracker/en/api/queues/create-version.md`,
    input: {
      queue: z.string().min(1).describe("Queue key."),
      name: z.string().min(1).describe("Version name."),
      description: z.string().optional().describe("Version description."),
      startDate: z.string().optional().describe("Version start date in `YYYY-MM-DD` format."),
      dueDate: z.string().optional().describe("Version end date in `YYYY-MM-DD` format."),
    },
    run: (tracker, a) =>
      tracker.request("POST", "/versions/", {
        body: given({
          queue: a.queue,
          name: a.name,
          description: a.description,
          startDate: a.startDate,
          dueDate: a.dueDate,
        }),
      }),
  }),

  tool({
    name: "tracker_get_queue_tags",
    description: `Get the list of tags added to a queue.

GET /v3/queues/{queueId}/tags
https://yandex.ru/support/tracker/en/api/queues/get-tags.md`,
    input: {
      queueId: z.string().min(1).describe("Queue ID or key. The queue key is case-sensitive."),
    },
    run: (tracker, a) => tracker.request("GET", path`/queues/${a.queueId}/tags`),
  }),

  tool({
    name: "tracker_delete_queue_tag",
    description: `Remove a tag from a queue.

POST /v3/queues/{queueId}/tags/_remove
https://yandex.ru/support/tracker/en/api/queues/delete-tag.md

Only a Yandex Tracker administrator can remove tags, and only tags that are
not used in any issue of the queue.`,
    effect: "modify",
    input: {
      queueId: z.string().min(1).describe("Queue ID or key. The queue key is case-sensitive."),
      tag: z.string().min(1).describe("Tag name."),
    },
    run: (tracker, a) =>
      tracker.request("POST", path`/queues/${a.queueId}/tags/_remove`, {
        body: given({ tag: a.tag }),
      }),
  }),

  tool({
    name: "tracker_patch_queue_permissions",
    description: `Set up the access permissions of a queue.

PATCH /v3/queues/{queueId}/permissions
https://yandex.ru/support/tracker/en/api/queues/manage-access.md

Specify at least one of the four permission fields.`,
    input: {
      queueId: z.string().min(1).describe("Queue ID or key. The queue key is case-sensitive."),
      create: z
        .record(z.string(), z.unknown())
        .optional()
        .describe(
          "Permissions to create issues in the queue, as `users`, `groups` and `roles` lists. Each list is either an array of IDs (which overrides the current permissions) or an object with `add` and `remove` arrays. Roles are `author`, `assignee`, `follower`, `access`.",
        ),
      write: z
        .record(z.string(), z.unknown())
        .optional()
        .describe("Permissions to edit issues in the queue, in the same format as `create`."),
      read: z
        .record(z.string(), z.unknown())
        .optional()
        .describe("Permissions to read issues in the queue, in the same format as `create`."),
      grant: z
        .record(z.string(), z.unknown())
        .optional()
        .describe("Permissions to update queue settings, in the same format as `create`."),
    },
    run: (tracker, a) =>
      tracker.request("PATCH", path`/queues/${a.queueId}/permissions`, {
        body: given({ create: a.create, write: a.write, read: a.read, grant: a.grant }),
      }),
  }),

  tool({
    name: "tracker_get_queue_user_access",
    description: `Get the permissions of one user for a queue.

GET /v3/queues/{queueId}/permissions/users/{userId}
https://yandex.ru/support/tracker/en/api/queues/get-user-access.md`,
    input: {
      queueId: z.string().min(1).describe("Queue ID or key. The queue key is case-sensitive."),
      userId: z.string().min(1).describe("Unique ID of the account or the user login."),
    },
    run: (tracker, a) =>
      tracker.request("GET", path`/queues/${a.queueId}/permissions/users/${a.userId}`),
  }),

  tool({
    name: "tracker_get_queue_group_access",
    description: `Get the permissions of one group for a queue.

GET /v3/queues/{queueId}/permissions/groups/{groupId}
https://yandex.ru/support/tracker/en/api/queues/get-group-access.md`,
    input: {
      queueId: z.string().min(1).describe("Queue ID or key. The queue key is case-sensitive."),
      groupId: z.string().min(1).describe("Unique group ID in the organization."),
    },
    run: (tracker, a) =>
      tracker.request("GET", path`/queues/${a.queueId}/permissions/groups/${a.groupId}`),
  }),

  tool({
    name: "tracker_create_local_field",
    description: `Create a local issue field linked to a queue.

POST /v3/queues/{queueId}/localFields
https://yandex.ru/support/tracker/en/api/queues/create-local-field.md`,
    input: {
      queueId: z.string().min(1).describe("Queue ID or key. The queue key is case-sensitive."),
      name: z
        .record(z.string(), z.unknown())
        .describe("Local field name: `en` in English, `ru` in Russian."),
      id: z.string().min(1).describe("Local field ID."),
      category: z
        .string()
        .min(1)
        .describe("Field category ID. Get the list of categories with GET /v3/fields/categories."),
      type: z
        .string()
        .min(1)
        .describe(
          "Local field type: `ru.yandex.startrek.core.fields.DateFieldType`, `ru.yandex.startrek.core.fields.DateTimeFieldType`, `ru.yandex.startrek.core.fields.StringFieldType`, `ru.yandex.startrek.core.fields.TextFieldType`, `ru.yandex.startrek.core.fields.FloatFieldType`, `ru.yandex.startrek.core.fields.IntegerFieldType`, `ru.yandex.startrek.core.fields.UserFieldType`, `ru.yandex.startrek.core.fields.UriFieldType`, `ru.yandex.startrek.core.fields.MoneyFieldType`, `ru.yandex.startrek.core.fields.MoneyWithRateFieldType`, `ru.yandex.startrek.core.fields.TimeTrackingDurationFieldType`.",
        ),
      optionsProvider: z
        .record(z.string(), z.unknown())
        .optional()
        .describe(
          "Drop-down list items: `type` (`FixedListOptionsProvider` for strings or numbers, `FixedUserListOptionsProvider` for users) and `values` (array of list values, up to 3000).",
        ),
      order: z
        .number()
        .int()
        .optional()
        .describe("Sequence number in the list of organization fields."),
      description: z.string().optional().describe("Local field description."),
      readonly: z
        .boolean()
        .optional()
        .describe("Whether the field value is non-editable: `true` or `false`."),
      visible: z
        .boolean()
        .optional()
        .describe("Whether the field is always visible in the interface."),
      hidden: z.boolean().optional().describe("Whether to hide the field even if it is not empty."),
      container: z
        .boolean()
        .optional()
        .describe(
          "Whether the field accepts multiple values, like **Tags**. Applies to one-line text, user and drop-down list fields.",
        ),
    },
    run: (tracker, a) =>
      tracker.request("POST", path`/queues/${a.queueId}/localFields`, {
        body: given({
          name: a.name,
          id: a.id,
          category: a.category,
          type: a.type,
          optionsProvider: a.optionsProvider,
          order: a.order,
          description: a.description,
          readonly: a.readonly,
          visible: a.visible,
          hidden: a.hidden,
          container: a.container,
        }),
      }),
  }),

  tool({
    name: "tracker_get_local_fields",
    description: `Get the local issue fields linked to a queue.

GET /v3/queues/{queueId}/localFields
https://yandex.ru/support/tracker/en/api/queues/get-local-fields.md`,
    input: {
      queueId: z.string().min(1).describe("Queue ID or key. The queue key is case-sensitive."),
    },
    run: (tracker, a) => tracker.request("GET", path`/queues/${a.queueId}/localFields`),
  }),

  tool({
    name: "tracker_get_local_field",
    description: `Get information about one local queue field.

GET /v3/queues/{queueId}/localFields/{fieldKey}
https://yandex.ru/support/tracker/en/api/queues/get-info-local-field.md`,
    input: {
      queueId: z.string().min(1).describe("Queue ID or key. The queue key is case-sensitive."),
      fieldKey: z
        .string()
        .min(1)
        .describe("Local field key. Get it with GET /v3/queues/{queueId}/localFields."),
    },
    run: (tracker, a) =>
      tracker.request("GET", path`/queues/${a.queueId}/localFields/${a.fieldKey}`),
  }),

  tool({
    name: "tracker_patch_local_field",
    description: `Edit a local issue field linked to a queue.

PATCH /v3/queues/{queueId}/localFields/{fieldKey}
https://yandex.ru/support/tracker/en/api/queues/edit-local-field.md`,
    input: {
      queueId: z.string().min(1).describe("Queue ID or key. The queue key is case-sensitive."),
      fieldKey: z
        .string()
        .min(1)
        .describe("Local field key. Get it with GET /v3/queues/{queueId}/localFields."),
      name: z
        .record(z.string(), z.unknown())
        .optional()
        .describe("Local field name: `en` in English, `ru` in Russian."),
      category: z
        .string()
        .optional()
        .describe("Field category ID. Get the list of categories with GET /v3/fields/categories."),
      order: z
        .number()
        .int()
        .optional()
        .describe("Sequence number in the list of organization fields."),
      description: z.string().optional().describe("Local field description."),
      optionsProvider: z
        .record(z.string(), z.unknown())
        .optional()
        .describe(
          "Drop-down list items: `type` (`FixedListOptionsProvider` or `FixedUserListOptionsProvider`) and `values` (array of list values).",
        ),
      readonly: z
        .boolean()
        .optional()
        .describe("Whether the field value is non-editable: `true` or `false`."),
      visible: z
        .boolean()
        .optional()
        .describe("Whether the field always appears in issues, even when it has no value."),
      hidden: z
        .boolean()
        .optional()
        .describe("Whether the field is hidden completely, even when it contains a value."),
    },
    run: (tracker, a) =>
      tracker.request("PATCH", path`/queues/${a.queueId}/localFields/${a.fieldKey}`, {
        body: given({
          name: a.name,
          category: a.category,
          order: a.order,
          description: a.description,
          optionsProvider: a.optionsProvider,
          readonly: a.readonly,
          visible: a.visible,
          hidden: a.hidden,
        }),
      }),
  }),

  tool({
    name: "tracker_create_workflow",
    description: `Create a workflow.

POST /v3/workflows
https://yandex.ru/support/tracker/en/api/queues/workflows/post-workflow.md`,
    input: {
      name: z.string().min(1).describe("Workflow name."),
      initialAction: z
        .record(z.string(), z.unknown())
        .describe(
          "Initial action that sets the status assigned to an issue when it is created: `name` (localized object) and `target` (status key, ID or object) are required, plus optional `id`, `description`, `screen`, `conditions` and `functions`.",
        ),
      steps: z
        .array(z.unknown())
        .describe(
          "Workflow steps, one per status: `status` (key, ID or object) is required, plus optional `description` (localized object), `actions` (array of transitions), `metaAction` and `statusType` (`NEW`, `IN_PROGRESS`, `PAUSED`, `DONE`, `CANCELLED`).",
        ),
      id: z
        .string()
        .optional()
        .describe("Workflow ID. Generated in the `W...` format when not specified."),
      queue: z
        .union([z.string(), z.number().int(), z.record(z.string(), z.unknown())])
        .optional()
        .describe(
          'Queue the workflow is linked to: key, ID or an object (`{"key": ...}`, `{"id": ...}`, `{"name": ...}`). Omit it to create a shared workflow.',
        ),
      type: z
        .string()
        .optional()
        .describe("Workflow type. Pass `VISUAL`; the API returns `visual`."),
      issueTypeResolutions: z
        .array(z.unknown())
        .optional()
        .describe(
          "Resolution settings per issue type: `issueType` (key or ID) and `resolutions` (array of resolution keys or IDs).",
        ),
    },
    run: (tracker, a) =>
      tracker.request("POST", "/workflows", {
        body: given({
          name: a.name,
          initialAction: a.initialAction,
          steps: a.steps,
          id: a.id,
          queue: a.queue,
          type: a.type,
          issueTypeResolutions: a.issueTypeResolutions,
        }),
      }),
  }),

  tool({
    name: "tracker_get_workflows",
    description: `Get the list of all workflows in the organization.

GET /v3/workflows
https://yandex.ru/support/tracker/en/api/queues/workflows/get-workflows.md`,
    input: {},
    run: (tracker) => tracker.request("GET", "/workflows"),
  }),

  tool({
    name: "tracker_get_workflow",
    description: `Get information about a workflow by its ID.

GET /v3/workflows/{workflowId}
https://yandex.ru/support/tracker/en/api/queues/workflows/get-workflow.md`,
    input: {
      workflowId: z.string().min(1).describe("Workflow ID."),
    },
    run: (tracker, a) => tracker.request("GET", path`/workflows/${a.workflowId}`),
  }),

  tool({
    name: "tracker_patch_workflow",
    description: `Edit a workflow: its name, initial action, steps, type and resolution settings.

PATCH /v3/workflows/{workflowId}
https://yandex.ru/support/tracker/en/api/queues/workflows/patch-workflow.md

Send only the parameters you want to change.`,
    input: {
      workflowId: z.string().min(1).describe("Workflow ID."),
      version: z
        .number()
        .int()
        .optional()
        .describe(
          "Current workflow version, to prevent conflicts during concurrent changes. Get it with the request for a workflow.",
        ),
      name: z.string().optional().describe("New workflow name."),
      type: z
        .string()
        .optional()
        .describe("Workflow type. Pass `VISUAL`; the API returns `visual`."),
      initialAction: z
        .record(z.string(), z.unknown())
        .optional()
        .describe("New initial action, in the format described under Creating a workflow."),
      steps: z
        .array(z.unknown())
        .optional()
        .describe("Updated workflow steps, in the format described under Creating a workflow."),
      issueTypeResolutions: z
        .array(z.unknown())
        .optional()
        .describe("Resolution settings per issue type: `issueType` and `resolutions`."),
    },
    run: (tracker, a) =>
      tracker.request("PATCH", path`/workflows/${a.workflowId}`, {
        params: given({ version: a.version }),
        body: given({
          name: a.name,
          type: a.type,
          initialAction: a.initialAction,
          steps: a.steps,
          issueTypeResolutions: a.issueTypeResolutions,
        }),
      }),
  }),

  tool({
    name: "tracker_patch_workflow_action",
    description: `Edit one action (transition) of a workflow step.

PATCH /v3/workflows/{workflowId}/steps/{status}/actions/{actionId}
https://yandex.ru/support/tracker/en/api/queues/workflows/patch-workflow-action.md`,
    input: {
      workflowId: z.string().min(1).describe("Workflow ID."),
      status: z
        .string()
        .min(1)
        .describe(
          "Key of the status (step) that contains the action, for example `open`, `inProgress` or `closed`.",
        ),
      actionId: z
        .string()
        .min(1)
        .describe("ID of the action inside the step, for example `inProgress`."),
      version: z
        .number()
        .int()
        .describe(
          "Current workflow version, used to control concurrent changes. Get it with the request for a workflow.",
        ),
      id: z.string().optional().describe("Action ID."),
      name: z
        .record(z.string(), z.unknown())
        .optional()
        .describe('Action name as a localized object, for example `{"en": ...}`.'),
      description: z
        .record(z.string(), z.unknown())
        .optional()
        .describe("Action description as a localized object."),
      target: z
        .union([z.string(), z.number().int(), z.record(z.string(), z.unknown())])
        .optional()
        .describe(
          'Target status the action moves the issue to: key, ID or an object (`{"key": ...}`, `{"id": ...}`, `{"name": ...}`).',
        ),
      screen: z
        .record(z.string(), z.unknown())
        .optional()
        .describe(
          "Transition screen with the fields that can be filled in when performing the action.",
        ),
      conditions: z.array(z.unknown()).optional().describe("Conditions for performing the action."),
      functions: z
        .array(z.unknown())
        .optional()
        .describe("Functions executed during the transition."),
    },
    run: (tracker, a) =>
      tracker.request(
        "PATCH",
        path`/workflows/${a.workflowId}/steps/${a.status}/actions/${a.actionId}`,
        {
          params: given({ version: a.version }),
          body: given({
            id: a.id,
            name: a.name,
            description: a.description,
            target: a.target,
            screen: a.screen,
            conditions: a.conditions,
            functions: a.functions,
          }),
        },
      ),
  }),

  tool({
    name: "tracker_delete_workflow",
    description: `Delete a workflow.

DELETE /v3/workflows/{workflowId}
https://yandex.ru/support/tracker/en/api/queues/workflows/delete-workflow.md`,
    input: {
      workflowId: z.string().min(1).describe("Workflow ID."),
    },
    run: (tracker, a) => tracker.request("DELETE", path`/workflows/${a.workflowId}`),
  }),

  tool({
    name: "tracker_create_autoaction",
    description: `Create an auto action in a queue.

POST /v3/queues/{queueId}/autoactions
https://yandex.ru/support/tracker/en/api/queues/create-autoaction.md`,
    input: {
      queueId: z.string().min(1).describe("Queue ID or key. The queue key is case-sensitive."),
      name: z.string().min(1).describe("Auto action name."),
      actions: z
        .array(z.unknown())
        .describe(
          'Actions performed on the issues, for example `{"type": "Transition", "status": {"key": "needInfo"}}`. The action objects are described at https://yandex.ru/support/tracker/en/api/queues/change-trigger-actions.md.',
        ),
      filter: z
        .union([z.record(z.string(), z.unknown()), z.array(z.unknown())])
        .optional()
        .describe(
          'Issue field filtering conditions that trigger the auto action, as field key to array of values, for example `{"status": ["inProgress"]}`. Specify at least one of `filter` and `query`.',
        ),
      query: z
        .string()
        .optional()
        .describe(
          "Query-language filter selecting the issues that trigger the auto action. Specify at least one of `filter` and `query`.",
        ),
      active: z
        .boolean()
        .optional()
        .describe("Auto action status: `true` active, `false` inactive."),
      enableNotifications: z
        .boolean()
        .optional()
        .describe("Whether to send notifications: `true` or `false`."),
      intervalMillis: z
        .number()
        .int()
        .optional()
        .describe("Auto action start frequency in milliseconds. Default `3600000` (hourly)."),
      calendar: z
        .record(z.string(), z.unknown())
        .optional()
        .describe('Period for which the auto action is active, as `{"id": <work schedule ID>}`.'),
    },
    run: (tracker, a) =>
      tracker.request("POST", path`/queues/${a.queueId}/autoactions`, {
        body: given({
          name: a.name,
          actions: a.actions,
          filter: a.filter,
          query: a.query,
          active: a.active,
          enableNotifications: a.enableNotifications,
          intervalMillis: a.intervalMillis,
          calendar: a.calendar,
        }),
      }),
  }),

  tool({
    name: "tracker_get_autoaction",
    description: `Get the parameters of an auto action.

GET /v3/queues/{queueId}/autoactions/{autoactionId}
https://yandex.ru/support/tracker/en/api/queues/get-autoaction.md`,
    input: {
      queueId: z.string().min(1).describe("Queue ID or key. The queue key is case-sensitive."),
      autoactionId: z.string().min(1).describe("Auto action ID."),
    },
    run: (tracker, a) =>
      tracker.request("GET", path`/queues/${a.queueId}/autoactions/${a.autoactionId}`),
  }),

  tool({
    name: "tracker_get_autoaction_logs",
    description: `Get the log of all runs of an auto action.

GET /v3/queues/{queueId}/autoactions/{autoactionId}/logs
https://yandex.ru/support/tracker/en/api/queues/view-autoaction-logs.md

Logs exist only for auto actions that configure automatic issue updates.
Each entry carries the run \`id\` to pass to tracker_get_autoaction_run_log.`,
    input: {
      queueId: z.string().min(1).describe("Queue ID or key. The queue key is case-sensitive."),
      autoactionId: z.string().min(1).describe("Auto action ID."),
    },
    run: (tracker, a) =>
      tracker.request("GET", path`/queues/${a.queueId}/autoactions/${a.autoactionId}/logs`),
  }),

  tool({
    name: "tracker_get_autoaction_run_log",
    description: `Get the log of one auto action run with the list of issues it found.

GET /v3/queues/{queueId}/autoactions/{autoactionId}/logs/{runId}
https://yandex.ru/support/tracker/en/api/queues/view-autoaction-logs.md`,
    input: {
      queueId: z.string().min(1).describe("Queue ID or key. The queue key is case-sensitive."),
      autoactionId: z.string().min(1).describe("Auto action ID."),
      runId: z.string().min(1).describe("ID of the auto action run."),
    },
    run: (tracker, a) =>
      tracker.request(
        "GET",
        path`/queues/${a.queueId}/autoactions/${a.autoactionId}/logs/${a.runId}`,
      ),
  }),

  tool({
    name: "tracker_create_trigger",
    description: `Create a trigger in a queue.

POST /v3/queues/{queueId}/triggers
https://yandex.ru/support/tracker/en/api/queues/create-trigger.md`,
    input: {
      queueId: z.string().min(1).describe("Queue ID or key. The queue key is case-sensitive."),
      name: z.string().min(1).describe("Trigger name."),
      actions: z
        .array(z.unknown())
        .describe(
          'Trigger actions, described at https://yandex.ru/support/tracker/en/api/queues/change-trigger-actions.md, for example `{"type": "Transition", "status": {"key": "open"}}`.',
        ),
      conditions: z
        .array(z.unknown())
        .optional()
        .describe(
          'Trigger conditions, described at https://yandex.ru/support/tracker/en/api/queues/change-trigger-conditions.md, for example `{"type": "CommentFullyMatchCondition", "word": "Open"}`.',
        ),
      active: z.boolean().optional().describe("Trigger status: `true` active, `false` inactive."),
    },
    run: (tracker, a) =>
      tracker.request("POST", path`/queues/${a.queueId}/triggers`, {
        body: given({
          name: a.name,
          actions: a.actions,
          conditions: a.conditions,
          active: a.active,
        }),
      }),
  }),

  tool({
    name: "tracker_get_triggers",
    description: `Get the list of all triggers created in a queue.

GET /v3/queues/{queueId}/triggers
https://yandex.ru/support/tracker/en/api/queues/get-triggers.md

The request uses relative pagination: results are sorted by ascending
trigger ID, so pass the ID of the last trigger of a page as \`id\` to get the
next one.`,
    input: {
      queueId: z.string().min(1).describe("Queue ID or key. The queue key is case-sensitive."),
      perPage: z.number().int().optional().describe("Number of triggers per page."),
      id: z.number().int().optional().describe("ID of the last trigger of the previous page."),
    },
    run: (tracker, a) =>
      tracker.request("GET", path`/queues/${a.queueId}/triggers`, {
        params: given({ perPage: a.perPage, id: a.id }),
      }),
  }),

  tool({
    name: "tracker_get_trigger",
    description: `Get the parameters of a queue trigger.

GET /v3/queues/{queueId}/triggers/{triggerId}
https://yandex.ru/support/tracker/en/api/queues/get-trigger.md`,
    input: {
      queueId: z.string().min(1).describe("Queue ID or key. The queue key is case-sensitive."),
      triggerId: z.string().min(1).describe("Trigger ID."),
    },
    run: (tracker, a) => tracker.request("GET", path`/queues/${a.queueId}/triggers/${a.triggerId}`),
  }),

  tool({
    name: "tracker_patch_trigger",
    description: `Update a queue trigger.

PATCH /v3/queues/{queueId}/triggers/{triggerId}
https://yandex.ru/support/tracker/en/api/queues/change-trigger.md`,
    input: {
      queueId: z.string().min(1).describe("Queue ID or key. The queue key is case-sensitive."),
      triggerId: z.string().min(1).describe("Trigger ID."),
      version: z
        .number()
        .int()
        .describe("Current trigger version. Get it with the request for trigger parameters."),
      name: z.string().optional().describe("Trigger name."),
      actions: z
        .array(z.unknown())
        .optional()
        .describe(
          "Trigger actions, described at https://yandex.ru/support/tracker/en/api/queues/change-trigger-actions.md.",
        ),
      conditions: z
        .union([z.array(z.unknown()), z.record(z.string(), z.unknown())])
        .optional()
        .describe(
          'Trigger conditions, described at https://yandex.ru/support/tracker/en/api/queues/change-trigger-conditions.md. An array means all conditions must be met; to combine them differently pass `{"type": "Or"|"And", "conditions": [...]}`.',
        ),
      active: z.boolean().optional().describe("Trigger status: `true` active, `false` inactive."),
      before: z
        .number()
        .int()
        .optional()
        .describe("ID of the trigger before which to place this trigger."),
    },
    run: (tracker, a) =>
      tracker.request("PATCH", path`/queues/${a.queueId}/triggers/${a.triggerId}`, {
        params: given({ version: a.version }),
        body: given({
          name: a.name,
          actions: a.actions,
          conditions: a.conditions,
          active: a.active,
          before: a.before,
        }),
      }),
  }),

  tool({
    name: "tracker_get_trigger_webhook_log",
    description: `Get the HTTP request action logs of a queue trigger.

GET /v3/queues/{queueId}/triggers/{triggerId}/webhooks/log
https://yandex.ru/support/tracker/en/api/queues/view-trigger-logs.md`,
    input: {
      queueId: z.string().min(1).describe("Queue ID or key. The queue key is case-sensitive."),
      triggerId: z.string().min(1).describe("Trigger ID."),
      issueId: z.string().optional().describe("ID of the issue where the trigger was activated."),
      limit: z
        .number()
        .int()
        .optional()
        .describe("Number of log entries in the response. Default 10, maximum 100."),
      from: z
        .string()
        .optional()
        .describe("Start of the log filter time range in `YYYY-MM-DDThh:mm:ss.sss±hhmm` format."),
      to: z
        .string()
        .optional()
        .describe("End of the log filter time range in `YYYY-MM-DDThh:mm:ss.sss±hhmm` format."),
    },
    run: (tracker, a) =>
      tracker.request("GET", path`/queues/${a.queueId}/triggers/${a.triggerId}/webhooks/log`, {
        params: given({ issueId: a.issueId, limit: a.limit, from: a.from, to: a.to }),
      }),
  }),

  tool({
    name: "tracker_get_components",
    description: `Get the list of all components created by the organization users.

GET /v3/components
https://yandex.ru/support/tracker/en/api/queues/get-components.md

This is the organization-wide list. For the components of a single queue,
call tracker_get_queue with \`expand=components\`.`,
    input: {},
    run: (tracker) => tracker.request("GET", "/components"),
  }),

  tool({
    name: "tracker_create_component",
    description: `Create a component.

POST /v3/components
https://yandex.ru/support/tracker/en/api/queues/post-component.md`,
    input: {
      name: z.string().min(1).describe("Component name."),
      queue: z.string().min(1).describe("Key of the queue where the component is created."),
      description: z.string().optional().describe("Component description."),
      lead: z.string().optional().describe("Username of the component owner."),
      assignAuto: z
        .boolean()
        .optional()
        .describe(
          "Default assignee attribute: `true` assigns the owner as the default assignee, `false` assigns nobody.",
        ),
    },
    run: (tracker, a) =>
      tracker.request("POST", "/components", {
        body: given({
          name: a.name,
          queue: a.queue,
          description: a.description,
          lead: a.lead,
          assignAuto: a.assignAuto,
        }),
      }),
  }),

  tool({
    name: "tracker_patch_component",
    description: `Change the parameters of a component.

PATCH /v3/components/{componentId}
https://yandex.ru/support/tracker/en/api/queues/patch-component.md`,
    input: {
      componentId: z.string().min(1).describe("Component ID."),
      version: z.number().int().describe("Current component version number."),
      name: z.string().optional().describe("Component name."),
      description: z.string().optional().describe("Component description."),
      lead: z.string().optional().describe("Username of the component owner."),
      assignAuto: z
        .boolean()
        .optional()
        .describe(
          "Default assignee attribute: `true` assigns the owner as the default assignee, `false` assigns nobody.",
        ),
    },
    run: (tracker, a) =>
      tracker.request("PATCH", path`/components/${a.componentId}`, {
        params: given({ version: a.version }),
        body: given({
          name: a.name,
          description: a.description,
          lead: a.lead,
          assignAuto: a.assignAuto,
        }),
      }),
  }),

  tool({
    name: "tracker_get_component_user_access",
    description: `Get the permissions of one user for a component.

GET /v3/components/{componentId}/permissions/users/{userId}
https://yandex.ru/support/tracker/en/api/queues/get-component-user-access.md`,
    input: {
      componentId: z.string().min(1).describe("Component ID."),
      userId: z.string().min(1).describe("Unique ID of the account or the user login."),
    },
    run: (tracker, a) =>
      tracker.request("GET", path`/components/${a.componentId}/permissions/users/${a.userId}`),
  }),

  tool({
    name: "tracker_get_component_group_access",
    description: `Get the permissions of one group for a component.

GET /v3/components/{componentId}/permissions/groups/{groupId}
https://yandex.ru/support/tracker/en/api/queues/get-component-group-access.md`,
    input: {
      componentId: z.string().min(1).describe("Component ID."),
      groupId: z.string().min(1).describe("Unique group ID in the organization."),
    },
    run: (tracker, a) =>
      tracker.request("GET", path`/components/${a.componentId}/permissions/groups/${a.groupId}`),
  }),
];
