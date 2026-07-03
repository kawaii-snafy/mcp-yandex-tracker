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
| `include_total` | boolean    |     | `false` | Also return the total match count (extra `_count` request). |

By default returns a materialized list (the SDK's lazy paginated result is
exhausted into an array). At least one of `query` / `filter` / `keys` is normally
needed for a meaningful search.

When `include_total` is `true`, the response shape changes to an object so the
caller can tell whether more pages exist:
`{"issues": [...], "total": <int>, "page": <int>, "per_page": <int>}`.

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

## Links

Issue links are a separate Tracker resource, not an issue field — they cannot be
set through `tracker_create_issue` / `tracker_update_issue`. Use these tools.

### `tracker_link_issues`

Create a link from one issue to another.

| Argument       | Type   | Req | Notes                                                       |
| -------------- | ------ | --- | ----------------------------------------------------------- |
| `issue_key`    | string | ✅  | Source issue.                                               |
| `relationship` | string | ✅  | Link type, e.g. `relates`, `depends on`, `is dependent by`, `is subtask for`, `is parent task for`, `duplicates`. Discover valid values with `tracker_list_link_types`. |
| `target_issue` | string | ✅  | Issue to link to.                                           |

### `tracker_list_links`

List an issue's links. Each entry carries an `id` used by `tracker_unlink_issues`.

| Argument    | Type   | Req |
| ----------- | ------ | --- |
| `issue_key` | string | ✅  |

### `tracker_unlink_issues`

Remove a link by its id (from `tracker_list_links`).

| Argument    | Type   | Req | Notes                          |
| ----------- | ------ | --- | ------------------------------ |
| `issue_key` | string | ✅  |                                |
| `link_id`   | string | ✅  | Link id from `tracker_list_links`. |

## Reference / dictionaries

Read-only lookups so a caller can resolve valid field values (queues, users,
types, priorities, custom fields) instead of guessing. The global dictionaries
take no arguments.

| Tool                            | Argument        | Returns                                   |
| ------------------------------- | --------------- | ----------------------------------------- |
| `tracker_list_queues`           | —               | All queues.                               |
| `tracker_list_users`            | —               | All users (for `assignee`, `followers`).  |
| `tracker_list_statuses`         | —               | Global status dictionary.                 |
| `tracker_list_issue_types`      | —               | Global issue-type dictionary.             |
| `tracker_list_priorities`       | —               | Global priority dictionary.               |
| `tracker_list_fields`           | —               | All fields, including custom ones.        |
| `tracker_list_link_types`       | —               | Link types (valid `relationship` values). |
| `tracker_list_queue_versions`   | `queue` (string, ✅) | Versions defined in that queue.      |
| `tracker_list_queue_components` | `queue` (string, ✅) | Components defined in that queue.    |

## Activity: history, worklog, checklist, attachments

### `tracker_get_changelog`

Get the change history of an issue.

| Argument    | Type   | Req |
| ----------- | ------ | --- |
| `issue_key` | string | ✅  |

### `tracker_list_worklog` / `tracker_add_worklog`

Read or add time-tracking records.

| Argument    | Type   | Req | Notes                                                    |
| ----------- | ------ | --- | -------------------------------------------------------- |
| `issue_key` | string | ✅  |                                                          |
| `duration`  | string | ✅  | `tracker_add_worklog` only. ISO 8601, e.g. `PT1H30M`.    |
| `comment`   | string |     | `tracker_add_worklog` only.                              |
| `start`     | string |     | `tracker_add_worklog` only. ISO 8601 datetime.           |

### `tracker_list_checklist` / `tracker_add_checklist_item`

Read or append checklist items.

| Argument    | Type    | Req | Notes                                       |
| ----------- | ------- | --- | ------------------------------------------- |
| `issue_key` | string  | ✅  |                                             |
| `text`      | string  | ✅  | `tracker_add_checklist_item` only.          |
| `checked`   | boolean |     | `tracker_add_checklist_item` only. Default `false`. |

### `tracker_list_attachments`

List attachment **metadata** (id, name, size, `content` url). The `content` url
is an authenticated API endpoint, **not** a shareable link — it needs the same
token/org headers as every other call, so it cannot be handed to a user as-is.
Use `tracker_download_attachment` to fetch the bytes.

| Argument    | Type   | Req |
| ----------- | ------ | --- |
| `issue_key` | string | ✅  |

### `tracker_download_attachment`

Download an attachment to a local directory (the server proxies the
authenticated fetch) and return the saved file path.

| Argument        | Type   | Req | Notes                                            |
| --------------- | ------ | --- | ------------------------------------------------ |
| `issue_key`     | string | ✅  |                                                  |
| `attachment_id` | string | ✅  | Id from `tracker_list_attachments`.              |
| `dest_dir`      | string | ✅  | Absolute directory to save into (created if needed). |
| `filename`      | string |     | Override the saved file name (basename only).    |

Returns `{"path": <saved path>, "name": <file name>, "size": <int>}`.

### `tracker_upload_attachment`

Upload a local file as an attachment on an issue. The path is validated up front,
so a missing/unreadable file returns a clean tool error.

| Argument    | Type   | Req | Notes                                          |
| ----------- | ------ | --- | ---------------------------------------------- |
| `issue_key` | string | ✅  |                                                |
| `file_path` | string | ✅  | Absolute path to the local file to upload.     |
| `filename`  | string |     | Name to store the attachment under in Tracker. |

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
