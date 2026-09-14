# Extending & scaling

For anyone adding tools or changing behavior. Read [ARCHITECTURE.md](ARCHITECTURE.md)
first for the map of the request lifecycle.

## Non-negotiable rules

These are load-bearing; a change that breaks one is a regression.

1. **The official documentation is the only source of truth for Yandex Tracker.**
   Index of every page: <https://yandex.ru/support/tracker/en/llms.txt>; any page
   is markdown by appending `.md`
   (`https://yandex.ru/support/tracker/en/api/<section>/<page>.md`). Blogs, Stack
   Overflow, observed production behavior and model memory are **not** sources. A
   path, parameter or field that is not on a page from `llms.txt` does not go into
   the code. If a capability is genuinely needed and genuinely undocumented, that
   is a deviation: record it in [TOOLS.md](TOOLS.md) with the reason.
2. **Only documented REST API v3 endpoints.** Every call goes through
   `Tracker.request()` in `src/client.ts`. Do not add a second HTTP path, an HTTP
   library, or an abstraction on top of `fetch`. The MCP side stays on the
   official SDK.
3. **One tool per endpoint, nothing in between.** The API's parameter names go in,
   the API's JSON comes out. No projections, no renaming, no client-side
   pagination, no convenience tools that compose several calls.
4. **No `any`, no `as`.** Let types be inferred — `tool()` derives the type of
   `run`'s arguments from `input`. The one cast in the project lives in
   `src/tool.ts` and is explained there.
5. **Never write to stdout.** stdout is the JSON-RPC channel. Diagnostics go to
   stderr. A stray `console.log` corrupts the stream and the host drops the
   connection.
6. **Keep dependencies minimal.** The runtime dependencies are
   `@modelcontextprotocol/server` and `zod`. Add another only with a clear reason.
7. **Type-check and test after any behavior change.** Bun transpiles without
   checking types, so `bun test` alone is not enough:
   ```sh
   bun run typecheck && bun test
   ```

## Adding a tool

A tool is one endpoint, so adding one starts by opening its page.

1. **Find the page** in <https://yandex.ru/support/tracker/en/llms.txt> and read
   the `.md` version. Note the method, the exact path (including whether the doc
   writes a trailing slash), every query parameter, and every body field.
2. **Add one entry** to the array in the `src/tools/` module that matches the
   page's section. Transcribe the parameters — same names, documented types,
   descriptions taken from the page:

   ```ts
   tool({
     name: "tracker_get_comments",
     description: `Get the comments for an issue.

   GET /v3/issues/{issueId}/comments
   https://yandex.ru/support/tracker/en/api/issues/get-comments.md`,
     input: {
       issueId: z.string().min(1).describe("Issue ID or key."),
       expand: z.string().optional().describe("Additional fields: attachments, html, all."),
       perPage: z.number().int().optional().describe("Comments per page."),
     },
     run: (tracker, a) =>
       tracker.request("GET", `/issues/${a.issueId}/comments`, {
         params: given({ expand: a.expand, perPage: a.perPage }),
       }),
   }),
   ```

   The description is always: summary line, blank line, `<METHOD> /v3/<path>`,
   the page URL. The SDK derives the JSON Schema from `input`; `.describe()` is
   what the agent reads, so every parameter gets one.

   Conventions the whole package follows:
   - Path placeholders become camelCase fields (`<issue_ID>` → `issueId`).
   - `given({...})` drops what the caller left unset; use it for `params` and
     `body` alike, and omit the option entirely when there is nothing to send.
   - Required parameters carry no `.optional()`; optional ones do.
   - When a page documents `If-Match: "<version>"`, add a trailing optional
     `version` field and pass `headers: ifMatch(a.version)`. When it documents
     `version` as a query parameter, it belongs in `params` instead.
   - Body too open-ended to enumerate (the page says "the same format as when
     editing issues")? Take one `fields` record and spread it last.
   - **`effect` only when the method misleads.** `tool()` reads the method out of
     the description and turns it into the MCP annotations a host uses to decide
     whether to ask the user: GET is `read`, POST is `create`, PATCH and DELETE
     are `modify`. Add `effect: "read" | "create" | "modify"` after the
     description when that is wrong — a `_search` POST that only reads, a GET
     that downloads a file onto the caller's disk, a POST like `_move` or
     `_start` that acts on an object that already exists. The exception list is
     restated in `tests/tools.test.ts`, so adding one is two edits on purpose.

3. **Regenerate the index**: `bun run docs:tools` rewrites the tables in
   [TOOLS.md](TOOLS.md) between its `<!-- tools:start -->` / `<!-- tools:end -->`
   markers and formats the result — commit whatever it changes. The preamble
   above the marker is hand-written; leave it alone. Do not copy Yandex's
   argument tables into the file either: the page is the reference.
4. **Tests need nothing**, unless you declared an `effect`.
   `tests/tools.test.ts` walks the registry, so a new tool is covered the moment
   it is added — and fails immediately if its description and its code disagree.
   Add a case there only for a deviation; an `effect` override is one, and goes
   in the table in "every tool tells the host what it does".

## Testing model

The suite runs on fakes — no network, no real token — except for the last file,
which runs the real built bundle with no credentials.

- **`tests/client.test.ts`** injects a fake `fetch` via `new Tracker(config, fetchImpl)`
  and asserts on the transport: URL building, auth and org headers, boolean
  spelling, repeated query keys, non-2xx → `TrackerApiError`, `204` → `null`,
  transport failure → status-0 error, streamed download, multipart upload.
- **`tests/tools.test.ts`** is the centrepiece. It reads the endpoint out of each
  tool's own description, synthesises the required arguments from the Zod shape,
  and checks the tool really issues that method and path. One test covers the
  whole surface.
- **`tests/stdio.test.ts`** builds the bundle and drives `node dist/cli.js` over
  real stdio. This is what proves the shipped artifact works without Bun.

## Scaling notes

- **Cached client.** `getTracker()` builds one `Tracker` lazily and reuses it, so
  the connection pool behind `fetch` is shared. The environment is read once, at
  first use — which is why a missing token is a tool error rather than a crash
  during the host's handshake. `buildServer()` takes the getter as a parameter so
  tests can swap it.
- **Server factory.** `serveStdio` calls `buildServer` as a factory — the SDK
  pins one instance per protocol era per connection — so registration must happen
  inside it, never as an import side effect.
- **More primitives.** Read-only context lives in `src/resources.ts` as
  `registerResource` calls — add more the same way. For templated prompts, use
  `registerPrompt`.
- **Response size.** Responses are raw Tracker JSON, and issue objects are large.
  Trim them with the API's own `fields` and `expand` parameters — never by
  filtering in the server.
- **Auth schemes.** OAuth vs IAM is decided in `authHeaders()` by `authScheme`.
  Add new schemes there, not in a tool.
