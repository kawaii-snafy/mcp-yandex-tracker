/**
 * Transport for the Yandex Tracker REST API v3.
 *
 * Everything in this module is a direct expression of the official
 * documentation — index at https://yandex.ru/support/tracker/en/llms.txt, every
 * page available as markdown by appending `.md`. No SDK, no undocumented
 * endpoints, no guesses.
 */

import { createWriteStream } from "node:fs";
import { mkdir, readFile, rm, stat } from "node:fs/promises";
import { basename, isAbsolute, join } from "node:path";
import { Readable } from "node:stream";
import { pipeline } from "node:stream/promises";

/** common-format.md: v3 is the current version and carries every method update. */
export const API_VERSION = "v3";

/**
 * The response headers the documentation gives a meaning to, spelled as it
 * spells them. Everything else Tracker sends — `Date`, `Server`, the transport
 * headers — would cost every call tokens and tell an agent nothing.
 *
 * - common-format.md: `X-Total-Pages`, `X-Total-Count` on paginated lists.
 * - get-changelog.md, get-comments.md, search-issues.md: `Link` to the next page.
 * - search-issues.md: `X-Scroll-Id`, `X-Scroll-Token` of a scrollable search.
 * - get-comment.md, get-component.md, get-version.md: `ETag`.
 */
export const RESPONSE_HEADERS = [
  "X-Total-Pages",
  "X-Total-Count",
  "Link",
  "X-Scroll-Id",
  "X-Scroll-Token",
  "ETag",
] as const;

/**
 * What a call returns: the decoded body untouched, and next to it the headers
 * some endpoints put the rest of their answer in — the scroll cursor, the total,
 * the next page.
 */
export type TrackerResponse = {
  headers: Partial<Record<(typeof RESPONSE_HEADERS)[number], string>>;
  body: unknown;
};

export type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

/** A query value, or a list of them when the API expects a repeated key. */
export type QueryValue = string | number | boolean | Array<string | number | boolean>;
export type QueryParams = Record<string, QueryValue>;

export class TrackerConfigError extends Error {
  override readonly name = "TrackerConfigError";
}

export class TrackerApiError extends Error {
  override readonly name = "TrackerApiError";
  readonly status: number;
  readonly payload: unknown;

  constructor(status: number, message: string, payload?: unknown) {
    super(`Yandex Tracker API error ${status}: ${message}`);
    this.status = status;
    this.payload = payload;
  }
}

export type TrackerConfig = {
  readonly token: string;
  readonly orgId?: string;
  readonly cloudOrgId?: string;
  readonly baseUrl: string;
  readonly authScheme: string;
  readonly timeout: number;
};

const DEFAULT_BASE_URL = "https://api.tracker.yandex.net";
const DEFAULT_AUTH_SCHEME = "OAuth";
const DEFAULT_TIMEOUT_MS = 30_000;
/** setTimeout's ceiling: Node fires any longer delay after 1 ms instead. */
const MAX_TIMEOUT_MS = 2 ** 31 - 1;

export function configFromEnv(
  env: Record<string, string | undefined> = process.env,
): TrackerConfig {
  const token = env.YANDEX_TRACKER_TOKEN;
  if (!token) {
    throw new TrackerConfigError(
      "Set YANDEX_TRACKER_TOKEN with an OAuth or IAM token for Yandex Tracker.",
    );
  }

  const orgId = env.YANDEX_TRACKER_ORG_ID;
  const cloudOrgId = env.YANDEX_TRACKER_CLOUD_ORG_ID;
  if (!orgId && !cloudOrgId) {
    throw new TrackerConfigError("Set YANDEX_TRACKER_ORG_ID or YANDEX_TRACKER_CLOUD_ORG_ID.");
  }

  return {
    token,
    orgId,
    cloudOrgId,
    baseUrl: stripApiVersion(env.YANDEX_TRACKER_BASE_URL ?? DEFAULT_BASE_URL),
    authScheme: env.YANDEX_TRACKER_AUTH_SCHEME ?? DEFAULT_AUTH_SCHEME,
    timeout: timeoutFrom(env.YANDEX_TRACKER_TIMEOUT),
  };
}

