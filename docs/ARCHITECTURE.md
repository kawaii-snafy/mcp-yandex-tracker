# Architecture

For maintainers and anyone scaling the server. If you only want to *use* the
tools, see [TOOLS.md](TOOLS.md); to *connect* it, see [INTEGRATION.md](INTEGRATION.md).

## Layout

```
yandex_tracker_mcp_server/
├── __init__.py    # package version (__version__)
├── __main__.py    # main() -> serve_stdio(); enables `python -m yandex_tracker_mcp_server`
├── server.py      # MCP protocol: tool schemas, dispatch, stdio loop, error mapping
└── client.py      # SDK wrapper: config, calls, transition matching, serialization
tests/             # unittest suite over fakes (no network)
```

Entry points, all reaching `serve_stdio()`:

- console script `mcp-yandex-tracker` (declared in `pyproject.toml`)
- `python -m yandex_tracker_mcp_server`
- `python run_server.py`

## Request lifecycle

```
stdin line
  └─ serve_stdio()                     # server.py
       ├─ json.loads(line)             # dict = single, list = JSON-RPC batch
       ├─ _handle_stdio_item(...)      # per element; non-dict -> -32600
       └─ McpServer.handle_message()
            ├─ no "id"  -> _handle_notification (returns nothing)
            └─ has "id" -> _dispatch(method, params)
                              ├─ initialize / ping / tools/list
                              ├─ resources/list / prompts/list  (empty)
                              └─ tools/call -> _call_tool()
                                   ├─ client = client_factory()   # fresh per call
                                   ├─ handlers[name](client, args)# server.py -> client.py
                                   └─ _tool_result / _tool_error
```

Responses are written back as newline-delimited JSON (compact separators). A
batch request produces a JSON array of responses; notifications and empty
batches produce no line at all.

## `server.py` — the protocol layer

- **`TOOLS`** — the list of tool descriptors (name, description, `inputSchema`).
  `_schema()` builds strict object schemas (`additionalProperties: false`).
  This is the single source of truth for tool shapes; keep [TOOLS.md](TOOLS.md)
  in sync.
- **`McpServer._dispatch`** — routes MCP methods. Supported: `initialize`,
  `ping`, `tools/list`, `tools/call`, `resources/list`, `prompts/list`. Anything
  else raises and becomes a JSON-RPC error. `initialize` advertises
  `protocolVersion` `2025-03-26` and a tools capability with
  `listChanged: false`.
- **`McpServer._call_tool`** — maps a tool name to a lambda that calls the
  matching `YandexTrackerClient` method, then wraps the result. `_required()`
  enforces mandatory arguments (empty string counts as missing).
- **Two error channels** — deliberately separate:
  - *Tool errors* (`_tool_error`, `isError: true`): raised by
    `TrackerApiError`, `TrackerConfigError`, or `ValueError` during a
    `tools/call`. The JSON-RPC call itself still succeeds.
  - *Protocol errors* (`_error_payload`, JSON-RPC `error`): parse errors
    (`-32700`), bad params/`ValueError` at dispatch (`-32602`), invalid request
    (`-32600`), everything else internal (`-32603`).
- **`serve_stdio`** — the read loop. Isolates per-item failures so one bad
  element in a batch cannot suppress the others' responses.

## `client.py` — the SDK layer

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

- **Official SDK only.** All Tracker access goes through `yandex_tracker_client`
  objects. No `requests`/`urllib`/raw HTTP — see [EXTENDING.md](EXTENDING.md).
- **stdout is protocol-only.** Diagnostics go to stderr (e.g. the notification
  fallback in `_handle_notification`). Anything printed to stdout corrupts the
  MCP stream.
- **Minimal dependencies.** The only runtime dependency is the SDK.
- **Stateless per call.** A new `YandexTrackerClient` (and thus a new SDK
  client, reading env afresh) is built for each `tools/call`. See the scaling
  note in [EXTENDING.md](EXTENDING.md) if this becomes a hotspot.
- **Testability by injection.** `McpServer` takes a `client_factory` and
  `YandexTrackerClient` takes a `tracker_client` / `tracker_client_factory`, so
  the whole stack runs against fakes with no network.
