# Agent Notes

- Built on the official MCP Python SDK (`mcp`, `MCPServer`). Keep runtime
  dependencies minimal: only `mcp` and `yandex_tracker_client` unless there is a
  clear reason to add another.
- Use only the official `yandex_tracker_client` SDK for Yandex Tracker operations. Do not add direct HTTP requests, custom REST endpoint wrappers, `urllib`, `requests`, or ad hoc API calls for Tracker behavior; route new Tracker capabilities through SDK objects such as `TrackerClient`, `client.issues[...]`, issue collections, comments, and transitions.
- Do not print logs to stdout; MCP stdio stdout must contain only JSON-RPC messages (MCPServer already routes its logging to stderr).
- Never materialize a Tracker collection with `list()`: they are
  cursor-paginated and iterating one follows every `next` link, so
  `list(client.users.get_all())` fetches the whole directory. Use
  `_take(collection, limit)` at every call site.
- Responses are projected, not raw: reads return a compact projection, writes
  return a receipt. Use `_slim_ref` / `_project` / `_slim_issue` /
  `_issue_receipt` / `_slim_link`; add `full: bool = False` only where the
  untrimmed payload is content a caller might actually need.
- Run `python3 -m unittest discover -s tests` after changing behavior.
- See `docs/` for the full guide: `EXTENDING.md` (adding tools, rules, scaling),
  `ARCHITECTURE.md` (internals), `TOOLS.md` (tool schemas), `INTEGRATION.md`
  (connecting hosts). The whole server is one module, `mcp_yandex_tracker.py`;
  tools are typed functions decorated with `@read_tool` / `@additive_tool` /
  `@destructive_tool` there — that choice is the tool's MCP annotations, and the
  suite fails until a new tool is classified. Keep `docs/TOOLS.md` in sync.
