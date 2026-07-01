# Agent Notes

- Keep the server dependency-free unless there is a clear reason to add a runtime package.
- Use only the official `yandex_tracker_client` SDK for Yandex Tracker operations. Do not add direct HTTP requests, custom REST endpoint wrappers, `urllib`, `requests`, or ad hoc API calls for Tracker behavior; route new Tracker capabilities through SDK objects such as `TrackerClient`, `client.issues[...]`, issue collections, comments, and transitions.
- Do not print logs to stdout; MCP stdio stdout must contain only JSON-RPC messages.
- Run `python3 -m unittest discover -s tests` after changing behavior.
- See `docs/` for the full guide: `EXTENDING.md` (adding tools, rules, scaling),
  `ARCHITECTURE.md` (internals), `TOOLS.md` (tool schemas), `INTEGRATION.md`
  (connecting hosts). Keep `docs/TOOLS.md` in sync with `TOOLS` in `server.py`.
