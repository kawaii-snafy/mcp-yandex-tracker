# Architecture

For maintainers and anyone scaling the server. If you only want to *use* the
tools, see [TOOLS.md](TOOLS.md); to *connect* it, see [INTEGRATION.md](INTEGRATION.md).

## Layout

The whole server is a single top-level module:

```
mcp_yandex_tracker.py   # everything: SDK client layer + FastMCP tools + main()
tests/                  # unittest suite over fakes (no network)
```

Inside `mcp_yandex_tracker.py`, two clearly-commented sections:

- **SDK client layer** — `YandexTrackerClient` and helpers: config, SDK calls,
  transition matching, serialization.
- **MCP server layer** — the `FastMCP` instance, the `@tool` wrapper, the client
  lifecycle, and the 35 `@tool` functions.

Entry points, all reaching `main()` (which calls `mcp.run(transport="stdio")`):

- console script `mcp-yandex-tracker` (declared in `pyproject.toml`)
- `python -m mcp_yandex_tracker`
- `python mcp_yandex_tracker.py`

## Protocol layer: the official MCP SDK

The JSON-RPC framing, stdio transport (`stdio_server`, UTF-8 pinned), lifecycle
(`initialize` handshake, capability negotiation), and `tools/list` / `tools/call`
routing are all provided by the SDK's `FastMCP`. We do **not** hand-roll them.

- A single module-level `mcp = FastMCP("mcp-yandex-tracker")` holds the server.
- Every tool is a plain typed Python function decorated with the local `@tool`
  wrapper (see below). FastMCP derives each tool's `inputSchema` from the
  function's type hints and `Annotated[..., Field(description=...)]` metadata,
  and its description from the docstring.
- `initialize` requires the standard MCP handshake before any `tools/call` —
  the SDK enforces this (a bare `tools/list` before `initialize` returns
  `-32602`).

### The `@tool` wrapper (MCP server layer)

`tool` is a thin decorator around `mcp.tool(structured_output=False)` that every
handler uses. It does two jobs:

- **Serialize once, compact.** The handler returns the raw client payload; the
  wrapper runs it through `_dump` (`json.dumps(..., ensure_ascii=False,
  separators=(",", ":"))`) into a single `TextContent` block.
  `structured_output=False` tells FastMCP not to also emit a duplicating
  `structuredContent` block or an output schema — this keeps responses
  token-lean and Cyrillic intact.
- **Map domain errors.** `TrackerApiError`, `TrackerConfigError`, and
  `ValueError` raised by the handler become a `ToolError`, which the SDK returns
  as a `tools/call` result with `isError: true` and a plain-text message (the
  JSON-RPC call itself still succeeds). `functools.wraps` preserves the handler
  signature so schema derivation still sees the typed parameters.

### Client lifecycle

- `get_client()` builds one `YandexTrackerClient` lazily and caches it in the
  module-level `_client`. The Tracker SDK opens a `requests.Session` (connection
  pool) on construction, so a single instance reused across tool calls keeps
  HTTP keep-alive instead of rebuilding a session every call.
- `_client_factory` (defaults to `YandexTrackerClient`) stays swappable so tests
  inject a fake by setting `server._client = None; server._client_factory = …`.

### Resources

Alongside the tools, a handful of `@mcp.resource(...)` functions expose
read-only context under the `tracker://` scheme: one template,
`tracker://issue/{key}`, plus static reference dictionaries
(`tracker://statuses`, `priorities`, `issue-types`, `fields`, `link-types`,
`queues`). They go through the same `get_client()` and serialize to compact
JSON (`application/json`) via the local `resource` wrapper. (On a failed read the
`ResourceError` a client sees is produced by FastMCP's resource path, which
re-wraps any handler error — the wrapper's own error mapping is just parity with
the tool path; its real job here is the compact serialization.)

Resources are a **user**-facing surface: in Claude Code the user `@`-mentions
one (e.g. `@yandex-tracker:tracker://issue/TEST-123`) to attach it as context.
The agent does not read them autonomously mid-task — the tools remain its path
to the same data, so resources are additive, never a replacement.

## SDK client layer

- **`TrackerConfig`** — frozen dataclass; `from_env()` reads the environment and
  validates that a token and one org id are present. `_split_base_url` peels a
  `/v2` or `/v3` suffix into the SDK's `api_version`. `_tracker_client_kwargs`
  maps config to SDK kwargs and chooses `token` vs `iam_token` by auth scheme.
- **`YandexTrackerClient`** — thin methods over the SDK
  (`client.issues[...]`, `.find`, `.create`, `.comments`, `.transitions`).
  Every method funnels through `_call_sdk`, which converts SDK-raised exceptions
  into `TrackerApiError` (preserving status and payload) while letting
  `ValueError` through unchanged.
- **Transition matching** — `_select_transition` / `_transition_matches`
  compare a requested status against transition id, display, and destination
  status id/key/display (normalized: `str().strip().casefold()`). It refuses
  ambiguous matches instead of guessing.
- **`_to_plain`** — recursively turns SDK objects into JSON-safe values:
  unwraps `.as_dict()`, recurses through dict/list/tuple/set, passes primitives
  through, and stringifies anything else. This is what makes tool payloads
  serializable regardless of SDK return types.

## Design constraints

- **Official SDKs only.** The MCP layer is the `mcp` SDK's `FastMCP`; all Tracker
  access goes through `yandex_tracker_client` objects. No `requests`/`urllib`/raw
  HTTP for Tracker behavior — see [EXTENDING.md](EXTENDING.md).
- **stdout is protocol-only.** FastMCP writes JSON-RPC to stdout and routes its
  own logging to stderr. Anything you print to stdout corrupts the MCP stream.
- **Minimal dependencies.** Runtime dependencies are `mcp` and the Tracker SDK.
- **Token-lean responses.** Tools return a single compact-JSON text block
  (`structured_output=False`); no output schema, no duplicating
  `structuredContent`.
- **Testability by injection.** The client singleton is built through
  `_client_factory`, and `YandexTrackerClient` takes a `tracker_client` /
  `tracker_client_factory`, so the whole stack runs against fakes with no
  network.
