#!/usr/bin/env node
import { serveStdio } from "@modelcontextprotocol/server/stdio";
import { buildServer } from "./server.ts";

// stdout is the JSON-RPC channel; everything diagnostic goes to stderr.
serveStdio(() => buildServer(), {
  onerror: (error) => console.error("yandex-tracker-mcp:", error),
});
