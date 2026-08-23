# Tool reference

Every tool is invoked with the MCP `tools/call` method and returns its payload
as JSON text (`content[0].text`) — the SDK objects are serialized to plain
JSON. Business failures (bad arguments, Tracker API errors, config problems)
come back as the **same shape** with `isError: true` and a plain-text message
instead of JSON.

The canonical schemas are derived from the decorated tool functions in
[`mcp_yandex_tracker.py`](../mcp_yandex_tracker.py) (from their type hints and
`Field` descriptions); this page is the human-readable mirror. If you change a
signature there, update this table.

Argument required-ness note: required string arguments carry a minimum length of
1, so an empty value (`""`) is rejected by input validation — the same `isError`
outcome as omitting the argument.

## Tool annotations

Every tool ships MCP `annotations` so a host can tell a lookup from a write
without parsing the name. Three buckets, and each tool sits in exactly one:

| Bucket | Annotation | Tools |
| ------ | ---------- | ----- |
| Read-only | `readOnlyHint: true` | The 22 `get_*` / `list_*` / `search_*` tools. |
| Additive | `readOnlyHint: false`, `destructiveHint: false` | `tracker_create_issue`, `tracker_add_comment`, `tracker_add_worklog`, `tracker_add_checklist_item`, `tracker_link_issues`, `tracker_upload_attachment`. |
| Destructive | `readOnlyHint: false`, `destructiveHint: true` | `tracker_update_issue`, `tracker_move_issue_status`, `tracker_execute_transition`, `tracker_update_comment`, `tracker_delete_comment`, `tracker_unlink_issues`, `tracker_update_checklist_item`, `tracker_delete_checklist_item`, `tracker_delete_attachment`, `tracker_download_attachment`. |

`readOnlyHint` is the one that earns its keep: it is what lets a host
auto-approve a lookup instead of prompting for every single call. "Destructive"
follows the MCP spec's own line — anything that overwrites a value or removes
data, as opposed to only adding something. That puts patches and status
transitions there alongside the deletes, and `tracker_download_attachment` too,
since it overwrites whatever local file already sits at `dest_dir/name`.

`idempotentHint` and `openWorldHint` are deliberately not emitted: every tool
here talks to the same external service, so open-world is uniform and says
nothing, and idempotency for a Tracker write depends on the queue's workflow
rather than on the tool.

## Two response conventions

**`limit` is a hard cap, never a page size.** Every Tracker collection is
cursor-paginated and iterating one follows each `next` link to the end, so a
list call without a cap is unbounded — `tracker_list_users` on a large
organization would walk the whole directory. Tools that list open-ended
collections take `limit` (integer 1–1000, default `50`) and stop there; the page
after the cap is never fetched. Raise it when you need more. Reference
dictionaries (statuses, priorities, fields, link types, queue versions and the
like) take no `limit`: truncating one would make a caller conclude a value does
not exist, so they carry an internal runaway guard of 500 entries instead.

**Writes answer with a receipt, reads with a projection.** A create or patch
response is worth two things — proof the write landed and the server's canonical
value of what changed — so mutating tools return a compact object rather than
the full entity. Tools where the full payload is real content a caller might
need (`tracker_create_issue`, `tracker_update_issue`, `tracker_list_links`,
`tracker_search_issues`) take `full: true` to opt out; the pure write receipts
(`tracker_add_comment`, `tracker_add_worklog`, `tracker_link_issues`) do not,
since the discarded part is either transport metadata or text the caller just
sent. Transport noise (`self`, `cloudUid`, `passportUid`) is stripped from every
response either way.

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
| `per_page` | integer 1–100   |     | `20`    | Hard cap on issues returned (not just page size). |
| `page`     | integer ≥ 1     |     | `1`     | Page number.                       |
| `include_total` | boolean    |     | `false` | Also return the total match count (extra `_count` request). |
| `full`     | boolean         |     | `false` | Return complete issue objects instead of the compact projection. |

By default returns a materialized list capped at `per_page`. The SDK result is
cursor-paginated, so iterating it to exhaustion would follow every "next" page;
`per_page` is enforced as a real limit (later pages are never fetched). At least
one of `query` / `filter` / `keys` is normally needed for a meaningful search.

Each issue is returned as a **compact projection** — `key`, `summary`, `status`,
`type`, `priority`, `assignee`, `queue`, `parent`, `epic`, `sprint`, `tags`,
`updatedAt`, `createdAt` — with nested references trimmed to their identifying
keys. This keeps a page of results small (a full 100-issue page can be hundreds
of KB). Pass `full: true` for the complete issue objects, or use
`tracker_get_issue` for one issue's full detail.

When `include_total` is `true`, the response shape changes to an object so the
caller can tell whether more pages exist:
`{"issues": [...], "total": <int>, "page": <int>, "per_page": <int>}`.

### `tracker_list_comments`

