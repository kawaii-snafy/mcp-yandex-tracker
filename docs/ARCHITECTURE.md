# Architecture

For maintainers and anyone scaling the server. If you only want to _use_ the
tools, see [TOOLS.md](TOOLS.md); to _connect_ it, see [INTEGRATION.md](INTEGRATION.md).

## Layout

```
src/
  cli.ts        # serveStdio(() => buildServer()) — the whole entry point
  server.ts     # buildServer(): registers the three tools and the resources
  dispatch.ts   # tracker_api / tracker_read / tracker_call over the registry
  client.ts     # config, errors, Tracker over fetch — all of the Tracker side
  tool.ts       # the ToolDef type and the tool() helper
  resources.ts  # the read-only tracker:// surface
  tools/
    index.ts    # sections, allTools, toolsByName — the thirteen arrays below
    issues.ts  bulkchange.ts  imports.ts  filters.ts  queues.ts  macros.ts
    boards.ts  entities.ts  projects.ts  dashboards.ts  gaps.ts  admin.ts
    users.ts
scripts/        # gen-tools-doc.ts
```

Tool modules mirror the sections of the official documentation, so a doc page
maps to exactly one code file.

## Build

`tsc` is the whole build, the way the official
[quickstart server](https://github.com/modelcontextprotocol/quickstart-resources/tree/main/weather-server-typescript)
does it: `npm run build` compiles `src/` to `build/` and then marks
`build/cli.js` executable, and `npm run typecheck` is the same config with
`--noEmit`. There is no bundler and no second toolchain to keep in step.

Two details make that work with sources Node can also run directly:
`allowImportingTsExtensions` lets the imports keep their `.ts` extension, which
is what Node's type stripping requires, and `rewriteRelativeImportExtensions`
rewrites them to `.js` on emit. `#!/usr/bin/env node` sits at the top of
`src/cli.ts`; `tsc` preserves it, so the published `bin` works under `npx`.

`tsconfig.json` covers `src` only — `rootDir` and `outDir` make `build/` mirror
it exactly. `scripts/gen-tools-doc.ts` is deliberately outside that config: it
is a dev utility Node runs from source, and including it would push an extra
directory level into `build/`.

Because nothing is bundled, `@modelcontextprotocol/server` and `zod` are real
`dependencies` and a host's `npx -y mcp-yandex-tracker` resolves them on first
run. That is the price of dropping the bundler, and it is why the list of two
is a design constraint rather than an accident.

## Protocol layer: the official MCP SDK

JSON-RPC framing, the stdio transport, lifecycle (`initialize` handshake,
capability negotiation) and `tools/list` / `tools/call` routing all come from
`@modelcontextprotocol/server` v2. We do **not** hand-roll them.

- `cli.ts` calls `serveStdio(() => buildServer())`. It takes a **factory**, not a
  server: the SDK pins one instance per protocol era per connection, so
  registration has to happen inside `buildServer` rather than as an import side
  effect.
- Three tools are registered with `registerTool(name, { title, description,
inputSchema, annotations }, handler)` — `tracker_api`, `tracker_read` and
  `tracker_call`, from `src/dispatch.ts`. `inputSchema` is a `ZodObject` built
  from the tool's `input` shape; the SDK derives the advertised JSON Schema from
  it, `.describe()` text and all. The registry's 179 endpoint tools go through
  the same `ToolDef` type but are not registered — see
  [The dispatch layer](#the-dispatch-layer).
- `annotations` is how a host decides whether a call needs the user's
  confirmation: `readOnlyHint` for the tools that only read, `destructiveHint`
  for the ones that edit or delete, `openWorldHint` throughout because every
  tool reaches a Tracker installation we know nothing about. They come from one
  mapping over the tool's `effect`; `title` is not repeated inside them, since
  the SDK's precedence is `title` → `annotations.title` → `name`. This is the
  whole reason there are two dispatchers and not one: an annotation is per tool,
  so a single tool that could both read and delete would have to be flagged
  destructive and drag a confirmation prompt onto every read.
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
by hand. `src/tools/index.ts` concatenates the modules into `allTools`, keys them
into `toolsByName`, and names each module in `sections` — the registry's table of
contents. Three consumers read that: `src/dispatch.ts` renders the catalogue and
looks endpoints up, `resources.ts` serves it under `tracker://api`, and
`scripts/gen-tools-doc.ts` builds the index in [TOOLS.md](TOOLS.md).

The description is a contract, not prose: summary line, blank line,
`<METHOD> /v3/<path>`, then the URL of the page the tool was written from.
Nothing enforces that the stated endpoint is the one `run` actually calls, so
the pair is kept in step by hand.

It has a third reader: `tool()` maps the method to the tool's `effect` (GET →
`read`, POST → `create`, PUT, PATCH and DELETE → `modify`) and its name to a
`title`, so neither is written out once per tool. Twenty endpoints where the
method misleads set `effect` in the literal — the six `_search` / `_count` POSTs
that only read, the two attachment GETs that write a file to the caller's disk,
and the POSTs (`_move`, `_execute`, `_start`, `_archive`, `_restore`, `_clear`,
`tags/_remove`, `bulkchange/_update`, `bulkchange/_transition`) that act on
something already there.

### The dispatch layer

`src/dispatch.ts` is what stands between the 179-entry registry and the three
tools on the wire. The arithmetic behind it: registering all 179 makes
`tools/list` ~195 KB ≈ 55k tokens, of which 131 KB is argument schemas — and an
agent needs one schema at a time, not all of them for the whole conversation.

So the endpoints are exposed as **data**:

- `renderCatalogue()` turns `sections` into one line per endpoint — name, `(read)`
  mark, summary. 14 KB ≈ 4k tokens for all 179, and it is interpolated straight
  into `tracker_api`'s description, so an agent sees every endpoint from the
  first message.
- `describeTool()` answers `tracker_api`: the endpoint line, the doc URL, which
  dispatcher to use, and `z.toJSONSchema(z.object(def.input))` — the same schema
  the SDK used to advertise, produced on request instead.
- `invoke()` is both dispatchers' body. It looks the name up in `toolsByName`,
  refuses an endpoint belonging to the other dispatcher, validates the arguments
  with `z.strictObject(def.input)` and calls `def.run`. `strictObject` rather than
  `object` because an unknown key is a typo in an argument name, and stripping it
  silently would send a request quietly missing a value — validation moved from
  the MCP boundary to here, so it has to be the stricter kind.

The standing cost is ~17 KB ≈ 4.8k tokens, and the registry itself is untouched:
still one tool per documented endpoint, still the same `ToolDef`, still generated
into [TOOLS.md](TOOLS.md). What changed is only how many of them are projected
into `tools/list`.

The cost is one extra round-trip before the first call to an endpoint whose schema
is not in context yet. `tracker_api` takes a list of names for that reason — an
agent that knows it needs four endpoints pays for one call, not four.

### Client lifecycle

- `getTracker()` builds one `Tracker` lazily and caches it. The environment is
  read on first use, not at startup, so a missing token surfaces as a clean tool
  error instead of killing the process mid-handshake. The connection pool behind
  `fetch` is shared across calls either way.
- `buildServer(tracker = getTracker)` takes the getter as a parameter, so tests
  pass a fake and never touch the network.

### Resources

`resources.ts` exposes read-only context under the `tracker://` scheme: the
endpoint catalogue (`tracker://api`, `tracker://api/{section}`, and
`tracker://api/{tool}` for one schema — the only resources that reach no network),
one issue template `tracker://issue/{key}`, plus static reference dictionaries
(`tracker://statuses`, `priorities`, `issue-types`, `fields`, `queues`).

Resources are a **user**-facing surface: in Claude Code the user `@`-mentions one
(e.g. `@yandex-tracker:tracker://issue/TEST-123`) to attach it as context. The
agent does not read them autonomously mid-task — `tracker_api` and the two
dispatchers remain its path to the same data, so resources are additive, never a
replacement. That asymmetry is also why the catalogue lives in a tool description
rather than only in `tracker://api`: an agent would never read the resource on its
own.

## HTTP client layer

`client.ts` is the entire Tracker side, and it is deliberately small. There is no
HTTP library: `fetch`, `FormData`, `File` and `AbortSignal.timeout` are built
into Node 20+.

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
- **Retries** — 429 and 5xx are retried with exponential backoff when a repeat
  cannot duplicate anything: GET, HEAD, OPTIONS and DELETE by method, plus
  whatever arrives through `idempotent()`. `error-codes.md` documents that 429
  exists but specifies neither a quota nor a `Retry-After` header, so the backoff
  is ours.
- **`idempotent()`** — the same client with every method treated as repeatable.
  The method is all this layer knows, and by method the six POSTs that only read
  (`/_search`, `/_count`) look unsafe — leaving a search, the call an agent makes
  most, surfacing every 429 raw. Whether an endpoint changes anything is the
  registry's `effect`, so `invoke()` in `src/dispatch.ts` decides and passes the
  view down; `run` bodies are unaware. It is two fields over the same `fetch`, so
  the connection pool is shared.
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
  Tracker and has to be explained to the agent separately. The dispatch layer is
  the one place the server adds a call of its own, and it adds no semantics — it
  addresses the registry by name and passes the arguments through.
- **stdout is protocol-only.** Anything written to stdout corrupts the MCP stream.
- **Minimal dependencies.** The server imports `@modelcontextprotocol/server`
  and `zod` and nothing else. Nothing is bundled, so both are real
  `dependencies` — every addition lands in every user's install.
- **Types are inferred, never asserted.** `any` and `as` are banned; the single
  cast in the project is in `src/tool.ts` and is explained there. Node strips the
  types without checking them, so `npm run typecheck` is a required step, not a
  nicety.
- **Injectable seams.** `buildServer` takes the client getter and `Tracker`
  takes a `fetch`, so the whole stack can be driven against fakes with no
  network.