/**
 * Seconds in the environment, milliseconds in the config. Anything else is
 * refused here, or it would surface as a network failure on every call:
 * `Number("30s")` is NaN, `Number("")` is 0, and a month-long "no timeout"
 * overflows setTimeout and fires at once.
 */
function timeoutFrom(value: string | undefined): number {
  if (value === undefined) return DEFAULT_TIMEOUT_MS;
  const ms = Number(value) * 1000;
  if (!Number.isFinite(ms) || ms <= 0 || ms > MAX_TIMEOUT_MS) {
    throw new TrackerConfigError(
      `YANDEX_TRACKER_TIMEOUT must be a number of seconds between 0 and ${Math.floor(MAX_TIMEOUT_MS / 1000)}, got "${value}".`,
    );
  }
  return ms;
}

/**
 * The version lives in the path this client builds, not in the configured host.
 * Older configs carry a `/v2` or `/v3` suffix; drop it silently.
 */
function stripApiVersion(baseUrl: string): string {
  const trimmed = baseUrl.replace(/\/+$/, "");
  for (const suffix of [`/${API_VERSION}`, "/v2"]) {
    if (trimmed.endsWith(suffix)) return trimmed.slice(0, -suffix.length);
  }
  return trimmed;
}

/**
 * common-format.md: `OAuth <token>` for OAuth tokens, `Bearer <token>` for IAM
 * ones, plus X-Cloud-Org-ID (Identity Hub) or X-Org-ID (Yandex 360). Exactly one
 * org header goes on the wire; cloud wins when both are set.
 */
export function authHeaders(config: TrackerConfig): Record<string, string> {
  const headers: Record<string, string> = {
    Authorization: `${config.authScheme} ${config.token}`,
  };
  if (config.cloudOrgId) headers["X-Cloud-Org-Id"] = config.cloudOrgId;
  else if (config.orgId) headers["X-Org-Id"] = config.orgId;
  return headers;
}

/**
 * Drop the arguments the caller left unset.
 *
 * Every tool builds its query string and its request body with this, so an
 * omitted optional parameter is simply absent from the request instead of being
 * sent as null. `false` and `""` are values and survive.
 */
export function given<T extends Record<string, unknown>>(values: T): Record<string, unknown> {
  return Object.fromEntries(Object.entries(values).filter(([, value]) => value !== undefined));
}

/**
 * Build a request path, keeping every interpolated value inside its segment.
 *
 * Tools take ids and names from an agent, and a raw `#`, `?` or `/` in one of
 * them would end the path early or address a different object: an attachment
 * named `report #3.pdf` would ask for `…/report`. Every path with a value in it
 * is written as path`/issues/${issueId}`.
 */
export function path(strings: TemplateStringsArray, ...values: Array<string | number>): string {
  return strings.reduce((built, literal, i) => built + segment(values[i - 1]!) + literal);
}

function segment(value: string | number): string {
  const text = String(value);
  // No escaping helps here: URL resolution drops "." and ".." segments, `%2E`
  // spelled or not, so a comment id of ".." would DELETE the entity it is on.
  // An empty one turns an object's path into its collection's.
  if (text === "" || text === "." || text === "..") {
    throw new TypeError(`"${text}" cannot be an id or a name in a request path.`);
  }
  // ":" and "@" are legal inside a segment, and the docs write them bare —
  // get-user.md addresses a numeric login as /users/login:12345.
  return encodeURIComponent(text).replaceAll("%3A", ":").replaceAll("%40", "@");
}

/**
 * Build the optimistic-locking header some endpoints document.
 *
 * Those pages show `If-Match: "<version>"` in their request example: the edit
 * only lands if the object is still at that version, otherwise Tracker answers
 * 409/412. Returns undefined when the caller did not ask for the check.
 */
export function ifMatch(version: string | number | undefined): Record<string, string> | undefined {
  return version === undefined ? undefined : { "If-Match": `"${version}"` };
}

export type RequestInit_ = {
  params?: Record<string, unknown>;
  body?: unknown;
  headers?: Record<string, string>;
  /**
   * Name of the multipart part on an upload. `file` on the attachment
   * endpoints, `file_data` on the import ones — the pages differ, so the
   * caller says which.
   */
  part?: string;
};

