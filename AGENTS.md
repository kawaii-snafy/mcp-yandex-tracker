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
- Keep runtime dependencies minimal: only `@modelcontextprotocol/server` and
  `zod`. HTTP is the built-in `fetch`; there is no HTTP library.
- **`any` is banned**, and so are `as` casts — the one that exists is in
  `src/tool.ts` and is explained there. Let types be inferred.
- Do not print logs to stdout; MCP stdio stdout must contain only JSON-RPC
  messages. Diagnostics go to stderr.
- **Bun does not type-check.** Run `bun run typecheck` (tsc) as well as
  `bun test` after changing behavior.
- See `docs/` for the full guide: `EXTENDING.md` (adding tools, rules, scaling),
  `ARCHITECTURE.md` (internals), `TOOLS.md` (the tool index), `INTEGRATION.md`
  (connecting hosts). `docs/TOOLS.md` is generated — `bun run docs:tools`.
