/**
 * Transport for the Yandex Tracker REST API v3.
 *
 * Everything in this module is a direct expression of the official
 * documentation — index at https://yandex.ru/support/tracker/en/llms.txt, every
 * page available as markdown by appending `.md`. No SDK, no undocumented
 * endpoints, no guesses.
 */

import { createWriteStream } from "node:fs";
import { mkdir, readFile, stat } from "node:fs/promises";
import { basename, join } from "node:path";
import { Readable } from "node:stream";
import { pipeline } from "node:stream/promises";

/** common-format.md: v3 is the current version and carries every method update. */
export const API_VERSION = "v3";

/**
 * The SDK this server used to wrap retried 10 times by default. Keep comparable
 * resilience for requests that are safe to repeat. error-codes.md documents 429
 * but specifies neither a quota nor a Retry-After header, so back off on our own.
 */
const RETRY_STATUSES = new Set([429, 500, 502, 503, 504]);
const RETRY_METHODS = new Set(["GET", "HEAD", "OPTIONS", "DELETE"]);
const RETRY_ATTEMPTS = 3;
const RETRY_BACKOFF_MS = 500;

export type HttpMethod = "GET" | "POST" | "PATCH" | "DELETE";

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

  const timeout = env.YANDEX_TRACKER_TIMEOUT;
  return {
    token,
    orgId,
    cloudOrgId,
    baseUrl: stripApiVersion(env.YANDEX_TRACKER_BASE_URL ?? DEFAULT_BASE_URL),
    authScheme: env.YANDEX_TRACKER_AUTH_SCHEME ?? DEFAULT_AUTH_SCHEME,
    timeout: timeout === undefined ? DEFAULT_TIMEOUT_MS : Number(timeout) * 1000,
  };
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

export function apiRoot(config: TrackerConfig): string {
  return `${stripApiVersion(config.baseUrl)}/${API_VERSION}`;
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

  /** Call one documented endpoint and return its decoded body. */
  async request(method: HttpMethod, path: string, init: RequestInit_ = {}): Promise<unknown> {
    const response = await this.#send(method, this.#url(path, init.params), {
      headers: init.headers,
      body: init.body === undefined ? undefined : JSON.stringify(init.body),
      json: init.body !== undefined,
    });
    return decode(response);
  }

  /** POST a local file as multipart/form-data (the part is named `file`). */
  async upload(path: string, filePath: string, init: RequestInit_ = {}): Promise<unknown> {
    // Validate up front so a missing or unreadable path is a clean argument
    // error rather than being mislabeled as a transport failure.
    let bytes: Buffer;
    try {
      bytes = await readFile(filePath);
    } catch {
      throw new TypeError(`File not found or not readable: ${filePath}`);
    }

    const form = new FormData();
    // post-attachment.md / temp-attachment.md: the multipart part is named `file`.
    // Content-Type is deliberately left alone — fetch sets the boundary.
    form.append("file", new File([bytes], basename(filePath)));
    const response = await this.#send("POST", this.#url(path, init.params), { body: form });
    return decode(response);
  }

  /** Stream a binary endpoint into `destDir` and return where it landed. */
  async download(
    path: string,
    destDir: string,
    fileName: string,
  ): Promise<{ path: string; name: string; size: number }> {
    // basename guards against path traversal through a Tracker-supplied or
    // caller-supplied name.
    const name = basename(fileName) || "attachment";
    const response = await this.#send("GET", this.#url(path));
    await mkdir(destDir, { recursive: true });
    const destPath = join(destDir, name);
    if (!response.body) throw new TrackerApiError(0, "Yandex Tracker returned an empty body.");
    await pipeline(Readable.fromWeb(response.body), createWriteStream(destPath));
    const { size } = await stat(destPath);
    return { path: destPath, name, size };
  }

  #url(path: string, params?: Record<string, unknown>): string {
    const url = new URL(apiRoot(this.config) + path);
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
    init: { headers?: Record<string, string>; body?: string | FormData; json?: boolean } = {},
  ): Promise<Response> {
    const headers: Record<string, string> = {
      ...authHeaders(this.config),
      ...(init.json ? { "Content-Type": "application/json" } : {}),
      ...init.headers,
    };

    let lastError: unknown;
    for (let attempt = 0; attempt <= RETRY_ATTEMPTS; attempt += 1) {
      let response: Response;
      try {
        response = await this.#fetch(url, {
          method,
          headers,
          body: init.body,
          signal: AbortSignal.timeout(this.config.timeout),
        });
      } catch (error) {
        lastError = error;
        if (attempt < RETRY_ATTEMPTS && RETRY_METHODS.has(method)) {
          await sleep(RETRY_BACKOFF_MS * 2 ** attempt);
          continue;
        }
        throw new TrackerApiError(0, `Failed to reach Yandex Tracker: ${message(error)}`);
      }

      if (
        RETRY_STATUSES.has(response.status) &&
        RETRY_METHODS.has(method) &&
        attempt < RETRY_ATTEMPTS
      ) {
        await sleep(RETRY_BACKOFF_MS * 2 ** attempt);
        continue;
      }
      if (!response.ok) throw await apiError(response);
      return response;
    }
    throw new TrackerApiError(0, `Failed to reach Yandex Tracker: ${message(lastError)}`);
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

async function decode(response: Response): Promise<unknown> {
  // error-codes.md: 204 means the DELETE went through and carries no body.
  if (response.status === 204) return null;
  const text = await response.text();
  if (!text) return null;
  try {
    return JSON.parse(text) as unknown;
  } catch {
    return text;
  }
}

async function apiError(response: Response): Promise<TrackerApiError> {
  const text = await response.text().catch(() => "");
  let payload: unknown;
  try {
    payload = text ? (JSON.parse(text) as unknown) : undefined;
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
  const body = payload as { errorMessages?: unknown; errors?: unknown };
  if (Array.isArray(body.errorMessages) && body.errorMessages.length > 0) {
    return body.errorMessages.map(String).join("; ");
  }
  if (typeof body.errors === "object" && body.errors !== null) {
    const entries = Object.entries(body.errors);
    if (entries.length > 0)
      return entries.map(([key, value]) => `${key}: ${String(value)}`).join("; ");
  }
  return undefined;
}

function message(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
