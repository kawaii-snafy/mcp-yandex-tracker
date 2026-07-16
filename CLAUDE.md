# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A single-file **stdio MCP server** that exposes Yandex Tracker to LLM agents. It
is built on the official MCP Python SDK (`FastMCP`) and reaches Tracker through
the official `yandex_tracker_client` SDK. There is no HTTP/SSE transport — one
process serves one client over stdin/stdout.

## Commands

```sh
# Setup (creates .venv, installs the package + deps editable)
python3 -m venv .venv && .venv/bin/python -m pip install -e .

# Run the full test suite (no network, all fakes)
.venv/bin/python -m unittest discover -s tests

# Run a single test
.venv/bin/python -m unittest tests.test_server.ServerTests.test_get_issue_returns_compact_text

# Run the server (any of these; all call main() -> mcp.run("stdio"))
.venv/bin/mcp-yandex-tracker
.venv/bin/python -m mcp_yandex_tracker
.venv/bin/python mcp_yandex_tracker.py
```

Always run the tests after changing behavior. There is no separate lint step.

Smoke-test without a host — MCP requires the `initialize` handshake before any
other request, so send it (and the `initialized` notification) first:

```sh
printf '%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{},"clientInfo":{"name":"probe","version":"1"}}}' \
  '{"jsonrpc":"2.0","method":"notifications/initialized"}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' \
| YANDEX_TRACKER_TOKEN="..." YANDEX_TRACKER_CLOUD_ORG_ID="..." .venv/bin/mcp-yandex-tracker
```

## Environment

`YANDEX_TRACKER_TOKEN` plus exactly one org id (`YANDEX_TRACKER_CLOUD_ORG_ID`
for cloud orgs, or `YANDEX_TRACKER_ORG_ID`) are required; a missing one surfaces
as a clean tool error, not a crash. Optional: `YANDEX_TRACKER_AUTH_SCHEME`
(`OAuth` default, `Bearer` for IAM tokens), `YANDEX_TRACKER_BASE_URL`,
`YANDEX_TRACKER_TIMEOUT`.

## Architecture

Everything is one module, `mcp_yandex_tracker.py`, split into two
clearly-commented sections. `FastMCP` owns the JSON-RPC framing, stdio
transport, UTF-8, lifecycle, and `tools/list` / `tools/call` routing — none of
that is hand-rolled here.

- **MCP server layer** — the `mcp = FastMCP(...)` instance and 35
  `@tool`-decorated typed functions named `tracker_*`. FastMCP derives each
  tool's input schema from the function's type hints and
  `Annotated[..., Field(description=...)]` metadata, and its description from the
  docstring. Each tool body just calls a `YandexTrackerClient` method and
  returns the raw payload. A few `@mcp.resource("tracker://...")` functions sit
  alongside the tools (issue snapshot + reference dictionaries) as a *user*-facing
  `@`-mention surface — additive context, not a replacement for the tools the
  agent calls autonomously.
- **SDK client layer** — `YandexTrackerClient` wraps the Tracker SDK; every
  method funnels through `_call_sdk` (maps SDK/transport exceptions to
  `TrackerApiError`) and `_to_plain` (recursively serializes SDK objects to
  JSON-safe values, stripping transport noise like `self`/`cloudUid`).

Two cross-cutting mechanisms to know before editing:

- **The `@tool` wrapper** (not `mcp.tool` directly). It serializes the handler's
  return value to a single compact-JSON `TextContent` via
  `structured_output=False` — this is deliberate: it keeps responses token-lean
  (no duplicating `structuredContent`, no output schema) and Cyrillic intact. It
  also maps `TrackerApiError` / `TrackerConfigError` / `ValueError` to a
  `ToolError`, which the SDK returns as an `isError: true` result (the JSON-RPC
  call still succeeds). Do not bypass it.
- **Cached client singleton.** `get_client()` builds one `YandexTrackerClient`
  lazily (via the swappable `_client_factory`) and reuses it for the process, so
  the SDK's `requests.Session` connection pool is shared across calls. Tests
  inject a fake by setting `server._client = None; server._client_factory =
  lambda: fake` — there is no per-instance server object.

## Non-negotiable rules

- **Official SDKs only.** All Tracker access goes through `yandex_tracker_client`
  objects (`TrackerClient`, `client.issues[...]`, collections, comments,
  transitions). Do **not** add `requests`/`urllib`/raw HTTP or ad-hoc REST
  wrappers for Tracker behavior. Runtime deps stay at `mcp` +
  `yandex_tracker_client`.
- **stdout is protocol-only.** FastMCP writes JSON-RPC to stdout and logs to
  stderr. Never `print()` to stdout — it corrupts the MCP stream.
- **Keep `docs/TOOLS.md` in sync** with the `@tool` signatures when you change a
  tool.

## Adding a tool

Add a method to `YandexTrackerClient` (SDK work inside a `_call_sdk` closure,
result wrapped in `_to_plain`), then a `@tool`-decorated typed function that
calls it, then document it in `docs/TOOLS.md` and cover it in
`tests/test_client.py` (SDK-level) and `tests/test_server.py`
(`mcp.call_tool(...)` level). See `docs/EXTENDING.md` for the full pattern.

## Further docs

`docs/` has the deep guides: `ARCHITECTURE.md` (internals), `EXTENDING.md`
(adding tools, scaling), `TOOLS.md` (per-tool argument reference), and
`INTEGRATION.md` (connecting hosts). `AGENTS.md` mirrors the non-negotiable
rules above.
