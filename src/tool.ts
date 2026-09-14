/**
 * The shape every one of the tools lives in.
 *
 * A tool is one documented Yandex Tracker v3 endpoint and nothing else: the
 * API's own parameter names go in, the API's own JSON comes out. Declaring them
 * as data rather than as registration calls means the server, the tests and the
 * `docs/TOOLS.md` generator all read the same list.
 */

import type { ZodObject, ZodRawShape, infer as Infer } from "zod";
import type { Tracker } from "./client.ts";

/**
 * What the endpoint does to the data behind it.
 *
 * A host decides from this whether a call needs the user's confirmation, so the
 * three cases are the ones that decision turns on: `read` never changes
 * Tracker, `create` only adds, `modify` edits or deletes something that is
 * already there.
 */
export type ToolEffect = "read" | "create" | "modify";

/** The endpoint line every description carries: `<METHOD> /v3/<path>`. */
const ENDPOINT = /^(GET|POST|PATCH|DELETE) (\/v3\/\S*)$/m;

/**
 * The effect the HTTP method implies, which is right for all but a handful of
 * endpoints. The exceptions declare `effect` for themselves: a search is a POST
 * because its filter does not fit in a query string, and a download is a GET
 * that still puts a file on the caller's disk.
 */
const EFFECT_BY_METHOD: Record<string, ToolEffect> = {
  GET: "read",
  POST: "create",
  PATCH: "modify",
  DELETE: "modify",
};

/** Read `<METHOD> /v3/<path>` back out of a description. */
export function parseEndpoint(description: string): { method: string; path: string } | undefined {
  const found = ENDPOINT.exec(description);
  return found ? { method: found[1]!, path: found[2]! } : undefined;
}

/**
 * `tracker_get_issue` → `Get issue`. Derived rather than written out 149 times:
 * the title is a label for the host's UI, and the name already says what the
 * endpoint is. The sentence explaining it is the description's job.
 */
function titleFrom(name: string): string {
  const words = name.replace(/^tracker_/, "").replaceAll("_", " ");
  return words.charAt(0).toUpperCase() + words.slice(1);
}

function effectFrom(description: string): ToolEffect {
  const endpoint = parseEndpoint(description);
  // A description without a parseable endpoint line is caught by
  // tests/tools.test.ts, not here; fall to the side that asks the user first.
  return (endpoint && EFFECT_BY_METHOD[endpoint.method]) ?? "modify";
}

export type ToolDef = {
  /** Tool name as the agent calls it, e.g. `tracker_get_issue`. */
  name: string;
  /** Short label for the host's UI, derived from the name. */
  title: string;
  /**
   * Summary line, blank line, `<METHOD> /v3/<path>`, then the URL of the page
   * the tool was written from. The endpoint line and the URL are load-bearing:
   * the contract test and the docs generator both parse them.
   */
  description: string;
  /** Resolved for every tool: declared by the literal, or read off the method. */
  effect: ToolEffect;
  /** Zod shape mirroring the endpoint's documented parameters. */
  input: ZodRawShape;
  run: (tracker: Tracker, args: Record<string, never>) => Promise<unknown>;
};

/** Declare one tool, inferring the type of `args` from `input`. */
export function tool<Shape extends ZodRawShape>(def: {
  name: string;
  description: string;
  /** Only where the HTTP method would imply the wrong thing. */
  effect?: ToolEffect;
  input: Shape;
  run: (tracker: Tracker, args: Infer<ZodObject<Shape>>) => Promise<unknown>;
}): ToolDef {
  // The one cast in the project. Outside, the registry is a homogeneous list;
  // inside each literal, `args` is fully inferred. The server validates the
  // arguments with this very shape before calling `run`, so erasing the
  // parameter type at the boundary cannot make `run` see something else.
  return {
    ...def,
    title: titleFrom(def.name),
    effect: def.effect ?? effectFrom(def.description),
  } as unknown as ToolDef;
}
