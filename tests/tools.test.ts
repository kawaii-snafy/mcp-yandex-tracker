import { describe, expect, test } from "bun:test";
import { z } from "zod";
import type { Tracker } from "../src/client.ts";
import type { ToolDef, ToolEffect } from "../src/tool.ts";
import { allTools } from "../src/tools/index.ts";

/**
 * Every tool description ends with the endpoint it wraps and the page it was
 * written from. Both are load-bearing: these tests hold the code to them, and
 * scripts/gen-tools-doc.ts builds docs/TOOLS.md out of them.
 */
const ENDPOINT = /^(GET|POST|PATCH|DELETE) (\/v3\/\S*)$/m;
const DOC_URL = /^https:\/\/yandex\.ru\/support\/tracker\/en\/api\/[\w/-]+\.md$/m;

type Recorded = {
  method: string;
  path: string;
  params?: Record<string, unknown>;
  body?: unknown;
  headers?: Record<string, string>;
  filePath?: string;
  destDir?: string;
  fileName?: string;
};

/** Records the HTTP call a tool asks for, without making one. */
function fakeTracker(result: unknown = { ok: true }) {
  const calls: Recorded[] = [];
  const tracker = {
    request: async (method: string, path: string, init: Record<string, unknown> = {}) => {
      calls.push({ method, path, ...init });
      return result;
    },
    upload: async (path: string, filePath: string, init: Record<string, unknown> = {}) => {
      calls.push({ method: "POST", path, filePath, ...init });
      return result;
    },
    download: async (path: string, destDir: string, fileName: string) => {
      calls.push({ method: "GET", path, destDir, fileName });
      return { path: `${destDir}/${fileName}`, name: fileName, size: 0 };
    },
  } as unknown as Tracker;
  return { tracker, calls, last: () => calls.at(-1)! };
}

/**
 * A stand-in value for a required argument, derived from its declared type.
 * Strings become `<name>` so a path placeholder stays recognisable in the URL.
 */
function sample(name: string, expected: string | undefined): unknown {
  switch (expected) {
    case "number":
      return 1;
    case "boolean":
      return true;
    case "array":
      return [];
    case "record":
      return {};
    default:
      // Strings, and unions — every union in the registry accepts a string.
      return `<${name}>`;
  }
}

/**
 * Which arguments a tool insists on, asked of Zod itself: parse an empty object
 * and read back the keys it complained about, along with the type it wanted.
 */
function requiredArguments(def: ToolDef): Record<string, unknown> {
  const result = z.object(def.input).safeParse({});
  if (result.success) return {};
  return Object.fromEntries(
    result.error.issues.map((issue) => {
      const name = String(issue.path[0]);
      const expected = "expected" in issue ? String(issue.expected) : undefined;
      return [name, sample(name, expected)];
    }),
  );
}

async function invoke(def: ToolDef, args: Record<string, unknown>) {
  const fake = fakeTracker();
  await def.run(fake.tracker, args as Record<string, never>);
  return fake;
}

describe("the tool surface is the documented API surface", () => {
  test("there are no duplicate tool names", () => {
    const names = allTools.map((def) => def.name);
    expect(new Set(names).size).toBe(names.length);
  });

  test("every tool is named tracker_* and names its endpoint and its doc page", () => {
    for (const def of allTools) {
      expect(def.name).toStartWith("tracker_");
      expect(def.description).toMatch(ENDPOINT);
      expect(def.description).toMatch(DOC_URL);
    }
  });

  test("every tool calls the endpoint its description claims", async () => {
    // Rather than restating 149 endpoints in a fixture, read each one out of the
    // tool's own description and check the tool really issues it. A description
    // that drifts from its code fails here, and so does a tool that reaches a
    // path nobody documented.
    for (const def of allTools) {
      const [, method, docPath] = ENDPOINT.exec(def.description)!;
      const args = requiredArguments(def);
      const fake = await invoke(def, args);

      expect(fake.calls).toHaveLength(1);
      const expected = docPath!
        .slice("/v3".length)
        .replaceAll(/\{(\w+)\}/g, (_, key: string) => String(args[key]));
      expect(`${def.name} ${fake.last().method} ${fake.last().path}`).toBe(
        `${def.name} ${method} ${expected}`,
      );
    }
  });

  test("an argument the caller omits is absent from the request", async () => {
    // given() drops unset arguments so Tracker never receives `null` for a
    // parameter the caller simply did not use.
    const fake = await invoke(byName("tracker_get_users"), {});
    expect(fake.last().params).toEqual({});
  });

  test("an argument the caller supplies is sent", async () => {
    const fake = await invoke(byName("tracker_get_users"), { perPage: 10 });
    expect(fake.last().params).toEqual({ perPage: 10 });
  });
});

