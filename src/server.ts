/** The MCP surface: one server, built from the tool registry. */

import { McpServer } from "@modelcontextprotocol/server";
import { z } from "zod";
import { Tracker } from "./client.ts";
import { registerResources } from "./resources.ts";
import { allTools } from "./tools/index.ts";

export const SERVER_NAME = "mcp-yandex-tracker";
export const SERVER_VERSION = "1.0.0";

let cached: Tracker | undefined;

/**
 * One client per process, built lazily.
 *
 * The environment is read on first use rather than at startup, so a missing
 * token surfaces as a clean tool error instead of killing the process before the
 * host has finished its handshake. The undici connection pool behind `fetch` is
 * shared across every call either way.
 */
export function getTracker(): Tracker {
  cached ??= new Tracker();
  return cached;
}

/**
 * Build a server with every tool and resource registered.
 *
 * `serveStdio` calls this as a factory — the SDK pins one instance per protocol
 * era per connection — so registration has to happen here rather than as an
 * import side effect. Tests pass their own `tracker` to swap in a fake.
 */
export function buildServer(tracker: () => Tracker = getTracker): McpServer {
  const server = new McpServer({ name: SERVER_NAME, version: SERVER_VERSION });

  for (const def of allTools) {
    server.registerTool(
      def.name,
      { description: def.description, inputSchema: z.object(def.input) },
      async (args) => ({
        // One compact JSON text block and no outputSchema: that keeps responses
        // token-lean (no duplicating structuredContent) and Cyrillic intact.
        // A thrown TrackerApiError / TrackerConfigError / ZodError is turned
        // into an `isError: true` result by the SDK, message and all.
        content: [
          { type: "text" as const, text: JSON.stringify(await def.run(tracker(), args as never)) },
        ],
      }),
    );
  }

  registerResources(server, tracker);
  return server;
}
