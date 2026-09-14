# Agent Notes

- **The official documentation is the only source of truth for Yandex Tracker.**
  Index of every page: <https://yandex.ru/support/tracker/en/llms.txt>; any page
  is markdown by appending `.md`
  (`https://yandex.ru/support/tracker/en/api/<section>/<page>.md`). Blogs, Stack
  Overflow, observed production behavior and model memory are **not** sources. A
  path, parameter or field that is not on a page from `llms.txt` does not go into
  the code.
- **Only documented REST API v3 endpoints.** Tracker is reached with `fetch`
  through `Tracker.request()` in `src/client.ts`. Do not add a second HTTP path,
  an SDK, or an abstraction layer on top of it. The MCP side stays on the
  official `@modelcontextprotocol/server`.
- **One tool per endpoint, nothing in between.** Parameter names are the API's
  own (`perPage`, `expand`, `markupType`), and the response is returned exactly
  as Tracker sent it — no reshaping, no filtering, no client-side pagination.
- Tools are **data**: each is a `tool({ name, description, input, run })` entry in
  the array its `src/tools/<section>.ts` exports. The server, the tests and the
  `docs/TOOLS.md` generator all read that same registry.
- Every tool ships a `title` and MCP annotations. Both are derived — the title
  from the name, `readOnlyHint` / `destructiveHint` from the method in the
  description — so add `effect` to a tool only when its method misleads (a
  `_search` POST, a GET that downloads to disk, a `_move`-style POST).
- Keep dependencies minimal: only `@modelcontextprotocol/server` and `zod`, and
  both are `devDependencies` because esbuild inlines them into `dist/cli.js` —
  the published package declares none, so a host installs one file. Adding a
  runtime import means adding to what every user downloads. HTTP is the built-in
  `fetch`; there is no HTTP library.
- **`any` is banned**, and so are `as` casts — the one that exists is in
  `src/tool.ts` and is explained there. Let types be inferred.
- Do not print logs to stdout; MCP stdio stdout must contain only JSON-RPC
  messages. Diagnostics go to stderr.
- **Node does not type-check.** It strips the types and runs, so `npm run
typecheck` (tsc) is as necessary as `npm test` after changing behavior.
- See `docs/` for the full guide: `EXTENDING.md` (adding tools, rules, scaling),
  `ARCHITECTURE.md` (internals), `TOOLS.md` (the tool index), `INTEGRATION.md`
  (connecting hosts). `docs/TOOLS.md` is generated — `npm run docs:tools`.
