/** Importing from another tracker — https://yandex.ru/support/tracker/en/api/import/import-ticket.md */

import { z } from "zod";
import { given, path } from "../client.ts";
import { tool } from "../tool.ts";

const issueId = z.string().min(1).describe("Key of the issue being imported into.");

const createdAt = z
  .string()
  .describe(
    "Creation date and time in `YYYY-MM-DDThh:mm:ss.sss±hhmm` format, no later than the current time.",
  );

const createdBy = z
  .union([z.string(), z.number().int()])
  .describe("Username or ID of the user who created the record.");

const updatedAt = z
  .string()
  .describe(
    "Date and time of the last update in `YYYY-MM-DDThh:mm:ss.sss±hhmm` format. Only used together with `updatedBy`.",
  );

const updatedBy = z
  .union([z.string(), z.number().int()])
  .describe(
    "Username or ID of the user who updated the record last. Only used together with `updatedAt`.",
  );

/**
 * Every endpoint here writes history rather than creating something new: the
 * imported issue, comment, link or worklog carries the author and the timestamps
 * of the system it came from. All of them require Administrator rights.
 */
export const importTools = [
  tool({
    name: "tracker_import_issue",
    description: `Import an issue from another issue tracker, keeping its author and dates.

POST /v3/issues/_import
https://yandex.ru/support/tracker/en/api/import/import-ticket.md

Requires Administrator rights in the organization. Unlike tracker_create_issue
this takes the original timestamps and author, and can set the issue key.`,
    input: {
      queue: z.string().min(1).describe("Key of the queue to import the issue into."),
      summary: z.string().min(1).describe("Issue name, at most 255 characters."),
      createdAt,
      createdBy,
      key: z
        .string()
        .optional()
        .describe(
          "Issue key, which must belong to `queue`. Assigned automatically when omitted. Numbering is incremental, so a high number leaves the values below it unused.",
        ),
      updatedAt: updatedAt.optional(),
      updatedBy: updatedBy.optional(),
      resolvedAt: z
        .string()
        .optional()
        .describe(
          "Date and time the resolution was set, in `YYYY-MM-DDThh:mm:ss.sss±hhmm` format. Only used together with `resolution` and `resolvedBy`.",
        ),
      resolvedBy: z
        .union([z.string(), z.number().int()])
        .optional()
        .describe(
          "Username or ID of the user who set the resolution. Only used together with `resolution` and `resolvedAt`.",
        ),
      status: z
        .number()
        .int()
        .optional()
        .describe(
          "Issue status ID, which must exist in the queue workflow for this issue type. Defaults to the initial status.",
        ),
      resolution: z
        .number()
        .int()
        .optional()
        .describe("Issue resolution ID. Only used together with `resolvedBy` and `resolvedAt`."),
      type: z
        .number()
        .int()
        .optional()
        .describe("Issue type ID, which must exist in the queue. Defaults to the queue's default."),
      priority: z
        .number()
        .int()
        .optional()
        .describe("Priority ID. Defaults to the queue's default priority."),
      description: z.string().optional().describe("Issue description, at most 512,000 characters."),
      deadline: z.string().optional().describe("Deadline in the YYYY-MM-DD format."),
      start: z.string().optional().describe("Start date in the YYYY-MM-DD format."),
      end: z.string().optional().describe("End date in the YYYY-MM-DD format."),
      assignee: z
        .union([z.string(), z.number().int()])
        .optional()
        .describe("Username or ID of the assignee."),
      affectedVersions: z
        .array(z.unknown())
        .optional()
        .describe(
          "IDs of the versions in the Affected version field. They must exist in the queue.",
        ),
      fixVersions: z
        .array(z.unknown())
        .optional()
        .describe("IDs of the versions in the Fix version field. They must exist in the queue."),
      components: z
        .array(z.unknown())
        .optional()
        .describe("IDs of the components that apply to the issue. They must exist in the queue."),
      tags: z.array(z.unknown()).optional().describe("Issue tags."),
      sprint: z.array(z.unknown()).optional().describe("IDs of the sprints the issue is part of."),
      followers: z
        .array(z.unknown())
        .optional()
        .describe("IDs or usernames of the issue followers."),
      access: z
        .array(z.unknown())
        .optional()
        .describe("IDs or usernames of the users in the Access field."),
      followingMaillists: z
        .array(z.unknown())
        .optional()
        .describe("IDs of the mailing lists subscribed to the issue."),
      unique: z.string().optional().describe("Unique issue ID; any value of your own."),
      originalEstimation: z
        .number()
        .int()
        .optional()
        .describe("Original estimate in milliseconds."),
      estimation: z.number().int().optional().describe("Estimate in milliseconds."),
      spent: z.number().int().optional().describe("Time spent in milliseconds."),
      storyPoints: z.number().optional().describe("Issue estimate in story points."),
      votedBy: z
        .array(z.unknown())
        .optional()
        .describe("IDs or usernames of the users who voted for the issue."),
      favoritedBy: z
        .array(z.unknown())
        .optional()
        .describe("IDs or usernames of the users who added the issue to favorites."),
      fields: z
        .record(z.string(), z.unknown())
        .optional()
        .describe(
          "Custom global fields and queue local fields, keyed by field ID. Merged into the request body last.",
        ),
    },
    run: (tracker, a) =>
      tracker.request("POST", "/issues/_import", {
        body: {
          ...given({
            queue: a.queue,
            summary: a.summary,
            createdAt: a.createdAt,
            createdBy: a.createdBy,
            key: a.key,
            updatedAt: a.updatedAt,
            updatedBy: a.updatedBy,
            resolvedAt: a.resolvedAt,
            resolvedBy: a.resolvedBy,
            status: a.status,
            resolution: a.resolution,
            type: a.type,
            priority: a.priority,
            description: a.description,
            deadline: a.deadline,
            start: a.start,
            end: a.end,
            assignee: a.assignee,
            affectedVersions: a.affectedVersions,
            fixVersions: a.fixVersions,
            components: a.components,
            tags: a.tags,
            sprint: a.sprint,
            followers: a.followers,
            access: a.access,
            followingMaillists: a.followingMaillists,
            unique: a.unique,
            originalEstimation: a.originalEstimation,
            estimation: a.estimation,
            spent: a.spent,
            storyPoints: a.storyPoints,
            votedBy: a.votedBy,
            favoritedBy: a.favoritedBy,
          }),
          ...a.fields,
        },
      }),
  }),

  tool({
    name: "tracker_import_comment",
    description: `Import a comment into an issue, keeping its author and dates.

POST /v3/issues/{issueId}/comments/_import
https://yandex.ru/support/tracker/en/api/import/import-comments.md

Requires Administrator rights in the organization.`,
    input: {
      issueId,
      text: z.string().min(1).describe("Text of the comment, at most 512,000 characters."),
      createdAt,
      createdBy,
      updatedAt: updatedAt.optional(),
      updatedBy: updatedBy.optional(),
    },
    run: (tracker, a) =>
      tracker.request("POST", path`/issues/${a.issueId}/comments/_import`, {
        body: given({
          text: a.text,
          createdAt: a.createdAt,
          createdBy: a.createdBy,
          updatedAt: a.updatedAt,
          updatedBy: a.updatedBy,
        }),
      }),
  }),

  tool({
    name: "tracker_import_link",
    description: `Import a link to another issue, keeping its author and dates.

POST /v3/issues/{issueId}/links/_import
https://yandex.ru/support/tracker/en/api/import/import-links.md

Requires Administrator rights in the organization.`,
    input: {
      issueId,
      relationship: z
        .string()
        .min(1)
        .describe(
          "Type of the link: `relates`, `is dependent by`, `depends on`, `is subtask for`, `is parent task for`, `duplicates`, `is duplicated by`, `is epic of`, `has epic`, `clone`, `original`.",
        ),
      issue: z.string().min(1).describe("ID or key of the issue being linked."),
      createdAt,
      createdBy,
      updatedAt: updatedAt.optional(),
      updatedBy: updatedBy.optional(),
    },
    run: (tracker, a) =>
      tracker.request("POST", path`/issues/${a.issueId}/links/_import`, {
        body: given({
          relationship: a.relationship,
          issue: a.issue,
          createdAt: a.createdAt,
          createdBy: a.createdBy,
          updatedAt: a.updatedAt,
          updatedBy: a.updatedBy,
        }),
      }),
  }),

  tool({
    name: "tracker_import_worklog",
    description: `Import a record of time spent on an issue, keeping its author and dates.

POST /v3/issues/{issueId}/worklogs/_import
https://yandex.ru/support/tracker/en/api/import/import-worklogs.md

Requires Administrator rights in the organization.`,
    input: {
      issueId,
      duration: z
        .string()
        .min(1)
        .describe(
          "Time spent in ISO 8601 duration format: `P6W` is six weeks, `PT300M` is 300 minutes, `P0Y0M30DT2H10M25S` is 30 days 2 hours 10 minutes 25 seconds.",
        ),
      start: z
        .string()
        .describe(
          "Date and time work on the issue started, in `YYYY-MM-DDThh:mm:ss.sss±hhmm` format.",
        ),
      createdAt,
      createdBy,
      comment: z.string().optional().describe("Comment on the record of time spent."),
    },
    run: (tracker, a) =>
      tracker.request("POST", path`/issues/${a.issueId}/worklogs/_import`, {
        body: given({
          duration: a.duration,
          start: a.start,
          createdAt: a.createdAt,
          createdBy: a.createdBy,
          comment: a.comment,
        }),
      }),
  }),

  tool({
    name: "tracker_import_attachment",
    description: `Import a file attached to an issue, keeping who attached it and when.

POST /v3/issues/{issueId}/attachments/_import
https://yandex.ru/support/tracker/en/api/import/import-attachments.md

Requires Administrator rights in the organization. Takes the path of a local
file, which it sends as the documented \`file_data\` part; up to 1024 Mbit.`,
    input: {
      issueId,
      filePath: z.string().min(1).describe("Path of the local file to upload."),
      filename: z.string().min(1).describe("File name in Tracker, at most 255 characters."),
      createdAt: z
        .string()
        .describe(
          "Date and time the file was attached, in `YYYY-MM-DDThh:mm:ss.sss±hhmm` format, within the issue's lifetime.",
        ),
      createdBy,
    },
    run: (tracker, a) =>
      tracker.upload(path`/issues/${a.issueId}/attachments/_import`, a.filePath, {
        part: "file_data",
        params: { filename: a.filename, createdAt: a.createdAt, createdBy: a.createdBy },
      }),
  }),

  tool({
    name: "tracker_import_comment_attachment",
    description: `Import a file attached to a comment, keeping who attached it and when.

POST /v3/issues/{issueId}/comments/{commentId}/attachments/_import
https://yandex.ru/support/tracker/en/api/import/import-attachments.md

Requires Administrator rights in the organization. Takes the path of a local
file, which it sends as the documented \`file_data\` part; up to 1024 Mbit.`,
    input: {
      issueId,
      commentId: z.string().min(1).describe("ID of the comment to attach the file to."),
      filePath: z.string().min(1).describe("Path of the local file to upload."),
      filename: z.string().min(1).describe("File name in Tracker, at most 255 characters."),
      createdAt: z
        .string()
        .describe(
          "Date and time the file was attached, in `YYYY-MM-DDThh:mm:ss.sss±hhmm` format, within the issue's lifetime.",
        ),
      createdBy,
    },
    run: (tracker, a) =>
      tracker.upload(
        path`/issues/${a.issueId}/comments/${a.commentId}/attachments/_import`,
        a.filePath,
        {
          part: "file_data",
          params: { filename: a.filename, createdAt: a.createdAt, createdBy: a.createdBy },
        },
      ),
  }),
];