List an issue's comments, oldest first.

| Argument    | Type           | Req | Default | Notes                       |
| ----------- | -------------- | --- | ------- | --------------------------- |
| `issue_key` | string         | ✅  |         |                             |
| `limit`     | integer 1–1000 |     | `50`    | Hard cap on comments returned. |

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
| `full`        | boolean |    | Return the complete issue object instead of the receipt. Default `false`. |

Returns a receipt: the new issue's `key`, its identifying fields, `version`, and
each entry of `fields` as the server stored it. `summary` and `description` are
not echoed — the caller just sent them.

### `tracker_update_issue`

| Argument    | Type   | Req | Notes                          |
| ----------- | ------ | --- | ------------------------------ |
| `issue_key` | string | ✅  |                                |
| `fields`    | object | ✅  | Raw Tracker PATCH body — API field names and values. |
| `full`      | boolean |    | Return the complete issue object instead of the receipt. Default `false`. |

Returns a receipt: the issue's identifying fields, its new `version`, and every
patched field as the server stored it — including fields outside the compact
projection (custom fields, `description`), so the caller always sees the
canonical value of what it changed. Returning the whole issue is what made this
the single most expensive tool in the server; pass `full: true` if you need it.

`fields` is passed straight through to the Tracker `PATCH` (the SDK adds no
named handling of its own), so it covers the common "special" cases too:

- **Tags** — add/remove or full replace:
  ```json
  {"tags": {"add": ["backend"], "remove": ["stale"]}}
  {"tags": ["backend", "urgent"]}
  ```
- **Components** — a multi-value field, same shape as tags; elements are
  component id or name (see `tracker_list_queue_components`):
  ```json
  {"components": {"add": ["Backend"], "remove": ["Legacy"]}}
  ```
- **Parent reassignment** — by key or id:
  ```json
  {"parent": {"key": "TEST-2"}}
  ```
- **Epic** — an epic association is a **link**, not an issue field. Use
  `tracker_link_issues` with the appropriate relationship, not `fields`.

### `tracker_add_comment`

| Argument    | Type   | Req |
| ----------- | ------ | --- |
| `issue_key` | string | ✅  |
| `text`      | string | ✅  |

Returns a receipt — comment `id`, author, timestamp — not the echoed text.

### `tracker_update_comment`

Replace the text of an existing comment.

| Argument     | Type   | Req | Notes                                    |
| ------------ | ------ | --- | ---------------------------------------- |
| `issue_key`  | string | ✅  |                                          |
| `comment_id` | string | ✅  | Comment id from `tracker_list_comments`. |
| `text`       | string | ✅  | Replacement text (not a patch — it overwrites). |

Returns a receipt — comment `id`, editor, timestamp.

### `tracker_delete_comment`

Delete a comment by its id (from `tracker_list_comments`).

| Argument     | Type   | Req | Notes                              |
| ------------ | ------ | --- | ---------------------------------- |
| `issue_key`  | string | ✅  |                                    |
| `comment_id` | string | ✅  | Comment id from `tracker_list_comments`. |

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

Returns the new link in the same compact shape as `tracker_list_links`.

### `tracker_list_links`

List an issue's links. Each entry carries an `id` used by `tracker_unlink_issues`.

| Argument    | Type           | Req | Default | Notes                        |
| ----------- | -------------- | --- | ------- | ---------------------------- |
| `issue_key` | string         | ✅  |         |                              |
| `limit`     | integer 1–1000 |     | `50`    | Hard cap on links returned.  |
| `full`      | boolean        |     | `false` | Return complete link objects. |

Each link comes back as `id`, `type` (keeping the `inward` / `outward` wording —
the type id alone does not say which way the relationship reads), `direction`,
`status`, and `object` trimmed to the linked issue's `key` / `id` / `display`.
The raw API embeds a **complete** issue object in every `object`, which is what
makes an unprojected link list cost several times what the relationships it
describes are worth. Pass `full: true` for the untrimmed payload.

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
| `tracker_list_queues`           | `limit` (optional, default `50`) | Queues, capped at `limit`. |
| `tracker_list_users`            | `email`, `group`, `limit` (all optional) | Users, optionally server-side filtered (see below). |
| `tracker_list_statuses`         | —               | Global status dictionary.                 |
| `tracker_list_issue_types`      | —               | Global issue-type dictionary.             |
| `tracker_list_priorities`       | —               | Global priority dictionary.               |
| `tracker_list_fields`           | —               | All fields, including custom ones.        |
| `tracker_list_link_types`       | —               | Link types (valid `relationship` values). |
| `tracker_list_queue_versions`   | `queue` (string, ✅) | Versions defined in that queue.      |
| `tracker_list_queue_components` | `queue` (string, ✅) | Components defined in that queue.    |
| `tracker_list_queue_local_fields` | `queue` (string, ✅) | Local (queue-specific custom) fields. |
| `tracker_list_queue_tags`       | `queue` (string, ✅) | Tags defined in that queue.          |

