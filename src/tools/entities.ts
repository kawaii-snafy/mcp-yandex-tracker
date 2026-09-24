/** Projects, portfolios and goals — https://yandex.ru/support/tracker/en/api/entities/about-entities.md */

import { z } from "zod";
import { given, path } from "../client.ts";
import { tool } from "../tool.ts";

export const entityTools = [
  tool({
    name: "tracker_create_entity",
    description: `Create a new entity: a goal, project, or project portfolio.

POST /v3/entities/{entityType}
https://yandex.ru/support/tracker/en/api/entities/create-entity.md`,
    input: {
      entityType: z.string().min(1).describe("Entity type: project, portfolio, goal."),
      summary: z.string().min(1).describe("Name (required field)."),
      queues: z
        .string()
        .optional()
        .describe("Queue (required for the project if the teamAccess field isn't specified)."),
      teamAccess: z
        .boolean()
        .optional()
        .describe("Access (required for the project if the queues field isn't specified)."),
      description: z.string().optional().describe("Description."),
      markupType: z
        .string()
        .optional()
        .describe(
          "Text markup type. If you use YFM markup in a comment or entity description, specify the `md` value.",
        ),
      author: z.string().optional().describe("Author (user ID)."),
      lead: z.string().optional().describe("Lead (user ID)."),
      teamUsers: z.array(z.unknown()).optional().describe("Participants (array of user IDs)."),
      clients: z.array(z.unknown()).optional().describe("Customers (array of user IDs)."),
      followers: z.array(z.unknown()).optional().describe("Followers (array of user IDs)."),
      start: z.string().optional().describe("Start date in `YYYY-MM-DDThh:mm:ss.sss±hhmm` format."),
      end: z.string().optional().describe("Deadline in `YYYY-MM-DDThh:mm:ss.sss±hhmm` format."),
      tags: z.array(z.unknown()).optional().describe("Tags."),
      parentEntity: z
        .record(z.string(), z.unknown())
        .optional()
        .describe(
          "Parent entity data: primary (ID of the main portfolio for projects and portfolios, or of the parent goal for goals) and secondary (IDs of additional portfolios; goals don't support secondary).",
        ),
      entityStatus: z
        .string()
        .optional()
        .describe(
          "Status. For projects or portfolios: draft, draft2, in_progress, according_to_plan, postponed, at_risk, blocked, launched, cancelled. For goals: draft, according_to_plan, at_risk, blocked, achieved, partially_achieved, not_achieved, exceeded, cancelled.",
        ),
      links: z
        .array(z.unknown())
        .optional()
        .describe(
          "Array of objects with settings of links to other entities: relationship (link type) and entity (ID of the linked entity).",
        ),
      fields: z
        .string()
        .optional()
        .describe("Additional entity fields to include in the response."),
    },
    run: (tracker, a) =>
      tracker.request("POST", path`/entities/${a.entityType}`, {
        params: given({ fields: a.fields }),
        body: {
          fields: given({
            summary: a.summary,
            queues: a.queues,
            teamAccess: a.teamAccess,
            description: a.description,
            markupType: a.markupType,
            author: a.author,
            lead: a.lead,
            teamUsers: a.teamUsers,
            clients: a.clients,
            followers: a.followers,
            start: a.start,
            end: a.end,
            tags: a.tags,
            parentEntity: a.parentEntity,
            entityStatus: a.entityStatus,
          }),
          ...given({ links: a.links }),
        },
      }),
  }),

  tool({
    name: "tracker_get_entity",
    description: `Get information about an entity: a goal, project, or project portfolio.

GET /v3/entities/{entityType}/{entityId}
https://yandex.ru/support/tracker/en/api/entities/get-entity.md`,
    input: {
      entityType: z.string().min(1).describe("Entity type: project, portfolio, goal."),
      entityId: z
        .string()
        .min(1)
        .describe("Entity ID. You can use the `id` or `shortId` parameter as the ID."),
      fields: z
        .string()
        .optional()
        .describe("Additional entity fields to include in the response."),
      expand: z
        .string()
        .optional()
        .describe(
          "Additional information to include in the response: `attachments` (attached files).",
        ),
    },
    run: (tracker, a) =>
      tracker.request("GET", path`/entities/${a.entityType}/${a.entityId}`, {
        params: given({ fields: a.fields, expand: a.expand }),
      }),
  }),

  tool({
    name: "tracker_update_entity",
    description: `Update information about an entity: a goal, project, or project portfolio.

PATCH /v3/entities/{entityType}/{entityId}
https://yandex.ru/support/tracker/en/api/entities/update-entity.md

This is also the request that edits a goal's key results, an entity's metrics
and its checklist — see keyResultItems, metricItems and checklistItems:
https://yandex.ru/support/tracker/en/api/entities/keyresults.md
https://yandex.ru/support/tracker/en/api/entities/metric.md
https://yandex.ru/support/tracker/en/api/entities/checklists/add-checklist.md`,
    input: {
      entityType: z.string().min(1).describe("Entity type: project, portfolio, goal."),
      entityId: z
        .string()
        .min(1)
        .describe("Entity ID. You can use the `id` or `shortId` parameter as the ID."),
      summary: z.string().optional().describe("Name."),
      queues: z
        .string()
        .optional()
        .describe("Queue (required for the project if the teamAccess field isn't specified)."),
      teamAccess: z
        .boolean()
        .optional()
        .describe("Access (required for the project if the queues field isn't specified)."),
      description: z.string().optional().describe("Description."),
      markupType: z
        .string()
        .optional()
        .describe(
          "Text markup type. If you use YFM markup in a comment or entity description, specify the `md` value.",
        ),
      author: z.string().optional().describe("Author (user ID)."),
      lead: z.string().optional().describe("Lead (user ID)."),
      teamUsers: z.array(z.unknown()).optional().describe("Participants (array of user IDs)."),
      clients: z.array(z.unknown()).optional().describe("Customers (array of user IDs)."),
      followers: z.array(z.unknown()).optional().describe("Followers (array of user IDs)."),
      start: z.string().optional().describe("Start date in `YYYY-MM-DDThh:mm:ss.sss±hhmm` format."),
      end: z.string().optional().describe("Deadline in `YYYY-MM-DDThh:mm:ss.sss±hhmm` format."),
      tags: z.array(z.unknown()).optional().describe("Tags."),
      parentEntity: z
        .record(z.string(), z.unknown())
        .optional()
        .describe(
          "Parent entity data: primary (ID of the main portfolio for projects and portfolios, or of the parent goal for goals) and secondary (IDs of additional portfolios; goals don't support secondary).",
        ),
      entityStatus: z
        .string()
        .optional()
        .describe(
          "Status. For projects or portfolios: draft, draft2, in_progress, according_to_plan, postponed, at_risk, blocked, launched, cancelled. For goals: draft, according_to_plan, at_risk, blocked, achieved, partially_achieved, not_achieved, exceeded, cancelled.",
        ),
      checklistItems: z
        .array(z.unknown())
        .optional()
        .describe(
          "Checklist of a project or portfolio; each object: id, text, checked, assignee, deadline, checklistItemType. Replaces the whole checklist.",
        ),
      metricItems: z
        .array(z.unknown())
        .optional()
        .describe(
          "Metrics; each object: text (metric name, required) and url (widget URL for an iframe). Replaces the whole list of metrics.",
        ),
      keyResultItems: z
        .array(z.unknown())
        .optional()
        .describe(
          "Key results of a goal; each object: type (`value` or `binary`, required), text (required), assignee, deadline, progress (start/end/current, required when type is `value`), achieved. Replaces the whole list of key results.",
        ),
      comment: z.string().optional().describe("Comment."),
      links: z
        .array(z.unknown())
        .optional()
        .describe(
          "Array of objects with settings of links to other entities: relationship (link type) and entity (ID of the linked entity).",
        ),
      fields: z
        .string()
        .optional()
        .describe("Additional entity fields to include in the response."),
      expand: z
        .string()
        .optional()
        .describe(
          "Additional information to include in the response: `attachments` (attached files).",
        ),
    },
    run: (tracker, a) => {
      const fields = given({
        summary: a.summary,
        queues: a.queues,
        teamAccess: a.teamAccess,
        description: a.description,
        markupType: a.markupType,
        author: a.author,
        lead: a.lead,
        teamUsers: a.teamUsers,
        clients: a.clients,
        followers: a.followers,
        start: a.start,
        end: a.end,
        tags: a.tags,
        parentEntity: a.parentEntity,
        entityStatus: a.entityStatus,
        checklistItems: a.checklistItems,
        metricItems: a.metricItems,
        keyResultItems: a.keyResultItems,
      });
      return tracker.request("PATCH", path`/entities/${a.entityType}/${a.entityId}`, {
        params: given({ fields: a.fields, expand: a.expand }),
        body: {
          ...given({ fields: Object.keys(fields).length > 0 ? fields : undefined }),
          ...given({ comment: a.comment, links: a.links }),
        },
      });
    },
  }),

  tool({
    name: "tracker_delete_entity",
    description: `Delete an entity: a goal, project, or project portfolio.

DELETE /v3/entities/{entityType}/{entityId}
https://yandex.ru/support/tracker/en/api/entities/delete-entity.md`,
    input: {
      entityType: z.string().min(1).describe("Entity type: project, portfolio, goal."),
      entityId: z
        .string()
        .min(1)
        .describe("Entity ID. You can use the `id` or `shortId` parameter as the ID."),
      withBoard: z.boolean().optional().describe("Delete together with the board."),
    },
    run: (tracker, a) =>
      tracker.request("DELETE", path`/entities/${a.entityType}/${a.entityId}`, {
        params: given({ withBoard: a.withBoard }),
      }),
  }),

  tool({
    name: "tracker_search_entities",
    description: `Get a list of entities that meet specific criteria.

POST /v3/entities/{entityType}/_search
https://yandex.ru/support/tracker/en/api/entities/search-entities.md

Entity field keys and value keys, e.g., statuses, sometimes differ from
similar issue keys.`,
    effect: "read",
    input: {
      entityType: z.string().min(1).describe("Entity type: project, portfolio, goal."),
      input: z.string().optional().describe("Substring in the entity name."),
      filter: z
        .record(z.string(), z.unknown())
        .optional()
        .describe(
          "Filtering parameters. The parameter can specify any field key and value for filtering.",
        ),
      orderBy: z
        .string()
        .optional()
        .describe("Sorting parameters. The parameter can specify any field key for sorting."),
      orderAsc: z.boolean().optional().describe("Sorting direction."),
      rootOnly: z.boolean().optional().describe("Output only entities that are not nested."),
      fields: z.string().optional().describe("Additional fields to include in the response."),
      perPage: z
        .number()
        .int()
        .optional()
        .describe("Number of issues per response page. The default value is 50."),
      page: z
        .number()
        .int()
        .optional()
        .describe("Page with search results. The default value is 1."),
    },
    run: (tracker, a) =>
      tracker.request("POST", path`/entities/${a.entityType}/_search`, {
        params: given({ fields: a.fields, perPage: a.perPage, page: a.page }),
        body: given({
          input: a.input,
          filter: a.filter,
          orderBy: a.orderBy,
          orderAsc: a.orderAsc,
          rootOnly: a.rootOnly,
        }),
      }),
  }),

  tool({
    name: "tracker_bulkchange_entities",
    description: `Update multiple goals, projects, or project portfolios at once.

POST /v3/entities/{entityType}/bulkchange/_update
https://yandex.ru/support/tracker/en/api/entities/bulkchange-entities.md`,
    effect: "modify",
    input: {
      entityType: z.string().min(1).describe("Entity type: project, portfolio, goal."),
      metaEntities: z.array(z.unknown()).describe("List of entity IDs."),
      values: z
        .record(z.string(), z.unknown())
        .describe(
          "Object with settings for bulk entity changes: fields (object with key-value pairs), comment, links (array of objects with relationship and entity).",
        ),
    },
    run: (tracker, a) =>
      tracker.request("POST", path`/entities/${a.entityType}/bulkchange/_update`, {
        body: given({ metaEntities: a.metaEntities, values: a.values }),
      }),
  }),

  tool({
    name: "tracker_get_entity_events",
    description: `Get a paginated entity event history.

GET /v3/entities/{entityType}/{entityId}/events/_relative
https://yandex.ru/support/tracker/en/api/entities/get-events-relative.md`,
    input: {
      entityType: z.string().min(1).describe("Entity type: project, portfolio, goal."),
      entityId: z
        .string()
        .min(1)
        .describe("Entity ID. You can use the `id` or `shortId` parameter as the ID."),
      perPage: z
        .number()
        .int()
        .optional()
        .describe("Sets the maximum number of events in the response. The default value is 50."),
      from: z
        .string()
        .optional()
        .describe(
          "ID of the event after which the list starts to be generated. The event itself is not included in the list. Not used together with `selected`.",
        ),
      selected: z
        .string()
        .optional()
        .describe(
          "ID of the event around which the list is generated. Not specified together with the `from` parameter.",
        ),
      newEventsOnTop: z
        .boolean()
        .optional()
        .describe("Reverses the order of events in the list. The default value is `false`."),
      direction: z
        .string()
        .optional()
        .describe(
          "Sets the order of events in the list: `forward` (default), or `backward`, which inverts the `newEventsOnTop` parameter value.",
        ),
    },
    run: (tracker, a) =>
      tracker.request("GET", path`/entities/${a.entityType}/${a.entityId}/events/_relative`, {
        params: given({
          perPage: a.perPage,
          from: a.from,
          selected: a.selected,
          newEventsOnTop: a.newEventsOnTop,
          direction: a.direction,
        }),
      }),
  }),

  tool({
    name: "tracker_entity_add_comment",
    description: `Add a comment to an entity.

POST /v3/entities/{entityType}/{entityId}/comments
https://yandex.ru/support/tracker/en/api/entities/comments/add-comment.md`,
    input: {
      entityType: z.string().min(1).describe("Entity type: project, portfolio, goal."),
      entityId: z
        .string()
        .min(1)
        .describe("Entity ID. You can use the `id` or `shortId` parameter as the ID."),
      text: z.string().min(1).describe("Text of the comment."),
      attachmentIds: z
        .array(z.unknown())
        .optional()
        .describe("IDs of temporary files that will be added as attachments."),
      summonees: z.array(z.unknown()).optional().describe("IDs or usernames of summoned users."),
      maillistSummonees: z
        .array(z.unknown())
        .optional()
        .describe("List of mailing lists mentioned in the comment."),
      isAddToFollowers: z
        .boolean()
        .optional()
        .describe("Adding a comment author to followers. The default value is `true`."),
      notify: z
        .boolean()
        .optional()
        .describe(
          "Notify the users specified in the Author, Lead, Participants, Customers, and Followers fields. The default value is `true`.",
        ),
      notifyAuthor: z
        .boolean()
        .optional()
        .describe("Notify the author of the changes. The default value is `false`."),
      expand: z
        .string()
        .optional()
        .describe(
          "Additional information to include in the response: `all`, `html` (comment HTML markup), `attachments`, `reactions`.",
        ),
    },
    run: (tracker, a) =>
      tracker.request("POST", path`/entities/${a.entityType}/${a.entityId}/comments`, {
        params: given({
          isAddToFollowers: a.isAddToFollowers,
          notify: a.notify,
          notifyAuthor: a.notifyAuthor,
          expand: a.expand,
        }),
        body: given({
          text: a.text,
          attachmentIds: a.attachmentIds,
          summonees: a.summonees,
          maillistSummonees: a.maillistSummonees,
        }),
      }),
  }),

  tool({
    name: "tracker_entity_patch_comment",
    description: `Edit an entity comment.

PATCH /v3/entities/{entityType}/{entityId}/comments/{commentId}
https://yandex.ru/support/tracker/en/api/entities/comments/patch-comment.md

The page's summary line omits the comment ID, but its Resource table and its
request example both address one comment, so the ID is part of the path.`,
    input: {
      entityType: z.string().min(1).describe("Entity type: project, portfolio, goal."),
      entityId: z.string().min(1).describe("Entity ID."),
      commentId: z.string().min(1).describe("Comment's unique ID."),
      text: z.string().optional().describe("Text of the comment."),
      attachmentIds: z
        .array(z.unknown())
        .optional()
        .describe("IDs of temporary files that will be added as attachments."),
      summonees: z.array(z.unknown()).optional().describe("IDs or usernames of summoned users."),
      maillistSummonees: z
        .array(z.unknown())
        .optional()
        .describe("List of mailing lists mentioned in the comment."),
      isAddToFollowers: z
        .boolean()
        .optional()
        .describe("Adding a comment author to followers. The default value is `true`."),
      notify: z
        .boolean()
        .optional()
        .describe(
          "Notify the users specified in the Author, Lead, Participants, Customers, and Followers fields. The default value is `true`.",
        ),
      notifyAuthor: z
        .boolean()
        .optional()
        .describe("Notify the author of the changes. The default value is `false`."),
      expand: z
        .string()
        .optional()
        .describe(
          "Additional information to include in the response: `all`, `html` (comment HTML markup), `attachments`, `reactions`.",
        ),
    },
    run: (tracker, a) =>
      tracker.request(
        "PATCH",
        path`/entities/${a.entityType}/${a.entityId}/comments/${a.commentId}`,
        {
          params: given({
            isAddToFollowers: a.isAddToFollowers,
            notify: a.notify,
            notifyAuthor: a.notifyAuthor,
            expand: a.expand,
          }),
          body: given({
            text: a.text,
            attachmentIds: a.attachmentIds,
            summonees: a.summonees,
            maillistSummonees: a.maillistSummonees,
          }),
        },
      ),
  }),

  tool({
    name: "tracker_entity_get_comments",
    description: `Get the list of comments for an entity.

GET /v3/entities/{entityType}/{entityId}/comments
https://yandex.ru/support/tracker/en/api/entities/comments/get-all-comments.md`,
    input: {
      entityType: z.string().min(1).describe("Entity type: project, portfolio, goal."),
      entityId: z
        .string()
        .min(1)
        .describe("Entity ID. You can use the `id` or `shortId` parameter as the ID."),
      expand: z
        .string()
        .optional()
        .describe(
          "Additional information to include in the response: `all`, `html` (comment HTML markup), `attachments`, `reactions`.",
        ),
    },
    run: (tracker, a) =>
      tracker.request("GET", path`/entities/${a.entityType}/${a.entityId}/comments`, {
        params: given({ expand: a.expand }),
      }),
  }),

  tool({
    name: "tracker_entity_get_comments_relative",
    description: `Get entity comments page by page.

GET /v3/entities/{entityType}/{entityId}/comments/_relative
https://yandex.ru/support/tracker/en/api/entities/comments/get-all-comments.md`,
    input: {
      entityType: z.string().min(1).describe("Entity type: project, portfolio, goal."),
      entityId: z
        .string()
        .min(1)
        .describe("Entity ID. You can use the `id` or `shortId` parameter as the ID."),
      perPage: z
        .number()
        .int()
        .optional()
        .describe("Defines the maximum number of comments in a response. The default value is 50."),
      from: z
        .string()
        .optional()
        .describe(
          "ID of the comment after which the list starts to be generated. The comment itself is not included in the list. Not used together with `selected`.",
        ),
      selected: z
        .string()
        .optional()
        .describe(
          "ID of the comment around which the list is generated. Not specified together with the `from` parameter.",
        ),
      newCommentsOnTop: z
        .boolean()
        .optional()
        .describe("Reverses the order of comments in the list. The default value is `false`."),
      direction: z
        .string()
        .optional()
        .describe(
          "Determines the order of comments in the list: `forward` (default), or `backward`, which inverts the `newCommentsOnTop` parameter value.",
        ),
    },
    run: (tracker, a) =>
      tracker.request("GET", path`/entities/${a.entityType}/${a.entityId}/comments/_relative`, {
        params: given({
          perPage: a.perPage,
          from: a.from,
          selected: a.selected,
          newCommentsOnTop: a.newCommentsOnTop,
          direction: a.direction,
        }),
      }),
  }),

  tool({
    name: "tracker_entity_get_comment",
    description: `Get one entity comment.

GET /v3/entities/{entityType}/{entityId}/comments/{commentId}
https://yandex.ru/support/tracker/en/api/entities/comments/get-comment.md`,
    input: {
      entityType: z.string().min(1).describe("Entity type: project, portfolio, goal."),
      entityId: z.string().min(1).describe("Entity ID."),
      commentId: z.string().min(1).describe("Comment's unique ID."),
      expand: z
        .string()
        .optional()
        .describe(
          "Additional information to include in the response: `all`, `html` (comment HTML markup), `attachments`, `reactions`.",
        ),
    },
    run: (tracker, a) =>
      tracker.request(
        "GET",
        path`/entities/${a.entityType}/${a.entityId}/comments/${a.commentId}`,
        {
          params: given({ expand: a.expand }),
        },
      ),
  }),

  tool({
    name: "tracker_entity_delete_comment",
    description: `Delete an entity comment.

DELETE /v3/entities/{entityType}/{entityId}/comments/{commentId}
https://yandex.ru/support/tracker/en/api/entities/comments/delete-comment.md`,
    input: {
      entityType: z.string().min(1).describe("Entity type: project, portfolio, goal."),
      entityId: z.string().min(1).describe("Entity ID."),
      commentId: z.string().min(1).describe("Comment's unique ID."),
      notify: z
        .boolean()
        .optional()
        .describe(
          "Notify the users specified in the Author, Lead, Participants, Customers, and Followers fields. The default value is `true`.",
        ),
      notifyAuthor: z
        .boolean()
        .optional()
        .describe("Notify the author of the changes. The default value is `false`."),
    },
    run: (tracker, a) =>
      tracker.request(
        "DELETE",
        path`/entities/${a.entityType}/${a.entityId}/comments/${a.commentId}`,
        {
          params: given({ notify: a.notify, notifyAuthor: a.notifyAuthor }),
        },
      ),
  }),

  tool({
    name: "tracker_entity_add_checklist_item",
    description: `Create a checklist in a project or portfolio, or add an item to it.

POST /v3/entities/{entityType}/{entityId}/checklistItems
https://yandex.ru/support/tracker/en/api/entities/checklists/add-checklist.md

New items are added to the end of the list.`,
    input: {
      entityType: z.string().min(1).describe("Entity type: project, portfolio."),
      entityId: z
        .string()
        .min(1)
        .describe("Entity ID. You can use the `id` or `shortId` parameter as the ID."),
      text: z.string().min(1).describe("Text of the checklist item."),
      checked: z
        .boolean()
        .optional()
        .describe("Item completion flag: `true` marks the item as completed, `false` doesn't."),
      assignee: z
        .string()
        .optional()
        .describe("ID or username of the user that the checklist item is assigned to."),
      deadline: z
        .record(z.string(), z.unknown())
        .optional()
        .describe(
          "Deadline for the checklist item: date (`YYYY-MM-DDThh:mm:ss.sss±hhmm`) and deadlineType.",
        ),
      notify: z
        .boolean()
        .optional()
        .describe(
          "Notify the users specified in the Author, Responsible, Participants, Customers, and Followers fields. The default value is `true`.",
        ),
      notifyAuthor: z
        .boolean()
        .optional()
        .describe("Notify the author of the changes. The default value is `false`."),
      fields: z
        .string()
        .optional()
        .describe("Additional entity fields to include in the response."),
      expand: z
        .string()
        .optional()
        .describe(
          "Additional information to include in the response: `attachments` (attached files).",
        ),
    },
    run: (tracker, a) =>
      tracker.request("POST", path`/entities/${a.entityType}/${a.entityId}/checklistItems`, {
        params: given({
          notify: a.notify,
          notifyAuthor: a.notifyAuthor,
          fields: a.fields,
          expand: a.expand,
        }),
        body: given({
          text: a.text,
          checked: a.checked,
          assignee: a.assignee,
          deadline: a.deadline,
        }),
      }),
  }),

  tool({
    name: "tracker_entity_patch_checklist",
    description: `Edit checklist items in a project or portfolio.

PATCH /v3/entities/{entityType}/{entityId}/checklistItems
https://yandex.ru/support/tracker/en/api/entities/checklists/patch-checklist.md

The number of items cannot change here — add or delete items with the
dedicated requests instead.`,
    input: {
      entityType: z.string().min(1).describe("Entity type: project, portfolio."),
      entityId: z
        .string()
        .min(1)
        .describe("Entity ID. You can use the `id` or `shortId` parameter as the ID."),
      checklistItems: z
        .array(z.unknown())
        .describe(
          "Checklist items to edit; each object takes id and text (both required) plus checked, assignee and deadline. An additional parameter left out is reset to its default value, so repeat the values you did not change.",
        ),
      notify: z
        .boolean()
        .optional()
        .describe(
          "Notify the users specified in the Author, Responsible, Participants, Customers, and Followers fields. The default value is `true`.",
        ),
      notifyAuthor: z
        .boolean()
        .optional()
        .describe("Notify the author of the changes. The default value is `false`."),
      fields: z
        .string()
        .optional()
        .describe("Additional entity fields to include in the response."),
      expand: z
        .string()
        .optional()
        .describe(
          "Additional information to include in the response: `attachments` (attached files).",
        ),
    },
    run: (tracker, a) =>
      tracker.request("PATCH", path`/entities/${a.entityType}/${a.entityId}/checklistItems`, {
        params: given({
          notify: a.notify,
          notifyAuthor: a.notifyAuthor,
          fields: a.fields,
          expand: a.expand,
        }),
        body: a.checklistItems,
      }),
  }),

  tool({
    name: "tracker_entity_patch_checklist_item",
    description: `Update information about a specific checklist item in a project or portfolio.

PATCH /v3/entities/{entityType}/{entityId}/checklistItems/{checklistItemId}
https://yandex.ru/support/tracker/en/api/entities/checklists/patch-checklist-item.md`,
    input: {
      entityType: z.string().min(1).describe("Entity type: project, portfolio."),
      entityId: z
        .string()
        .min(1)
        .describe("Entity ID. You can use the `id` or `shortId` parameter as the ID."),
      checklistItemId: z.string().min(1).describe("Checklist item ID."),
      text: z.string().optional().describe("Text of the checklist item."),
      checked: z
        .boolean()
        .optional()
        .describe("Item completion flag: `true` marks the item as completed, `false` doesn't."),
      assignee: z
        .string()
        .optional()
        .describe("ID or username of the user that the checklist item is assigned to."),
      deadline: z
        .record(z.string(), z.unknown())
        .optional()
        .describe(
          "Deadline for the checklist item: date (`YYYY-MM-DDThh:mm:ss.sss±hhmm`) and deadlineType.",
        ),
      notify: z
        .boolean()
        .optional()
        .describe(
          "Notify the users specified in the Author, Responsible, Participants, Customers, and Followers fields. The default value is `true`.",
        ),
      notifyAuthor: z
        .boolean()
        .optional()
        .describe("Notify the author of the changes. The default value is `false`."),
      fields: z
        .string()
        .optional()
        .describe("Additional entity fields to include in the response."),
      expand: z
        .string()
        .optional()
        .describe(
          "Additional information to include in the response: `attachments` (attached files).",
        ),
    },
    run: (tracker, a) =>
      tracker.request(
        "PATCH",
        path`/entities/${a.entityType}/${a.entityId}/checklistItems/${a.checklistItemId}`,
        {
          params: given({
            notify: a.notify,
            notifyAuthor: a.notifyAuthor,
            fields: a.fields,
            expand: a.expand,
          }),
          body: given({
            text: a.text,
            checked: a.checked,
            assignee: a.assignee,
            deadline: a.deadline,
          }),
        },
      ),
  }),

  tool({
    name: "tracker_entity_move_checklist_item",
    description: `Move a checklist item across projects and portfolios.

POST /v3/entities/{entityType}/{entityId}/checklistItems/{checklistItemId}/_move
https://yandex.ru/support/tracker/en/api/entities/checklists/move-checklist-item.md`,
    effect: "modify",
    input: {
      entityType: z.string().min(1).describe("Entity type: project, portfolio."),
      entityId: z
        .string()
        .min(1)
        .describe("Entity ID. You can use the `id` or `shortId` parameter as the ID."),
      checklistItemId: z.string().min(1).describe("Checklist item ID."),
      before: z
        .string()
        .min(1)
        .describe("ID of the checklist item to be preceded by the inserted one."),
      notify: z
        .boolean()
        .optional()
        .describe(
          "Notify the users specified in the Author, Responsible, Participants, Customers, and Followers fields. The default value is `true`.",
        ),
      notifyAuthor: z
        .boolean()
        .optional()
        .describe("Notify the author of the changes. The default value is `false`."),
      fields: z
        .string()
        .optional()
        .describe("Additional entity fields to include in the response."),
      expand: z
        .string()
        .optional()
        .describe(
          "Additional information to include in the response: `attachments` (attached files).",
        ),
    },
    run: (tracker, a) =>
      tracker.request(
        "POST",
        path`/entities/${a.entityType}/${a.entityId}/checklistItems/${a.checklistItemId}/_move`,
        {
          params: given({
            notify: a.notify,
            notifyAuthor: a.notifyAuthor,
            fields: a.fields,
            expand: a.expand,
          }),
          body: given({ before: a.before }),
        },
      ),
  }),

  tool({
    name: "tracker_entity_delete_checklist",
    description: `Delete all checklist items from a project or portfolio.

DELETE /v3/entities/{entityType}/{entityId}/checklistItems
https://yandex.ru/support/tracker/en/api/entities/checklists/delete-checklist.md

The action cannot be undone.`,
    input: {
      entityType: z.string().min(1).describe("Entity type: project, portfolio."),
      entityId: z
        .string()
        .min(1)
        .describe("Entity ID. You can use the `id` or `shortId` parameter as the ID."),
      notify: z
        .boolean()
        .optional()
        .describe(
          "Notify the users specified in the Author, Responsible, Participants, Customers, and Followers fields. The default value is `true`.",
        ),
      notifyAuthor: z
        .boolean()
        .optional()
        .describe("Notify the author of the changes. The default value is `false`."),
      fields: z
        .string()
        .optional()
        .describe("Additional entity fields to include in the response."),
      expand: z
        .string()
        .optional()
        .describe(
          "Additional information to include in the response: `attachments` (attached files).",
        ),
    },
    run: (tracker, a) =>
      tracker.request("DELETE", path`/entities/${a.entityType}/${a.entityId}/checklistItems`, {
        params: given({
          notify: a.notify,
          notifyAuthor: a.notifyAuthor,
          fields: a.fields,
          expand: a.expand,
        }),
      }),
  }),

  tool({
    name: "tracker_entity_delete_checklist_item",
    description: `Delete an item from a project or portfolio's checklist.

DELETE /v3/entities/{entityType}/{entityId}/checklistItems/{checklistItemId}
https://yandex.ru/support/tracker/en/api/entities/checklists/delete-checklist-item.md

The action cannot be undone.`,
    input: {
      entityType: z.string().min(1).describe("Entity type: project, portfolio."),
      entityId: z
        .string()
        .min(1)
        .describe("Entity ID. You can use the `id` or `shortId` parameter as the ID."),
      checklistItemId: z.string().min(1).describe("Checklist item ID."),
      notify: z
        .boolean()
        .optional()
        .describe(
          "Notify the users specified in the Author, Responsible, Participants, Customers, and Followers fields. The default value is `true`.",
        ),
      notifyAuthor: z
        .boolean()
        .optional()
        .describe("Notify the author of the changes. The default value is `false`."),
      fields: z
        .string()
        .optional()
        .describe("Additional entity fields to include in the response."),
      expand: z
        .string()
        .optional()
        .describe(
          "Additional information to include in the response: `attachments` (attached files).",
        ),
    },
    run: (tracker, a) =>
      tracker.request(
        "DELETE",
        path`/entities/${a.entityType}/${a.entityId}/checklistItems/${a.checklistItemId}`,
        {
          params: given({
            notify: a.notify,
            notifyAuthor: a.notifyAuthor,
            fields: a.fields,
            expand: a.expand,
          }),
        },
      ),
  }),

  tool({
    name: "tracker_entity_get_attachments",
    description: `Get the list of files attached to an entity.

GET /v3/entities/{entityType}/{entityId}/attachments
https://yandex.ru/support/tracker/en/api/entities/attachments/get-all-attachments.md`,
    input: {
      entityType: z.string().min(1).describe("Entity type: project, portfolio, goal."),
      entityId: z
        .string()
        .min(1)
        .describe("Entity ID. You can use the `id` or `shortId` parameter as the ID."),
    },
    run: (tracker, a) =>
      tracker.request("GET", path`/entities/${a.entityType}/${a.entityId}/attachments`),
  }),

  tool({
    name: "tracker_entity_get_attachment",
    description: `Get information about a file attached to an entity.

GET /v3/entities/{entityType}/{entityId}/attachments/{fileId}
https://yandex.ru/support/tracker/en/api/entities/attachments/get-attachment.md

Returns the attachment's metadata, not its contents.`,
    input: {
      entityType: z.string().min(1).describe("Entity type: project, portfolio, goal."),
      entityId: z.string().min(1).describe("Entity ID."),
      fileId: z.string().min(1).describe("File's unique ID."),
    },
    run: (tracker, a) =>
      tracker.request("GET", path`/entities/${a.entityType}/${a.entityId}/attachments/${a.fileId}`),
  }),

  tool({
    name: "tracker_entity_add_attachment",
    description: `Attach an already-uploaded temporary file to an entity.

POST /v3/entities/{entityType}/{entityId}/attachments/{fileId}
https://yandex.ru/support/tracker/en/api/entities/attachments/add-attachment.md

This sends no file contents: upload the file first with POST /v3/attachments/
(tracker_post_temp_attachment) and pass the temporary file ID it returns as
fileId.`,
    input: {
      entityType: z.string().min(1).describe("Entity type: project, portfolio, goal."),
      entityId: z.string().min(1).describe("Entity ID."),
      fileId: z.string().min(1).describe("ID of a temporary file preloaded into Tracker."),
      notify: z
        .boolean()
        .optional()
        .describe(
          "Notify the users specified in the Author, Lead, Participants, Customers, and Followers fields. The default value is `true`.",
        ),
      notifyAuthor: z
        .boolean()
        .optional()
        .describe("Notify the author of the changes. The default value is `false`."),
      fields: z
        .string()
        .optional()
        .describe("Additional entity fields to include in the response."),
      expand: z
        .string()
        .optional()
        .describe(
          "Additional information to include in the response: `all`, `attachments` (attached files).",
        ),
    },
    run: (tracker, a) =>
      tracker.request(
        "POST",
        path`/entities/${a.entityType}/${a.entityId}/attachments/${a.fileId}`,
        {
          params: given({
            notify: a.notify,
            notifyAuthor: a.notifyAuthor,
            fields: a.fields,
            expand: a.expand,
          }),
        },
      ),
  }),

  tool({
    name: "tracker_entity_delete_attachment",
    description: `Delete a file attached to an entity.

DELETE /v3/entities/{entityType}/{entityId}/attachments/{fileId}
https://yandex.ru/support/tracker/en/api/entities/attachments/delete-attachment.md`,
    input: {
      entityType: z.string().min(1).describe("Entity type: project, portfolio, goal."),
      entityId: z.string().min(1).describe("Entity ID."),
      fileId: z.string().min(1).describe("File's unique ID."),
    },
    run: (tracker, a) =>
      tracker.request(
        "DELETE",
        path`/entities/${a.entityType}/${a.entityId}/attachments/${a.fileId}`,
      ),
  }),

  tool({
    name: "tracker_entity_add_links",
    description: `Create a link between the entity in the path and another entity.

POST /v3/entities/{entityType}/{entityId}/links
https://yandex.ru/support/tracker/en/api/entities/links/add-links.md

To add a parent entity for a project or portfolio, edit the parentEntity
field with tracker_update_entity instead.`,
    input: {
      entityType: z.string().min(1).describe("Entity type: project, portfolio, goal."),
      entityId: z
        .string()
        .min(1)
        .describe("Entity ID. You can use the `id` or `shortId` parameter as the ID."),
      relationship: z
        .string()
        .min(1)
        .describe(
          "Link type. For projects and portfolios: `depends on` (the current entity depends on the linked one), `is dependent by` (the current entity blocks the linked one), `works towards` (project link to a goal). For goals: `parent entity` (parent goal), `child entity` (subgoal), `depends on`, `is dependent by`, `is supported by` (link to a project).",
        ),
      entity: z.string().min(1).describe("ID of the linked entity."),
    },
    run: (tracker, a) =>
      tracker.request("POST", path`/entities/${a.entityType}/${a.entityId}/links`, {
        body: given({ relationship: a.relationship, entity: a.entity }),
      }),
  }),

  tool({
    name: "tracker_entity_get_links",
    description: `Get information about an entity's links with other entities.

GET /v3/entities/{entityType}/{entityId}/links
https://yandex.ru/support/tracker/en/api/entities/links/get-links.md`,
    input: {
      entityType: z.string().min(1).describe("Entity type: project, portfolio, goal."),
      entityId: z
        .string()
        .min(1)
        .describe("Entity ID. You can use the `id` or `shortId` parameter as the ID."),
      fields: z
        .string()
        .optional()
        .describe("Fields of the linked entities to include in the response."),
    },
    run: (tracker, a) =>
      tracker.request("GET", path`/entities/${a.entityType}/${a.entityId}/links`, {
        params: given({ fields: a.fields }),
      }),
  }),

  tool({
    name: "tracker_entity_delete_link",
    description: `Delete the link between the entity in the path and the entity in \`right\`.

DELETE /v3/entities/{entityType}/{entityId}/links
https://yandex.ru/support/tracker/en/api/entities/links/delete-link.md`,
    input: {
      entityType: z.string().min(1).describe("Entity type: project, portfolio, goal."),
      entityId: z
        .string()
        .min(1)
        .describe("Entity ID. You can use the `id` or `shortId` parameter as the ID."),
      right: z.string().min(1).describe("ID of the entity whose link is deleted."),
    },
    run: (tracker, a) =>
      tracker.request("DELETE", path`/entities/${a.entityType}/${a.entityId}/links`, {
        params: given({ right: a.right }),
      }),
  }),

  tool({
    name: "tracker_entity_get_permissions",
    description: `Get an entity's permissions in the \`acl\` object format.

GET /v3/entities/{entityType}/{entityId}/permissions
https://yandex.ru/support/tracker/en/api/entities/get-access.md

Unlike tracker_entity_get_extended_permissions, this does not return
permissionSources, the parent entity the current one inherits access from.`,
    input: {
      entityType: z.string().min(1).describe("Entity type: project, portfolio, goal."),
      entityId: z
        .string()
        .min(1)
        .describe("Entity ID. You can use the `id` or `shortId` parameter as the ID."),
    },
    run: (tracker, a) =>
      tracker.request("GET", path`/entities/${a.entityType}/${a.entityId}/permissions`),
  }),

  tool({
    name: "tracker_entity_get_extended_permissions",
    description: `Get an entity's access settings, including inherited ones.

GET /v3/entities/{entityType}/{entityId}/extendedPermissions
https://yandex.ru/support/tracker/en/api/entities/get-access.md

Adds permissionSources — the parent entity the current one inherits access
settings from — next to \`acl\` as a field of its own.`,
    input: {
      entityType: z.string().min(1).describe("Entity type: project, portfolio, goal."),
      entityId: z
        .string()
        .min(1)
        .describe("Entity ID. You can use the `id` or `shortId` parameter as the ID."),
    },
    run: (tracker, a) =>
      tracker.request("GET", path`/entities/${a.entityType}/${a.entityId}/extendedPermissions`),
  }),

  tool({
    name: "tracker_entity_patch_permissions",
    description: `Grant or revoke access to an entity.

PATCH /v3/entities/{entityType}/{entityId}/permissions
https://yandex.ru/support/tracker/en/api/entities/patch-access.md

The body is the \`acl\` object itself, so permissionSources cannot be set here —
use tracker_entity_patch_extended_permissions for that. Access inheritance
must be off before permissions can be changed.`,
    input: {
      entityType: z.string().min(1).describe("Entity type: project, portfolio, goal."),
      entityId: z
        .string()
        .min(1)
        .describe("Entity ID. You can use the `id` or `shortId` parameter as the ID."),
      grant: z
        .record(z.string(), z.unknown())
        .optional()
        .describe(
          "Permissions to grant, keyed by access type — READ, WRITE or GRANT — each an object with users (IDs or usernames), groups (group IDs) and roles (AUTHOR, OWNER, CLIENT, FOLLOWER, MEMBER).",
        ),
      revoke: z
        .record(z.string(), z.unknown())
        .optional()
        .describe(
          "Permissions to revoke, keyed by access type — READ, WRITE or GRANT — each an object with users (IDs or usernames), groups (group IDs) and roles (AUTHOR, OWNER, CLIENT, FOLLOWER, MEMBER).",
        ),
    },
    run: (tracker, a) =>
      tracker.request("PATCH", path`/entities/${a.entityType}/${a.entityId}/permissions`, {
        body: given({ grant: a.grant, revoke: a.revoke }),
      }),
  }),

  tool({
    name: "tracker_entity_patch_extended_permissions",
    description: `Grant or revoke access to an entity, including access inheritance.

PATCH /v3/entities/{entityType}/{entityId}/extendedPermissions
https://yandex.ru/support/tracker/en/api/entities/patch-access.md

While permissionSources is non-empty, acl is rejected and the entity's
teamAccess parameter is ignored — disable inheritance first.`,
    input: {
      entityType: z.string().min(1).describe("Entity type: project, portfolio, goal."),
      entityId: z
        .string()
        .min(1)
        .describe("Entity ID. You can use the `id` or `shortId` parameter as the ID."),
      permissionSources: z
        .union([z.string(), z.array(z.unknown())])
        .optional()
        .describe(
          "ID of the parent entity the current one inherits access settings from: the main portfolio for projects and portfolios, or the parent goal for goals. Pass an empty array to disable access inheritance.",
        ),
      acl: z
        .record(z.string(), z.unknown())
        .optional()
        .describe(
          "Permissions to change: grant and revoke objects, each keyed by access type — READ, WRITE or GRANT — with users (IDs or usernames), groups (group IDs) and roles (AUTHOR, OWNER, CLIENT, FOLLOWER, MEMBER).",
        ),
    },
    run: (tracker, a) =>
      tracker.request("PATCH", path`/entities/${a.entityType}/${a.entityId}/extendedPermissions`, {
        body: given({ permissionSources: a.permissionSources, acl: a.acl }),
      }),
  }),
];
