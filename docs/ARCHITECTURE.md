# Architecture

For maintainers and anyone scaling the server. If you only want to _use_ the
tools, see [TOOLS.md](TOOLS.md); to _connect_ it, see [INTEGRATION.md](INTEGRATION.md).

## Layout

```
src/
  cli.ts        # serveStdio(() => buildServer()) — the whole entry point
  server.ts     # buildServer(): registers every tool and resource; getTracker()
  client.ts     # config, errors, Tracker over fetch — all of the Tracker side
  tool.ts       # the ToolDef type and the tool() helper
  resources.ts  # the read-only tracker:// surface
  tools/
    index.ts    # allTools — the six arrays below, concatenated
    issues.ts  queues.ts  boards.ts  entities.ts  admin.ts  users.ts
tests/          # bun test; fakes for the transport, the real bundle for stdio
scripts/        # gen-tools-doc.ts
```

Tool modules mirror the sections of the official documentation, so a doc page
maps to exactly one code file.

The published artifact is `dist/cli.js`: one Node-compatible ESM bundle with a
`#!/usr/bin/env node` banner, produced by `bun build --target node`. Dependencies
are bundled in, so a cold `npx -y mcp-yandex-tracker` has no dependency tree to
install — which matters because that is exactly how a host launches it.

## Protocol layer: the official MCP SDK

JSON-RPC framing, the stdio transport, lifecycle (`initialize` handshake,
capability negotiation) and `tools/list` / `tools/call` routing all come from
`@modelcontextprotocol/server` v2. We do **not** hand-roll them.

- `cli.ts` calls `serveStdio(() => buildServer())`. It takes a **factory**, not a
  server: the SDK pins one instance per protocol era per connection, so
  registration has to happen inside `buildServer` rather than as an import side
  effect.
- Each tool is registered with `registerTool(name, { description, inputSchema },
handler)`. `inputSchema` is a `ZodObject` built from the tool's `input` shape;
  the SDK derives the advertised JSON Schema from it, `.describe()` text and all.
- No `outputSchema` is declared. That keeps responses token-lean — one compact
  JSON text block, no duplicating `structuredContent`, nothing extra in every
  `tools/list`.
- **Errors are thrown, not wrapped.** A `TrackerApiError`, `TrackerConfigError`
  or Zod validation error propagating out of a handler is turned by the SDK into
  a `tools/call` result with `isError: true` carrying the message — the JSON-RPC
  call itself still succeeds. No handler needs a try/catch.

## The tool registry

A tool is data, not a registration call:

```ts
tool({
  name: "tracker_get_issue",
  description: `Get the parameters of an issue.

GET /v3/issues/{issueId}
https://yandex.ru/support/tracker/en/api/issues/get-issue.md`,
  input: { issueId: z.string().min(1).describe("Issue ID or key.") },
  run: (tracker, a) => tracker.request("GET", `/issues/${a.issueId}`),
});
```

`tool()` infers the type of `run`'s `args` from `input`, so nothing is annotated
by hand. Three consumers read the same array: `buildServer` registers it,
`tests/tools.test.ts` checks every entry against its own description, and
`scripts/gen-tools-doc.ts` builds the index in [TOOLS.md](TOOLS.md).

The description is a contract, not prose: summary line, blank line,
`<METHOD> /v3/<path>`, then the URL of the page the tool was written from. The
test suite parses both halves and fails if a tool reaches an endpoint other than
the one it claims.

### Client lifecycle

- `getTracker()` builds one `Tracker` lazily and caches it. The environment is
  read on first use, not at startup, so a missing token surfaces as a clean tool
  error instead of killing the process mid-handshake. The connection pool behind
  `fetch` is shared across calls either way.
- `buildServer(tracker = getTracker)` takes the getter as a parameter, so tests
  pass a fake and never touch the network.

### Resources

`resources.ts` exposes read-only context under the `tracker://` scheme: one
template, `tracker://issue/{key}`, plus static reference dictionaries
(`tracker://statuses`, `priorities`, `issue-types`, `fields`, `queues`).

Resources are a **user**-facing surface: in Claude Code the user `@`-mentions one
(e.g. `@yandex-tracker:tracker://issue/TEST-123`) to attach it as context. The
agent does not read them autonomously mid-task — the tools remain its path to the
same data, so resources are additive, never a replacement.

## HTTP client layer

`client.ts` is the entire Tracker side, and it is deliberately small. There is no
HTTP library: `fetch`, `FormData`, `File` and `AbortSignal.timeout` are built
into both Node 20+ and Bun.

- **Config** — `configFromEnv()` reads the environment and validates that a token
  and one org id are present. `apiRoot()` always ends in `/v3`: the version
  belongs to the path this client builds, so a leftover `/v2` or `/v3` suffix on
  `YANDEX_TRACKER_BASE_URL` is stripped. `authHeaders()` picks `OAuth` vs
  `Bearer` from `authScheme` and sends exactly one org header —
  `X-Cloud-Org-Id` when a cloud org id is set, `X-Org-Id` otherwise.
- **`Tracker.request(method, path, { params, body, headers })`** — the only way
  out. Builds `{apiRoot}{path}`, sends it with the configured timeout, and
  returns the decoded body untouched. `upload()` and `download()` are the two
  variants the wire format forces: multipart in, streamed bytes out.
- **Query spelling** — booleans go out as `true`/`false` rather than JavaScript's
  `String(true)`, and an array value becomes a repeated key, which is how
  `createdAt=from:…&createdAt=to:…` is expressed.
- **Errors** — a transport failure becomes `TrackerApiError(0, "Failed to reach
Yandex Tracker: …")`; any non-2xx becomes `TrackerApiError(status, message,
payload)`. The error body shape is _not_ documented anywhere in the API
  reference, so the message is read best-effort from `errorMessages` / `errors`
  with a fallback to the raw body and then the HTTP status text.
- **Retries** — 429 and 5xx are retried for idempotent methods with exponential
  backoff. `error-codes.md` documents that 429 exists but specifies neither a
  quota nor a `Retry-After` header, so the backoff is ours.
- **`given({...})`** — drops the arguments a caller left unset, so an omitted
  optional parameter is absent from the request rather than sent as `null`.

## Design constraints

- **The official documentation is the only source of truth for Tracker.** Index:
  <https://yandex.ru/support/tracker/en/llms.txt>; any page becomes markdown by
  appending `.md`. Every tool's description links to the page it was written
  from — see [EXTENDING.md](EXTENDING.md).
- **One tool per documented endpoint.** The API's parameter names go in, the
  API's JSON comes out. No projections, no renaming, no client-side pagination or
  filtering: anything the server invents is a place where it can drift from
  Tracker and has to be explained to the agent separately.
- **stdout is protocol-only.** Anything written to stdout corrupts the MCP stream.
- **Minimal dependencies.** Runtime dependencies are
  `@modelcontextprotocol/server` and `zod`.
- **Types are inferred, never asserted.** `any` and `as` are banned; the single
  cast in the project is in `src/tool.ts` and is explained there. Bun does not
  type-check, so `bun run typecheck` is a required step, not a nicety.
- **Testability by injection.** `buildServer` takes the client getter and
  `Tracker` takes a `fetch`, so the whole stack runs against fakes with no
  network.
