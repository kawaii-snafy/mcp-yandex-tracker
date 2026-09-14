/**
 * Read-only context the user can @-mention in a host.
 *
 * Resources are a *user*-facing surface (pulled into a prompt via @-mention and
 * attached as context), not something the agent reads autonomously mid-task —
 * the tools remain the agent's path to the same data. These add a natural way to
 * drop an issue snapshot or a reference dictionary into the conversation.
 */

import { ResourceTemplate, type McpServer } from "@modelcontextprotocol/server";
import type { Tracker } from "./client.ts";

const DICTIONARIES = [
  ["queues", "tracker://queues", "/queues/", "The Yandex Tracker queue list."],
  ["statuses", "tracker://statuses", "/statuses", "The global Yandex Tracker status dictionary."],
  [
    "priorities",
    "tracker://priorities",
    "/priorities",
    "The global Yandex Tracker priority dictionary.",
  ],
  [
    "issue-types",
    "tracker://issue-types",
    "/issuetypes",
    "The global Yandex Tracker issue-type dictionary.",
  ],
  ["fields", "tracker://fields", "/fields", "Yandex Tracker fields, including custom fields."],
] as const;

export function registerResources(server: McpServer, tracker: () => Tracker): void {
  server.registerResource(
    "issue",
    new ResourceTemplate("tracker://issue/{key}", { list: undefined }),
    {
      description: "A single Yandex Tracker issue by key (e.g. tracker://issue/TEST-123).",
      mimeType: "application/json",
    },
    async (uri, { key }) => ({
      contents: [
        {
          uri: uri.href,
          mimeType: "application/json",
          text: JSON.stringify(await tracker().request("GET", `/issues/${String(key)}`)),
        },
      ],
    }),
  );

  for (const [name, uri, path, description] of DICTIONARIES) {
    server.registerResource(name, uri, { description, mimeType: "application/json" }, async () => ({
      contents: [
        {
          uri,
          mimeType: "application/json",
          text: JSON.stringify(await tracker().request("GET", path)),
        },
      ],
    }));
  }
}
