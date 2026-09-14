/** The older projects API — https://yandex.ru/support/tracker/en/api/projects/get-projects.md */

import { z } from "zod";
import { given } from "../client.ts";
import { tool } from "../tool.ts";

const projectId = z.union([z.string(), z.number().int()]).describe("Project ID.");

const expand = z
  .string()
  .describe("Additional fields to include in the response. `queues` adds the project's queues.");

const status = z
  .string()
  .describe("Stage of the project: `DRAFT`, `IN_PROGRESS`, `LAUNCHED` or `POSTPONED`.");

const lead = z
  .union([z.string(), z.number().int()])
  .describe("ID or username of the project lead.");

const description = z.string().describe("Project description. Not shown in the Tracker interface.");

const startDate = z.string().describe("Project start date in the YYYY-MM-DD format.");
const endDate = z.string().describe("Project end date in the YYYY-MM-DD format.");

const queues = z
  .union([z.array(z.unknown()), z.string(), z.number().int()])
  .describe("Queues whose issues belong to the project.");

/**
 * Every tool here has a successor in the `entities` API, which handles projects
 * and portfolios through one set of endpoints; each page says so and the
 * descriptions repeat it. They stay because Tracker still documents and serves
 * them, and an organization created before the switch still has these projects.
 */
export const projectTools = [
  tool({
    name: "tracker_get_projects",
    description: `Get every project in the organization.

GET /v3/projects
https://yandex.ru/support/tracker/en/api/projects/get-projects.md

The page recommends tracker_search_entities as the newer way to list projects
and portfolios alike.`,
    input: { expand: expand.optional() },
    run: (tracker, a) =>
      tracker.request("GET", "/projects", { params: given({ expand: a.expand }) }),
  }),

  tool({
    name: "tracker_get_project",
    description: `Get the parameters of one project.

GET /v3/projects/{projectId}
https://yandex.ru/support/tracker/en/api/projects/get-project.md

The page recommends tracker_get_entity as the newer way to read a project.`,
    input: { projectId, expand: expand.optional() },
    run: (tracker, a) =>
      tracker.request("GET", `/projects/${a.projectId}`, { params: given({ expand: a.expand }) }),
  }),

  tool({
    name: "tracker_get_project_queues",
    description: `Get the queues whose issues belong to a project.

GET /v3/projects/{projectId}/queues
https://yandex.ru/support/tracker/en/api/projects/get-project-queues.md`,
    input: {
      projectId,
      expand: z
        .string()
        .optional()
        .describe(
          "Additional fields per queue: `all`, `projects`, `components`, `versions`, `types`, `team`, `workflows`, `fields`, `notification_fields`, `issue_types_config`, `enabled_feaures`, `signature_settings`.",
        ),
    },
    run: (tracker, a) =>
      tracker.request("GET", `/projects/${a.projectId}/queues`, {
        params: given({ expand: a.expand }),
      }),
  }),

  tool({
    name: "tracker_create_project",
    description: `Create a project.

POST /v3/projects/
https://yandex.ru/support/tracker/en/api/projects/create-project.md

The page recommends tracker_create_entity as the newer way to create a project.`,
    input: {
      name: z.string().min(1).describe("Project name."),
      queues,
      description: description.optional(),
      lead: lead.optional(),
      status: status.optional(),
      startDate: startDate.optional(),
      endDate: endDate.optional(),
    },
    run: (tracker, a) =>
      tracker.request("POST", "/projects/", {
        body: given({
          name: a.name,
          queues: a.queues,
          description: a.description,
          lead: a.lead,
          status: a.status,
          startDate: a.startDate,
          endDate: a.endDate,
        }),
      }),
  }),

  tool({
    name: "tracker_update_project",
    description: `Update a project.

PUT /v3/projects/{projectId}
https://yandex.ru/support/tracker/en/api/projects/update-project.md

The only PUT in the API: the body replaces the project, so send every field it
should keep. The page recommends tracker_update_entity as the newer way.`,
    input: {
      projectId,
      version: z
        .union([z.string(), z.number().int()])
        .describe("Current project version. The update applies only to that version."),
      queues,
      name: z.string().min(1).optional().describe("Project name."),
      description: description.optional(),
      lead: lead.optional(),
      status: status.optional(),
      startDate: startDate.optional(),
      endDate: endDate.optional(),
      expand: expand.optional(),
    },
    run: (tracker, a) =>
      tracker.request("PUT", `/projects/${a.projectId}`, {
        params: given({ version: a.version, expand: a.expand }),
        body: given({
          queues: a.queues,
          name: a.name,
          description: a.description,
          lead: a.lead,
          status: a.status,
          startDate: a.startDate,
          endDate: a.endDate,
        }),
      }),
  }),

  tool({
    name: "tracker_delete_project",
    description: `Delete a project.

DELETE /v3/projects/{projectId}
https://yandex.ru/support/tracker/en/api/projects/delete-project.md

The page recommends tracker_delete_entity as the newer way to delete a project.`,
    input: { projectId },
    run: (tracker, a) => tracker.request("DELETE", `/projects/${a.projectId}`),
  }),
];
