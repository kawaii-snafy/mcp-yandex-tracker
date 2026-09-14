# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A **stdio MCP server** that exposes the Yandex Tracker REST API v3 to LLM agents.
It is a deliberately thin wrapper: **one tool per documented endpoint**, the API's
own parameter names on the way in, the API's own JSON on the way out. It is built
on the official MCP Python SDK (`MCPServer`) and reaches Tracker with plain
`requests` calls. There is no HTTP/SSE transport — one process serves one client
over stdin/stdout.

## The rule that governs every other decision

**The official documentation is the only source of truth for Yandex Tracker.**

- Index of every page: <https://yandex.ru/support/tracker/en/llms.txt>
- Any page is markdown by appending `.md`:
  `https://yandex.ru/support/tracker/en/api/<section>/<page>.md`

Blogs, Stack Overflow, the `yandex_tracker_client` SDK this server used to wrap,
observed production behavior, and model memory are **not** sources. A path,
parameter or field that is not on a page from `llms.txt` does not go into the
code. Before touching a tool, open its page — every tool's docstring links to it.
If something is genuinely needed and genuinely undocumented, that is a deviation:
record it in `docs/TOOLS.md` with the reason.

## Commands

```sh
# Setup (creates .venv, installs the package + deps editable)
python3 -m venv .venv && .venv/bin/python -m pip install -e .

# Run the full test suite (no network, all fakes)
.venv/bin/python -m unittest discover -s tests

# Run a single test
.venv/bin/python -m unittest tests.test_client.RequestTests.test_builds_a_v3_url_and_passes_the_timeout

# Run the server (either; both call main() -> mcp.run("stdio"))
.venv/bin/mcp-yandex-tracker
.venv/bin/python -m mcp_yandex_tracker
```

Always run the tests after changing behavior. There is no separate lint step.

Smoke-test without a host — MCP requires the `initialize` handshake before any
other request, so send it (and the `initialized` notification) first:

```sh
{ printf '%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{},"clientInfo":{"name":"probe","version":"1"}}}' \
  '{"jsonrpc":"2.0","method":"notifications/initialized"}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/list"}'
  sleep 5
} | YANDEX_TRACKER_TOKEN="..." YANDEX_TRACKER_CLOUD_ORG_ID="..." .venv/bin/mcp-yandex-tracker
```

The trailing `sleep` keeps stdin open: `printf` alone closes it immediately and
the server shuts down on EOF, often before it has answered `tools/list` — you
then get only the `initialize` reply.

## Environment

`YANDEX_TRACKER_TOKEN` plus exactly one org id (`YANDEX_TRACKER_CLOUD_ORG_ID`
for cloud orgs, or `YANDEX_TRACKER_ORG_ID`) are required; a missing one surfaces
as a clean tool error, not a crash. Optional: `YANDEX_TRACKER_AUTH_SCHEME`
(`OAuth` default, `Bearer` for IAM tokens), `YANDEX_TRACKER_BASE_URL` (host only
— the client always appends `/v3`), `YANDEX_TRACKER_TIMEOUT`.

## Architecture

```
mcp_yandex_tracker/
  client.py      # TrackerConfig, the errors, Tracker.request() — the whole Tracker side
  server.py      # the MCPServer instance, the @tool / @resource wrappers, main()
  resources.py   # the read-only tracker:// surface
  tools/         # issues.py queues.py boards.py entities.py admin.py users.py
```

`MCPServer` owns the JSON-RPC framing, stdio transport, UTF-8, lifecycle, and
`tools/list` / `tools/call` routing — none of that is hand-rolled here. Tool
modules mirror the sections of the documentation, so a doc page maps to exactly
one code file.

Three cross-cutting mechanisms to know before editing:

- **`Tracker.request(method, path, params=, json=, files=, headers=)`** is the
  only way out. It builds `{base_url}/v3{path}`, sends it on the shared
  `requests.Session`, maps a transport failure to `TrackerApiError(0, …)` and any
  non-2xx to `TrackerApiError(status, message, payload)`, and returns the decoded
  body **untouched**. `upload()` and `download()` are the two variants the wire
  format forces. The error-body shape is undocumented, so message extraction is
  best-effort with a fallback to the raw body.
- **The `@tool` wrapper** (not `mcp.tool` directly). It serializes the handler's
  return value to a single compact-JSON `TextContent` via
  `structured_output=False` — this is deliberate: it keeps responses token-lean
  (no duplicating `structuredContent`, no output schema) and Cyrillic intact. It
  also maps `TrackerApiError` / `TrackerConfigError` / `ValueError` to a
  `ToolError`, which the SDK returns as an `isError: true` result (the JSON-RPC
  call still succeeds). Do not bypass it.
- **Cached client singleton.** `get_client()` builds one `Tracker` lazily (via the
  swappable `_client_factory`) and reuses it for the process, so the
  `requests.Session` connection pool is shared across calls. Tests inject a fake
  by setting `server._client = None; server._client_factory = lambda: fake`.

## Non-negotiable rules

- **Documentation first** — the rule above. No undocumented endpoints, no guessed
  parameters, no knowledge carried over from the old SDK.
- **One tool per endpoint, nothing in between.** No projections, no renaming, no
  client-side pagination, no convenience tools that compose several calls. If a
  response is too big, trim it with the API's own `fields` / `expand`.
- **No second HTTP path.** All Tracker access goes through `Tracker.request()`.
  Do not add an SDK or a wrapper layer on top of `requests`. Runtime deps stay at
  `mcp` + `requests`.
- **stdout is protocol-only.** MCPServer writes JSON-RPC to stdout and logs to
  stderr. Never `print()` to stdout — it corrupts the MCP stream.
- **Keep `docs/TOOLS.md` in sync** with the tools when you change one.

## Adding a tool

Find the endpoint's page in `llms.txt`, read the `.md`, transcribe its parameters
into a `@tool` function in the matching `tools/` module (docstring = summary,
blank line, `<METHOD> /v3/<path>`, page URL), add the row to `docs/TOOLS.md`, and
add a row to the routing table in `tests/test_server.py`. See `docs/EXTENDING.md`
for the full pattern and the naming conventions.

## Further docs

`docs/` has the deep guides: `ARCHITECTURE.md` (internals), `EXTENDING.md`
(adding tools, scaling), `TOOLS.md` (the tool index), and `INTEGRATION.md`
(connecting hosts). `AGENTS.md` mirrors the non-negotiable rules above.
