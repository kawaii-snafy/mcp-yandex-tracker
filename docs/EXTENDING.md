# Extending & scaling

For anyone adding tools or changing behavior. Read [ARCHITECTURE.md](ARCHITECTURE.md)
first for the map of the request lifecycle.

## Non-negotiable rules

These are load-bearing; a change that breaks one is a regression.

1. **The official documentation is the only source of truth for Yandex Tracker.**
   Index of every page: <https://yandex.ru/support/tracker/en/llms.txt>; any page
   is markdown by appending `.md`
   (`https://yandex.ru/support/tracker/en/api/<section>/<page>.md`). Blogs, Stack
   Overflow, the `yandex_tracker_client` SDK this server used to wrap, observed
   production behavior and model memory are **not** sources. A path, parameter or
   field that is not on a page from `llms.txt` does not go into the code. If a
   capability is genuinely needed and genuinely undocumented, that is a deviation:
   record it in [TOOLS.md](TOOLS.md) with the reason.
2. **Only documented REST API v3 endpoints.** Every call goes through
   `Tracker.request()` in `mcp_yandex_tracker/client.py`. Do not add a second HTTP
   path, an SDK, or an abstraction layer on top of `requests`. The MCP side stays
   on the official `mcp` SDK.
3. **One tool per endpoint, nothing in between.** The API's parameter names go in,
   the API's JSON comes out. No projections, no renaming, no client-side
   pagination, no convenience tools that compose several calls.
4. **Never write to stdout.** stdout is the JSON-RPC channel. Diagnostics go to
   stderr (`print(..., file=sys.stderr)`). A stray `print()` corrupts the stream
   and the host will drop the connection.
5. **Keep dependencies minimal.** The runtime dependencies are `mcp` (the official
   MCP SDK) and `requests`. Add another only with a clear reason.
6. **Run the tests after any behavior change:**
   ```sh
   python3 -m unittest discover -s tests
   ```

## Adding a tool

A tool is one endpoint, so adding one starts by opening its page.

1. **Find the page** in <https://yandex.ru/support/tracker/en/llms.txt> and read
   the `.md` version. Note the method, the exact path (including whether the doc
   writes a trailing slash), every query parameter, and every body field.
2. **Write the function** in the `mcp_yandex_tracker/tools/` module that matches
   the page's section. Transcribe the parameters — same names, documented types,
   descriptions taken from the page:

   ```python
   @tool
   def tracker_get_comments(
       issueId: NonEmptyStr,
       expand: Annotated[
           str | None, Field(description="Additional fields: attachments, html, all.")
       ] = None,
       perPage: Annotated[int | None, Field(description="Comments per page.")] = None,
   ) -> Any:
       """Get the comments for an issue.

       GET /v3/issues/{issueId}/comments
       https://yandex.ru/support/tracker/en/api/issues/get-comments.md
       """
       return get_client().request(
           "GET",
           f"/issues/{issueId}/comments",
           params=given(expand=expand, perPage=perPage),
       )
   ```

   The docstring is always: summary line, blank line, `<METHOD> /v3/<path>`, the
   page URL. MCPServer derives the `inputSchema` from the type hints and the
   `Field` descriptions, and the tool description from the docstring.

   Conventions the whole package follows:
   - Path placeholders become camelCase arguments (`<issue_ID>` → `issueId`).
   - `given(**kwargs)` drops what the caller left unset; use it for `params=` and
     `json=` alike, and omit the argument entirely when there is nothing to send.
   - Required parameters have no default; optional ones are
     `X | None = None` inside `Annotated[..., Field(description=…)]`.
   - When a page documents `If-Match: "<version>"`, add a trailing optional
     `version` argument and pass `headers=if_match(version)`. When it documents
     `version` as a query parameter, it belongs in `params=given(...)` instead.
   - `from` is a Python keyword: name that argument `from_` and put it into the
     params dict under `"from"`. This is the only name in the package that does
     not match the API.
   - Body too open-ended to enumerate (the page says "the same format as when
     editing issues")? Take one `fields: dict | None` and merge it last.
3. **`docs/TOOLS.md` — add the row.** Tool name, method, path, doc link. Do not
   copy Yandex's argument tables into it; the page is the reference.
4. **`tests/` — cover it.** Add a row to the routing table in
   `tests/test_server.py`: arguments in, `(METHOD, path, params, body)` out.

## Testing model

The suite (`tests/`) runs entirely on fakes — no network, no real token.

- **`tests/test_client.py`** injects a fake `requests.Session` via
  `Tracker(config=…, session=…)` and asserts on the transport: URL building, auth
  and org headers, non-2xx → `TrackerApiError`, `204` → `None`, transport failure
  → status-0 error, streamed download, multipart upload.
- **`tests/test_server.py`** injects a fake `Tracker` by pointing the client
  singleton at it (`server._client = None; server._client_factory = lambda: fake`)
  and asserts on protocol behavior via `mcp.list_tools()` / `mcp.call_tool(...)`.
  Its centerpiece is one table with a row per tool, mapping arguments to the HTTP
  call they must produce — that is what keeps the tool surface honest.

## Scaling notes

- **Cached client.** `get_client()` builds one `Tracker` lazily and reuses it for
  the life of the process, so the `requests.Session` connection pool is shared
  across tool calls. The environment is read once, at first use. If you ever need
  per-request config, swap the singleton for a keyed cache rather than reaching
  for a different HTTP layer.
- **More primitives.** Read-only context is exposed as `@resource` functions in
  `mcp_yandex_tracker/resources.py`, wrapped by the local `resource` helper
  (compact JSON + `ResourceError` mapping) — add more the same way. To add
  templated prompts, use `@mcp.prompt()`; MCPServer surfaces them as host slash
  commands.
- **Transport.** MCPServer owns JSON-RPC framing, batching, and the stdio loop.
  There is no read loop to maintain here.
- **Response size.** Responses are raw Tracker JSON, and issue objects are large.
  Trim them with the API's own `fields` and `expand` parameters — never by
  filtering in the server.
- **Auth schemes.** OAuth vs IAM is decided in `TrackerConfig.headers()` by
  `auth_scheme`. Add new schemes there, not in the tool handlers.