type FetchLike = typeof fetch;

/** The only way out to Yandex Tracker. There is nothing else in this layer. */
export class Tracker {
  readonly config: TrackerConfig;
  readonly #fetch: FetchLike;

  constructor(config: TrackerConfig = configFromEnv(), fetchImpl: FetchLike = fetch) {
    this.config = config;
    this.#fetch = fetchImpl;
  }

  /** Call one documented endpoint and return its decoded body with its headers. */
  async request(
    method: HttpMethod,
    path: string,
    init: RequestInit_ = {},
  ): Promise<TrackerResponse> {
    const response = await this.#send(method, this.#url(path, init.params), {
      headers: init.headers,
      body: init.body === undefined ? undefined : JSON.stringify(init.body),
      json: init.body !== undefined,
    });
    return decode(response);
  }

  /** POST a local file as multipart/form-data under the documented part name. */
  async upload(path: string, filePath: string, init: RequestInit_ = {}): Promise<TrackerResponse> {
    // Validate up front so a missing or unreadable path is a clean argument
    // error rather than being mislabeled as a transport failure.
    let bytes: Buffer;
    try {
      bytes = await readFile(filePath);
    } catch {
      throw new TypeError(`File not found or not readable: ${filePath}`);
    }

    const form = new FormData();
    // post-attachment.md / temp-attachment.md name the part `file`;
    // import-attachments.md names it `file_data`.
    // Content-Type is deliberately left alone — fetch sets the boundary.
    form.append(init.part ?? "file", new File([bytes], basename(filePath)));
    const response = await this.#send("POST", this.#url(path, init.params), { body: form });
    return decode(response);
  }

  /** Stream a binary endpoint into `destDir` and return where it landed. */
  async download(
    path: string,
    destDir: string,
    fileName: string,
  ): Promise<{ path: string; name: string; size: number }> {
    // Every argument is checked before the request, so a bad one costs no transfer.
    //
    // A relative directory would resolve against wherever the host happened to
    // start this process — somewhere the agent cannot see, and a relative `path`
    // back would not tell it either.
    if (!isAbsolute(destDir)) {
      throw new TypeError(`destDir must be an absolute path, got "${destDir}".`);
    }
    // basename keeps a Tracker-supplied or caller-supplied name inside destDir;
    // "." and ".." are the names it lets through that still point outside a file.
    const name = basename(fileName);
    if (name === "" || name === "." || name === "..") {
      throw new TypeError(`"${fileName}" is not a file name to save under.`);
    }
    const destPath = join(destDir, name);
    const taken = () => new TypeError(`${destPath} already exists — pass another saveAs.`);
    if (
      await stat(destPath).then(
        () => true,
        () => false,
      )
    )
      throw taken();

    // Before the request too: a destDir that cannot be created is the caller's
    // mistake, not something to find out with a response already streaming.
    await mkdir(destDir, { recursive: true });

    const response = await this.#send("GET", this.#url(path), { stream: true });
    if (!response.body) throw new TrackerApiError(0, "Yandex Tracker returned an empty body.");
    try {
      // `wx`, not the default `w`: a file that appeared since the check above
      // is refused rather than truncated.
      await pipeline(Readable.fromWeb(response.body), createWriteStream(destPath, { flags: "wx" }));
    } catch (error) {
      // EEXIST means the file is someone else's; anything else left a file of
      // ours behind, and a truncated one would pass for finished.
      if (errorCode(error) === "EEXIST") throw taken();
      await rm(destPath, { force: true });
      throw new TrackerApiError(0, `Download from Yandex Tracker broke off: ${message(error)}`);
    }
    const { size } = await stat(destPath);
    return { path: destPath, name, size };
  }

  #url(path: string, params?: Record<string, unknown>): string {
    // configFromEnv has already dropped any version suffix from the host.
    const url = new URL(`${this.config.baseUrl}/${API_VERSION}${path}`);
    for (const [key, value] of Object.entries(params ?? {})) {
      // A repeated key is how `createdAt=from:…&createdAt=to:…` is expressed.
      for (const item of Array.isArray(value) ? value : [value]) {
        if (item !== undefined) url.searchParams.append(key, wireValue(item));
      }
    }
    return url.toString();
  }

  async #send(
    method: HttpMethod,
    url: string,
    init: {
      headers?: Record<string, string>;
      body?: string | FormData;
      json?: boolean;
      /** The body is a file to stream, read without the deadline. */
      stream?: boolean;
    } = {},
  ): Promise<Response> {
    const headers: Record<string, string> = {
      ...authHeaders(this.config),
      ...(init.json ? { "Content-Type": "application/json" } : {}),
      ...init.headers,
    };

    // No retries: a repeat after a lost response can duplicate a create or turn
    // a delete that went through into a 404, and only the agent knows which of
    // its calls are safe to send again. A 429 or 5xx goes back to it as is.
    //
    // The deadline runs until the caller has read the body — a JSON answer that
    // stalls halfway fails like one that never came — except for a download,
    // whose deadline ends with the headers: a large attachment takes longer to
    // arrive than any sensible wait for an answer. Sending an upload is always
    // inside it, since fetch sends the body before the headers come back.
    const abort = new AbortController();
    // unref: a pending deadline must not keep the process alive once stdin closes.
    const timer = setTimeout(
      () => abort.abort(new Error("timed out")),
      this.config.timeout,
    ).unref();
    let response: Response;
    try {
      response = await this.#fetch(url, { method, headers, body: init.body, signal: abort.signal });
    } catch (error) {
      throw new TrackerApiError(0, `Failed to reach Yandex Tracker: ${message(error)}`);
    }
    if (!response.ok) throw await apiError(response);
    if (init.stream) clearTimeout(timer);
    return response;
  }
}

