/** Issues, comments, checklists, attachments, worklog and fields — https://yandex.ru/support/tracker/en/api/issues/get-issue.md */

import { z } from "zod";
import { given } from "../client.ts";
import { tool } from "../tool.ts";

export const issueTools = [
  tool({
    name: "tracker_create_issue",
    description: `Create an issue.

POST /v3/issues/
https://yandex.ru/support/tracker/en/api/issues/create-issue.md

How every field value is shaped is described in
https://yandex.ru/support/tracker/en/api/issues/request-fields.md, and the
shape of the issue you get back in
https://yandex.ru/support/tracker/en/api/issues/response-fields.md.`,
    input: {
      summary: z.string().min(1).describe("Issue summary."),
      queue: z
        .union([z.string(), z.number().int(), z.record(z.string(), z.unknown())])
        .describe(
          "Queue to create the issue in: a string (queue key), a number (queue ID), or an object with `id` and/or `key`.",
        ),
      notify: z
        .boolean()
        .optional()
        .describe(
          "Send a notification about the issue being created to users subscribed to this event. The notification is sent by default.",
        ),
      parent: z
        .union([z.string(), z.record(z.string(), z.unknown())])
        .optional()
        .describe("Parent issue: its key, or an object with `id` and/or `key`."),
      description: z.string().optional().describe("Issue description."),
      markupType: z
        .string()
        .optional()
        .describe("Type of text markup. Specify `md` when the description uses YFM markup."),
      sprint: z
        .union([z.array(z.unknown()), z.number().int(), z.string()])
        .optional()
        .describe("Block with information about sprints: array of objects or strings."),
      type: z
        .union([z.string(), z.number().int(), z.record(z.string(), z.unknown())])
        .optional()
        .describe(
          "Issue type: a string (type key), a number (type ID), or an object with `id` and/or `key`.",
        ),
      priority: z
        .union([z.string(), z.number().int(), z.record(z.string(), z.unknown())])
        .optional()
        .describe(
          "Issue priority: a string (priority key), a number (priority ID), or an object with `id` and/or `key`.",
        ),
      followers: z.array(z.unknown()).optional().describe("IDs or usernames of issue followers."),
      assignee: z
        .union([z.string(), z.number().int()])
        .optional()
        .describe("Login or ID of the issue assignee."),
      author: z
        .union([z.string(), z.number().int(), z.record(z.string(), z.unknown())])
        .optional()
        .describe("ID or username of the issue author."),
      project: z
        .record(z.string(), z.unknown())
        .optional()
        .describe(
          "Block with information about issue projects: `primary` (shortId of the main project) and `secondary` (array of shortIds).",
        ),
      links: z
        .array(z.unknown())
        .optional()
        .describe(
          "Links to other issues. Each object has `issue` (ID or key of the linked issue) and `relationship`: `relates`, `is dependent by`, `depends on`, `is subtask for`, `is parent task for`, `duplicates`, `is duplicated by`, `is epic of`, `has epic`.",
        ),
      unique: z
        .string()
        .optional()
        .describe(
          "Value that must be unique within the organization. Reusing it returns error 409 instead of creating a duplicate issue.",
        ),
      attachmentIds: z
        .array(z.unknown())
        .optional()
        .describe("IDs of temporary files to attach to the issue description."),
      tags: z.array(z.unknown()).optional().describe("Issue tags."),
      access: z
        .array(z.unknown())
        .optional()
        .describe("IDs or logins of users listed in the Access field."),
      affectedVersions: z
        .array(z.unknown())
        .optional()
        .describe(
          "IDs of versions listed in the Found in versions field. The versions must exist in the queue.",
        ),
      boards: z.array(z.unknown()).optional().describe("IDs of boards to add the issue to."),
      components: z
        .array(z.unknown())
        .optional()
        .describe("Names or IDs of queue components added to the issue."),
      createdBy: z
        .union([z.string(), z.number().int()])
        .optional()
        .describe("Login or ID of the issue author."),
      deadline: z.string().optional().describe("Issue deadline in the YYYY-MM-DD format."),
      descriptionAttachmentIds: z
        .array(z.unknown())
        .optional()
        .describe("IDs of temporary files to add to the issue description."),
      emailCc: z.array(z.unknown()).optional().describe('Email recipients in the "Cc" field.'),
      emailCreatedBy: z
        .string()
        .optional()
        .describe("Email address the email was created on behalf of."),
      emailFrom: z.string().optional().describe("Email sender address."),
      emailTo: z.string().optional().describe("Email recipients."),
      end: z.string().optional().describe("Date of issue completion in the YYYY-MM-DD format."),
      epic: z.string().optional().describe("Key or ID of the epic the issue belongs to."),
      estimation: z
        .string()
        .optional()
        .describe(
          "Estimate in workdays, hours or minutes, as `<number><unit>` — for example `1d`, `2h`, `30m`.",
        ),
      fixVersions: z
        .array(z.unknown())
        .optional()
        .describe(
          "IDs of versions listed in the Fix in versions field. The versions must exist in the queue.",
        ),
      linkedGoals: z
        .union([z.record(z.string(), z.unknown()), z.number().int(), z.string()])
        .optional()
        .describe(
          "Goal ID (it becomes the primary goal) or an object with `primary` and `secondary` goal IDs.",
        ),
      originalEstimation: z
        .string()
        .optional()
        .describe(
          "Original estimate in workdays, hours or minutes, as `<number><unit>` — for example `1d`, `2h`, `30m`.",
        ),
      pendingReplyFrom: z
        .array(z.unknown())
        .optional()
        .describe("Logins or IDs of users a reply is expected from."),
      possibleSpam: z
        .boolean()
        .optional()
        .describe("Indication that the issue was created from an email that is spam."),
      qaEngineer: z
        .union([z.string(), z.number().int()])
        .optional()
        .describe("Login or ID of the QA engineer."),
      receivedReplyFor: z
        .union([z.string(), z.number().int()])
        .optional()
        .describe("Login or ID of the user a reply was received for."),
      start: z
        .string()
        .optional()
        .describe("Start date of work on the issue in the YYYY-MM-DD format."),
      storyPoints: z.number().optional().describe("Issue estimate in story points."),
      fields: z
        .record(z.string(), z.unknown())
        .optional()
        .describe(
          "Custom global fields and queue local fields, keyed by field ID. Merged into the request body last.",
        ),
    },
    run: (tracker, a) =>
      tracker.request("POST", "/issues/", {
        params: given({ notify: a.notify }),
        body: {
          ...given({
            summary: a.summary,
            queue: a.queue,
            parent: a.parent,
            description: a.description,
            markupType: a.markupType,
            sprint: a.sprint,
            type: a.type,
            priority: a.priority,
            followers: a.followers,
            assignee: a.assignee,
            author: a.author,
            project: a.project,
            links: a.links,
            unique: a.unique,
            attachmentIds: a.attachmentIds,
            tags: a.tags,
            access: a.access,
            affectedVersions: a.affectedVersions,
            boards: a.boards,
            components: a.components,
            createdBy: a.createdBy,
            deadline: a.deadline,
            descriptionAttachmentIds: a.descriptionAttachmentIds,
            emailCc: a.emailCc,
            emailCreatedBy: a.emailCreatedBy,
            emailFrom: a.emailFrom,
            emailTo: a.emailTo,
            end: a.end,
            epic: a.epic,
            estimation: a.estimation,
            fixVersions: a.fixVersions,
            linkedGoals: a.linkedGoals,
            originalEstimation: a.originalEstimation,
            pendingReplyFrom: a.pendingReplyFrom,
            possibleSpam: a.possibleSpam,
            qaEngineer: a.qaEngineer,
            receivedReplyFor: a.receivedReplyFor,
            start: a.start,
            storyPoints: a.storyPoints,
          }),
          ...(a.fields ?? {}),
        },
      }),
  }),

  tool({
    name: "tracker_get_issue",
    description: `Get the parameters of one issue.

GET /v3/issues/{issueId}
https://yandex.ru/support/tracker/en/api/issues/get-issue.md`,
    input: {
      issueId: z.string().min(1).describe("ID or key of the issue."),
      fields: z
        .string()
        .optional()
        .describe(
          "Issue fields to include in the response, comma-separated — for example `status,assignee,summary`. Without it the response includes all basic fields.",
        ),
      expand: z
        .string()
        .optional()
        .describe(
          "Additional fields to include: `links`, `comments`, `transitions`, `attachments`.",
        ),
    },
    run: (tracker, a) =>
      tracker.request("GET", `/issues/${a.issueId}`, {
        params: given({ fields: a.fields, expand: a.expand }),
      }),
  }),

  tool({
    name: "tracker_patch_issue",
    description: `Edit an issue.

PATCH /v3/issues/{issueId}
https://yandex.ru/support/tracker/en/api/issues/patch-issue.md

The status is the one field this cannot change — use tracker_new_transition.
Array fields also accept the \`set\`/\`add\`/\`remove\` operators instead of a plain
value (see https://yandex.ru/support/tracker/en/api/common-format.md#body);
pass those through \`fields\`. How every field value is shaped is described in
https://yandex.ru/support/tracker/en/api/issues/request-fields.md, and the
shape of the issue you get back in
https://yandex.ru/support/tracker/en/api/issues/response-fields.md.`,
    input: {
      issueId: z.string().min(1).describe("ID or key of the issue."),
      version: z
        .number()
        .int()
        .optional()
        .describe("Issue version. Changes are only made to the current version."),
      summary: z.string().optional().describe("Issue name."),
      parent: z
        .union([z.string(), z.record(z.string(), z.unknown())])
        .optional()
        .describe("Parent issue: its key, or an object with `id` and/or `key`."),
      description: z.string().optional().describe("Issue description."),
      markupType: z
        .string()
        .optional()
        .describe("Type of text markup. Specify `md` when the description uses YFM markup."),
      sprint: z
        .union([z.array(z.unknown()), z.number().int(), z.string()])
        .optional()
        .describe(
          "Block with information about sprints: array of objects with `id`, or of strings.",
        ),
      type: z
        .union([z.string(), z.number().int(), z.record(z.string(), z.unknown())])
        .optional()
        .describe(
          "Issue type: a string (type key), a number (type ID), or an object with `id` and/or `key`.",
        ),
      priority: z
        .union([z.string(), z.number().int(), z.record(z.string(), z.unknown())])
        .optional()
        .describe(
          "Issue priority: a string (priority key), a number (priority ID), or an object with `id` and/or `key`.",
        ),
      followers: z.array(z.unknown()).optional().describe("IDs or usernames of issue followers."),
      project: z
        .record(z.string(), z.unknown())
        .optional()
        .describe(
          "Block with information about issue projects: `primary` (shortId of the main project) and `secondary` (array of shortIds).",
        ),
      attachmentIds: z
        .array(z.unknown())
        .optional()
        .describe("IDs of temporary files to add as attachments."),
      descriptionAttachmentIds: z
        .array(z.unknown())
        .optional()
        .describe("IDs of temporary files to add to the issue description."),
      tags: z.array(z.unknown()).optional().describe("Issue tags."),
      access: z
        .array(z.unknown())
        .optional()
        .describe("IDs or logins of users listed in the Access field."),
      affectedVersions: z
        .array(z.unknown())
        .optional()
        .describe(
          "IDs of versions listed in the Found in versions field. The versions must exist in the queue.",
        ),
      assignee: z
        .union([z.string(), z.number().int()])
        .optional()
        .describe("Login or ID of the issue assignee."),
      boards: z.array(z.unknown()).optional().describe("IDs of boards to add the issue to."),
      components: z
        .array(z.unknown())
        .optional()
        .describe("Names or IDs of queue components added to the issue."),
      createdBy: z
        .union([z.string(), z.number().int()])
        .optional()
        .describe("Login or ID of the issue author."),
      deadline: z.string().optional().describe("Issue deadline in the YYYY-MM-DD format."),
      emailCc: z.array(z.unknown()).optional().describe('Email recipients in the "Cc" field.'),
      emailCreatedBy: z
        .string()
        .optional()
        .describe("Email address the email was created on behalf of."),
      emailFrom: z.string().optional().describe("Email sender address."),
      emailTo: z.string().optional().describe("Email recipients."),
      end: z.string().optional().describe("Date of issue completion in the YYYY-MM-DD format."),
      epic: z.string().optional().describe("Key or ID of the epic the issue belongs to."),
      estimation: z
        .string()
        .optional()
        .describe(
          "Estimate in workdays, hours or minutes, as `<number><unit>` — for example `1d`, `2h`, `30m`.",
        ),
      fixVersions: z
        .array(z.unknown())
        .optional()
        .describe(
          "IDs of versions listed in the Fix in versions field. The versions must exist in the queue.",
        ),
      linkedGoals: z
        .union([z.record(z.string(), z.unknown()), z.number().int(), z.string()])
        .optional()
        .describe(
          "Goal ID (it becomes the primary goal) or an object with `primary` and `secondary` goal IDs.",
        ),
      links: z
        .array(z.unknown())
        .optional()
        .describe(
          "List of linked issues. Each object has `issue` (ID or key) and `relationship`: `relates`, `is dependent by`, `depends on`, `is subtask for`, `is parent task for`, `duplicates`, `is duplicated by`, `is epic of`, `has epic`.",
        ),
      originalEstimation: z
        .string()
        .optional()
        .describe(
          "Original estimate in workdays, hours or minutes, as `<number><unit>` — for example `1d`, `2h`, `30m`.",
        ),
      pendingReplyFrom: z
        .array(z.unknown())
        .optional()
        .describe("Logins or IDs of users a reply is expected from."),
      possibleSpam: z
        .boolean()
        .optional()
        .describe("Indication that the issue was created from an email that is spam."),
      qaEngineer: z
        .union([z.string(), z.number().int()])
        .optional()
        .describe("Login or ID of the QA engineer."),
      receivedReplyFor: z
        .union([z.string(), z.number().int()])
        .optional()
        .describe("Login or ID of the user a reply was received for."),
      start: z
        .string()
        .optional()
        .describe("Start date of work on the issue in the YYYY-MM-DD format."),
      storyPoints: z.number().optional().describe("Issue estimate in story points."),
      unique: z.string().optional().describe("Value that must be unique within the organization."),
      fields: z
        .record(z.string(), z.unknown())
        .optional()
        .describe(
          "Custom global fields, queue local fields, and fields set through the `set`/`add`/`remove` operators. Merged into the request body last.",
        ),
    },
    run: (tracker, a) =>
      tracker.request("PATCH", `/issues/${a.issueId}`, {
        params: given({ version: a.version }),
        body: {
          ...given({
            summary: a.summary,
            parent: a.parent,
            description: a.description,
            markupType: a.markupType,
            sprint: a.sprint,
            type: a.type,
            priority: a.priority,
            followers: a.followers,
            project: a.project,
            attachmentIds: a.attachmentIds,
            descriptionAttachmentIds: a.descriptionAttachmentIds,
            tags: a.tags,
            access: a.access,
            affectedVersions: a.affectedVersions,
            assignee: a.assignee,
            boards: a.boards,
            components: a.components,
            createdBy: a.createdBy,
            deadline: a.deadline,
            emailCc: a.emailCc,
            emailCreatedBy: a.emailCreatedBy,
            emailFrom: a.emailFrom,
            emailTo: a.emailTo,
            end: a.end,
            epic: a.epic,
            estimation: a.estimation,
            fixVersions: a.fixVersions,
            linkedGoals: a.linkedGoals,
            links: a.links,
            originalEstimation: a.originalEstimation,
            pendingReplyFrom: a.pendingReplyFrom,
            possibleSpam: a.possibleSpam,
            qaEngineer: a.qaEngineer,
            receivedReplyFor: a.receivedReplyFor,
            start: a.start,
            storyPoints: a.storyPoints,
            unique: a.unique,
          }),
          ...(a.fields ?? {}),
        },
      }),
  }),

  tool({
    name: "tracker_move_issue",
    description: `Move an issue to another queue.

POST /v3/issues/{issueId}/_move
https://yandex.ru/support/tracker/en/api/issues/move-issue.md

Nothing is moved when the issue's type or status does not exist in the target
queue; local field values are always reset by the move.`,
    effect: "modify",
    input: {
      issueId: z.string().min(1).describe("ID or key of the issue."),
      queue: z.string().min(1).describe("Key of the queue to move the issue to."),
      notify: z
        .boolean()
        .optional()
        .describe(
          "Notify the users specified in the issue fields about the change. `true` by default.",
        ),
      notifyAuthor: z
        .boolean()
        .optional()
        .describe("Notify the issue reporter. `false` by default."),
      moveAllFields: z
        .boolean()
        .optional()
        .describe(
          "Move the issue's versions, components and projects if the new queue has similar ones. `false` by default, which clears them.",
        ),
      initialStatus: z
        .boolean()
        .optional()
        .describe(
          "Reset the issue status to the initial one — needed when the new queue has a different workflow. `false` by default.",
        ),
      expand: z
        .string()
        .optional()
        .describe(
          "Additional fields to include in the response: `attachments`, `comments`, `workflow`, `transitions`.",
        ),
      fields: z
        .record(z.string(), z.unknown())
        .optional()
        .describe(
          "Issue parameters to change while moving. Same body format as editing an issue — see https://yandex.ru/support/tracker/en/api/issues/patch-issue.md.",
        ),
    },
    run: (tracker, a) =>
      tracker.request("POST", `/issues/${a.issueId}/_move`, {
        params: given({
          queue: a.queue,
          notify: a.notify,
          notifyAuthor: a.notifyAuthor,
          moveAllFields: a.moveAllFields,
          initialStatus: a.initialStatus,
          expand: a.expand,
        }),
        body: a.fields,
      }),
  }),

  tool({
    name: "tracker_search_issues",
    description: `Find the issues that meet the given criteria.

POST /v3/issues/_search
https://yandex.ru/support/tracker/en/api/issues/search-issues.md

The page lists five ways to select the issues: \`queue\`, \`keys\`, \`filter\`,
\`query\` and \`query2\`. Of these it states that \`queue\`, \`keys\`, \`filter\` and
\`query\` are mutually exclusive — combining them returns error 400; it says
nothing about combining \`query2\` with the rest, so send one selector at a
time. Use paginated output below 10,000 rows and the scroll parameters above
it; release a scroll snapshot with tracker_clear_scroll.
\`perPage\` and \`page\` are the paginated-output parameters this page links to
in https://yandex.ru/support/tracker/en/api/common-format.md.`,
    effect: "read",
    input: {
      expand: z
        .string()
        .optional()
        .describe("Additional fields to include in the response: `transitions`, `attachments`."),
      perPage: z
        .number()
        .int()
        .optional()
        .describe("Number of issues per response page. Default 50."),
      page: z.number().int().optional().describe("Page number of the paginated output. Default 1."),
      scrollType: z
        .string()
        .optional()
        .describe(
          "Scrolling type, used only in the first request of a scrollable sequence: `sorted` (use the sorting from the request) or `unsorted`. Not allowed together with `queue` or `keys`.",
        ),
      perScroll: z
        .number()
        .int()
        .optional()
        .describe(
          "Maximum number of issues per scrollable response. Default 100, maximum 1000. Used only in the first request of a scrollable sequence.",
        ),
      scrollTTLMillis: z
        .number()
        .int()
        .optional()
        .describe("Scroll context lifetime in milliseconds. Default 60000."),
      scrollId: z
        .string()
        .optional()
        .describe(
          "Page ID, taken from the `X-Scroll-Id` header of the previous response. Specified only in the second and following requests of a scrollable sequence.",
        ),
      queue: z.string().optional().describe("Queue to search in."),
      keys: z
        .union([z.string(), z.array(z.unknown())])
        .optional()
        .describe("Issue key or list of issue keys."),
      filter: z
        .record(z.string(), z.unknown())
        .optional()
        .describe("Issue filtering parameters: any issue field name and a value."),
      query: z.string().optional().describe("Filter using the query language."),
      query2: z
        .record(z.string(), z.unknown())
        .optional()
        .describe(
          "Filter using query language 2.0 as an MLJ (Mongo-like JSON) object — see https://yandex.ru/support/tracker/en/api/issues/query2.md.",
        ),
      order: z
        .string()
        .optional()
        .describe(
          "Sorting direction and field as `[+/-]<field_key>`. Only works together with `filter`.",
        ),
    },
    run: (tracker, a) =>
      tracker.request("POST", "/issues/_search", {
        params: given({
          expand: a.expand,
          perPage: a.perPage,
          page: a.page,
          scrollType: a.scrollType,
          perScroll: a.perScroll,
          scrollTTLMillis: a.scrollTTLMillis,
          scrollId: a.scrollId,
        }),
        body: given({
          queue: a.queue,
          keys: a.keys,
          filter: a.filter,
          query: a.query,
          query2: a.query2,
          order: a.order,
        }),
      }),
  }),

  tool({
    name: "tracker_count_issues",
    description: `Count the issues that meet the given criteria.

POST /v3/issues/_count
https://yandex.ru/support/tracker/en/api/issues/count-issues.md`,
    effect: "read",
    input: {
      filter: z
        .record(z.string(), z.unknown())
        .optional()
        .describe("Issue filtering parameters: any issue field name and a value."),
      query: z.string().optional().describe("Filter using the query language."),
    },
    run: (tracker, a) =>
      tracker.request("POST", "/issues/_count", {
        body: given({ filter: a.filter, query: a.query }),
      }),
  }),

  tool({
    name: "tracker_get_suggest",
    description: `Get the issue suggestions shown when searching by summary.

GET /v3/issues/_suggest
https://yandex.ru/support/tracker/en/api/issues/get-suggest.md`,
    input: {
      input: z
        .string()
        .min(1)
        .describe(
          "Text to filter issues by summary. A space between words also matches any text in place of the space.",
        ),
      queue: z.string().optional().describe("Key of the queue to search issues in."),
      full: z
        .boolean()
        .optional()
        .describe(
          "Return detailed information for each issue. Default `false`. Required to enable `fields`, `expand` and `embed`.",
        ),
      fields: z
        .string()
        .optional()
        .describe("Additional issue fields to return. Requires `full=true`."),
      expand: z
        .string()
        .optional()
        .describe(
          "Additional information to include: `all`, `html`, `attachments`, `comments`, `links`, `localLinkRefs`, `aliases`, `transitions`, `permissions`, `sla`, `update_limits`. Requires `full=true`.",
        ),
      embed: z
        .string()
        .optional()
        .describe(
          "More detail for the parameters named in `expand`: `attachments`, `comments`, `transitions`, `sla`. Requires `full=true`.",
        ),
    },
    run: (tracker, a) =>
      tracker.request("GET", "/issues/_suggest", {
        params: given({
          input: a.input,
          queue: a.queue,
          full: a.full,
          fields: a.fields,
          expand: a.expand,
          embed: a.embed,
        }),
      }),
  }),

  tool({
    name: "tracker_clear_scroll",
    description: `Release the resources of a scrollable issue search snapshot.

POST /v3/system/search/scroll/_clear
https://yandex.ru/support/tracker/en/api/issues/search-release.md

The body of this endpoint is a bare map rather than named parameters, so
\`scrolls\` is a wrapper this tool adds and sends as the whole body.`,
    effect: "modify",
    input: {
      scrolls: z
        .record(z.string(), z.unknown())
        .describe(
          "One `<scrollId>: <scrollToken>` pair per result page, taken from the `X-Scroll-Id` and `X-Scroll-Token` headers of the scrollable search responses. Sent as the request body itself.",
        ),
    },
    run: (tracker, a) =>
      tracker.request("POST", "/system/search/scroll/_clear", { body: a.scrolls }),
  }),

  tool({
    name: "tracker_get_changelog",
    description: `Get the history of changes to an issue.

GET /v3/issues/{issueId}/changelog
https://yandex.ru/support/tracker/en/api/issues/get-changelog.md`,
    input: {
      issueId: z.string().min(1).describe("ID or key of the issue."),
      id: z.string().optional().describe("ID of the change the requested changes follow."),
      perPage: z.number().int().optional().describe("Number of changes per page. Default 50."),
      field: z
        .string()
        .optional()
        .describe("ID of the changed issue parameter — for example `checklistItems` or `status`."),
      type: z
        .string()
        .optional()
        .describe(
          "Key of the change type: `IssueUpdated`, `IssueCreated`, `IssueMoved`, `IssueCloned`, `IssueCommentAdded`, `IssueCommentUpdated`, `IssueCommentRemoved`, `IssueWorklogAdded`, `IssueWorklogUpdated`, `IssueWorklogRemoved`, `IssueCommentReactionAdded`, `IssueCommentReactionRemoved`, `IssueVoteAdded`, `IssueVoteRemoved`, `IssueLinked`, `IssueLinkChanged`, `IssueUnlinked`, `RelatedIssueResolutionChanged`, `IssueAttachmentAdded`, `IssueAttachmentRemoved`, `IssueWorkflow`.",
        ),
    },
    run: (tracker, a) =>
      tracker.request("GET", `/issues/${a.issueId}/changelog`, {
        params: given({ id: a.id, perPage: a.perPage, field: a.field, type: a.type }),
      }),
  }),

  tool({
    name: "tracker_link_issue",
    description: `Create a link between two issues.

POST /v3/issues/{issueId}/links
https://yandex.ru/support/tracker/en/api/issues/link-issue.md`,
    input: {
      issueId: z.string().min(1).describe("ID or key of the current issue."),
      relationship: z
        .string()
        .min(1)
        .describe(
          'Link type between the issues: `relates` — simple link; `is dependent by` — the current issue blocks the linked issue; `depends on` — the current issue depends on the linked issue; `is subtask for` — the current issue is a subtask of the linked issue; `is parent task for` — the current issue is a parent task for the linked issue; `duplicates` — the current issue is a duplicate of the linked issue; `is duplicated by` — the linked issue is a duplicate of the current issue; `is epic of` — the current issue is an epic for the linked issue (only for issues of the "Epic" type); `has epic` — the linked issue is an epic for the current issue (only for issues of the "Epic" type).',
        ),
      issue: z.string().min(1).describe("ID or key of the linked issue."),
    },
    run: (tracker, a) =>
      tracker.request("POST", `/issues/${a.issueId}/links`, {
        body: given({ relationship: a.relationship, issue: a.issue }),
      }),
  }),

  tool({
    name: "tracker_get_links",
    description: `Get the links of an issue.

GET /v3/issues/{issueId}/links
https://yandex.ru/support/tracker/en/api/issues/get-links.md`,
    input: {
      issueId: z.string().min(1).describe("ID or key of the issue."),
    },
    run: (tracker, a) => tracker.request("GET", `/issues/${a.issueId}/links`),
  }),

  tool({
    name: "tracker_delete_link",
    description: `Unlink an issue from another issue.

DELETE /v3/issues/{issueId}/links/{linkId}
https://yandex.ru/support/tracker/en/api/issues/delete-link-issue.md`,
    input: {
      issueId: z.string().min(1).describe("ID or key of the current issue."),
      linkId: z
        .string()
        .min(1)
        .describe("ID of the link with another issue, from tracker_get_links."),
    },
    run: (tracker, a) => tracker.request("DELETE", `/issues/${a.issueId}/links/${a.linkId}`),
  }),

  tool({
    name: "tracker_get_external_links",
    description: `Get the issue's links to external application objects.

GET /v3/issues/{issueId}/remotelinks
https://yandex.ru/support/tracker/en/api/issues/get-external-links.md`,
    input: {
      issueId: z.string().min(1).describe("ID or key of the issue."),
    },
    run: (tracker, a) => tracker.request("GET", `/issues/${a.issueId}/remotelinks`),
  }),

  tool({
    name: "tracker_add_external_link",
    description: `Create a link to an object in an external application.

POST /v3/issues/{issueId}/remotelinks
https://yandex.ru/support/tracker/en/api/issues/add-external-link.md`,
    input: {
      issueId: z.string().min(1).describe("ID or key of the current issue."),
      relationship: z.string().min(1).describe("Link type. `RELATES` is the recommended value."),
      key: z.string().min(1).describe("Key of the external application object."),
      origin: z.string().min(1).describe("ID of the application whose object the link points to."),
      backlink: z
        .boolean()
        .optional()
        .describe(
          "Set `true` to have Tracker ask the external application to create the duplicate link on its side.",
        ),
    },
    run: (tracker, a) =>
      tracker.request("POST", `/issues/${a.issueId}/remotelinks`, {
        params: given({ backlink: a.backlink }),
        body: given({ relationship: a.relationship, key: a.key, origin: a.origin }),
      }),
  }),

  tool({
    name: "tracker_delete_external_link",
    description: `Delete an issue's link to an external application object.

DELETE /v3/issues/{issueId}/remotelinks/{externalLinkId}
https://yandex.ru/support/tracker/en/api/issues/delete-external-link.md`,
    input: {
      issueId: z.string().min(1).describe("ID or key of the current issue."),
      externalLinkId: z
        .string()
        .min(1)
        .describe("External link ID, from tracker_get_external_links."),
    },
    run: (tracker, a) =>
      tracker.request("DELETE", `/issues/${a.issueId}/remotelinks/${a.externalLinkId}`),
  }),

  tool({
    name: "tracker_get_transitions",
    description: `Get the status transitions available for an issue.

GET /v3/issues/{issueId}/transitions
https://yandex.ru/support/tracker/en/api/issues/get-transitions.md`,
    input: {
      issueId: z.string().min(1).describe("ID or key of the issue."),
    },
    run: (tracker, a) => tracker.request("GET", `/issues/${a.issueId}/transitions`),
  }),

  tool({
    name: "tracker_new_transition",
    description: `Switch an issue to a new status.

POST /v3/issues/{issueId}/transitions/{transitionId}/_execute
https://yandex.ru/support/tracker/en/api/issues/new-transition.md

The response lists the transitions available in the NEW status, not the
updated issue.`,
    effect: "modify",
    input: {
      issueId: z.string().min(1).describe("ID or key of the issue."),
      transitionId: z.string().min(1).describe("Transition ID, from tracker_get_transitions."),
      comment: z.string().optional().describe("Comment on the issue."),
      fields: z
        .record(z.string(), z.unknown())
        .optional()
        .describe(
          "Issue parameters to change along with the transition, when the transition settings allow it — see https://yandex.ru/support/tracker/en/api/issues/request-fields.md. Custom global fields and queue local fields go here too.",
        ),
    },
    run: (tracker, a) =>
      tracker.request("POST", `/issues/${a.issueId}/transitions/${a.transitionId}/_execute`, {
        body: { ...given({ comment: a.comment }), ...(a.fields ?? {}) },
      }),
  }),

  tool({
    name: "tracker_add_comment",
    description: `Add a comment to an issue.

POST /v3/issues/{issueId}/comments
https://yandex.ru/support/tracker/en/api/issues/add-comment.md`,
    input: {
      issueId: z.string().min(1).describe("ID or key of the issue."),
      text: z.string().min(1).describe("Comment on the issue."),
      isAddToFollowers: z
        .boolean()
        .optional()
        .describe("Add the user who made the comment to the issue followers. `true` by default."),
      attachmentIds: z
        .array(z.unknown())
        .optional()
        .describe(
          "IDs of temporary files to attach to the comment. They also appear on the issue's Attachments tab.",
        ),
      summonees: z.array(z.unknown()).optional().describe("IDs or usernames of summoned users."),
      maillistSummonees: z
        .array(z.unknown())
        .optional()
        .describe("Mailing lists mentioned in the comment."),
      markupType: z
        .string()
        .optional()
        .describe("Type of text markup. Specify `md` when the comment uses YFM markup."),
    },
    run: (tracker, a) =>
      tracker.request("POST", `/issues/${a.issueId}/comments`, {
        params: given({ isAddToFollowers: a.isAddToFollowers }),
        body: given({
          text: a.text,
          attachmentIds: a.attachmentIds,
          summonees: a.summonees,
          maillistSummonees: a.maillistSummonees,
          markupType: a.markupType,
        }),
      }),
  }),

  tool({
    name: "tracker_get_comments",
    description: `Get the comments on an issue.

GET /v3/issues/{issueId}/comments
https://yandex.ru/support/tracker/en/api/issues/get-comments.md`,
    input: {
      issueId: z.string().min(1).describe("ID or key of the issue."),
      expand: z
        .string()
        .optional()
        .describe(
          "Additional fields to include: `attachments`, `html` (comment HTML markup), `all`.",
        ),
      perPage: z.number().int().optional().describe("Number of comments per page. Default 50."),
      id: z.string().optional().describe("Comment `id` the requested page starts after."),
    },
    run: (tracker, a) =>
      tracker.request("GET", `/issues/${a.issueId}/comments`, {
        params: given({ expand: a.expand, perPage: a.perPage, id: a.id }),
      }),
  }),

  tool({
    name: "tracker_edit_comment",
    description: `Edit a comment on an issue.

PATCH /v3/issues/{issueId}/comments/{commentId}
https://yandex.ru/support/tracker/en/api/issues/edit-comment.md`,
    input: {
      issueId: z.string().min(1).describe("ID or key of the issue."),
      commentId: z
        .string()
        .min(1)
        .describe("Unique ID of the comment, numeric (id) or string (longId)."),
      text: z.string().min(1).describe("Edited issue comment."),
      attachmentIds: z
        .array(z.unknown())
        .optional()
        .describe("IDs of temporary files to add as attachments."),
      summonees: z.array(z.unknown()).optional().describe("IDs or usernames of summoned users."),
      markupType: z
        .string()
        .optional()
        .describe("Type of text markup. Specify `md` when the comment uses YFM markup."),
    },
    run: (tracker, a) =>
      tracker.request("PATCH", `/issues/${a.issueId}/comments/${a.commentId}`, {
        body: given({
          text: a.text,
          attachmentIds: a.attachmentIds,
          summonees: a.summonees,
          markupType: a.markupType,
        }),
      }),
  }),

  tool({
    name: "tracker_delete_comment",
    description: `Delete a comment on an issue.

DELETE /v3/issues/{issueId}/comments/{commentId}
https://yandex.ru/support/tracker/en/api/issues/delete-comment.md`,
    input: {
      issueId: z.string().min(1).describe("ID or key of the issue."),
      commentId: z
        .string()
        .min(1)
        .describe("Unique ID of the comment, numeric (id) or string (longId)."),
    },
    run: (tracker, a) => tracker.request("DELETE", `/issues/${a.issueId}/comments/${a.commentId}`),
  }),

  tool({
    name: "tracker_add_reaction_to_comment",
    description: `React to a comment on an issue.

POST /v3/issues/{issueId}/comments/{commentId}/reactions/{reactionName}
https://yandex.ru/support/tracker/en/api/issues/add-reaction-to-comment.md`,
    input: {
      issueId: z.string().min(1).describe("Issue ID or key."),
      commentId: z
        .string()
        .min(1)
        .describe("Unique ID of the comment, numeric (id) or string (longId)."),
      reactionName: z
        .string()
        .min(1)
        .describe(
          "Reaction name: `LIKE`, `DISLIKE`, `LAUGH`, `HOORAY`, `CONFUSED`, `HEART`, `ROCKET`, `EYES`, `FIRE`, `OK`, `FACEPALM`, `CHECK`.",
        ),
    },
    run: (tracker, a) =>
      tracker.request(
        "POST",
        `/issues/${a.issueId}/comments/${a.commentId}/reactions/${a.reactionName}`,
      ),
  }),

  tool({
    name: "tracker_add_checklist_item",
    description: `Create a checklist on an issue or add an item to it.

POST /v3/issues/{issueId}/checklistItems
https://yandex.ru/support/tracker/en/api/issues/add-checklist-item.md

The response is the whole issue, not the created item.`,
    input: {
      issueId: z.string().min(1).describe("Issue ID or key."),
      text: z.string().min(1).describe("Text of the item."),
      checked: z.boolean().optional().describe("Mark the item as completed."),
      assignee: z
        .string()
        .optional()
        .describe("ID or username of the user the checklist item is assigned to."),
      deadline: z
        .record(z.string(), z.unknown())
        .optional()
        .describe(
          "Deadline for the checklist item: `date` in `YYYY-MM-DDThh:mm:ss.sss±hhmm` format and `deadlineType`.",
        ),
    },
    run: (tracker, a) =>
      tracker.request("POST", `/issues/${a.issueId}/checklistItems`, {
        body: given({
          text: a.text,
          checked: a.checked,
          assignee: a.assignee,
          deadline: a.deadline,
        }),
      }),
  }),

  tool({
    name: "tracker_get_checklist",
    description: `Get the checklist of an issue.

GET /v3/issues/{issueId}/checklistItems
https://yandex.ru/support/tracker/en/api/issues/get-checklist.md`,
    input: {
      issueId: z.string().min(1).describe("Issue ID or key."),
    },
    run: (tracker, a) => tracker.request("GET", `/issues/${a.issueId}/checklistItems`),
  }),

  tool({
    name: "tracker_edit_checklist_item",
    description: `Edit an item of an issue's checklist.

PATCH /v3/issues/{issueId}/checklistItems/{checklistItemId}
https://yandex.ru/support/tracker/en/api/issues/edit-checklist.md

The response is the whole issue with its full checklist. (The page
contradicts itself: its parameter table describes one item, its example shows
an array of every item. This follows the table, which matches the item id in
the path, and that is what the endpoint accepts.)`,
    input: {
      issueId: z.string().min(1).describe("Issue ID or key."),
      checklistItemId: z.string().min(1).describe("Checklist item ID, from tracker_get_checklist."),
      text: z.string().min(1).describe("Text of the checklist item."),
      checked: z.boolean().optional().describe("Mark the item as completed."),
      assignee: z
        .string()
        .optional()
        .describe("ID or username of the user the checklist item is assigned to."),
      deadline: z
        .record(z.string(), z.unknown())
        .optional()
        .describe(
          "Deadline for the checklist item: `date` in `YYYY-MM-DDThh:mm:ss.sss±hhmm` format and `deadlineType`.",
        ),
    },
    run: (tracker, a) =>
      tracker.request("PATCH", `/issues/${a.issueId}/checklistItems/${a.checklistItemId}`, {
        body: given({
          text: a.text,
          checked: a.checked,
          assignee: a.assignee,
          deadline: a.deadline,
        }),
      }),
  }),

  tool({
    name: "tracker_delete_checklist",
    description: `Delete the whole checklist from an issue.

DELETE /v3/issues/{issueId}/checklistItems
https://yandex.ru/support/tracker/en/api/issues/delete-checklist.md`,
    input: {
      issueId: z.string().min(1).describe("Issue ID or key."),
    },
    run: (tracker, a) => tracker.request("DELETE", `/issues/${a.issueId}/checklistItems`),
  }),

  tool({
    name: "tracker_delete_checklist_item",
    description: `Delete one item from an issue's checklist.

DELETE /v3/issues/{issueId}/checklistItems/{checklistItemId}
https://yandex.ru/support/tracker/en/api/issues/delete-checklist-item.md`,
    input: {
      issueId: z.string().min(1).describe("Issue ID or key."),
      checklistItemId: z.string().min(1).describe("Checklist item ID, from tracker_get_checklist."),
    },
    run: (tracker, a) =>
      tracker.request("DELETE", `/issues/${a.issueId}/checklistItems/${a.checklistItemId}`),
  }),

  tool({
    name: "tracker_get_attachments",
    description: `Get the files attached to an issue and to the comments below it.

GET /v3/issues/{issueId}/attachments
https://yandex.ru/support/tracker/en/api/issues/get-attachments-list.md`,
    input: {
      issueId: z.string().min(1).describe("Issue ID or key."),
    },
    run: (tracker, a) => tracker.request("GET", `/issues/${a.issueId}/attachments`),
  }),

  tool({
    name: "tracker_get_attachment",
    description: `Download a file attached to an issue.

GET /v3/issues/{issueId}/attachments/{fileId}/{fileName}
https://yandex.ru/support/tracker/en/api/issues/get-attachment.md

Writes the file to \`destDir\` and returns {"path", "name", "size"}.`,
    effect: "create",
    input: {
      issueId: z.string().min(1).describe("Issue ID or key."),
      fileId: z.string().min(1).describe("Unique file ID, from tracker_get_attachments."),
      fileName: z
        .string()
        .min(1)
        .describe("File name, from tracker_get_attachments. Part of the request path."),
      destDir: z.string().min(1).describe("Local directory to save the downloaded file in."),
      saveAs: z
        .string()
        .optional()
        .describe("Name to save the file under locally. Defaults to `fileName`."),
    },
    run: (tracker, a) =>
      tracker.download(
        `/issues/${a.issueId}/attachments/${a.fileId}/${a.fileName}`,
        a.destDir,
        a.saveAs ?? a.fileName,
      ),
  }),

  tool({
    name: "tracker_get_attachment_preview",
    description: `Download the thumbnail of an image file attached to an issue.

GET /v3/issues/{issueId}/thumbnails/{fileId}
https://yandex.ru/support/tracker/en/api/issues/get-attachment-preview.md

Writes the thumbnail to \`destDir\` and returns {"path", "name", "size"}.`,
    effect: "create",
    input: {
      issueId: z.string().min(1).describe("Issue ID or key."),
      fileId: z
        .string()
        .min(1)
        .describe("Unique ID of the attached file, from tracker_get_attachments."),
      destDir: z.string().min(1).describe("Local directory to save the thumbnail in."),
      saveAs: z
        .string()
        .optional()
        .describe("Name to save the thumbnail under locally. Defaults to `fileId`."),
    },
    run: (tracker, a) =>
      tracker.download(
        `/issues/${a.issueId}/thumbnails/${a.fileId}`,
        a.destDir,
        a.saveAs ?? a.fileId,
      ),
  }),

  tool({
    name: "tracker_post_attachment",
    description: `Attach a file to an issue.

POST /v3/issues/{issueId}/attachments/
https://yandex.ru/support/tracker/en/api/issues/post-attachment.md

The file appears on the issue's Attachments tab.`,
    input: {
      issueId: z.string().min(1).describe("Issue ID or key."),
      filePath: z
        .string()
        .min(1)
        .describe("Path to the local file to upload. Maximum size 1024 Mbit."),
      filename: z
        .string()
        .optional()
        .describe(
          "New name to store the file under on the server. The local file name is used when omitted.",
        ),
    },
    run: (tracker, a) =>
      tracker.upload(`/issues/${a.issueId}/attachments/`, a.filePath, {
        params: given({ filename: a.filename }),
      }),
  }),

  tool({
    name: "tracker_post_temp_attachment",
    description: `Upload a temporary file.

POST /v3/attachments/
https://yandex.ru/support/tracker/en/api/issues/temp-attachment.md

Pass the returned ID in \`attachmentIds\` when creating an issue or adding a
comment. Each temporary file ID can be used only once.`,
    input: {
      filePath: z
        .string()
        .min(1)
        .describe("Path to the local file to upload. Maximum size 1024 Mbit."),
      filename: z
        .string()
        .optional()
        .describe(
          "New name to store the file under on the server. The local file name is used when omitted.",
        ),
    },
    run: (tracker, a) =>
      tracker.upload("/attachments/", a.filePath, { params: given({ filename: a.filename }) }),
  }),

  tool({
    name: "tracker_delete_attachment",
    description: `Delete a file attached to an issue.

DELETE /v3/issues/{issueId}/attachments/{fileId}/
https://yandex.ru/support/tracker/en/api/issues/delete-attachment.md`,
    input: {
      issueId: z.string().min(1).describe("Issue ID or key."),
      fileId: z.string().min(1).describe("Unique file ID, from tracker_get_attachments."),
    },
    run: (tracker, a) => tracker.request("DELETE", `/issues/${a.issueId}/attachments/${a.fileId}/`),
  }),

  tool({
    name: "tracker_new_worklog",
    description: `Add a record of time spent on an issue.

POST /v3/issues/{issueId}/worklog
https://yandex.ru/support/tracker/en/api/issues/new-worklog.md

Time spent is measured in business weeks (5 days) and business days (8 hours),
so a submitted \`P5D\` comes back as \`P1W\`.`,
    input: {
      issueId: z.string().min(1).describe("Issue ID or key."),
      start: z
        .string()
        .min(1)
        .describe(
          "Date and time when work on the issue started, in `YYYY-MM-DDThh:mm:ss.sss±hhmm` format.",
        ),
      duration: z
        .string()
        .min(1)
        .describe(
          "Time spent in ISO 8601 `PnYnMnDTnHnMnS` or `PnW` format — for example `P6W` (6 weeks), `PT300M` (300 minutes), `P0Y0M30DT2H10M25S`.",
        ),
      comment: z
        .string()
        .optional()
        .describe("Text of the comment on the record, saved to the Report on time spent."),
    },
    run: (tracker, a) =>
      tracker.request("POST", `/issues/${a.issueId}/worklog`, {
        body: given({ start: a.start, duration: a.duration, comment: a.comment }),
      }),
  }),

  tool({
    name: "tracker_get_issue_worklog",
    description: `Get all the records of time spent on an issue.

GET /v3/issues/{issueId}/worklog
https://yandex.ru/support/tracker/en/api/issues/issue-worklog.md`,
    input: {
      issueId: z.string().min(1).describe("Issue ID or key."),
    },
    run: (tracker, a) => tracker.request("GET", `/issues/${a.issueId}/worklog`),
  }),

  tool({
    name: "tracker_patch_worklog",
    description: `Edit a record of time spent on an issue.

PATCH /v3/issues/{issueId}/worklog/{recordId}
https://yandex.ru/support/tracker/en/api/issues/patch-worklog.md

Time spent is measured in business weeks (5 days) and business days (8 hours),
so a submitted \`P5D\` comes back as \`P1W\`.`,
    input: {
      issueId: z.string().min(1).describe("Issue ID or key."),
      recordId: z.string().min(1).describe("ID of the record of time spent."),
      duration: z
        .string()
        .min(1)
        .describe(
          "Time spent in ISO 8601 `PnYnMnDTnHnMnS` or `PnW` format — for example `P6W` (6 weeks), `PT300M` (300 minutes), `P0Y0M30DT2H10M25S`.",
        ),
      comment: z
        .string()
        .optional()
        .describe("Text of the comment on the record, saved to the Report on time spent."),
    },
    run: (tracker, a) =>
      tracker.request("PATCH", `/issues/${a.issueId}/worklog/${a.recordId}`, {
        body: given({ duration: a.duration, comment: a.comment }),
      }),
  }),

  tool({
    name: "tracker_delete_worklog",
    description: `Delete a record of time spent on an issue.

DELETE /v3/issues/{issueId}/worklog/{recordId}
https://yandex.ru/support/tracker/en/api/issues/delete-worklog.md`,
    input: {
      issueId: z.string().min(1).describe("Issue ID or key."),
      recordId: z.string().min(1).describe("ID of the record of time spent."),
    },
    run: (tracker, a) => tracker.request("DELETE", `/issues/${a.issueId}/worklog/${a.recordId}`),
  }),

  tool({
    name: "tracker_get_worklog",
    description: `Select records of time spent by author and creation date.

GET /v3/worklog
https://yandex.ru/support/tracker/en/api/issues/get-worklog.md`,
    input: {
      createdBy: z.string().optional().describe("ID or username of the record author."),
      from: z
        .string()
        .optional()
        .describe(
          "Start of the interval the records were created in, in `YYYY-MM-DDThh:mm:ss.sss±hhmm` format. Sent as `createdAt=from:<start>`; requires `createdBy`.",
        ),
      to: z
        .string()
        .optional()
        .describe(
          "End of the interval the records were created in, in `YYYY-MM-DDThh:mm:ss.sss±hhmm` format. Sent as `createdAt=to:<end>`; requires `createdBy`.",
        ),
    },
    run: (tracker, a) => {
      const params = given({ createdBy: a.createdBy });
      const createdAt: string[] = [];
      if (a.from !== undefined) createdAt.push(`from:${a.from}`);
      if (a.to !== undefined) createdAt.push(`to:${a.to}`);
      if (createdAt.length > 0) params.createdAt = createdAt;
      return tracker.request("GET", "/worklog", { params });
    },
  }),

  tool({
    name: "tracker_search_worklog",
    description: `Select records of time spent by author and creation date.

POST /v3/worklog/_search
https://yandex.ru/support/tracker/en/api/issues/get-worklog.md`,
    effect: "read",
    input: {
      createdBy: z.string().optional().describe("ID or username of the record author."),
      createdAt: z
        .record(z.string(), z.unknown())
        .optional()
        .describe(
          "Record creation date and time: `from` and `to`, both in `YYYY-MM-DDThh:mm:ss.sss±hhmm` format.",
        ),
    },
    run: (tracker, a) =>
      tracker.request("POST", "/worklog/_search", {
        body: given({ createdBy: a.createdBy, createdAt: a.createdAt }),
      }),
  }),

  tool({
    name: "tracker_get_global_fields",
    description: `Get all the global issue fields of the organization.

GET /v3/fields
https://yandex.ru/support/tracker/en/api/issues/get-global-fields.md`,
    input: {},
    run: (tracker) => tracker.request("GET", "/fields"),
  }),

  tool({
    name: "tracker_create_field",
    description: `Create a global issue field.

POST /v3/fields
https://yandex.ru/support/tracker/en/api/issues/create-field.md`,
    input: {
      name: z
        .record(z.string(), z.unknown())
        .describe("Field name: `en` in English and `ru` in Russian."),
      id: z.string().min(1).describe("Field ID."),
      category: z
        .string()
        .min(1)
        .describe(
          "ID of the field category. Get the list of categories with `GET /v3/fields/categories`.",
        ),
      type: z
        .string()
        .min(1)
        .describe(
          "Field type: `ru.yandex.startrek.core.fields.DateFieldType` (date), `ru.yandex.startrek.core.fields.DateTimeFieldType` (date/time), `ru.yandex.startrek.core.fields.StringFieldType` (one-line text), `ru.yandex.startrek.core.fields.TextFieldType` (multi-line text), `ru.yandex.startrek.core.fields.FloatFieldType` (fractional number), `ru.yandex.startrek.core.fields.IntegerFieldType` (integer), `ru.yandex.startrek.core.fields.UserFieldType` (user's name), `ru.yandex.startrek.core.fields.UriFieldType` (link).",
        ),
      optionsProvider: z
        .record(z.string(), z.unknown())
        .optional()
        .describe(
          "Drop-down list settings: `type` (`FixedListOptionsProvider` for strings or numbers, `FixedUserListOptionsProvider` for users) and `values` (up to 3000 entries).",
        ),
      order: z
        .number()
        .int()
        .optional()
        .describe("Sequence number in the list of organization fields."),
      description: z.string().optional().describe("Field description."),
      readonly: z
        .boolean()
        .optional()
        .describe("`true` makes the field value non-editable, `false` editable."),
      visible: z
        .boolean()
        .optional()
        .describe("`true` keeps the field always visible in the interface."),
      hidden: z
        .boolean()
        .optional()
        .describe("`true` hides the field in the interface even when it is not empty."),
      container: z
        .boolean()
        .optional()
        .describe(
          "`true` allows multiple values in the field, as in Tags. Applies to `StringFieldType`, `UserFieldType` and drop-down lists.",
        ),
    },
    run: (tracker, a) =>
      tracker.request("POST", "/fields", {
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
    name: "tracker_get_field",
    description: `Get the parameters and possible values of one issue field.

GET /v3/fields/{fieldId}
https://yandex.ru/support/tracker/en/api/issues/get-issue-fields.md`,
    input: {
      fieldId: z.string().min(1).describe("Issue field ID."),
    },
    run: (tracker, a) => tracker.request("GET", `/fields/${a.fieldId}`),
  }),

  tool({
    name: "tracker_patch_field",
    description: `Edit an issue field: its name, and its possible values and settings.

PATCH /v3/fields/{fieldId}
https://yandex.ru/support/tracker/en/api/issues/patch-issue-field-name.md
https://yandex.ru/support/tracker/en/api/issues/patch-issue-field-value.md

The two pages describe the same endpoint — renaming a field and editing its
values — and the arguments below are the union of what they document.`,
    input: {
      fieldId: z.string().min(1).describe("Issue field ID."),
      version: z
        .string()
        .optional()
        .describe("Current version of the issue field. Changes apply only to it."),
      name: z
        .record(z.string(), z.unknown())
        .optional()
        .describe("Field name: `en` in English and `ru` in Russian."),
      category: z
        .string()
        .optional()
        .describe(
          "ID of the field category. Get the list of categories with `GET /v3/fields/categories`.",
        ),
      order: z
        .number()
        .int()
        .optional()
        .describe("Sequence number in the list of organization fields."),
      description: z.string().optional().describe("Field description."),
      readonly: z
        .boolean()
        .optional()
        .describe("`true` makes the field value non-editable, `false` editable."),
      hidden: z
        .boolean()
        .optional()
        .describe("`true` hides the field in the interface even when it is not empty."),
      visible: z
        .boolean()
        .optional()
        .describe("`true` keeps the field always visible in the interface."),
      optionsProvider: z
        .record(z.string(), z.unknown())
        .optional()
        .describe(
          "Allowed field values: `type` (type of field values) and `values` (array of field values).",
        ),
    },
    run: (tracker, a) =>
      tracker.request("PATCH", `/fields/${a.fieldId}`, {
        params: given({ version: a.version }),
        body: given({
          name: a.name,
          category: a.category,
          order: a.order,
          description: a.description,
          readonly: a.readonly,
          hidden: a.hidden,
          visible: a.visible,
          optionsProvider: a.optionsProvider,
        }),
      }),
  }),

  tool({
    name: "tracker_create_field_category",
    description: `Create a category for issue fields.

POST /v3/fields/categories
https://yandex.ru/support/tracker/en/api/issues/create-issue-field-category.md`,
    input: {
      name: z
        .record(z.string(), z.unknown())
        .describe("Category name: `en` in English and `ru` in Russian."),
      order: z
        .number()
        .int()
        .describe(
          "Weight of the field in the interface. Lower weights are displayed above higher ones.",
        ),
      description: z.string().optional().describe("Category description."),
    },
    run: (tracker, a) =>
      tracker.request("POST", "/fields/categories", {
        body: given({ name: a.name, order: a.order, description: a.description }),
      }),
  }),

  tool({
    name: "tracker_patch_field_category",
    description: `Edit a category of issue fields.

PATCH /v3/fields/categories/{categoryId}
https://yandex.ru/support/tracker/en/api/issues/patch-issue-field-category.md`,
    input: {
      categoryId: z.string().min(1).describe("ID of the issue field category."),
      name: z
        .record(z.string(), z.unknown())
        .describe("Category name: `en` in English and `ru` in Russian."),
      order: z
        .number()
        .int()
        .describe(
          "Weight of the field in the interface. Lower weights are displayed above higher ones.",
        ),
      description: z.string().optional().describe("Category description."),
      version: z
        .number()
        .int()
        .optional()
        .describe("Category version. Changes apply only to the current version."),
    },
    run: (tracker, a) =>
      tracker.request("PATCH", `/fields/categories/${a.categoryId}`, {
        params: given({ version: a.version }),
        body: given({ name: a.name, order: a.order, description: a.description }),
      }),
  }),

  tool({
    name: "tracker_get_applications",
    description: `Get the external applications an issue can be linked to.

GET /v3/applications
https://yandex.ru/support/tracker/en/api/issues/get-applications.md`,
    input: {},
    run: (tracker) => tracker.request("GET", "/applications"),
  }),

  tool({
    name: "tracker_create_report",
    description: `Generate a report of the issues matching the given search criteria.

POST /v3/entities/report/
https://yandex.ru/support/tracker/en/api/issues/create-report.md`,
    input: {
      fields: z
        .record(z.string(), z.unknown())
        .describe(
          "Report parameters: `summary` (report name) and `parameters` with `type` (`issueFilterExport`), `format` (`xlsx`, `xml` or `csv`), `filter` (one of `query`, `filter` or `filterId`, plus `sorts` with `orderBy`/`orderAsc`) and `fields` (issue fields to include).",
        ),
    },
    run: (tracker, a) =>
      tracker.request("POST", "/entities/report/", { body: given({ fields: a.fields }) }),
  }),

  tool({
    name: "tracker_search_reports",
    description: `Find the issue reports matching the given criteria.

POST /v3/entities/report/_search
https://yandex.ru/support/tracker/en/api/issues/search-reports.md`,
    effect: "read",
    input: {
      filter: z
        .record(z.string(), z.unknown())
        .optional()
        .describe(
          "Report filter. Only `id` (report ID), `shortId` (short report ID) and `author` (the `id` of the report's `createdBy`) can be filtered on.",
        ),
      orderBy: z
        .string()
        .optional()
        .describe(
          "Field to sort reports by: `id`, `shortId`, `createdBy`, `createdAt`, `updatedAt`, `self`.",
        ),
      orderAsc: z
        .boolean()
        .optional()
        .describe("Sort direction: `true` ascending, `false` descending."),
      perPage: z
        .number()
        .int()
        .optional()
        .describe("Number of reports per response page. Default 50."),
      page: z.number().int().optional().describe("Page number. Default 1."),
    },
    run: (tracker, a) =>
      tracker.request("POST", "/entities/report/_search", {
        params: given({ perPage: a.perPage, page: a.page }),
        body: given({ filter: a.filter, orderBy: a.orderBy, orderAsc: a.orderAsc }),
      }),
  }),
];
