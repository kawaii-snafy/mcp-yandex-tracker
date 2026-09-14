# Tool reference

This server is a thin wrapper over the [Yandex Tracker REST API
v3](https://yandex.ru/support/tracker/en/llms.txt): **one tool per documented
endpoint**, the API's own parameter names on the way in, the API's own JSON on
the way out.

That is why this page is an index rather than a copy of Yandex's argument tables.
The documentation is the reference — every row below links to the page its tool
was written from, and every tool repeats that link in its own description, so an
agent holding the tool already holds the way to the spec.

Naming follows the endpoint, not the SDK this server used to wrap: path
placeholders become camelCase arguments (`<issue_ID>` → `issueId`), and query and
body parameters keep the API's spelling (`perPage`, `expand`, `markupType`).

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
{"jsonrpc":"2.0","id":7,"method":"tools/call",
 "params":{"name":"tracker_get_issue","arguments":{"issueId":"TEST-1","expand":"attachments"}}}
```

## Where the wrapper is not literal

Seven places where a tool cannot be a byte-for-byte mirror of its endpoint. There
are no others.

| What | Why |
| --- | --- |
| `from_` on `tracker_get_worklog`, `tracker_get_entity_events`, `tracker_entity_get_comments_relative`, `tracker_get_trigger_webhook_log` | `from` is a Python keyword. It goes on the wire as `from`; this is the only argument name in the server that differs from the API. |
| `destDir` / `saveAs` on `tracker_get_attachment`, `tracker_get_attachment_preview` | Those endpoints return a file. An MCP result is text, so the tool streams the bytes to a local directory and returns `{"path", "name", "size"}`. |
| `filePath` on `tracker_post_attachment`, `tracker_post_temp_attachment` | Those endpoints take `multipart/form-data`. The tool reads the local path and sends it as the documented `file` part. |
| `version` on the board, column and sprint edits | Those pages document it as the `If-Match: "<version>"` header rather than a parameter. Elsewhere (`tracker_patch_issue`, the workflow / trigger / component / dictionary edits) `version` is a real query parameter and is passed as one. |
| `page` on `tracker_search_issues`, `tracker_get_users`, `tracker_get_queues` | Those pages describe the result as paginated and link to [common-format](https://yandex.ru/support/tracker/en/api/common-format.md) instead of repeating the parameters. `perPage` + `page` come from there. |
| The nine `relationship` values in `tracker_link_issue`'s description | No endpoint in the API lists link types, so the values enumerated on [link-issue](https://yandex.ru/support/tracker/en/api/issues/link-issue.md) are the only place to learn them. |
| `commentId` on `tracker_entity_patch_comment`; the per-item body of `tracker_edit_checklist_item` | Those two pages contradict themselves (summary vs resource table, example vs parameter table). Both tools follow the page's parameter table, which matches the path — and that is what the endpoint accepts in practice. |

## The tools

### Issues — 48 tools

Issues, comments, checklists, attachments, worklog, links, transitions and the field dictionary.

| Tool | Endpoint | Documentation |
| --- | --- | --- |
| `tracker_create_issue` | `POST /v3/issues/` | [issues/create-issue](https://yandex.ru/support/tracker/en/api/issues/create-issue.md) |
| `tracker_get_issue` | `GET /v3/issues/{issueId}` | [issues/get-issue](https://yandex.ru/support/tracker/en/api/issues/get-issue.md) |
| `tracker_patch_issue` | `PATCH /v3/issues/{issueId}` | [issues/patch-issue](https://yandex.ru/support/tracker/en/api/issues/patch-issue.md) |
| `tracker_move_issue` | `POST /v3/issues/{issueId}/_move` | [issues/move-issue](https://yandex.ru/support/tracker/en/api/issues/move-issue.md) |
| `tracker_search_issues` | `POST /v3/issues/_search` | [issues/search-issues](https://yandex.ru/support/tracker/en/api/issues/search-issues.md) |
| `tracker_count_issues` | `POST /v3/issues/_count` | [issues/count-issues](https://yandex.ru/support/tracker/en/api/issues/count-issues.md) |
| `tracker_get_suggest` | `GET /v3/issues/_suggest` | [issues/get-suggest](https://yandex.ru/support/tracker/en/api/issues/get-suggest.md) |
| `tracker_clear_scroll` | `POST /v3/system/search/scroll/_clear` | [issues/search-release](https://yandex.ru/support/tracker/en/api/issues/search-release.md) |
| `tracker_get_changelog` | `GET /v3/issues/{issueId}/changelog` | [issues/get-changelog](https://yandex.ru/support/tracker/en/api/issues/get-changelog.md) |
| `tracker_link_issue` | `POST /v3/issues/{issueId}/links` | [issues/link-issue](https://yandex.ru/support/tracker/en/api/issues/link-issue.md) |
| `tracker_get_links` | `GET /v3/issues/{issueId}/links` | [issues/get-links](https://yandex.ru/support/tracker/en/api/issues/get-links.md) |
| `tracker_delete_link` | `DELETE /v3/issues/{issueId}/links/{linkId}` | [issues/delete-link-issue](https://yandex.ru/support/tracker/en/api/issues/delete-link-issue.md) |
| `tracker_get_external_links` | `GET /v3/issues/{issueId}/remotelinks` | [issues/get-external-links](https://yandex.ru/support/tracker/en/api/issues/get-external-links.md) |
| `tracker_add_external_link` | `POST /v3/issues/{issueId}/remotelinks` | [issues/add-external-link](https://yandex.ru/support/tracker/en/api/issues/add-external-link.md) |
| `tracker_delete_external_link` | `DELETE /v3/issues/{issueId}/remotelinks/{externalLinkId}` | [issues/delete-external-link](https://yandex.ru/support/tracker/en/api/issues/delete-external-link.md) |
| `tracker_get_transitions` | `GET /v3/issues/{issueId}/transitions` | [issues/get-transitions](https://yandex.ru/support/tracker/en/api/issues/get-transitions.md) |
| `tracker_new_transition` | `POST /v3/issues/{issueId}/transitions/{transitionId}/_execute` | [issues/new-transition](https://yandex.ru/support/tracker/en/api/issues/new-transition.md) |
| `tracker_add_comment` | `POST /v3/issues/{issueId}/comments` | [issues/add-comment](https://yandex.ru/support/tracker/en/api/issues/add-comment.md) |
| `tracker_get_comments` | `GET /v3/issues/{issueId}/comments` | [issues/get-comments](https://yandex.ru/support/tracker/en/api/issues/get-comments.md) |
| `tracker_edit_comment` | `PATCH /v3/issues/{issueId}/comments/{commentId}` | [issues/edit-comment](https://yandex.ru/support/tracker/en/api/issues/edit-comment.md) |
| `tracker_delete_comment` | `DELETE /v3/issues/{issueId}/comments/{commentId}` | [issues/delete-comment](https://yandex.ru/support/tracker/en/api/issues/delete-comment.md) |
| `tracker_add_reaction_to_comment` | `POST /v3/issues/{issueId}/comments/{commentId}/reactions/{reactionName}` | [issues/add-reaction-to-comment](https://yandex.ru/support/tracker/en/api/issues/add-reaction-to-comment.md) |
| `tracker_add_checklist_item` | `POST /v3/issues/{issueId}/checklistItems` | [issues/add-checklist-item](https://yandex.ru/support/tracker/en/api/issues/add-checklist-item.md) |
| `tracker_get_checklist` | `GET /v3/issues/{issueId}/checklistItems` | [issues/get-checklist](https://yandex.ru/support/tracker/en/api/issues/get-checklist.md) |
| `tracker_edit_checklist_item` | `PATCH /v3/issues/{issueId}/checklistItems/{checklistItemId}` | [issues/edit-checklist](https://yandex.ru/support/tracker/en/api/issues/edit-checklist.md) |
| `tracker_delete_checklist` | `DELETE /v3/issues/{issueId}/checklistItems` | [issues/delete-checklist](https://yandex.ru/support/tracker/en/api/issues/delete-checklist.md) |
| `tracker_delete_checklist_item` | `DELETE /v3/issues/{issueId}/checklistItems/{checklistItemId}` | [issues/delete-checklist-item](https://yandex.ru/support/tracker/en/api/issues/delete-checklist-item.md) |
| `tracker_get_attachments` | `GET /v3/issues/{issueId}/attachments` | [issues/get-attachments-list](https://yandex.ru/support/tracker/en/api/issues/get-attachments-list.md) |
| `tracker_get_attachment` | `GET /v3/issues/{issueId}/attachments/{fileId}/{fileName}` | [issues/get-attachment](https://yandex.ru/support/tracker/en/api/issues/get-attachment.md) |
| `tracker_get_attachment_preview` | `GET /v3/issues/{issueId}/thumbnails/{fileId}` | [issues/get-attachment-preview](https://yandex.ru/support/tracker/en/api/issues/get-attachment-preview.md) |
| `tracker_post_attachment` | `POST /v3/issues/{issueId}/attachments/` | [issues/post-attachment](https://yandex.ru/support/tracker/en/api/issues/post-attachment.md) |
| `tracker_post_temp_attachment` | `POST /v3/attachments/` | [issues/temp-attachment](https://yandex.ru/support/tracker/en/api/issues/temp-attachment.md) |
| `tracker_delete_attachment` | `DELETE /v3/issues/{issueId}/attachments/{fileId}/` | [issues/delete-attachment](https://yandex.ru/support/tracker/en/api/issues/delete-attachment.md) |
| `tracker_new_worklog` | `POST /v3/issues/{issueId}/worklog` | [issues/new-worklog](https://yandex.ru/support/tracker/en/api/issues/new-worklog.md) |
| `tracker_get_issue_worklog` | `GET /v3/issues/{issueId}/worklog` | [issues/issue-worklog](https://yandex.ru/support/tracker/en/api/issues/issue-worklog.md) |
| `tracker_patch_worklog` | `PATCH /v3/issues/{issueId}/worklog/{recordId}` | [issues/patch-worklog](https://yandex.ru/support/tracker/en/api/issues/patch-worklog.md) |
| `tracker_delete_worklog` | `DELETE /v3/issues/{issueId}/worklog/{recordId}` | [issues/delete-worklog](https://yandex.ru/support/tracker/en/api/issues/delete-worklog.md) |
| `tracker_get_worklog` | `GET /v3/worklog` | [issues/get-worklog](https://yandex.ru/support/tracker/en/api/issues/get-worklog.md) |
| `tracker_search_worklog` | `POST /v3/worklog/_search` | [issues/get-worklog](https://yandex.ru/support/tracker/en/api/issues/get-worklog.md) |
| `tracker_get_global_fields` | `GET /v3/fields` | [issues/get-global-fields](https://yandex.ru/support/tracker/en/api/issues/get-global-fields.md) |
| `tracker_create_field` | `POST /v3/fields` | [issues/create-field](https://yandex.ru/support/tracker/en/api/issues/create-field.md) |
| `tracker_get_field` | `GET /v3/fields/{fieldId}` | [issues/get-issue-fields](https://yandex.ru/support/tracker/en/api/issues/get-issue-fields.md) |
| `tracker_patch_field` | `PATCH /v3/fields/{fieldId}` | [issues/patch-issue-field-name](https://yandex.ru/support/tracker/en/api/issues/patch-issue-field-name.md) |
| `tracker_create_field_category` | `POST /v3/fields/categories` | [issues/create-issue-field-category](https://yandex.ru/support/tracker/en/api/issues/create-issue-field-category.md) |
| `tracker_patch_field_category` | `PATCH /v3/fields/categories/{categoryId}` | [issues/patch-issue-field-category](https://yandex.ru/support/tracker/en/api/issues/patch-issue-field-category.md) |
| `tracker_get_applications` | `GET /v3/applications` | [issues/get-applications](https://yandex.ru/support/tracker/en/api/issues/get-applications.md) |
| `tracker_create_report` | `POST /v3/entities/report/` | [issues/create-report](https://yandex.ru/support/tracker/en/api/issues/create-report.md) |
| `tracker_search_reports` | `POST /v3/entities/report/_search` | [issues/search-reports](https://yandex.ru/support/tracker/en/api/issues/search-reports.md) |

### Queues — 37 tools

Queues, versions, tags, permissions, local fields, workflows, triggers, autoactions and components.

| Tool | Endpoint | Documentation |
| --- | --- | --- |
| `tracker_create_queue` | `POST /v3/queues/` | [queues/create-queue](https://yandex.ru/support/tracker/en/api/queues/create-queue.md) |
| `tracker_get_queues` | `GET /v3/queues/` | [queues/get-queues](https://yandex.ru/support/tracker/en/api/queues/get-queues.md) |
| `tracker_get_queue` | `GET /v3/queues/{queueId}` | [queues/get-queue](https://yandex.ru/support/tracker/en/api/queues/get-queue.md) |
| `tracker_delete_queue` | `DELETE /v3/queues/{queueId}` | [queues/delete-queue](https://yandex.ru/support/tracker/en/api/queues/delete-queue.md) |
| `tracker_restore_queue` | `POST /v3/queues/{queueId}/_restore` | [queues/restore-queue](https://yandex.ru/support/tracker/en/api/queues/restore-queue.md) |
| `tracker_get_queue_fields` | `GET /v3/queues/{queueId}/fields` | [queues/get-fields](https://yandex.ru/support/tracker/en/api/queues/get-fields.md) |
| `tracker_get_queue_versions` | `GET /v3/queues/{queueId}/versions` | [queues/get-versions](https://yandex.ru/support/tracker/en/api/queues/get-versions.md) |
| `tracker_create_version` | `POST /v3/versions/` | [queues/create-version](https://yandex.ru/support/tracker/en/api/queues/create-version.md) |
| `tracker_get_queue_tags` | `GET /v3/queues/{queueId}/tags` | [queues/get-tags](https://yandex.ru/support/tracker/en/api/queues/get-tags.md) |
| `tracker_delete_queue_tag` | `POST /v3/queues/{queueId}/tags/_remove` | [queues/delete-tag](https://yandex.ru/support/tracker/en/api/queues/delete-tag.md) |
| `tracker_patch_queue_permissions` | `PATCH /v3/queues/{queueId}/permissions` | [queues/manage-access](https://yandex.ru/support/tracker/en/api/queues/manage-access.md) |
| `tracker_get_queue_user_access` | `GET /v3/queues/{queueId}/permissions/users/{userId}` | [queues/get-user-access](https://yandex.ru/support/tracker/en/api/queues/get-user-access.md) |
| `tracker_get_queue_group_access` | `GET /v3/queues/{queueId}/permissions/groups/{groupId}` | [queues/get-group-access](https://yandex.ru/support/tracker/en/api/queues/get-group-access.md) |
| `tracker_create_local_field` | `POST /v3/queues/{queueId}/localFields` | [queues/create-local-field](https://yandex.ru/support/tracker/en/api/queues/create-local-field.md) |
| `tracker_get_local_fields` | `GET /v3/queues/{queueId}/localFields` | [queues/get-local-fields](https://yandex.ru/support/tracker/en/api/queues/get-local-fields.md) |
| `tracker_get_local_field` | `GET /v3/queues/{queueId}/localFields/{fieldKey}` | [queues/get-info-local-field](https://yandex.ru/support/tracker/en/api/queues/get-info-local-field.md) |
| `tracker_patch_local_field` | `PATCH /v3/queues/{queueId}/localFields/{fieldKey}` | [queues/edit-local-field](https://yandex.ru/support/tracker/en/api/queues/edit-local-field.md) |
| `tracker_create_workflow` | `POST /v3/workflows` | [queues/workflows/post-workflow](https://yandex.ru/support/tracker/en/api/queues/workflows/post-workflow.md) |
| `tracker_get_workflows` | `GET /v3/workflows` | [queues/workflows/get-workflows](https://yandex.ru/support/tracker/en/api/queues/workflows/get-workflows.md) |
| `tracker_get_workflow` | `GET /v3/workflows/{workflowId}` | [queues/workflows/get-workflow](https://yandex.ru/support/tracker/en/api/queues/workflows/get-workflow.md) |
| `tracker_patch_workflow` | `PATCH /v3/workflows/{workflowId}` | [queues/workflows/patch-workflow](https://yandex.ru/support/tracker/en/api/queues/workflows/patch-workflow.md) |
| `tracker_patch_workflow_action` | `PATCH /v3/workflows/{workflowId}/steps/{status}/actions/{actionId}` | [queues/workflows/patch-workflow-action](https://yandex.ru/support/tracker/en/api/queues/workflows/patch-workflow-action.md) |
| `tracker_delete_workflow` | `DELETE /v3/workflows/{workflowId}` | [queues/workflows/delete-workflow](https://yandex.ru/support/tracker/en/api/queues/workflows/delete-workflow.md) |
| `tracker_create_autoaction` | `POST /v3/queues/{queueId}/autoactions` | [queues/create-autoaction](https://yandex.ru/support/tracker/en/api/queues/create-autoaction.md) |
| `tracker_get_autoaction` | `GET /v3/queues/{queueId}/autoactions/{autoactionId}` | [queues/get-autoaction](https://yandex.ru/support/tracker/en/api/queues/get-autoaction.md) |
| `tracker_get_autoaction_logs` | `GET /v3/queues/{queueId}/autoactions/{autoactionId}/logs` | [queues/view-autoaction-logs](https://yandex.ru/support/tracker/en/api/queues/view-autoaction-logs.md) |
| `tracker_get_autoaction_run_log` | `GET /v3/queues/{queueId}/autoactions/{autoactionId}/logs/{runId}` | [queues/view-autoaction-logs](https://yandex.ru/support/tracker/en/api/queues/view-autoaction-logs.md) |
| `tracker_create_trigger` | `POST /v3/queues/{queueId}/triggers` | [queues/create-trigger](https://yandex.ru/support/tracker/en/api/queues/create-trigger.md) |
| `tracker_get_triggers` | `GET /v3/queues/{queueId}/triggers` | [queues/get-triggers](https://yandex.ru/support/tracker/en/api/queues/get-triggers.md) |
| `tracker_get_trigger` | `GET /v3/queues/{queueId}/triggers/{triggerId}` | [queues/get-trigger](https://yandex.ru/support/tracker/en/api/queues/get-trigger.md) |
| `tracker_patch_trigger` | `PATCH /v3/queues/{queueId}/triggers/{triggerId}` | [queues/change-trigger](https://yandex.ru/support/tracker/en/api/queues/change-trigger.md) |
| `tracker_get_trigger_webhook_log` | `GET /v3/queues/{queueId}/triggers/{triggerId}/webhooks/log` | [queues/view-trigger-logs](https://yandex.ru/support/tracker/en/api/queues/view-trigger-logs.md) |
| `tracker_get_components` | `GET /v3/components` | [queues/get-components](https://yandex.ru/support/tracker/en/api/queues/get-components.md) |
| `tracker_create_component` | `POST /v3/components` | [queues/post-component](https://yandex.ru/support/tracker/en/api/queues/post-component.md) |
| `tracker_patch_component` | `PATCH /v3/components/{componentId}` | [queues/patch-component](https://yandex.ru/support/tracker/en/api/queues/patch-component.md) |
| `tracker_get_component_user_access` | `GET /v3/components/{componentId}/permissions/users/{userId}` | [queues/get-component-user-access](https://yandex.ru/support/tracker/en/api/queues/get-component-user-access.md) |
| `tracker_get_component_group_access` | `GET /v3/components/{componentId}/permissions/groups/{groupId}` | [queues/get-component-group-access](https://yandex.ru/support/tracker/en/api/queues/get-component-group-access.md) |

### Boards & sprints — 18 tools

Boards, their columns, and sprints.

| Tool | Endpoint | Documentation |
| --- | --- | --- |
| `tracker_get_boards` | `GET /v3/boards` | [boards/get-boards](https://yandex.ru/support/tracker/en/api/boards/get-boards.md) |
| `tracker_get_boards_paginate` | `GET /v3/boards/_paginate` | [boards/get-boards-paginate](https://yandex.ru/support/tracker/en/api/boards/get-boards-paginate.md) |
| `tracker_get_board` | `GET /v3/boards/{boardId}` | [boards/get-board](https://yandex.ru/support/tracker/en/api/boards/get-board.md) |
| `tracker_create_board` | `POST /v3/boards/` | [boards/post-board](https://yandex.ru/support/tracker/en/api/boards/post-board.md) |
| `tracker_patch_board` | `PATCH /v3/boards/{boardId}` | [boards/patch-board](https://yandex.ru/support/tracker/en/api/boards/patch-board.md) |
| `tracker_delete_board` | `DELETE /v3/boards/{boardId}` | [boards/delete-board](https://yandex.ru/support/tracker/en/api/boards/delete-board.md) |
| `tracker_get_board_columns` | `GET /v3/boards/{boardId}/columns` | [boards/get-columns](https://yandex.ru/support/tracker/en/api/boards/get-columns.md) |
| `tracker_get_board_column` | `GET /v3/boards/{boardId}/columns/{columnId}` | [boards/get-column](https://yandex.ru/support/tracker/en/api/boards/get-column.md) |
| `tracker_create_board_column` | `POST /v3/boards/{boardId}/columns/` | [boards/post-column](https://yandex.ru/support/tracker/en/api/boards/post-column.md) |
| `tracker_patch_board_column` | `PATCH /v3/boards/{boardId}/columns/{columnId}` | [boards/patch-column](https://yandex.ru/support/tracker/en/api/boards/patch-column.md) |
| `tracker_delete_board_column` | `DELETE /v3/boards/{boardId}/columns/{columnId}` | [boards/delete-column](https://yandex.ru/support/tracker/en/api/boards/delete-column.md) |
| `tracker_get_board_sprints` | `GET /v3/boards/{boardId}/sprints` | [boards/get-sprints](https://yandex.ru/support/tracker/en/api/boards/get-sprints.md) |
| `tracker_get_sprint` | `GET /v3/sprints/{sprintId}` | [boards/get-sprint](https://yandex.ru/support/tracker/en/api/boards/get-sprint.md) |
| `tracker_create_sprint` | `POST /v3/sprints` | [boards/post-sprint](https://yandex.ru/support/tracker/en/api/boards/post-sprint.md) |
| `tracker_patch_sprint` | `PATCH /v3/sprints/{sprintId}` | [boards/patch-sprint](https://yandex.ru/support/tracker/en/api/boards/patch-sprint.md) |
| `tracker_start_sprint` | `POST /v3/sprints/{sprintId}/_start` | [boards/start-sprint](https://yandex.ru/support/tracker/en/api/boards/start-sprint.md) |
| `tracker_archive_sprint` | `POST /v3/sprints/{sprintId}/_archive` | [boards/archive-sprint](https://yandex.ru/support/tracker/en/api/boards/archive-sprint.md) |
| `tracker_delete_sprint` | `DELETE /v3/sprints/{sprintId}` | [boards/delete-sprint](https://yandex.ru/support/tracker/en/api/boards/delete-sprint.md) |

### Projects, portfolios & goals — 30 tools

The `entities` API, with their comments, checklists, attachments, links and permissions.

| Tool | Endpoint | Documentation |
| --- | --- | --- |
| `tracker_create_entity` | `POST /v3/entities/{entityType}` | [entities/create-entity](https://yandex.ru/support/tracker/en/api/entities/create-entity.md) |
| `tracker_get_entity` | `GET /v3/entities/{entityType}/{entityId}` | [entities/get-entity](https://yandex.ru/support/tracker/en/api/entities/get-entity.md) |
| `tracker_update_entity` | `PATCH /v3/entities/{entityType}/{entityId}` | [entities/update-entity](https://yandex.ru/support/tracker/en/api/entities/update-entity.md) |
| `tracker_delete_entity` | `DELETE /v3/entities/{entityType}/{entityId}` | [entities/delete-entity](https://yandex.ru/support/tracker/en/api/entities/delete-entity.md) |
| `tracker_search_entities` | `POST /v3/entities/{entityType}/_search` | [entities/search-entities](https://yandex.ru/support/tracker/en/api/entities/search-entities.md) |
| `tracker_bulkchange_entities` | `POST /v3/entities/{entityType}/bulkchange/_update` | [entities/bulkchange-entities](https://yandex.ru/support/tracker/en/api/entities/bulkchange-entities.md) |
| `tracker_get_entity_events` | `GET /v3/entities/{entityType}/{entityId}/events/_relative` | [entities/get-events-relative](https://yandex.ru/support/tracker/en/api/entities/get-events-relative.md) |
| `tracker_entity_add_comment` | `POST /v3/entities/{entityType}/{entityId}/comments` | [entities/comments/add-comment](https://yandex.ru/support/tracker/en/api/entities/comments/add-comment.md) |
| `tracker_entity_patch_comment` | `PATCH /v3/entities/{entityType}/{entityId}/comments/{commentId}` | [entities/comments/patch-comment](https://yandex.ru/support/tracker/en/api/entities/comments/patch-comment.md) |
| `tracker_entity_get_comments` | `GET /v3/entities/{entityType}/{entityId}/comments` | [entities/comments/get-all-comments](https://yandex.ru/support/tracker/en/api/entities/comments/get-all-comments.md) |
| `tracker_entity_get_comments_relative` | `GET /v3/entities/{entityType}/{entityId}/comments/_relative` | [entities/comments/get-all-comments](https://yandex.ru/support/tracker/en/api/entities/comments/get-all-comments.md) |
| `tracker_entity_get_comment` | `GET /v3/entities/{entityType}/{entityId}/comments/{commentId}` | [entities/comments/get-comment](https://yandex.ru/support/tracker/en/api/entities/comments/get-comment.md) |
| `tracker_entity_delete_comment` | `DELETE /v3/entities/{entityType}/{entityId}/comments/{commentId}` | [entities/comments/delete-comment](https://yandex.ru/support/tracker/en/api/entities/comments/delete-comment.md) |
| `tracker_entity_add_checklist_item` | `POST /v3/entities/{entityType}/{entityId}/checklistItems` | [entities/checklists/add-checklist](https://yandex.ru/support/tracker/en/api/entities/checklists/add-checklist.md) |
| `tracker_entity_patch_checklist` | `PATCH /v3/entities/{entityType}/{entityId}/checklistItems` | [entities/checklists/patch-checklist](https://yandex.ru/support/tracker/en/api/entities/checklists/patch-checklist.md) |
| `tracker_entity_patch_checklist_item` | `PATCH /v3/entities/{entityType}/{entityId}/checklistItems/{checklistItemId}` | [entities/checklists/patch-checklist-item](https://yandex.ru/support/tracker/en/api/entities/checklists/patch-checklist-item.md) |
| `tracker_entity_move_checklist_item` | `POST /v3/entities/{entityType}/{entityId}/checklistItems/{checklistItemId}/_move` | [entities/checklists/move-checklist-item](https://yandex.ru/support/tracker/en/api/entities/checklists/move-checklist-item.md) |
| `tracker_entity_delete_checklist` | `DELETE /v3/entities/{entityType}/{entityId}/checklistItems` | [entities/checklists/delete-checklist](https://yandex.ru/support/tracker/en/api/entities/checklists/delete-checklist.md) |
| `tracker_entity_delete_checklist_item` | `DELETE /v3/entities/{entityType}/{entityId}/checklistItems/{checklistItemId}` | [entities/checklists/delete-checklist-item](https://yandex.ru/support/tracker/en/api/entities/checklists/delete-checklist-item.md) |
| `tracker_entity_get_attachments` | `GET /v3/entities/{entityType}/{entityId}/attachments` | [entities/attachments/get-all-attachments](https://yandex.ru/support/tracker/en/api/entities/attachments/get-all-attachments.md) |
| `tracker_entity_get_attachment` | `GET /v3/entities/{entityType}/{entityId}/attachments/{fileId}` | [entities/attachments/get-attachment](https://yandex.ru/support/tracker/en/api/entities/attachments/get-attachment.md) |
| `tracker_entity_add_attachment` | `POST /v3/entities/{entityType}/{entityId}/attachments/{fileId}` | [entities/attachments/add-attachment](https://yandex.ru/support/tracker/en/api/entities/attachments/add-attachment.md) |
| `tracker_entity_delete_attachment` | `DELETE /v3/entities/{entityType}/{entityId}/attachments/{fileId}` | [entities/attachments/delete-attachment](https://yandex.ru/support/tracker/en/api/entities/attachments/delete-attachment.md) |
| `tracker_entity_add_links` | `POST /v3/entities/{entityType}/{entityId}/links` | [entities/links/add-links](https://yandex.ru/support/tracker/en/api/entities/links/add-links.md) |
| `tracker_entity_get_links` | `GET /v3/entities/{entityType}/{entityId}/links` | [entities/links/get-links](https://yandex.ru/support/tracker/en/api/entities/links/get-links.md) |
| `tracker_entity_delete_link` | `DELETE /v3/entities/{entityType}/{entityId}/links` | [entities/links/delete-link](https://yandex.ru/support/tracker/en/api/entities/links/delete-link.md) |
| `tracker_entity_get_permissions` | `GET /v3/entities/{entityType}/{entityId}/permissions` | [entities/get-access](https://yandex.ru/support/tracker/en/api/entities/get-access.md) |
| `tracker_entity_get_extended_permissions` | `GET /v3/entities/{entityType}/{entityId}/extendedPermissions` | [entities/get-access](https://yandex.ru/support/tracker/en/api/entities/get-access.md) |
| `tracker_entity_patch_permissions` | `PATCH /v3/entities/{entityType}/{entityId}/permissions` | [entities/patch-access](https://yandex.ru/support/tracker/en/api/entities/patch-access.md) |
| `tracker_entity_patch_extended_permissions` | `PATCH /v3/entities/{entityType}/{entityId}/extendedPermissions` | [entities/patch-access](https://yandex.ru/support/tracker/en/api/entities/patch-access.md) |

### Reference dictionaries — 12 tools

Issue types, statuses, resolutions and priorities.

| Tool | Endpoint | Documentation |
| --- | --- | --- |
| `tracker_get_issuetypes` | `GET /v3/issuetypes` | [admin/get-issue-types](https://yandex.ru/support/tracker/en/api/admin/get-issue-types.md) |
| `tracker_create_issuetype` | `POST /v3/issuetypes/` | [admin/create-issue-type](https://yandex.ru/support/tracker/en/api/admin/create-issue-type.md) |
| `tracker_patch_issuetype` | `PATCH /v3/issuetypes/{issueTypeId}` | [admin/patch-issue-type](https://yandex.ru/support/tracker/en/api/admin/patch-issue-type.md) |
| `tracker_get_statuses` | `GET /v3/statuses` | [admin/get-statuses](https://yandex.ru/support/tracker/en/api/admin/get-statuses.md) |
| `tracker_create_status` | `POST /v3/statuses/` | [admin/create-status](https://yandex.ru/support/tracker/en/api/admin/create-status.md) |
| `tracker_patch_status` | `PATCH /v3/statuses/{statusId}` | [admin/patch-status](https://yandex.ru/support/tracker/en/api/admin/patch-status.md) |
| `tracker_get_resolutions` | `GET /v3/resolutions` | [admin/get-resolutions](https://yandex.ru/support/tracker/en/api/admin/get-resolutions.md) |
| `tracker_create_resolution` | `POST /v3/resolutions/` | [admin/create-resolution](https://yandex.ru/support/tracker/en/api/admin/create-resolution.md) |
| `tracker_patch_resolution` | `PATCH /v3/resolutions/{resolutionId}` | [admin/patch-resolution](https://yandex.ru/support/tracker/en/api/admin/patch-resolution.md) |
| `tracker_get_priorities` | `GET /v3/priorities` | [admin/get-priorities](https://yandex.ru/support/tracker/en/api/admin/get-priorities.md) |
| `tracker_create_priority` | `POST /v3/priorities/` | [admin/create-priority](https://yandex.ru/support/tracker/en/api/admin/create-priority.md) |
| `tracker_patch_priority` | `PATCH /v3/priorities/{priorityId}` | [admin/patch-priority](https://yandex.ru/support/tracker/en/api/admin/patch-priority.md) |

### Users — 4 tools

The organization's users and the token owner.

| Tool | Endpoint | Documentation |
| --- | --- | --- |
| `tracker_get_myself` | `GET /v3/myself` | [users/get-user-info](https://yandex.ru/support/tracker/en/api/users/get-user-info.md) |
| `tracker_get_users` | `GET /v3/users` | [users/get-users](https://yandex.ru/support/tracker/en/api/users/get-users.md) |
| `tracker_get_user` | `GET /v3/users/{userId}` | [users/get-user](https://yandex.ru/support/tracker/en/api/users/get-user.md) |
| `tracker_get_users_relative` | `GET /v3/users/_relative` | [users/get-users-relative](https://yandex.ru/support/tracker/en/api/users/get-users-relative.md) |

