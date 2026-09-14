# Architecture

For maintainers and anyone scaling the server. If you only want to *use* the
tools, see [TOOLS.md](TOOLS.md); to *connect* it, see [INTEGRATION.md](INTEGRATION.md).

## Layout

```
mcp_yandex_tracker/
  __init__.py       # re-exports and, by importing them, registers everything below
  __main__.py       # python -m mcp_yandex_tracker
  _version.py       # the version literal pyproject reads statically
  client.py         # TrackerConfig, the errors, and Tracker.request() — all of Tracker
  server.py         # the MCPServer instance, the @tool / @resource wrappers, main()
  resources.py      # the read-only tracker:// surface
  tools/
    __init__.py     # imports every module below; that import *is* the registration
    issues.py  queues.py  boards.py  entities.py  admin.py  users.py
tests/              # unittest suite over a fake requests.Session (no network)
```

Tool modules mirror the sections of the official documentation, so a doc page maps
to exactly one code file.

Entry points, all reaching `main()` (which calls `mcp.run(transport="stdio")`):

- console script `mcp-yandex-tracker` (declared in `pyproject.toml`)
- `python -m mcp_yandex_tracker`

## Protocol layer: the official MCP SDK

The JSON-RPC framing, stdio transport (`stdio_server`, UTF-8 pinned), lifecycle
(`initialize` handshake, capability negotiation), and `tools/list` / `tools/call`
routing are all provided by the SDK's `MCPServer`. We do **not** hand-roll them.

- A single module-level `mcp = MCPServer("mcp-yandex-tracker", version=__version__)`
  in `server.py` holds the server. `MCPServer` accepts a `version` kwarg directly,
  so `serverInfo` advertises our package version instead of the `mcp` SDK's.
- Every tool is a plain typed Python function decorated with the local `@tool`
  wrapper (see below). MCPServer derives each tool's `inputSchema` from the
  function's type hints and `Annotated[..., Field(description=…)]` metadata, and
  its description from the docstring.
- `initialize` requires the standard MCP handshake before any `tools/call` — the
  SDK enforces this (a bare `tools/list` before `initialize` returns `-32602`).

### The `@tool` wrapper

`tool` is a thin decorator around `mcp.tool(structured_output=False)` that every
handler uses. It does two jobs:

- **Serialize once, compact.** The handler returns the raw Tracker payload; the
  wrapper runs it through `_dump` (`json.dumps(..., ensure_ascii=False,
  separators=(",", ":"))`) into a single `TextContent` block.
  `structured_output=False` tells MCPServer not to also emit a duplicating
  `structuredContent` block or an output schema — this keeps responses token-lean
  and Cyrillic intact.
- **Map domain errors.** `TrackerApiError`, `TrackerConfigError`, and `ValueError`
  raised by the handler become a `ToolError`, which the SDK returns as a
  `tools/call` result with `isError: true` and a plain-text message (the JSON-RPC
  call itself still succeeds). `functools.wraps` preserves the handler signature
  so schema derivation still sees the typed parameters.

### Client lifecycle

- `get_client()` builds one `Tracker` lazily and caches it in the module-level
  `_client`. `Tracker` opens a `requests.Session` (connection pool) on
  construction, so a single instance reused across tool calls keeps HTTP
  keep-alive instead of rebuilding a session every call.
- `_client_factory` (defaults to `Tracker`) stays swappable so tests inject a fake
  by setting `server._client = None; server._client_factory = …`.

### Resources

`resources.py` exposes read-only context under the `tracker://` scheme: one
template, `tracker://issue/{key}`, plus static reference dictionaries
(`tracker://statuses`, `priorities`, `issue-types`, `fields`, `queues`). They go
through the same `get_client()` and serialize to compact JSON
(`application/json`) via the local `resource` wrapper. (On a failed read
MCPServer re-raises the wrapper's `ResourceError` untouched, so the wrapper's
error mapping — not just its compact serialization — is what carries the Tracker
message across. That pass-through is why the dependency floor is mcp 2.1; 2.0
replaced the detail with a generic `Error reading resource <uri>`.)

Resources are a **user**-facing surface: in Claude Code the user `@`-mentions one
(e.g. `@yandex-tracker:tracker://issue/TEST-123`) to attach it as context. The
agent does not read them autonomously mid-task — the tools remain its path to the
same data, so resources are additive, never a replacement.

## HTTP client layer

`client.py` is the entire Tracker side, and it is deliberately small.

- **`TrackerConfig`** — frozen dataclass; `from_env()` reads the environment and
  validates that a token and one org id are present. `api_root` always ends in
  `/v3`: the version belongs to the path this client builds, so a leftover `/v2`
  or `/v3` suffix on `YANDEX_TRACKER_BASE_URL` is stripped. `headers()` picks
  `OAuth` vs `Bearer` from `auth_scheme` and sends exactly one org header —
  `X-Cloud-Org-Id` when a cloud org id is set, `X-Org-Id` otherwise.
- **`Tracker.request(method, path, params=, json=, files=)`** — the only way out.
  Builds `{api_root}{path}`, sends it on the shared session with the configured
  timeout, and returns the decoded body untouched. `Tracker.upload()` and
  `Tracker.download()` are the two variants the wire format forces: multipart in,
  streamed bytes out.
- **Errors** — a transport failure becomes `TrackerApiError(0, "Failed to reach
  Yandex Tracker: …")`; any non-2xx becomes `TrackerApiError(status, message,
  payload)`. The error body shape is *not* documented anywhere in the API
  reference, so `_error_message` reads `errorMessages` / `errors` best-effort and
  falls back to the raw body and then the HTTP reason.
- **Retries** — an `HTTPAdapter` with `Retry` on 429 and 5xx, for idempotent
  methods only. `error-codes.md` documents that 429 exists but specifies neither a
  quota nor a `Retry-After` header, so the backoff is ours.
- **`given(**kwargs)`** — drops the arguments a caller left unset. Every tool
  builds its query string and body with it, so an omitted optional parameter is
  absent from the request rather than sent as `null`.

## Design constraints

- **The official documentation is the only source of truth for Tracker.** Index:
  <https://yandex.ru/support/tracker/en/llms.txt>; any page becomes markdown by
  appending `.md`. Not the old SDK, not blogs, not observed behavior. Every tool's
  docstring links to the page it was written from — see [EXTENDING.md](EXTENDING.md).
- **One tool per documented endpoint.** The API's parameter names go in, the API's
  JSON comes out. No projections, no renaming, no client-side pagination or
  filtering: anything the server invents is a place where it can drift from
  Tracker and has to be explained to the agent separately.
- **stdout is protocol-only.** MCPServer writes JSON-RPC to stdout and routes its
  own logging to stderr. Anything you print to stdout corrupts the MCP stream.
- **Minimal dependencies.** Runtime dependencies are `mcp` and `requests`.
- **Token-lean responses.** Tools return a single compact-JSON text block
  (`structured_output=False`); no output schema, no duplicating
  `structuredContent`. Responses are trimmed with the API's own `fields` and
  `expand` parameters, never by us.
- **Testability by injection.** The client singleton is built through
  `_client_factory`, and `Tracker` takes a `session`, so the whole stack runs
  against a fake `requests.Session` with no network.