/**
 * Spell a query value the way the API reads it: every documented boolean
 * parameter (`notify`, `full`, `localized`, …) is a JSON boolean, so it has to
 * go out lowercase rather than as JavaScript's `String(true)`.
 */
function wireValue(value: unknown): string {
  return typeof value === "boolean" ? (value ? "true" : "false") : String(value);
}

async function decode(response: Response): Promise<TrackerResponse> {
  const headers: TrackerResponse["headers"] = {};
  for (const name of RESPONSE_HEADERS) {
    const value = response.headers.get(name);
    if (value !== null) headers[name] = value;
  }
  return { headers, body: await decodeBody(response) };
}

async function decodeBody(response: Response): Promise<unknown> {
  // error-codes.md: 204 means the DELETE went through and carries no body.
  if (response.status === 204) return null;
  const text = await response.text().catch((error: unknown) => {
    throw new TrackerApiError(
      0,
      `Failed to read the response from Yandex Tracker: ${message(error)}`,
    );
  });
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

async function apiError(response: Response): Promise<TrackerApiError> {
  const text = await response.text().catch(() => "");
  let payload: unknown;
  try {
    payload = text ? JSON.parse(text) : undefined;
  } catch {
    payload = undefined;
  }
  const detail = errorMessage(payload) ?? text.trim();
  return new TrackerApiError(
    response.status,
    detail || response.statusText || "request failed",
    payload,
  );
}

/**
 * The error body shape is *not* documented anywhere in the API reference, so
 * this stays best effort: read the fields Tracker actually sends, and let the
 * caller fall back to the raw body when it sends something else.
 */
function errorMessage(payload: unknown): string | undefined {
  if (typeof payload !== "object" || payload === null) return undefined;
  if (
    "errorMessages" in payload &&
    Array.isArray(payload.errorMessages) &&
    payload.errorMessages.length > 0
  ) {
    return payload.errorMessages.map(String).join("; ");
  }
  if ("errors" in payload && typeof payload.errors === "object" && payload.errors !== null) {
    const entries = Object.entries(payload.errors);
    if (entries.length > 0)
      return entries.map(([key, value]) => `${key}: ${String(value)}`).join("; ");
  }
  return undefined;
}

function errorCode(error: unknown): unknown {
  return error instanceof Error && "code" in error ? error.code : undefined;
}

function message(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}
