# Extending & scaling

For anyone adding tools or changing behavior. Read [ARCHITECTURE.md](ARCHITECTURE.md)
first for the map of the request lifecycle.

## Non-negotiable rules

These are load-bearing; a change that breaks one is a regression.

1. **Official SDK only.** Route every Tracker capability through
   `yandex_tracker_client` objects (`TrackerClient`, `client.issues[...]`,
   issue collections, `.comments`, `.transitions`). Do **not** add `requests`,
   `urllib`, raw HTTP, or ad-hoc REST wrappers.
2. **Never write to stdout.** stdout is the JSON-RPC channel. Diagnostics go to
   stderr (`print(..., file=sys.stderr)`). A stray `print()` corrupts the stream
   and the host will drop the connection.
3. **Keep dependencies minimal.** The runtime dependencies are `mcp` (the
   official MCP SDK) and `yandex_tracker_client`. Add another only with a clear
   reason.
4. **Run the tests after any behavior change:**
   ```sh
   python3 -m unittest discover -s tests
   ```

## Adding a tool

A tool spans two edits plus tests. Follow the existing patterns.

1. **SDK client layer — add the capability.** Add a method to `YandexTrackerClient`
   that performs the SDK work inside a closure passed to `_call_sdk`, and wrap
   the return value in `_to_plain` so it serializes:

   ```python
   def link_issues(self, issue_key: str, target_key: str, relationship: str) -> Any:
       def link(client: Any) -> Any:
           issue = client.issues[issue_key]
           return issue.links.create(relationship=relationship, issue=target_key)

       return _to_plain(self._call_sdk(link))
   ```

   `_call_sdk` turns SDK exceptions into `TrackerApiError`; raise `ValueError`
   for bad arguments you detect yourself (it maps to a tool error, not a crash).

2. **MCP server layer — add the `@tool` function.** Write a typed function named
   `tracker_<verb>_<noun>`; FastMCP derives the `inputSchema` from its
   parameters. Required arguments have no default; optional ones default to
   `None`/a literal. Attach parameter descriptions with
   `Annotated[..., Field(description="…")]` and the tool description as the
   docstring. Return the raw client payload — the `@tool` wrapper serializes it
   to compact JSON and maps domain errors:

   ```python
   @tool
   def tracker_link_issues(
       issue_key: str,
       relationship: Annotated[str, Field(description="Link type, e.g. relates.")],
       target_issue: str,
   ) -> Any:
       """Create a link between two Yandex Tracker issues."""
       return get_client().link_issue(issue_key, relationship, target_issue)
   ```

3. **`docs/TOOLS.md` — document it.** Add the argument table so integrators see
   it without reading code.

4. **`tests/` — cover it.** Extend the fakes in `tests/test_client.py`
   (`FakeIssue`, `FakeCollection`, …) and add a `mcp.call_tool(...)` assertion in
   `tests/test_server.py` against the `FakeClient`.

## Testing model

The suite (`tests/`) runs entirely on fakes — no network, no real token.

- **`test_server.py`** injects a `FakeClient` by pointing the client singleton
  at it (`server._client = None; server._client_factory = lambda: fake`) and
  asserts on protocol behavior via `mcp.list_tools()` / `mcp.call_tool(...)`:
  tool listing, no output schema, tool-call results, and error mapping (domain
  errors surface as `ToolError`).
- **`test_client.py`** injects a fake SDK client via
  `YandexTrackerClient(tracker_client=…)` and asserts on SDK usage, config
  parsing, transition matching, and `_to_plain` serialization.

When you add a tool, mirror both layers: a client-level test that it calls the
right SDK method, and a server-level test that the tool name dispatches to it.

## Scaling notes

- **Cached client.** `get_client()` builds one `YandexTrackerClient` lazily and
  reuses it for the life of the process, so the SDK's `requests.Session`
  (connection pool) is shared across tool calls. The env is read once, at first
  use. If you ever need per-request config, swap the singleton for a keyed cache
  rather than reaching for a different HTTP layer.
- **More primitives.** Read-only context is already exposed as `@mcp.resource`
  functions under `tracker://` (issue snapshot + reference dictionaries), wrapped
  by the local `resource` helper (compact JSON + `ResourceError` mapping) — add
  more the same way. To add templated prompts, use `@mcp.prompt()`; FastMCP
  surfaces them as host slash commands.
- **Transport.** FastMCP owns JSON-RPC framing, batching, and the stdio loop.
  There is no read loop to maintain here.
- **Serialization edge cases.** If a new SDK return type does not expose
  `.as_dict()` and isn't a container/primitive, `_to_plain` stringifies it.
  Prefer teaching `_to_plain` (or the method) to unwrap it into structured JSON
  over returning an opaque string.
- **Auth schemes.** OAuth vs IAM is decided in `_tracker_client_kwargs` by
  `auth_scheme`. Add new schemes there, not in the tool handlers.
