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
3. **Keep dependencies minimal.** The SDK is the only runtime dependency. Add
   one only with a clear reason.
4. **Run the tests after any behavior change:**
   ```sh
   python3 -m unittest discover -s tests
   ```

## Adding a tool

A tool spans three edits plus tests. Follow the existing patterns.

1. **`client.py` — add the capability.** Add a method to `YandexTrackerClient`
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

2. **`server.py` — declare the schema.** Add an entry to `TOOLS` using
   `_schema(properties, required)`. Keep `additionalProperties: false` (it is
   baked into `_schema`) and name the tool `tracker_<verb>_<noun>`.

3. **`server.py` — wire the handler.** Add a lambda to the `handlers` dict in
   `_call_tool`, using `_required(a, "x")` for mandatory args and `a.get("x")`
   for optional ones.

4. **`docs/TOOLS.md` — document it.** Add the argument table so integrators see
   it without reading code.

5. **`tests/` — cover it.** Extend the fakes in `tests/test_client.py`
   (`FakeIssue`, `FakeCollection`, …) and add a `tools/call` assertion in
   `tests/test_server.py` against the `FakeClient`.

## Testing model

The suite (`tests/`) runs entirely on fakes — no network, no real token.

- **`test_server.py`** injects a `FakeClient` via `McpServer(client_factory=…)`
  and asserts on protocol behavior: capabilities, tool listing, tool-call
  results, the two error channels, stdio framing, batch handling, notifications.
- **`test_client.py`** injects a fake SDK client via
  `YandexTrackerClient(tracker_client=…)` and asserts on SDK usage, config
  parsing, transition matching, and `_to_plain` serialization.

When you add a tool, mirror both layers: a client-level test that it calls the
right SDK method, and a server-level test that the tool name dispatches to it.

## Scaling notes

- **Per-call client construction.** `_call_tool` builds a fresh
  `YandexTrackerClient` — and therefore a fresh SDK client — on every
  `tools/call`, re-reading the environment each time. This keeps the server
  stateless and simple. If call volume makes SDK/session setup a bottleneck,
  cache the client on the `McpServer` (guard it against config changes) rather
  than reaching for a different HTTP layer.
- **New MCP methods.** To support more of the protocol (resources, prompts,
  logging), extend `McpServer._dispatch`. Unhandled methods currently raise and
  surface as JSON-RPC errors.
- **Batching.** `serve_stdio` already handles JSON-RPC batches and isolates
  per-item failures; preserve that isolation if you touch the read loop.
- **Serialization edge cases.** If a new SDK return type does not expose
  `.as_dict()` and isn't a container/primitive, `_to_plain` stringifies it.
  Prefer teaching `_to_plain` (or the method) to unwrap it into structured JSON
  over returning an opaque string.
- **Auth schemes.** OAuth vs IAM is decided in `_tracker_client_kwargs` by
  `auth_scheme`. Add new schemes there, not in the tool handlers.
