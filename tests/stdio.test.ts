import { beforeAll, expect, test } from "bun:test";
import { spawn } from "node:child_process";
import { createInterface } from "node:readline";
import { allTools } from "../src/tools/index.ts";

const CLI = "dist/cli.js";

/**
 * Drive the *built* bundle the way a host does: `node dist/cli.js`, newline
 * delimited JSON-RPC over stdio. This is the only test that proves the shipped
 * artifact works on a machine without Bun — and the one that would catch the
 * bundler falling out with the SDK.
 */
async function talk(requests: unknown[]): Promise<Record<string, unknown>[]> {
  const child = spawn("node", [CLI], { stdio: ["pipe", "pipe", "pipe"] });
  const messages: Record<string, unknown>[] = [];
  const lines = createInterface({ input: child.stdout });

  const done = new Promise<void>((resolve) => {
    lines.on("line", (line) => {
      if (!line.trim()) return;
      messages.push(JSON.parse(line) as Record<string, unknown>);
      // Every request gets one response; notifications get none.
      if (messages.length >= requests.filter(isRequest).length) resolve();
    });
    child.on("exit", () => resolve());
  });

  for (const request of requests) child.stdin.write(`${JSON.stringify(request)}\n`);
  await Promise.race([done, Bun.sleep(15_000)]);
  child.kill();
  return messages;
}

function isRequest(message: unknown): boolean {
  return typeof message === "object" && message !== null && "id" in message;
}

const HANDSHAKE = [
  {
    jsonrpc: "2.0",
    id: 1,
    method: "initialize",
    params: {
      protocolVersion: "2025-11-25",
      capabilities: {},
      clientInfo: { name: "probe", version: "1" },
    },
  },
  { jsonrpc: "2.0", method: "notifications/initialized" },
];

beforeAll(async () => {
  const build = Bun.spawn(["bun", "run", "build"], { stdout: "ignore", stderr: "inherit" });
  expect(await build.exited).toBe(0);
});

test("the built bundle serves the whole tool surface under node", async () => {
  const messages = await talk([...HANDSHAKE, { jsonrpc: "2.0", id: 2, method: "tools/list" }]);

  const init = messages.find((message) => message.id === 1) as { result: Record<string, unknown> };
  expect(init.result.serverInfo).toEqual({ name: "mcp-yandex-tracker", version: "1.0.0" });

  const listed = messages.find((message) => message.id === 2) as {
    result: { tools: { name: string }[] };
  };
  expect(listed.result.tools).toHaveLength(allTools.length);
  expect(listed.result.tools.map((entry) => entry.name)).toContain("tracker_get_issue");
});

test("stdio preserves cyrillic", async () => {
  // End-to-end guard for the UTF-8 byte transport. An unknown-tool call never
  // reaches Tracker, so this needs no credentials.
  const name = "задача_кириллица_проверка";
  const messages = await talk([
    ...HANDSHAKE,
    { jsonrpc: "2.0", id: 2, method: "tools/call", params: { name, arguments: {} } },
  ]);
  expect(JSON.stringify(messages.find((message) => message.id === 2))).toContain(name);
});
