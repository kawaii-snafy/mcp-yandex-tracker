/**
 * The surface the host sees: a catalogue and two ways to call it.
 *
 * The registry still holds one tool per documented endpoint — 179 of them — but
 * projecting all 179 into `tools/list` costs about 55k tokens of every context,
 * and two thirds of that is argument schemas an agent needs one at a time. So
 * the endpoints are exposed as *data* instead: `tracker_api` names them all in
 * its description and hands out a schema on request, `tracker_read` and
 * `tracker_call` run them. Same endpoints, same arguments, same responses, ~4k
 * tokens standing cost.
 *
 * Two dispatchers rather than one because `effect` has to survive as MCP
 * annotations: a host gives `tracker_read` a standing permission and confirms
 * `tracker_call`, which one dispatcher covering both could never express.
 */

import { z } from "zod";
import type { Tracker } from "./client.ts";
import { parseEndpoint, tool, type ToolDef } from "./tool.ts";
import { sections, toolsByName } from "./tools/index.ts";

/** The tool a given endpoint is invoked through. */
function dispatcherFor(def: ToolDef): "tracker_read" | "tracker_call" {
  return def.effect === "read" ? "tracker_read" : "tracker_call";
}

/** The summary line every description opens with. */
function summaryOf(def: ToolDef): string {
  return def.description.split("\n", 1)[0] ?? def.name;
}

/**
 * Every endpoint as one line, grouped by documentation section.
 *
 * This is what replaces 179 tool definitions, so it carries exactly what
 * choosing an endpoint takes: the name, what it does, and — as a `(read)` mark —
 * which dispatcher runs it. Arguments are deliberately absent; that is the
 * question `tracker_api` answers.
 */
export function renderCatalogue(only?: readonly string[]): string {
  const lines: string[] = [];
  for (const section of sections) {
    if (only && !only.includes(section.id)) continue;
    lines.push(`## ${section.id} — ${section.tools.length} endpoints`, section.blurb);
    for (const def of section.tools) {
      const mark = def.effect === "read" ? " (read)" : "";
      lines.push(`${def.name}${mark} — ${summaryOf(def)}`);
    }
    lines.push("");
  }
  return lines.join("\n").trimEnd();
}

/** One endpoint, fully: where it goes, how it is called, what it takes. */
export function describeTool(def: ToolDef): Record<string, unknown> {
  const endpoint = parseEndpoint(def.description);
  const schema = z.toJSONSchema(z.object(def.input), { io: "input" });
  // The draft URI is the same on all 179 and says nothing about the arguments.
  delete schema.$schema;
  return {
    tool: def.name,
    endpoint: endpoint ? `${endpoint.method} ${endpoint.path}` : undefined,
    call: dispatcherFor(def),
    description: def.description,
    arguments: schema,
  };
}

function lookup(name: string): ToolDef {
  const def = toolsByName.get(name);
  if (!def) {
    throw new Error(
      `Unknown endpoint "${name}". Every name is listed in the description of tracker_api.`,
    );
  }
  return def;
}

/**
 * Run one endpoint from the registry.
 *
 * `strictObject` rather than `object`: unknown keys are a typo in an argument
 * name, and stripping them silently would send a request quietly missing a
 * value. Validation happens here instead of at the MCP boundary — the same Zod
 * shape either way, just applied when the endpoint is known.
 *
 * A `read` endpoint gets `tracker.idempotent()`: knowing an endpoint changes
 * nothing is knowing a repeat is safe, and this is the only place that knows it.
 * Without it the six `/_search` and `/_count` POSTs — a search being the call an
 * agent repeats most — would surface every 429 instead of backing off.
 */
async function invoke(
  tracker: Tracker,
  through: "tracker_read" | "tracker_call",
  name: string,
  args: Record<string, unknown> | undefined,
): Promise<unknown> {
  const def = lookup(name);
  if (dispatcherFor(def) !== through) {
    throw new Error(
      `"${name}" is a ${def.effect} endpoint — call it with ${dispatcherFor(def)}, not ${through}.`,
    );
  }
  const client = def.effect === "read" ? tracker.idempotent() : tracker;
  return def.run(client, z.strictObject(def.input).parse(args ?? {}));
}

const TOOL_ARG = z
  .string()
  .min(1)
  .describe("Endpoint name from the catalogue, e.g. `tracker_get_issue`.");

const ARGS_ARG = z
  .record(z.string(), z.unknown())
  .optional()
  .describe(
    "Arguments for the endpoint, spelled exactly as the schema from tracker_api names them. Omit for an endpoint that takes none.",
  );

export const dispatchTools: readonly ToolDef[] = [
  tool({
    name: "tracker_api",
    description: `Look up the arguments of Yandex Tracker endpoints. Every endpoint this server covers is listed below; ask this tool for the ones you intend to call — several at once — and you get their JSON Schema, HTTP method and documentation URL back.

Then run the endpoint: the ones marked \`(read)\` through tracker_read, all others through tracker_call.

${renderCatalogue()}`,
    effect: "read",
    input: {
      tools: z
        .array(TOOL_ARG)
        .min(1)
        .describe("Endpoint names to describe. Ask for every endpoint you plan to use at once."),
    },
    run: async (_tracker, { tools }) => tools.map((name) => describeTool(lookup(name))),
  }),

  tool({
    name: "tracker_read",
    description: `Call a Yandex Tracker endpoint that only reads. Accepts the endpoints marked \`(read)\` in the catalogue in tracker_api's description; anything that writes goes through tracker_call.

Returns the API's own JSON, untouched. Trim a large response with the endpoint's own \`fields\` and \`expand\` arguments.`,
    effect: "read",
    input: { tool: TOOL_ARG, args: ARGS_ARG },
    run: async (tracker, { tool: name, args }) => invoke(tracker, "tracker_read", name, args),
  }),

  tool({
    name: "tracker_call",
    description: `Call a Yandex Tracker endpoint that creates, edits or deletes something. Accepts every endpoint *not* marked \`(read)\` in the catalogue in tracker_api's description.

Get the arguments from tracker_api first — this is the tool that changes data, and a wrong field name is rejected rather than dropped. Returns the API's own JSON, untouched.`,
    effect: "modify",
    input: { tool: TOOL_ARG, args: ARGS_ARG },
    run: async (tracker, { tool: name, args }) => invoke(tracker, "tracker_call", name, args),
  }),
];
