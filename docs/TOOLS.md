# Tool reference

This server is a thin wrapper over the [Yandex Tracker REST API
v3](https://yandex.ru/support/tracker/en/llms.txt): **one tool per documented
endpoint**, the API's own parameter names on the way in, the API's own JSON on
the way out.

That is why this page is an index rather than a copy of Yandex's argument tables.
The documentation is the reference — every row below links to the page its tool
was written from, and every tool repeats that link in its own description, so an
agent holding the tool already holds the way to the spec.

Naming follows the endpoint: path placeholders become camelCase arguments
(`<issue_ID>` → `issueId`), and query and body parameters keep the API's spelling
(`perPage`, `expand`, `markupType`).

The **Effect** column is what the tool tells your host about the call, as MCP
annotations: `read` (`readOnlyHint`) changes nothing and can be granted a
standing permission, `create` only adds, and `modify` (`destructiveHint`) edits
or deletes something that already exists and should be confirmed. It follows the
HTTP method except where the method misleads — the five `_search` / `_count`
endpoints are POSTs that read, the two attachment downloads are GETs that write
a file to your disk, and POSTs like `tracker_move_issue` or `tracker_start_sprint`
act on an object that is already there.

> Everything under [The tools](#the-tools) is generated from the tool registry:
> `bun run docs:tools` rewrites it. Edit the tools, not the tables. This section
> and the two below it are hand-written.

## Calling convention

Tools are invoked with the MCP `tools/call` method and return their payload as a
single JSON text block (`content[0].text`) — raw Tracker JSON, nothing stripped
and nothing reshaped. Trim large responses with the API's own `fields` and
`expand` parameters.

Business failures (bad arguments, Tracker API errors, config problems) come back
in the **same shape** with `isError: true` and a plain-text message instead of
JSON. Required string arguments carry a minimum length of 1, so an empty value
(`""`) is rejected by input validation — the same `isError` outcome as omitting
the argument.

An argument you leave out is absent from the request; it is never sent as `null`.

```json
{
  "jsonrpc": "2.0",
  "id": 7,
  "method": "tools/call",
  "params": {
    "name": "tracker_get_issue",
    "arguments": { "issueId": "TEST-1", "expand": "attachments" }
  }
}
```

## Where the wrapper is not literal

Six places where a tool cannot be a byte-for-byte mirror of its endpoint. There
are no others.

| What                                                                                              | Why                                                                                                                                                                                                                                       |
| ------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `destDir` / `saveAs` on `tracker_get_attachment`, `tracker_get_attachment_preview`                | Those endpoints return a file. An MCP result is text, so the tool streams the bytes to a local directory and returns `{"path", "name", "size"}`.                                                                                          |
| `filePath` on `tracker_post_attachment`, `tracker_post_temp_attachment`                           | Those endpoints take `multipart/form-data`. The tool reads the local path and sends it as the documented `file` part.                                                                                                                     |
| `version` on the board, column and sprint edits                                                   | Those pages document it as the `If-Match: "<version>"` header rather than a parameter. Elsewhere (`tracker_patch_issue`, the workflow / trigger / component / dictionary edits) `version` is a real query parameter and is passed as one. |
| `page` on `tracker_search_issues`, `tracker_get_users`, `tracker_get_queues`                      | Those pages describe the result as paginated and link to [common-format](https://yandex.ru/support/tracker/en/api/common-format.md) instead of repeating the parameters. `perPage` + `page` come from there.                              |
| The nine `relationship` values in `tracker_link_issue`'s description                              | No endpoint in the API lists link types, so the values enumerated on [link-issue](https://yandex.ru/support/tracker/en/api/issues/link-issue.md) are the only place to learn them.                                                        |
| `commentId` on `tracker_entity_patch_comment`; the per-item body of `tracker_edit_checklist_item` | Those two pages contradict themselves (summary vs resource table, example vs parameter table). Both tools follow the page's parameter table, which matches the path — and that is what the endpoint accepts in practice.                  |

Every other argument is spelled exactly as the API spells it, `from` included.

## The tools

<!-- tools:start -->

### Issues — 48 tools

Issues, comments, checklists, attachments, worklog, links, transitions and the field dictionary.

| Tool                              | Endpoint                                                                  | Effect | Documentation                                                                                                        |
| --------------------------------- | ------------------------------------------------------------------------- | ------ | -------------------------------------------------------------------------------------------------------------------- |
| `tracker_create_issue`            | `POST /v3/issues/`                                                        | create | [issues/create-issue](https://yandex.ru/support/tracker/en/api/issues/create-issue.md)                               |
| `tracker_get_issue`               | `GET /v3/issues/{issueId}`                                                | read   | [issues/get-issue](https://yandex.ru/support/tracker/en/api/issues/get-issue.md)                                     |
| `tracker_patch_issue`             | `PATCH /v3/issues/{issueId}`                                              | modify | [issues/patch-issue](https://yandex.ru/support/tracker/en/api/issues/patch-issue.md)                                 |
| `tracker_move_issue`              | `POST /v3/issues/{issueId}/_move`                                         | modify | [issues/move-issue](https://yandex.ru/support/tracker/en/api/issues/move-issue.md)                                   |
| `tracker_search_issues`           | `POST /v3/issues/_search`                                                 | read   | [issues/search-issues](https://yandex.ru/support/tracker/en/api/issues/search-issues.md)                             |
| `tracker_count_issues`            | `POST /v3/issues/_count`                                                  | read   | [issues/count-issues](https://yandex.ru/support/tracker/en/api/issues/count-issues.md)                               |
| `tracker_get_suggest`             | `GET /v3/issues/_suggest`                                                 | read   | [issues/get-suggest](https://yandex.ru/support/tracker/en/api/issues/get-suggest.md)                                 |
| `tracker_clear_scroll`            | `POST /v3/system/search/scroll/_clear`                                    | modify | [issues/search-release](https://yandex.ru/support/tracker/en/api/issues/search-release.md)                           |
| `tracker_get_changelog`           | `GET /v3/issues/{issueId}/changelog`                                      | read   | [issues/get-changelog](https://yandex.ru/support/tracker/en/api/issues/get-changelog.md)                             |
| `tracker_link_issue`              | `POST /v3/issues/{issueId}/links`                                         | create | [issues/link-issue](https://yandex.ru/support/tracker/en/api/issues/link-issue.md)                                   |
| `tracker_get_links`               | `GET /v3/issues/{issueId}/links`                                          | read   | [issues/get-links](https://yandex.ru/support/tracker/en/api/issues/get-links.md)                                     |
| `tracker_delete_link`             | `DELETE /v3/issues/{issueId}/links/{linkId}`                              | modify | [issues/delete-link-issue](https://yandex.ru/support/tracker/en/api/issues/delete-link-issue.md)                     |
| `tracker_get_external_links`      | `GET /v3/issues/{issueId}/remotelinks`                                    | read   | [issues/get-external-links](https://yandex.ru/support/tracker/en/api/issues/get-external-links.md)                   |
| `tracker_add_external_link`       | `POST /v3/issues/{issueId}/remotelinks`                                   | create | [issues/add-external-link](https://yandex.ru/support/tracker/en/api/issues/add-external-link.md)                     |
| `tracker_delete_external_link`    | `DELETE /v3/issues/{issueId}/remotelinks/{externalLinkId}`                | modify | [issues/delete-external-link](https://yandex.ru/support/tracker/en/api/issues/delete-external-link.md)               |
| `tracker_get_transitions`         | `GET /v3/issues/{issueId}/transitions`                                    | read   | [issues/get-transitions](https://yandex.ru/support/tracker/en/api/issues/get-transitions.md)                         |
| `tracker_new_transition`          | `POST /v3/issues/{issueId}/transitions/{transitionId}/_execute`           | modify | [issues/new-transition](https://yandex.ru/support/tracker/en/api/issues/new-transition.md)                           |
| `tracker_add_comment`             | `POST /v3/issues/{issueId}/comments`                                      | create | [issues/add-comment](https://yandex.ru/support/tracker/en/api/issues/add-comment.md)                                 |
| `tracker_get_comments`            | `GET /v3/issues/{issueId}/comments`                                       | read   | [issues/get-comments](https://yandex.ru/support/tracker/en/api/issues/get-comments.md)                               |
| `tracker_edit_comment`            | `PATCH /v3/issues/{issueId}/comments/{commentId}`                         | modify | [issues/edit-comment](https://yandex.ru/support/tracker/en/api/issues/edit-comment.md)                               |
| `tracker_delete_comment`          | `DELETE /v3/issues/{issueId}/comments/{commentId}`                        | modify | [issues/delete-comment](https://yandex.ru/support/tracker/en/api/issues/delete-comment.md)                           |
| `tracker_add_reaction_to_comment` | `POST /v3/issues/{issueId}/comments/{commentId}/reactions/{reactionName}` | create | [issues/add-reaction-to-comment](https://yandex.ru/support/tracker/en/api/issues/add-reaction-to-comment.md)         |
| `tracker_add_checklist_item`      | `POST /v3/issues/{issueId}/checklistItems`                                | create | [issues/add-checklist-item](https://yandex.ru/support/tracker/en/api/issues/add-checklist-item.md)                   |
| `tracker_get_checklist`           | `GET /v3/issues/{issueId}/checklistItems`                                 | read   | [issues/get-checklist](https://yandex.ru/support/tracker/en/api/issues/get-checklist.md)                             |
| `tracker_edit_checklist_item`     | `PATCH /v3/issues/{issueId}/checklistItems/{checklistItemId}`             | modify | [issues/edit-checklist](https://yandex.ru/support/tracker/en/api/issues/edit-checklist.md)                           |
| `tracker_delete_checklist`        | `DELETE /v3/issues/{issueId}/checklistItems`                              | modify | [issues/delete-checklist](https://yandex.ru/support/tracker/en/api/issues/delete-checklist.md)                       |
| `tracker_delete_checklist_item`   | `DELETE /v3/issues/{issueId}/checklistItems/{checklistItemId}`            | modify | [issues/delete-checklist-item](https://yandex.ru/support/tracker/en/api/issues/delete-checklist-item.md)             |
| `tracker_get_attachments`         | `GET /v3/issues/{issueId}/attachments`                                    | read   | [issues/get-attachments-list](https://yandex.ru/support/tracker/en/api/issues/get-attachments-list.md)               |
| `tracker_get_attachment`          | `GET /v3/issues/{issueId}/attachments/{fileId}/{fileName}`                | create | [issues/get-attachment](https://yandex.ru/support/tracker/en/api/issues/get-attachment.md)                           |
| `tracker_get_attachment_preview`  | `GET /v3/issues/{issueId}/thumbnails/{fileId}`                            | create | [issues/get-attachment-preview](https://yandex.ru/support/tracker/en/api/issues/get-attachment-preview.md)           |
| `tracker_post_attachment`         | `POST /v3/issues/{issueId}/attachments/`                                  | create | [issues/post-attachment](https://yandex.ru/support/tracker/en/api/issues/post-attachment.md)                         |
| `tracker_post_temp_attachment`    | `POST /v3/attachments/`                                                   | create | [issues/temp-attachment](https://yandex.ru/support/tracker/en/api/issues/temp-attachment.md)                         |
| `tracker_delete_attachment`       | `DELETE /v3/issues/{issueId}/attachments/{fileId}/`                       | modify | [issues/delete-attachment](https://yandex.ru/support/tracker/en/api/issues/delete-attachment.md)                     |
| `tracker_new_worklog`             | `POST /v3/issues/{issueId}/worklog`                                       | create | [issues/new-worklog](https://yandex.ru/support/tracker/en/api/issues/new-worklog.md)                                 |
| `tracker_get_issue_worklog`       | `GET /v3/issues/{issueId}/worklog`                                        | read   | [issues/issue-worklog](https://yandex.ru/support/tracker/en/api/issues/issue-worklog.md)                             |
| `tracker_patch_worklog`           | `PATCH /v3/issues/{issueId}/worklog/{recordId}`                           | modify | [issues/patch-worklog](https://yandex.ru/support/tracker/en/api/issues/patch-worklog.md)                             |
| `tracker_delete_worklog`          | `DELETE /v3/issues/{issueId}/worklog/{recordId}`                          | modify | [issues/delete-worklog](https://yandex.ru/support/tracker/en/api/issues/delete-worklog.md)                           |
| `tracker_get_worklog`             | `GET /v3/worklog`                                                         | read   | [issues/get-worklog](https://yandex.ru/support/tracker/en/api/issues/get-worklog.md)                                 |
| `tracker_search_worklog`          | `POST /v3/worklog/_search`                                                | read   | [issues/get-worklog](https://yandex.ru/support/tracker/en/api/issues/get-worklog.md)                                 |
| `tracker_get_global_fields`       | `GET /v3/fields`                                                          | read   | [issues/get-global-fields](https://yandex.ru/support/tracker/en/api/issues/get-global-fields.md)                     |
| `tracker_create_field`            | `POST /v3/fields`                                                         | create | [issues/create-field](https://yandex.ru/support/tracker/en/api/issues/create-field.md)                               |
| `tracker_get_field`               | `GET /v3/fields/{fieldId}`                                                | read   | [issues/get-issue-fields](https://yandex.ru/support/tracker/en/api/issues/get-issue-fields.md)                       |
| `tracker_patch_field`             | `PATCH /v3/fields/{fieldId}`                                              | modify | [issues/patch-issue-field-name](https://yandex.ru/support/tracker/en/api/issues/patch-issue-field-name.md)           |
| `tracker_create_field_category`   | `POST /v3/fields/categories`                                              | create | [issues/create-issue-field-category](https://yandex.ru/support/tracker/en/api/issues/create-issue-field-category.md) |
| `tracker_patch_field_category`    | `PATCH /v3/fields/categories/{categoryId}`                                | modify | [issues/patch-issue-field-category](https://yandex.ru/support/tracker/en/api/issues/patch-issue-field-category.md)   |
| `tracker_get_applications`        | `GET /v3/applications`                                                    | read   | [issues/get-applications](https://yandex.ru/support/tracker/en/api/issues/get-applications.md)                       |
| `tracker_create_report`           | `POST /v3/entities/report/`                                               | create | [issues/create-report](https://yandex.ru/support/tracker/en/api/issues/create-report.md)                             |
| `tracker_search_reports`          | `POST /v3/entities/report/_search`                                        | read   | [issues/search-reports](https://yandex.ru/support/tracker/en/api/issues/search-reports.md)                           |

### Queues — 37 tools

Queues, versions, tags, permissions, local fields, workflows, triggers, autoactions and components.

| Tool                                 | Endpoint                                                             | Effect | Documentation                                                                                                                |
| ------------------------------------ | -------------------------------------------------------------------- | ------ | ---------------------------------------------------------------------------------------------------------------------------- |
| `tracker_create_queue`               | `POST /v3/queues/`                                                   | create | [queues/create-queue](https://yandex.ru/support/tracker/en/api/queues/create-queue.md)                                       |
| `tracker_get_queues`                 | `GET /v3/queues/`                                                    | read   | [queues/get-queues](https://yandex.ru/support/tracker/en/api/queues/get-queues.md)                                           |
| `tracker_get_queue`                  | `GET /v3/queues/{queueId}`                                           | read   | [queues/get-queue](https://yandex.ru/support/tracker/en/api/queues/get-queue.md)                                             |
| `tracker_delete_queue`               | `DELETE /v3/queues/{queueId}`                                        | modify | [queues/delete-queue](https://yandex.ru/support/tracker/en/api/queues/delete-queue.md)                                       |
| `tracker_restore_queue`              | `POST /v3/queues/{queueId}/_restore`                                 | modify | [queues/restore-queue](https://yandex.ru/support/tracker/en/api/queues/restore-queue.md)                                     |
| `tracker_get_queue_fields`           | `GET /v3/queues/{queueId}/fields`                                    | read   | [queues/get-fields](https://yandex.ru/support/tracker/en/api/queues/get-fields.md)                                           |
| `tracker_get_queue_versions`         | `GET /v3/queues/{queueId}/versions`                                  | read   | [queues/get-versions](https://yandex.ru/support/tracker/en/api/queues/get-versions.md)                                       |
| `tracker_create_version`             | `POST /v3/versions/`                                                 | create | [queues/create-version](https://yandex.ru/support/tracker/en/api/queues/create-version.md)                                   |
| `tracker_get_queue_tags`             | `GET /v3/queues/{queueId}/tags`                                      | read   | [queues/get-tags](https://yandex.ru/support/tracker/en/api/queues/get-tags.md)                                               |
| `tracker_delete_queue_tag`           | `POST /v3/queues/{queueId}/tags/_remove`                             | modify | [queues/delete-tag](https://yandex.ru/support/tracker/en/api/queues/delete-tag.md)                                           |
| `tracker_patch_queue_permissions`    | `PATCH /v3/queues/{queueId}/permissions`                             | modify | [queues/manage-access](https://yandex.ru/support/tracker/en/api/queues/manage-access.md)                                     |
| `tracker_get_queue_user_access`      | `GET /v3/queues/{queueId}/permissions/users/{userId}`                | read   | [queues/get-user-access](https://yandex.ru/support/tracker/en/api/queues/get-user-access.md)                                 |
| `tracker_get_queue_group_access`     | `GET /v3/queues/{queueId}/permissions/groups/{groupId}`              | read   | [queues/get-group-access](https://yandex.ru/support/tracker/en/api/queues/get-group-access.md)                               |
| `tracker_create_local_field`         | `POST /v3/queues/{queueId}/localFields`                              | create | [queues/create-local-field](https://yandex.ru/support/tracker/en/api/queues/create-local-field.md)                           |
| `tracker_get_local_fields`           | `GET /v3/queues/{queueId}/localFields`                               | read   | [queues/get-local-fields](https://yandex.ru/support/tracker/en/api/queues/get-local-fields.md)                               |
| `tracker_get_local_field`            | `GET /v3/queues/{queueId}/localFields/{fieldKey}`                    | read   | [queues/get-info-local-field](https://yandex.ru/support/tracker/en/api/queues/get-info-local-field.md)                       |
| `tracker_patch_local_field`          | `PATCH /v3/queues/{queueId}/localFields/{fieldKey}`                  | modify | [queues/edit-local-field](https://yandex.ru/support/tracker/en/api/queues/edit-local-field.md)                               |
| `tracker_create_workflow`            | `POST /v3/workflows`                                                 | create | [queues/workflows/post-workflow](https://yandex.ru/support/tracker/en/api/queues/workflows/post-workflow.md)                 |
| `tracker_get_workflows`              | `GET /v3/workflows`                                                  | read   | [queues/workflows/get-workflows](https://yandex.ru/support/tracker/en/api/queues/workflows/get-workflows.md)                 |
| `tracker_get_workflow`               | `GET /v3/workflows/{workflowId}`                                     | read   | [queues/workflows/get-workflow](https://yandex.ru/support/tracker/en/api/queues/workflows/get-workflow.md)                   |
| `tracker_patch_workflow`             | `PATCH /v3/workflows/{workflowId}`                                   | modify | [queues/workflows/patch-workflow](https://yandex.ru/support/tracker/en/api/queues/workflows/patch-workflow.md)               |
| `tracker_patch_workflow_action`      | `PATCH /v3/workflows/{workflowId}/steps/{status}/actions/{actionId}` | modify | [queues/workflows/patch-workflow-action](https://yandex.ru/support/tracker/en/api/queues/workflows/patch-workflow-action.md) |
| `tracker_delete_workflow`            | `DELETE /v3/workflows/{workflowId}`                                  | modify | [queues/workflows/delete-workflow](https://yandex.ru/support/tracker/en/api/queues/workflows/delete-workflow.md)             |
| `tracker_create_autoaction`          | `POST /v3/queues/{queueId}/autoactions`                              | create | [queues/create-autoaction](https://yandex.ru/support/tracker/en/api/queues/create-autoaction.md)                             |
| `tracker_get_autoaction`             | `GET /v3/queues/{queueId}/autoactions/{autoactionId}`                | read   | [queues/get-autoaction](https://yandex.ru/support/tracker/en/api/queues/get-autoaction.md)                                   |
| `tracker_get_autoaction_logs`        | `GET /v3/queues/{queueId}/autoactions/{autoactionId}/logs`           | read   | [queues/view-autoaction-logs](https://yandex.ru/support/tracker/en/api/queues/view-autoaction-logs.md)                       |
| `tracker_get_autoaction_run_log`     | `GET /v3/queues/{queueId}/autoactions/{autoactionId}/logs/{runId}`   | read   | [queues/view-autoaction-logs](https://yandex.ru/support/tracker/en/api/queues/view-autoaction-logs.md)                       |
| `tracker_create_trigger`             | `POST /v3/queues/{queueId}/triggers`                                 | create | [queues/create-trigger](https://yandex.ru/support/tracker/en/api/queues/create-trigger.md)                                   |
| `tracker_get_triggers`               | `GET /v3/queues/{queueId}/triggers`                                  | read   | [queues/get-triggers](https://yandex.ru/support/tracker/en/api/queues/get-triggers.md)                                       |
| `tracker_get_trigger`                | `GET /v3/queues/{queueId}/triggers/{triggerId}`                      | read   | [queues/get-trigger](https://yandex.ru/support/tracker/en/api/queues/get-trigger.md)                                         |
| `tracker_patch_trigger`              | `PATCH /v3/queues/{queueId}/triggers/{triggerId}`                    | modify | [queues/change-trigger](https://yandex.ru/support/tracker/en/api/queues/change-trigger.md)                                   |
| `tracker_get_trigger_webhook_log`    | `GET /v3/queues/{queueId}/triggers/{triggerId}/webhooks/log`         | read   | [queues/view-trigger-logs](https://yandex.ru/support/tracker/en/api/queues/view-trigger-logs.md)                             |
| `tracker_get_components`             | `GET /v3/components`                                                 | read   | [queues/get-components](https://yandex.ru/support/tracker/en/api/queues/get-components.md)                                   |
| `tracker_create_component`           | `POST /v3/components`                                                | create | [queues/post-component](https://yandex.ru/support/tracker/en/api/queues/post-component.md)                                   |
| `tracker_patch_component`            | `PATCH /v3/components/{componentId}`                                 | modify | [queues/patch-component](https://yandex.ru/support/tracker/en/api/queues/patch-component.md)                                 |
| `tracker_get_component_user_access`  | `GET /v3/components/{componentId}/permissions/users/{userId}`        | read   | [queues/get-component-user-access](https://yandex.ru/support/tracker/en/api/queues/get-component-user-access.md)             |
| `tracker_get_component_group_access` | `GET /v3/components/{componentId}/permissions/groups/{groupId}`      | read   | [queues/get-component-group-access](https://yandex.ru/support/tracker/en/api/queues/get-component-group-access.md)           |

### Boards & sprints — 18 tools

Boards, their columns, and sprints.

| Tool                          | Endpoint                                         | Effect | Documentation                                                                                        |
| ----------------------------- | ------------------------------------------------ | ------ | ---------------------------------------------------------------------------------------------------- |
| `tracker_get_boards`          | `GET /v3/boards`                                 | read   | [boards/get-boards](https://yandex.ru/support/tracker/en/api/boards/get-boards.md)                   |
| `tracker_get_boards_paginate` | `GET /v3/boards/_paginate`                       | read   | [boards/get-boards-paginate](https://yandex.ru/support/tracker/en/api/boards/get-boards-paginate.md) |
| `tracker_get_board`           | `GET /v3/boards/{boardId}`                       | read   | [boards/get-board](https://yandex.ru/support/tracker/en/api/boards/get-board.md)                     |
| `tracker_create_board`        | `POST /v3/boards/`                               | create | [boards/post-board](https://yandex.ru/support/tracker/en/api/boards/post-board.md)                   |
| `tracker_patch_board`         | `PATCH /v3/boards/{boardId}`                     | modify | [boards/patch-board](https://yandex.ru/support/tracker/en/api/boards/patch-board.md)                 |
| `tracker_delete_board`        | `DELETE /v3/boards/{boardId}`                    | modify | [boards/delete-board](https://yandex.ru/support/tracker/en/api/boards/delete-board.md)               |
| `tracker_get_board_columns`   | `GET /v3/boards/{boardId}/columns`               | read   | [boards/get-columns](https://yandex.ru/support/tracker/en/api/boards/get-columns.md)                 |
| `tracker_get_board_column`    | `GET /v3/boards/{boardId}/columns/{columnId}`    | read   | [boards/get-column](https://yandex.ru/support/tracker/en/api/boards/get-column.md)                   |
| `tracker_create_board_column` | `POST /v3/boards/{boardId}/columns/`             | create | [boards/post-column](https://yandex.ru/support/tracker/en/api/boards/post-column.md)                 |
| `tracker_patch_board_column`  | `PATCH /v3/boards/{boardId}/columns/{columnId}`  | modify | [boards/patch-column](https://yandex.ru/support/tracker/en/api/boards/patch-column.md)               |
| `tracker_delete_board_column` | `DELETE /v3/boards/{boardId}/columns/{columnId}` | modify | [boards/delete-column](https://yandex.ru/support/tracker/en/api/boards/delete-column.md)             |
| `tracker_get_board_sprints`   | `GET /v3/boards/{boardId}/sprints`               | read   | [boards/get-sprints](https://yandex.ru/support/tracker/en/api/boards/get-sprints.md)                 |
| `tracker_get_sprint`          | `GET /v3/sprints/{sprintId}`                     | read   | [boards/get-sprint](https://yandex.ru/support/tracker/en/api/boards/get-sprint.md)                   |
| `tracker_create_sprint`       | `POST /v3/sprints`                               | create | [boards/post-sprint](https://yandex.ru/support/tracker/en/api/boards/post-sprint.md)                 |
| `tracker_patch_sprint`        | `PATCH /v3/sprints/{sprintId}`                   | modify | [boards/patch-sprint](https://yandex.ru/support/tracker/en/api/boards/patch-sprint.md)               |
| `tracker_start_sprint`        | `POST /v3/sprints/{sprintId}/_start`             | modify | [boards/start-sprint](https://yandex.ru/support/tracker/en/api/boards/start-sprint.md)               |
| `tracker_archive_sprint`      | `POST /v3/sprints/{sprintId}/_archive`           | modify | [boards/archive-sprint](https://yandex.ru/support/tracker/en/api/boards/archive-sprint.md)           |
| `tracker_delete_sprint`       | `DELETE /v3/sprints/{sprintId}`                  | modify | [boards/delete-sprint](https://yandex.ru/support/tracker/en/api/boards/delete-sprint.md)             |

### Projects, portfolios & goals — 30 tools

The `entities` API, with their comments, checklists, attachments, links and permissions.

| Tool                                        | Endpoint                                                                           | Effect | Documentation                                                                                                                      |
| ------------------------------------------- | ---------------------------------------------------------------------------------- | ------ | ---------------------------------------------------------------------------------------------------------------------------------- |
| `tracker_create_entity`                     | `POST /v3/entities/{entityType}`                                                   | create | [entities/create-entity](https://yandex.ru/support/tracker/en/api/entities/create-entity.md)                                       |
| `tracker_get_entity`                        | `GET /v3/entities/{entityType}/{entityId}`                                         | read   | [entities/get-entity](https://yandex.ru/support/tracker/en/api/entities/get-entity.md)                                             |
| `tracker_update_entity`                     | `PATCH /v3/entities/{entityType}/{entityId}`                                       | modify | [entities/update-entity](https://yandex.ru/support/tracker/en/api/entities/update-entity.md)                                       |
| `tracker_delete_entity`                     | `DELETE /v3/entities/{entityType}/{entityId}`                                      | modify | [entities/delete-entity](https://yandex.ru/support/tracker/en/api/entities/delete-entity.md)                                       |
| `tracker_search_entities`                   | `POST /v3/entities/{entityType}/_search`                                           | read   | [entities/search-entities](https://yandex.ru/support/tracker/en/api/entities/search-entities.md)                                   |
| `tracker_bulkchange_entities`               | `POST /v3/entities/{entityType}/bulkchange/_update`                                | modify | [entities/bulkchange-entities](https://yandex.ru/support/tracker/en/api/entities/bulkchange-entities.md)                           |
| `tracker_get_entity_events`                 | `GET /v3/entities/{entityType}/{entityId}/events/_relative`                        | read   | [entities/get-events-relative](https://yandex.ru/support/tracker/en/api/entities/get-events-relative.md)                           |
| `tracker_entity_add_comment`                | `POST /v3/entities/{entityType}/{entityId}/comments`                               | create | [entities/comments/add-comment](https://yandex.ru/support/tracker/en/api/entities/comments/add-comment.md)                         |
| `tracker_entity_patch_comment`              | `PATCH /v3/entities/{entityType}/{entityId}/comments/{commentId}`                  | modify | [entities/comments/patch-comment](https://yandex.ru/support/tracker/en/api/entities/comments/patch-comment.md)                     |
| `tracker_entity_get_comments`               | `GET /v3/entities/{entityType}/{entityId}/comments`                                | read   | [entities/comments/get-all-comments](https://yandex.ru/support/tracker/en/api/entities/comments/get-all-comments.md)               |
| `tracker_entity_get_comments_relative`      | `GET /v3/entities/{entityType}/{entityId}/comments/_relative`                      | read   | [entities/comments/get-all-comments](https://yandex.ru/support/tracker/en/api/entities/comments/get-all-comments.md)               |
| `tracker_entity_get_comment`                | `GET /v3/entities/{entityType}/{entityId}/comments/{commentId}`                    | read   | [entities/comments/get-comment](https://yandex.ru/support/tracker/en/api/entities/comments/get-comment.md)                         |
| `tracker_entity_delete_comment`             | `DELETE /v3/entities/{entityType}/{entityId}/comments/{commentId}`                 | modify | [entities/comments/delete-comment](https://yandex.ru/support/tracker/en/api/entities/comments/delete-comment.md)                   |
| `tracker_entity_add_checklist_item`         | `POST /v3/entities/{entityType}/{entityId}/checklistItems`                         | create | [entities/checklists/add-checklist](https://yandex.ru/support/tracker/en/api/entities/checklists/add-checklist.md)                 |
| `tracker_entity_patch_checklist`            | `PATCH /v3/entities/{entityType}/{entityId}/checklistItems`                        | modify | [entities/checklists/patch-checklist](https://yandex.ru/support/tracker/en/api/entities/checklists/patch-checklist.md)             |
| `tracker_entity_patch_checklist_item`       | `PATCH /v3/entities/{entityType}/{entityId}/checklistItems/{checklistItemId}`      | modify | [entities/checklists/patch-checklist-item](https://yandex.ru/support/tracker/en/api/entities/checklists/patch-checklist-item.md)   |
| `tracker_entity_move_checklist_item`        | `POST /v3/entities/{entityType}/{entityId}/checklistItems/{checklistItemId}/_move` | modify | [entities/checklists/move-checklist-item](https://yandex.ru/support/tracker/en/api/entities/checklists/move-checklist-item.md)     |
| `tracker_entity_delete_checklist`           | `DELETE /v3/entities/{entityType}/{entityId}/checklistItems`                       | modify | [entities/checklists/delete-checklist](https://yandex.ru/support/tracker/en/api/entities/checklists/delete-checklist.md)           |
| `tracker_entity_delete_checklist_item`      | `DELETE /v3/entities/{entityType}/{entityId}/checklistItems/{checklistItemId}`     | modify | [entities/checklists/delete-checklist-item](https://yandex.ru/support/tracker/en/api/entities/checklists/delete-checklist-item.md) |
| `tracker_entity_get_attachments`            | `GET /v3/entities/{entityType}/{entityId}/attachments`                             | read   | [entities/attachments/get-all-attachments](https://yandex.ru/support/tracker/en/api/entities/attachments/get-all-attachments.md)   |
| `tracker_entity_get_attachment`             | `GET /v3/entities/{entityType}/{entityId}/attachments/{fileId}`                    | read   | [entities/attachments/get-attachment](https://yandex.ru/support/tracker/en/api/entities/attachments/get-attachment.md)             |
| `tracker_entity_add_attachment`             | `POST /v3/entities/{entityType}/{entityId}/attachments/{fileId}`                   | create | [entities/attachments/add-attachment](https://yandex.ru/support/tracker/en/api/entities/attachments/add-attachment.md)             |
| `tracker_entity_delete_attachment`          | `DELETE /v3/entities/{entityType}/{entityId}/attachments/{fileId}`                 | modify | [entities/attachments/delete-attachment](https://yandex.ru/support/tracker/en/api/entities/attachments/delete-attachment.md)       |
| `tracker_entity_add_links`                  | `POST /v3/entities/{entityType}/{entityId}/links`                                  | create | [entities/links/add-links](https://yandex.ru/support/tracker/en/api/entities/links/add-links.md)                                   |
| `tracker_entity_get_links`                  | `GET /v3/entities/{entityType}/{entityId}/links`                                   | read   | [entities/links/get-links](https://yandex.ru/support/tracker/en/api/entities/links/get-links.md)                                   |
| `tracker_entity_delete_link`                | `DELETE /v3/entities/{entityType}/{entityId}/links`                                | modify | [entities/links/delete-link](https://yandex.ru/support/tracker/en/api/entities/links/delete-link.md)                               |
| `tracker_entity_get_permissions`            | `GET /v3/entities/{entityType}/{entityId}/permissions`                             | read   | [entities/get-access](https://yandex.ru/support/tracker/en/api/entities/get-access.md)                                             |
| `tracker_entity_get_extended_permissions`   | `GET /v3/entities/{entityType}/{entityId}/extendedPermissions`                     | read   | [entities/get-access](https://yandex.ru/support/tracker/en/api/entities/get-access.md)                                             |
| `tracker_entity_patch_permissions`          | `PATCH /v3/entities/{entityType}/{entityId}/permissions`                           | modify | [entities/patch-access](https://yandex.ru/support/tracker/en/api/entities/patch-access.md)                                         |
| `tracker_entity_patch_extended_permissions` | `PATCH /v3/entities/{entityType}/{entityId}/extendedPermissions`                   | modify | [entities/patch-access](https://yandex.ru/support/tracker/en/api/entities/patch-access.md)                                         |

### Reference dictionaries — 12 tools

Issue types, statuses, resolutions and priorities.

| Tool                        | Endpoint                               | Effect | Documentation                                                                                  |
| --------------------------- | -------------------------------------- | ------ | ---------------------------------------------------------------------------------------------- |
| `tracker_get_issuetypes`    | `GET /v3/issuetypes`                   | read   | [admin/get-issue-types](https://yandex.ru/support/tracker/en/api/admin/get-issue-types.md)     |
| `tracker_create_issuetype`  | `POST /v3/issuetypes/`                 | create | [admin/create-issue-type](https://yandex.ru/support/tracker/en/api/admin/create-issue-type.md) |
| `tracker_patch_issuetype`   | `PATCH /v3/issuetypes/{issueTypeId}`   | modify | [admin/patch-issue-type](https://yandex.ru/support/tracker/en/api/admin/patch-issue-type.md)   |
| `tracker_get_statuses`      | `GET /v3/statuses`                     | read   | [admin/get-statuses](https://yandex.ru/support/tracker/en/api/admin/get-statuses.md)           |
| `tracker_create_status`     | `POST /v3/statuses/`                   | create | [admin/create-status](https://yandex.ru/support/tracker/en/api/admin/create-status.md)         |
| `tracker_patch_status`      | `PATCH /v3/statuses/{statusId}`        | modify | [admin/patch-status](https://yandex.ru/support/tracker/en/api/admin/patch-status.md)           |
| `tracker_get_resolutions`   | `GET /v3/resolutions`                  | read   | [admin/get-resolutions](https://yandex.ru/support/tracker/en/api/admin/get-resolutions.md)     |
| `tracker_create_resolution` | `POST /v3/resolutions/`                | create | [admin/create-resolution](https://yandex.ru/support/tracker/en/api/admin/create-resolution.md) |
| `tracker_patch_resolution`  | `PATCH /v3/resolutions/{resolutionId}` | modify | [admin/patch-resolution](https://yandex.ru/support/tracker/en/api/admin/patch-resolution.md)   |
| `tracker_get_priorities`    | `GET /v3/priorities`                   | read   | [admin/get-priorities](https://yandex.ru/support/tracker/en/api/admin/get-priorities.md)       |
| `tracker_create_priority`   | `POST /v3/priorities/`                 | create | [admin/create-priority](https://yandex.ru/support/tracker/en/api/admin/create-priority.md)     |
| `tracker_patch_priority`    | `PATCH /v3/priorities/{priorityId}`    | modify | [admin/patch-priority](https://yandex.ru/support/tracker/en/api/admin/patch-priority.md)       |

### Users — 4 tools

The organization's users and the token owner.

| Tool                         | Endpoint                  | Effect | Documentation                                                                                    |
| ---------------------------- | ------------------------- | ------ | ------------------------------------------------------------------------------------------------ |
| `tracker_get_myself`         | `GET /v3/myself`          | read   | [users/get-user-info](https://yandex.ru/support/tracker/en/api/users/get-user-info.md)           |
| `tracker_get_users`          | `GET /v3/users`           | read   | [users/get-users](https://yandex.ru/support/tracker/en/api/users/get-users.md)                   |
| `tracker_get_user`           | `GET /v3/users/{userId}`  | read   | [users/get-user](https://yandex.ru/support/tracker/en/api/users/get-user.md)                     |
| `tracker_get_users_relative` | `GET /v3/users/_relative` | read   | [users/get-users-relative](https://yandex.ru/support/tracker/en/api/users/get-users-relative.md) |

<!-- tools:end -->
