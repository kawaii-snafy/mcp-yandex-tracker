# Agent Notes

- Keep the server dependency-free unless there is a clear reason to add a runtime package.
- Use only the official `yandex_tracker_client` SDK for Yandex Tracker operations. Do not add direct HTTP requests, custom REST endpoint wrappers, `urllib`, `requests`, or ad hoc API calls for Tracker behavior; route new Tracker capabilities through SDK objects such as `TrackerClient`, `client.issues[...]`, issue collections, comments, and transitions.
- Do not print logs to stdout; MCP stdio stdout must contain only JSON-RPC messages.
- Run `python3 -m unittest discover -s tests` after changing behavior.
