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

export type ToolDef = {
  /** Tool name as the agent calls it, e.g. `tracker_get_issue`. */
  name: string;
  /**
   * Summary line, blank line, `<METHOD> /v3/<path>`, then the URL of the page
   * the tool was written from. The endpoint line and the URL are load-bearing:
   * the contract test and the docs generator both parse them.
   */
  description: string;
  /** Zod shape mirroring the endpoint's documented parameters. */
  input: ZodRawShape;
  run: (tracker: Tracker, args: Record<string, never>) => Promise<unknown>;
};

/** Declare one tool, inferring the type of `args` from `input`. */
export function tool<Shape extends ZodRawShape>(def: {
  name: string;
  description: string;
  input: Shape;
  run: (tracker: Tracker, args: Infer<ZodObject<Shape>>) => Promise<unknown>;
}): ToolDef {
  // The one cast in the project. Outside, the registry is a homogeneous list;
  // inside each literal, `args` is fully inferred. The server validates the
  // arguments with this very shape before calling `run`, so erasing the
  // parameter type at the boundary cannot make `run` see something else.
  return def as unknown as ToolDef;
}
