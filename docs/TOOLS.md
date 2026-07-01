# Tool reference

Every tool is invoked with the MCP `tools/call` method and returns its payload
as JSON text (`content[0].text`) — the SDK objects are serialized to plain
JSON. Business failures (bad arguments, Tracker API errors, config problems)
come back as the **same shape** with `isError: true` and a plain-text message
instead of JSON.

The canonical schemas live in `TOOLS` in
[`server.py`](../yandex_tracker_mcp_server/server.py); this page is the
human-readable mirror. If you change a schema there, update this table.

Argument required-ness note: a required string that is empty (`""`) is rejected
the same as if it were missing.

## Read

### `tracker_get_issue`

Get one issue by key.

| Argument    | Type   | Req | Notes                         |
| ----------- | ------ | --- | ----------------------------- |
| `issue_key` | string | ✅  | e.g. `TEST-123`.              |

### `tracker_search_issues`

Search via query language, a filter object, or explicit keys.

| Argument   | Type            | Req | Default | Notes                              |
| ---------- | --------------- | --- | ------- | ---------------------------------- |
| `query`    | string          |     |         | Tracker query language.            |
| `filter`   | object          |     |         | Field filter, e.g. `{"queue":"TEST"}`. |
| `order`    | string          |     |         | Sort expression.                   |
| `keys`     | array\<string\> |     |         | Fetch specific issue keys.         |
| `per_page` | integer 1–100   |     | `20`    | Page size.                         |
| `page`     | integer ≥ 1     |     | `1`     | Page number.                       |

Returns a materialized list (the SDK's lazy paginated result is exhausted into
an array). At least one of `query` / `filter` / `keys` is normally needed for a
meaningful search.

### `tracker_list_comments`

List all comments on an issue.

| Argument    | Type   | Req |
| ----------- | ------ | --- |
| `issue_key` | string | ✅  |

### `tracker_list_transitions`

List the workflow transitions currently available on an issue. Use this to
discover the `transition_id` values for `tracker_execute_transition`, or the
status names for `tracker_move_issue_status`.

| Argument    | Type   | Req |
| ----------- | ------ | --- |
| `issue_key` | string | ✅  |

## Write

### `tracker_create_issue`

| Argument      | Type   | Req | Notes                                  |
| ------------- | ------ | --- | -------------------------------------- |
| `queue`       | string | ✅  | Target queue key.                      |
| `summary`     | string | ✅  | Issue title.                           |
| `description` | string |     | Body.                                  |
| `fields`      | object |     | Any additional Tracker fields, merged into the create payload. |

### `tracker_update_issue`

| Argument    | Type   | Req | Notes                          |
| ----------- | ------ | --- | ------------------------------ |
| `issue_key` | string | ✅  |                                |
| `fields`    | object | ✅  | Fields to patch on the issue.  |

### `tracker_add_comment`

| Argument    | Type   | Req |
| ----------- | ------ | --- |
| `issue_key` | string | ✅  |
| `text`      | string | ✅  |

## Transitions

Two ways to move an issue through its workflow. Prefer `tracker_move_issue_status`
when you know the target status by name; use `tracker_execute_transition` when
you already have the transition id (e.g. from `tracker_list_transitions`).

### `tracker_move_issue_status`

Resolve a transition by matching `status` against each available transition's
**id**, **display name**, or the destination status's **id / key / display**
(case-insensitive, trimmed), then execute it.

| Argument    | Type   | Req | Notes                                                         |
| ----------- | ------ | --- | ------------------------------------------------------------- |
| `issue_key` | string | ✅  |                                                              |
| `status`    | string | ✅  | Transition id/display or destination status id/key/display.   |
| `fields`    | object |     | Transition-screen fields (e.g. `{"comment": "done"}`, resolution). |

If nothing matches, the error lists the available transitions as
`id->status`. If more than one transition matches, it errors with the
ambiguous ids rather than guessing — fall back to `tracker_execute_transition`
with an explicit id.

### `tracker_execute_transition`

Execute a transition by its exact id.

| Argument        | Type   | Req | Notes                          |
| --------------- | ------ | --- | ------------------------------ |
| `issue_key`     | string | ✅  |                                |
| `transition_id` | string | ✅  | e.g. `start_progress`, `close`. |
| `fields`        | object |     | Transition-screen fields.       |

## Example call

```json
{"jsonrpc":"2.0","id":7,"method":"tools/call","params":{
  "name":"tracker_move_issue_status",
  "arguments":{"issue_key":"TEST-1","status":"In progress","fields":{"comment":"starting"}}
}}
```

Successful response (abridged):

```json
{"jsonrpc":"2.0","id":7,"result":{
  "content":[{"type":"text","text":"{ ...transition result as JSON... }"}],
  "isError":false
}}
```
