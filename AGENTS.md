# Agent Notes

- **The official documentation is the only source of truth for Yandex Tracker.**
  Index of every page: <https://yandex.ru/support/tracker/en/llms.txt>; any page
  is markdown by appending `.md`
  (`https://yandex.ru/support/tracker/en/api/<section>/<page>.md`). Blogs, Stack
  Overflow, the old `yandex_tracker_client` SDK, observed production behavior and
  model memory are **not** sources. A path, parameter or field that is not on a
  page from `llms.txt` does not go into the code.
- **Only documented REST API v3 endpoints.** Tracker is reached with plain
  `requests` calls through `Tracker.request()` in `mcp_yandex_tracker/client.py`.
  Do not add a second HTTP path, an SDK, or an abstraction layer on top of
  `requests`. The MCP side stays on the official `mcp` SDK (`MCPServer`).
- **One tool per endpoint, nothing in between.** Parameter names are the API's
  own (`perPage`, `expand`, `markupType`), and the response is returned exactly
  as Tracker sent it — no reshaping, no filtering, no client-side pagination.
- Keep runtime dependencies minimal: only `mcp` and `requests` unless there is a
  clear reason to add another.
- Do not print logs to stdout; MCP stdio stdout must contain only JSON-RPC
  messages (MCPServer already routes its logging to stderr).
- Run `python3 -m unittest discover -s tests` after changing behavior.
- See `docs/` for the full guide: `EXTENDING.md` (adding tools, rules, scaling),
  `ARCHITECTURE.md` (internals), `TOOLS.md` (the tool index), `INTEGRATION.md`
  (connecting hosts). Tools live in `mcp_yandex_tracker/tools/<section>.py`,
  one file per documentation section — keep `docs/TOOLS.md` in sync.
