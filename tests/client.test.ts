import assert from "node:assert/strict";
import { describe, test } from "node:test";
import { mkdtemp, readFile, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import {
  apiRoot,
  authHeaders,
  configFromEnv,
  given,
  ifMatch,
  Tracker,
  TrackerApiError,
  TrackerConfigError,
  type TrackerConfig,
} from "../src/client.ts";

function config(overrides: Partial<TrackerConfig> = {}): TrackerConfig {
  return {
    token: "tkn",
    orgId: "42",
    baseUrl: "https://api.tracker.yandex.net",
    authScheme: "OAuth",
    timeout: 30_000,
    ...overrides,
  };
}

type Call = { url: string; method: string; headers: Record<string, string>; body: unknown };

/** A fetch stand-in that records every call and replays queued responses. */
function fakeFetch(...responses: Response[]) {
  const calls: Call[] = [];
  const queue = responses.length > 0 ? responses : [Response.json({})];
  const impl = (async (input: string | URL | Request, init?: RequestInit) => {
    calls.push({
      url: String(input),
      method: init?.method ?? "GET",
      headers: (init?.headers ?? {}) as Record<string, string>,
      body: init?.body,
    });
    // Clone the standing response so a test may call more than once: a body
    // can only be read once.
    return queue.length > 1 ? queue.shift()! : queue[0]!.clone();
  }) as typeof fetch;
  return { impl, calls, last: () => calls.at(-1)! };
}

function client(...responses: Response[]) {
  const f = fakeFetch(...responses);
  return { tracker: new Tracker(config(), f.impl), f };
}

describe("config", () => {
  test("requires a token and one org id", () => {
    assert.throws(() => configFromEnv({}), TrackerConfigError);
    assert.throws(() => configFromEnv({ YANDEX_TRACKER_TOKEN: "tkn" }), TrackerConfigError);
  });

  test("reads every supported variable", () => {
    const parsed = configFromEnv({
      YANDEX_TRACKER_TOKEN: "tkn",
      YANDEX_TRACKER_CLOUD_ORG_ID: "cloud-1",
      YANDEX_TRACKER_AUTH_SCHEME: "Bearer",
      YANDEX_TRACKER_BASE_URL: "https://tracker.example/",
      YANDEX_TRACKER_TIMEOUT: "5",
    });
    assert.equal(parsed.cloudOrgId, "cloud-1");
    assert.equal(parsed.authScheme, "Bearer");
    assert.equal(parsed.baseUrl, "https://tracker.example");
    assert.equal(parsed.timeout, 5000);
  });

  test("always targets v3, whatever the configured host ends with", () => {
    // A /v2 or /v3 suffix left over in an old config is dropped: the version
    // belongs to the path this client builds, not to the configured host.
    for (const baseUrl of ["https://api.tracker.yandex.net", "https://api.tracker.yandex.net/v2"]) {
      assert.equal(apiRoot(config({ baseUrl })), "https://api.tracker.yandex.net/v3");
    }
  });

  test("sends the OAuth scheme and the plain org header", () => {
    const headers = authHeaders(config());
    assert.equal(headers.Authorization, "OAuth tkn");
    assert.equal(headers["X-Org-Id"], "42");
    assert.equal(headers["X-Cloud-Org-Id"], undefined);
  });

  test("cloud org wins and Bearer passes through", () => {
    const headers = authHeaders(config({ cloudOrgId: "cloud-1", authScheme: "Bearer" }));
    assert.equal(headers.Authorization, "Bearer tkn");
    assert.equal(headers["X-Cloud-Org-Id"], "cloud-1");
    assert.equal(headers["X-Org-Id"], undefined);
  });
});

describe("helpers", () => {
  test("given drops only undefined", () => {
    assert.deepEqual(given({ a: 1, b: undefined, c: false, d: "" }), { a: 1, c: false, d: "" });
  });

  test("ifMatch quotes the version and disappears when unset", () => {
    assert.deepEqual(ifMatch(7), { "If-Match": '"7"' });
    assert.equal(ifMatch(undefined), undefined);
  });
});

describe("request", () => {
  test("builds a v3 url", async () => {
    const { tracker, f } = client(Response.json({ key: "TEST-1" }));
    assert.deepEqual(await tracker.request("GET", "/issues/TEST-1"), { key: "TEST-1" });
    assert.equal(f.last().url, "https://api.tracker.yandex.net/v3/issues/TEST-1");
    assert.equal(f.last().method, "GET");
  });

  test("sends params and a json body", async () => {
    const { tracker, f } = client();
    await tracker.request("POST", "/issues/_search", {
      params: { perPage: 5 },
      body: { queue: "TEST" },
    });
    assert.equal(f.last().url, "https://api.tracker.yandex.net/v3/issues/_search?perPage=5");
    assert.equal(f.last().body, '{"queue":"TEST"}');
    assert.equal(f.last().headers["Content-Type"], "application/json");
  });

  test("booleans go out lowercase", async () => {
    // String(true) would put `True`-style JS spelling on the wire; every
    // documented boolean parameter is a JSON boolean.
    const { tracker, f } = client();
    await tracker.request("POST", "/issues/", { params: { notify: false } });
    assert.ok(f.last().url.endsWith("?notify=false"));
    await tracker.request("GET", "/priorities", { params: { localized: true } });
    assert.ok(f.last().url.endsWith("?localized=true"));
  });

  test("a list parameter becomes a repeated key", async () => {
    const { tracker, f } = client();
    await tracker.request("GET", "/worklog", {
      params: { createdAt: ["from:2026-01-01", "to:2026-12-31"] },
    });
    assert.ok(f.last().url.endsWith("?createdAt=from%3A2026-01-01&createdAt=to%3A2026-12-31"));
  });

  test("no content decodes to null", async () => {
    const { tracker } = client(new Response(null, { status: 204 }));
    assert.equal(await tracker.request("DELETE", "/issues/TEST-1/comments/1"), null);
  });

  test("a non-json body falls back to text", async () => {
    const { tracker } = client(new Response("plain"));
    assert.equal(await tracker.request("GET", "/whatever"), "plain");
  });

  test("an If-Match header rides along", async () => {
    const { tracker, f } = client();
    await tracker.request("PATCH", "/boards/1", { headers: { "If-Match": '"7"' } });
    assert.equal(f.last().headers["If-Match"], '"7"');
  });
});

describe("errors", () => {
  test("errorMessages becomes the message", async () => {
    const body = { errorMessages: ["Issue not found"], statusCode: 404 };
    const { tracker } = client(Response.json(body, { status: 404 }));
    const error = (await tracker
      .request("GET", "/issues/NOPE-1")
      .catch((e: unknown) => e)) as TrackerApiError;
    assert.ok(error instanceof TrackerApiError);
    assert.equal(error.status, 404);
    assert.ok(error.message.includes("Issue not found"));
    assert.deepEqual(error.payload, body);
  });

  test("an errors map becomes the message", async () => {
    const { tracker } = client(
      Response.json({ errors: { summary: "must not be empty" } }, { status: 422 }),
    );
    await assert.rejects(tracker.request("POST", "/issues/"), /summary: must not be empty/);
  });

  test("an unknown error shape falls back to the raw body", async () => {
    // The error body shape is not documented, so an unexpected one must still
    // reach the caller instead of being swallowed.
    const { tracker } = client(new Response("gateway exploded", { status: 400 }));
    await assert.rejects(tracker.request("GET", "/issues/TEST-1"), /gateway exploded/);
  });

  test("an empty error body falls back to the status text", async () => {
    const { tracker } = client(new Response("", { status: 403, statusText: "Forbidden" }));
    await assert.rejects(tracker.request("GET", "/issues/TEST-1"), /Forbidden/);
  });

  test("a transport failure becomes a status-zero api error", async () => {
    const tracker = new Tracker(config(), (() => {
      throw new TypeError("fetch failed");
    }) as unknown as typeof fetch);
    const error = (await tracker
      .request("POST", "/issues/")
      .catch((e: unknown) => e)) as TrackerApiError;
    assert.ok(error instanceof TrackerApiError);
    assert.equal(error.status, 0);
    assert.ok(error.message.includes("Failed to reach Yandex Tracker"));
  });
});

describe("download", () => {
  test("streams to disk and reports where it landed", async () => {
    const { tracker, f } = client(new Response("abcde"));
    const dir = await mkdtemp(join(tmpdir(), "tracker-"));
    const result = await tracker.download(
      "/issues/TEST-1/attachments/7/report.txt",
      dir,
      "report.txt",
    );
    assert.deepEqual(result, { path: join(dir, "report.txt"), name: "report.txt", size: 5 });
    assert.equal(await readFile(result.path, "utf8"), "abcde");
    assert.ok(f.last().url.endsWith("/v3/issues/TEST-1/attachments/7/report.txt"));
  });

  test("a traversing file name cannot escape the destination", async () => {
    const { tracker } = client(new Response("x"));
    const dir = await mkdtemp(join(tmpdir(), "tracker-"));
    const result = await tracker.download("/issues/TEST-1/attachments/7/evil", dir, "../evil.txt");
    assert.equal(dirname(result.path), dir);
    assert.equal(result.name, "evil.txt");
  });

  test("creates the destination directory", async () => {
    const { tracker } = client(new Response("x"));
    const dir = join(await mkdtemp(join(tmpdir(), "tracker-")), "a", "b");
    const result = await tracker.download("/issues/TEST-1/attachments/7/f.txt", dir, "f.txt");
    assert.equal(await readFile(result.path, "utf8"), "x");
  });
});

describe("upload", () => {
  test("posts the file under the documented part name", async () => {
    const { tracker, f } = client(Response.json({ id: "7" }));
    const dir = await mkdtemp(join(tmpdir(), "tracker-"));
    const filePath = join(dir, "notes.txt");
    await writeFile(filePath, "hello");

    await tracker.upload("/issues/TEST-1/attachments/", filePath, {
      params: { filename: "renamed.txt" },
    });
    assert.ok(f.last().url.endsWith("/v3/issues/TEST-1/attachments/?filename=renamed.txt"));
    const form = f.last().body as FormData;
    assert.ok(form instanceof FormData);
    const part = form.get("file") as File;
    assert.equal(part.name, "notes.txt");
    assert.equal(await part.text(), "hello");
    // fetch owns the multipart boundary, so we must not set Content-Type.
    assert.equal(f.last().headers["Content-Type"], undefined);
  });

  test("the import endpoints name the part file_data", async () => {
    // post-attachment.md calls the part `file`; import-attachments.md calls it
    // `file_data`. The caller says which, and nothing else differs.
    const { tracker, f } = client(Response.json({ id: "7" }));
    const dir = await mkdtemp(join(tmpdir(), "tracker-"));
    const filePath = join(dir, "notes.txt");
    await writeFile(filePath, "hello");

    await tracker.upload("/issues/TEST-1/attachments/_import", filePath, { part: "file_data" });
    const form = f.last().body as FormData;
    assert.equal(form.get("file"), null);
    assert.equal((form.get("file_data") as File).name, "notes.txt");
  });

  test("a missing file is an argument error, not a transport error", async () => {
    const { tracker, f } = client();
    await assert.rejects(tracker.upload("/issues/TEST-1/attachments/", "/no/such/file"), TypeError);
    assert.equal(f.calls.length, 0);
  });
});