describe("every tool tells the host what it does", () => {
  // Claude's connector review requires a title and a read-only or destructive
  // hint on every tool; the hint is what decides whether the user is asked
  // before each call. src/server.ts turns `effect` into both.
  test("every tool has a title and an effect", () => {
    for (const def of allTools) {
      expect(def.title).not.toBe("");
      expect(def.title).not.toContain("_");
      expect(["read", "create", "modify"]).toContain(def.effect);
    }
  });

  test("the effect matches the method unless the tool overrides it", () => {
    // The exceptions are listed here rather than derived, so adding one is a
    // deliberate edit: a search is a POST that changes nothing, a download is a
    // GET that writes to the caller's disk, and a POST ending in `_move`,
    // `_start` and friends acts on something that already exists.
    const overrides: Record<string, ToolEffect> = {
      tracker_search_issues: "read",
      tracker_count_issues: "read",
      tracker_search_entities: "read",
      tracker_search_worklog: "read",
      tracker_search_reports: "read",
      tracker_get_attachment: "create",
      tracker_get_attachment_preview: "create",
      tracker_bulkchange_entities: "modify",
      tracker_entity_move_checklist_item: "modify",
      tracker_move_issue: "modify",
      tracker_new_transition: "modify",
      tracker_restore_queue: "modify",
      tracker_delete_queue_tag: "modify",
      tracker_archive_sprint: "modify",
      tracker_start_sprint: "modify",
      tracker_clear_scroll: "modify",
    };
    const byMethod: Record<string, ToolEffect> = {
      GET: "read",
      POST: "create",
      PATCH: "modify",
      DELETE: "modify",
    };

    for (const def of allTools) {
      const [, method] = ENDPOINT.exec(def.description)!;
      expect(`${def.name} ${def.effect}`).toBe(
        `${def.name} ${overrides[def.name] ?? byMethod[method!]}`,
      );
    }
  });

  test("no tool that writes is advertised as read-only", () => {
    // The hint that grants a standing permission, held to the one thing it must
    // never cover: an endpoint that is not a GET, and is not one of the five
    // documented searches, cannot be read.
    const searches = allTools.filter((def) => def.effect === "read");
    for (const def of searches) {
      const [, method, path] = ENDPOINT.exec(def.description)!;
      if (method === "GET") continue;
      expect(`${def.name} ${path}`).toMatch(/(_search|_count)$/);
    }
  });
});

describe("the places a tool cannot mirror its endpoint byte for byte", () => {
  test("optimistic locking on a board edit travels as an If-Match header", async () => {
    // The board, column and sprint pages document a header rather than a
    // parameter; everywhere else `version` is a real query parameter.
    const fake = await invoke(byName("tracker_patch_board"), { boardId: "42", version: 7 });
    expect(fake.last().headers).toEqual({ "If-Match": '"7"' });
  });

  test("omitting the version sends no If-Match", async () => {
    const fake = await invoke(byName("tracker_patch_board"), { boardId: "42", name: "Board" });
    expect(fake.last().headers).toBeUndefined();
  });

  test("a query-parameter version stays a query parameter", async () => {
    const fake = await invoke(byName("tracker_patch_issue"), { issueId: "TEST-1", version: 3 });
    expect(fake.last().params).toEqual({ version: 3 });
    expect(fake.last().headers).toBeUndefined();
  });

  test("download streams to the requested directory", async () => {
    const fake = await invoke(byName("tracker_get_attachment"), {
      issueId: "TEST-1",
      fileId: "7",
      fileName: "report.txt",
      destDir: "/tmp/x",
    });
    expect(fake.last().path).toBe("/issues/TEST-1/attachments/7/report.txt");
    expect(fake.last().destDir).toBe("/tmp/x");
    expect(fake.last().fileName).toBe("report.txt");
  });

  test("download honours a local name override", async () => {
    const fake = await invoke(byName("tracker_get_attachment"), {
      issueId: "TEST-1",
      fileId: "7",
      fileName: "report.txt",
      destDir: "/tmp/x",
      saveAs: "local.txt",
    });
    expect(fake.last().fileName).toBe("local.txt");
    // The remote path still uses the name Tracker knows the file by.
    expect(fake.last().path).toEndWith("/report.txt");
  });

  test("upload sends the local path and the rename parameter", async () => {
    const fake = await invoke(byName("tracker_post_attachment"), {
      issueId: "TEST-1",
      filePath: "/tmp/a.txt",
      filename: "b.txt",
    });
    expect(fake.last().path).toBe("/issues/TEST-1/attachments/");
    expect(fake.last().filePath).toBe("/tmp/a.txt");
    expect(fake.last().params).toEqual({ filename: "b.txt" });
  });

  test("`from` keeps the API's spelling", async () => {
    // Python had to call this argument `from_`; TypeScript does not.
    const fake = await invoke(byName("tracker_get_entity_events"), {
      entityType: "project",
      entityId: "1",
      from: "2026-01-01",
    });
    expect(fake.last().params).toMatchObject({ from: "2026-01-01" });
  });
});

function byName(name: string): ToolDef {
  const def = allTools.find((candidate) => candidate.name === name);
  if (!def) throw new Error(`no tool named ${name}`);
  return def;
}