### `tracker_list_users` filters

Tracker's users endpoint supports two **server-side** filters, both optional:

| Argument   | Type          | Notes                                       |
| ---------- | ------------- | ------------------------------------------- |
| `email`    | string         | Exact-match email filter.                  |
| `group`    | string         | Group id filter.                           |
| `limit`    | integer 1–1000 | Hard cap on users returned. Default `50`.  |

There is **no** server-side search by login or name — fetch the list and match
client-side for that, raising `limit` if the directory is larger than the
default. `limit` bounds the users you get back, not just the page size: the
underlying iterator would otherwise walk every page of the directory.

### `tracker_get_user`

Get one user by login or uid.

| Argument       | Type   | Req | Notes                        |
| -------------- | ------ | --- | ---------------------------- |
| `login_or_uid` | string | ✅  | Login (e.g. `jsmith`) or uid. |

### `tracker_get_current_user`

Get the authenticated user (the token owner). Takes no arguments.

## Activity: history, worklog, checklist, attachments

### `tracker_get_changelog`

Get the change history of an issue, oldest first. The optional `field` / `type`
filters map to the native changelog get-params.

| Argument    | Type           | Req | Notes                                         |
| ----------- | -------------- | --- | --------------------------------------------- |
| `issue_key` | string         | ✅  |                                               |
| `field`     | string         |     | Restrict to changes of a single field id, e.g. `status`. |
| `type`      | string         |     | Restrict by change type, e.g. `IssueWorkflow`, `IssueUpdated`. |
| `limit`     | integer 1–1000 |     | Hard cap on entries returned. Default `50`.   |

### `tracker_list_worklog` / `tracker_add_worklog`

Read or add time-tracking records.

| Argument    | Type   | Req | Notes                                                    |
| ----------- | ------ | --- | -------------------------------------------------------- |
| `issue_key` | string | ✅  |                                                          |
| `limit`     | integer 1–1000 |  | `tracker_list_worklog` only. Hard cap, default `50`.     |
| `duration`  | string | ✅  | `tracker_add_worklog` only. ISO 8601, e.g. `PT1H30M`.    |
| `comment`   | string |     | `tracker_add_worklog` only.                              |
| `start`     | string |     | `tracker_add_worklog` only. ISO 8601 datetime.           |

`tracker_add_worklog` returns a receipt — record id, duration, start, author,
timestamp. The raw record embeds the entire parent issue.

### `tracker_list_checklist` / `tracker_add_checklist_item`

Read or append checklist items.

| Argument    | Type    | Req | Notes                                       |
| ----------- | ------- | --- | ------------------------------------------- |
| `issue_key` | string  | ✅  |                                             |
| `limit`     | integer 1–1000 | | `tracker_list_checklist` only. Hard cap, default `50`. |
| `text`      | string  | ✅  | `tracker_add_checklist_item` only.          |
| `checked`   | boolean |     | `tracker_add_checklist_item` only. Default `false`. |

The SDK's `checklistItems.create()` discards the API response, so
`tracker_add_checklist_item` re-reads the checklist and returns it — otherwise
the caller would get a bare `null` and no id for the item it just added.

### `tracker_update_checklist_item` / `tracker_delete_checklist_item`

Edit or remove an existing item. `tracker_update_checklist_item` is how an item
gets ticked off.

| Argument    | Type    | Req | Notes                                            |
| ----------- | ------- | --- | ------------------------------------------------ |
| `issue_key` | string  | ✅  |                                                  |
| `item_id`   | string  | ✅  | Item id from `tracker_list_checklist`.           |
| `text`      | string  |     | `tracker_update_checklist_item` only. New text; omit to leave unchanged. |
| `checked`   | boolean |     | `tracker_update_checklist_item` only. New state; omit to leave unchanged. |

`tracker_update_checklist_item` needs at least one of `text` / `checked` —
calling it with neither is a tool error. Tracker documents `PATCH` and `DELETE`
on a single checklist item but not `GET`, so both tools locate the item by
scanning the checklist rather than addressing it directly.

### `tracker_list_attachments`

List attachment **metadata** (id, name, size, `content` url). The `content` url
is an authenticated API endpoint, **not** a shareable link — it needs the same
token/org headers as every other call, so it cannot be handed to a user as-is.
Use `tracker_download_attachment` to fetch the bytes. Takes an optional `limit`
(integer 1–1000, default `50`) capping how many entries come back.

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

### `tracker_delete_attachment`

Delete an attachment by its id (from `tracker_list_attachments`).

| Argument        | Type   | Req | Notes                               |
| --------------- | ------ | --- | ----------------------------------- |
| `issue_key`     | string | ✅  |                                     |
| `attachment_id` | string | ✅  | Id from `tracker_list_attachments`. |

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
