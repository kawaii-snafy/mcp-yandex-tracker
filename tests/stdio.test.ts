import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { createInterface } from "node:readline";
import { before, test } from "node:test";
import { setTimeout as delay } from "node:timers/promises";
import { allTools } from "../src/tools/index.ts";

const CLI = "dist/cli.js";

/**
 * Drive the *built* bundle the way a host does: `node dist/cli.js`, newline
 * delimited JSON-RPC over stdio. This is the only test that proves the shipped
 * artifact works as published — and the one that would catch the
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
  // `ref: false` so the timeout never holds the test process open once the
  // conversation is over; it is a ceiling, not a wait.
  await Promise.race([done, delay(15_000, undefined, { ref: false })]);
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

before(async () => {
  // The suite tests the artifact, so it builds it first rather than trusting
  // whatever dist/ happens to hold.
  const build = spawn("node", ["scripts/build.mjs"], { stdio: ["ignore", "ignore", "inherit"] });
  const code = await new Promise<number | null>((resolve) => build.on("exit", resolve));
  assert.equal(code, 0);
});

test("the built bundle serves the whole tool surface under node", async () => {
  const messages = await talk([...HANDSHAKE, { jsonrpc: "2.0", id: 2, method: "tools/list" }]);

  const init = messages.find((message) => message.id === 1) as { result: Record<string, unknown> };
  assert.deepEqual(init.result.serverInfo, { name: "mcp-yandex-tracker", version: "1.0.0" });

  const listed = messages.find((message) => message.id === 2) as {
    result: { tools: { name: string; title?: string; annotations?: Record<string, boolean> }[] };
  };
  assert.equal(listed.result.tools.length, allTools.length);
  assert.ok(listed.result.tools.map((entry) => entry.name).includes("tracker_get_issue"));

  // The annotations a host reads to decide whether to ask the user, checked on
  // the wire rather than in the registry: reading an issue runs unattended,
  // deleting one does not.
  for (const entry of listed.result.tools) {
    assert.ok(entry.title);
    assert.notEqual(entry.annotations, undefined);
  }
  const byName = new Map(listed.result.tools.map((entry) => [entry.name, entry]));
  assert.partialDeepStrictEqual(byName.get("tracker_get_issue")?.annotations, {
    readOnlyHint: true,
  });
  assert.partialDeepStrictEqual(byName.get("tracker_delete_comment")?.annotations, {
    readOnlyHint: false,
    destructiveHint: true,
  });
});

test("stdio preserves cyrillic", async () => {
  // End-to-end guard for the UTF-8 byte transport. An unknown-tool call never
  // reaches Tracker, so this needs no credentials.
  const name = "задача_кириллица_проверка";
  const messages = await talk([
    ...HANDSHAKE,
    { jsonrpc: "2.0", id: 2, method: "tools/call", params: { name, arguments: {} } },
  ]);
  assert.ok(JSON.stringify(messages.find((message) => message.id === 2)).includes(name));
});
