# Agent Notes

- Built on the official MCP Python SDK (`mcp`, `FastMCP`). Keep runtime
  dependencies minimal: only `mcp` and `yandex_tracker_client` unless there is a
  clear reason to add another.
- Use only the official `yandex_tracker_client` SDK for Yandex Tracker operations. Do not add direct HTTP requests, custom REST endpoint wrappers, `urllib`, `requests`, or ad hoc API calls for Tracker behavior; route new Tracker capabilities through SDK objects such as `TrackerClient`, `client.issues[...]`, issue collections, comments, and transitions.
- Do not print logs to stdout; MCP stdio stdout must contain only JSON-RPC messages (FastMCP already routes its logging to stderr).
- Run `python3 -m unittest discover -s tests` after changing behavior.
- See `docs/` for the full guide: `EXTENDING.md` (adding tools, rules, scaling),
  `ARCHITECTURE.md` (internals), `TOOLS.md` (tool schemas), `INTEGRATION.md`
  (connecting hosts). The whole server is one module, `mcp_yandex_tracker.py`;
  tools are `@tool`-decorated functions there — keep `docs/TOOLS.md` in sync.
