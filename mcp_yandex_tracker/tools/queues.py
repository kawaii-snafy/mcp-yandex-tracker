"""Queues, local fields, workflows, triggers and components — https://yandex.ru/support/tracker/en/api/queues/get-queues.md"""

from __future__ import annotations

from typing import Annotated, Any

from pydantic import Field

from ..client import given
from ..server import NonEmptyStr, get_client, tool


@tool
def tracker_create_queue(
    key: Annotated[NonEmptyStr, Field(description="Queue key.")],
    name: Annotated[NonEmptyStr, Field(description="Queue name.")],
    lead: Annotated[NonEmptyStr, Field(description="Username or ID of the queue owner.")],
    defaultType: Annotated[
        NonEmptyStr, Field(description="ID or key of the default issue type.")
    ],
    defaultPriority: Annotated[
        NonEmptyStr, Field(description="ID or key of the default issue priority.")
    ],
    issueTypesConfig: Annotated[
        list,
        Field(
            description=(
                "Settings of queue issue types, one object per issue type, each with "
                "`issueType` (issue type key), `workflow` (workflow ID, for example "
                "`hrPresetWorkflow`, `developmentPresetWorkflow` or "
                "`scrumDevelopmentPresetWorkflow`) and `resolutions` (array of resolution "
                "IDs or keys)."
            )
        ),
    ],
) -> Any:
    """Create a queue.

    POST /v3/queues/
    https://yandex.ru/support/tracker/en/api/queues/create-queue.md
    """
    return get_client().request(
        "POST",
        "/queues/",
        json=given(
            key=key,
            name=name,
            lead=lead,
            defaultType=defaultType,
            defaultPriority=defaultPriority,
            issueTypesConfig=issueTypesConfig,
        ),
    )


@tool
def tracker_get_queues(
    expand: Annotated[
        str | None,
        Field(
            description=(
                "Additional fields to include in the response: `projects`, `components`, "
                "`versions`, `types`, `team`, `workflows`."
            )
        ),
    ] = None,
    perPage: Annotated[
        int | None, Field(description="Number of queues per response page. Default 50.")
    ] = None,
    page: Annotated[int | None, Field(description="Page number. Default 1.")] = None,
) -> Any:
    """Get the list of available queues.

    GET /v3/queues/
    https://yandex.ru/support/tracker/en/api/queues/get-queues.md

    With more than 50 queues the result is paginated: `perPage` and `page` are
    the pagination parameters from common-format.md the endpoint page links to.
    """
    return get_client().request(
        "GET", "/queues/", params=given(expand=expand, perPage=perPage, page=page)
    )


@tool
def tracker_get_queue(
    queueId: Annotated[
        NonEmptyStr, Field(description="Queue ID or key. The queue key is case-sensitive.")
    ],
    expand: Annotated[
        str | None,
        Field(
            description=(
                "Additional fields to include in the response: `all`, `projects`, "
                "`components`, `versions`, `types`, `team`, `workflows`, `fields`, "
                "`issueTypesConfig`."
            )
        ),
    ] = None,
) -> Any:
    """Get information about a queue.

    GET /v3/queues/{queueId}
    https://yandex.ru/support/tracker/en/api/queues/get-queue.md

    This is also how you list the components of one queue: pass
    `expand=components`. GET /v3/components returns every component of the
    organization instead.
    """
    return get_client().request("GET", f"/queues/{queueId}", params=given(expand=expand))


@tool
def tracker_delete_queue(
    queueId: Annotated[
        NonEmptyStr, Field(description="Queue ID or key. The queue key is case-sensitive.")
    ],
) -> Any:
    """Delete a queue.

    DELETE /v3/queues/{queueId}
    https://yandex.ru/support/tracker/en/api/queues/delete-queue.md
    """
    return get_client().request("DELETE", f"/queues/{queueId}")


@tool
def tracker_restore_queue(
    queueId: Annotated[
        NonEmptyStr, Field(description="Queue ID or key. The queue key is case-sensitive.")
    ],
) -> Any:
    """Restore a deleted queue.

    POST /v3/queues/{queueId}/_restore
    https://yandex.ru/support/tracker/en/api/queues/restore-queue.md

    Only an organization administrator can make this request.
    """
    return get_client().request("POST", f"/queues/{queueId}/_restore")


@tool
def tracker_get_queue_fields(
    queueId: Annotated[
        NonEmptyStr, Field(description="Queue ID or key. The queue key is case-sensitive.")
    ],
) -> Any:
    """Get information about the required fields of a queue.

    GET /v3/queues/{queueId}/fields
    https://yandex.ru/support/tracker/en/api/queues/get-fields.md
    """
    return get_client().request("GET", f"/queues/{queueId}/fields")


@tool
def tracker_get_queue_versions(
    queueId: Annotated[
        NonEmptyStr, Field(description="Queue ID or key. The queue key is case-sensitive.")
    ],
) -> Any:
    """Get information about the versions of a queue.

    GET /v3/queues/{queueId}/versions
    https://yandex.ru/support/tracker/en/api/queues/get-versions.md
    """
    return get_client().request("GET", f"/queues/{queueId}/versions")


@tool
def tracker_create_version(
    queue: Annotated[NonEmptyStr, Field(description="Queue key.")],
    name: Annotated[NonEmptyStr, Field(description="Version name.")],
    description: Annotated[str | None, Field(description="Version description.")] = None,
    startDate: Annotated[
        str | None, Field(description="Version start date in `YYYY-MM-DD` format.")
    ] = None,
    dueDate: Annotated[
        str | None, Field(description="Version end date in `YYYY-MM-DD` format.")
    ] = None,
) -> Any:
    """Create a queue version.

    POST /v3/versions/
    https://yandex.ru/support/tracker/en/api/queues/create-version.md
    """
    return get_client().request(
        "POST",
        "/versions/",
        json=given(
            queue=queue,
            name=name,
            description=description,
            startDate=startDate,
            dueDate=dueDate,
        ),
    )


@tool
def tracker_get_queue_tags(
    queueId: Annotated[
        NonEmptyStr, Field(description="Queue ID or key. The queue key is case-sensitive.")
    ],
) -> Any:
    """Get the list of tags added to a queue.

    GET /v3/queues/{queueId}/tags
    https://yandex.ru/support/tracker/en/api/queues/get-tags.md
    """
    return get_client().request("GET", f"/queues/{queueId}/tags")


@tool
def tracker_delete_queue_tag(
    queueId: Annotated[
        NonEmptyStr, Field(description="Queue ID or key. The queue key is case-sensitive.")
    ],
    tag: Annotated[NonEmptyStr, Field(description="Tag name.")],
) -> Any:
    """Remove a tag from a queue.

    POST /v3/queues/{queueId}/tags/_remove
    https://yandex.ru/support/tracker/en/api/queues/delete-tag.md

    Only a Yandex Tracker administrator can remove tags, and only tags that are
    not used in any issue of the queue.
    """
    return get_client().request("POST", f"/queues/{queueId}/tags/_remove", json=given(tag=tag))


@tool
def tracker_patch_queue_permissions(
    queueId: Annotated[
        NonEmptyStr, Field(description="Queue ID or key. The queue key is case-sensitive.")
    ],
    create: Annotated[
        dict | None,
        Field(
            description=(
                "Permissions to create issues in the queue, as `users`, `groups` and "
                "`roles` lists. Each list is either an array of IDs (which overrides the "
                "current permissions) or an object with `add` and `remove` arrays. Roles "
                "are `author`, `assignee`, `follower`, `access`."
            )
        ),
    ] = None,
    write: Annotated[
        dict | None,
        Field(
            description=(
                "Permissions to edit issues in the queue, in the same format as `create`."
            )
        ),
    ] = None,
    read: Annotated[
        dict | None,
        Field(
            description=(
                "Permissions to read issues in the queue, in the same format as `create`."
            )
        ),
    ] = None,
    grant: Annotated[
        dict | None,
        Field(
            description=(
                "Permissions to update queue settings, in the same format as `create`."
            )
        ),
    ] = None,
) -> Any:
    """Set up the access permissions of a queue.

    PATCH /v3/queues/{queueId}/permissions
    https://yandex.ru/support/tracker/en/api/queues/manage-access.md

    Specify at least one of the four permission fields.
    """
    return get_client().request(
        "PATCH",
        f"/queues/{queueId}/permissions",
        json=given(create=create, write=write, read=read, grant=grant),
    )


@tool
def tracker_get_queue_user_access(
    queueId: Annotated[
        NonEmptyStr, Field(description="Queue ID or key. The queue key is case-sensitive.")
    ],
    userId: Annotated[
        NonEmptyStr, Field(description="Unique ID of the account or the user login.")
    ],
) -> Any:
    """Get the permissions of one user for a queue.

    GET /v3/queues/{queueId}/permissions/users/{userId}
    https://yandex.ru/support/tracker/en/api/queues/get-user-access.md
    """
    return get_client().request("GET", f"/queues/{queueId}/permissions/users/{userId}")


@tool
def tracker_get_queue_group_access(
    queueId: Annotated[
        NonEmptyStr, Field(description="Queue ID or key. The queue key is case-sensitive.")
    ],
    groupId: Annotated[
        NonEmptyStr, Field(description="Unique group ID in the organization.")
    ],
) -> Any:
    """Get the permissions of one group for a queue.

    GET /v3/queues/{queueId}/permissions/groups/{groupId}
    https://yandex.ru/support/tracker/en/api/queues/get-group-access.md
    """
    return get_client().request("GET", f"/queues/{queueId}/permissions/groups/{groupId}")


@tool
def tracker_create_local_field(
    queueId: Annotated[
        NonEmptyStr, Field(description="Queue ID or key. The queue key is case-sensitive.")
    ],
    name: Annotated[
        dict,
        Field(
            description=(
                "Local field name: `en` in English, `ru` in Russian."
            )
        ),
    ],
    id: Annotated[NonEmptyStr, Field(description="Local field ID.")],
    category: Annotated[
        NonEmptyStr,
        Field(
            description=(
                "Field category ID. Get the list of categories with "
                "GET /v3/fields/categories."
            )
        ),
    ],
    type: Annotated[
        NonEmptyStr,
        Field(
            description=(
                "Local field type: `ru.yandex.startrek.core.fields.DateFieldType`, "
                "`ru.yandex.startrek.core.fields.DateTimeFieldType`, "
                "`ru.yandex.startrek.core.fields.StringFieldType`, "
                "`ru.yandex.startrek.core.fields.TextFieldType`, "
                "`ru.yandex.startrek.core.fields.FloatFieldType`, "
                "`ru.yandex.startrek.core.fields.IntegerFieldType`, "
                "`ru.yandex.startrek.core.fields.UserFieldType`, "
                "`ru.yandex.startrek.core.fields.UriFieldType`, "
                "`ru.yandex.startrek.core.fields.MoneyFieldType`, "
                "`ru.yandex.startrek.core.fields.MoneyWithRateFieldType`, "
                "`ru.yandex.startrek.core.fields.TimeTrackingDurationFieldType`."
            )
        ),
    ],
    optionsProvider: Annotated[
        dict | None,
        Field(
            description=(
                "Drop-down list items: `type` (`FixedListOptionsProvider` for strings or "
                "numbers, `FixedUserListOptionsProvider` for users) and `values` (array of "
                "list values, up to 3000)."
            )
        ),
    ] = None,
    order: Annotated[
        int | None,
        Field(description="Sequence number in the list of organization fields."),
    ] = None,
    description: Annotated[str | None, Field(description="Local field description.")] = None,
    readonly: Annotated[
        bool | None,
        Field(description="Whether the field value is non-editable: `true` or `false`."),
    ] = None,
    visible: Annotated[
        bool | None,
        Field(description="Whether the field is always visible in the interface."),
    ] = None,
    hidden: Annotated[
        bool | None,
        Field(description="Whether to hide the field even if it is not empty."),
    ] = None,
    container: Annotated[
        bool | None,
        Field(
            description=(
                "Whether the field accepts multiple values, like **Tags**. Applies to "
                "one-line text, user and drop-down list fields."
            )
        ),
    ] = None,
) -> Any:
    """Create a local issue field linked to a queue.

    POST /v3/queues/{queueId}/localFields
    https://yandex.ru/support/tracker/en/api/queues/create-local-field.md
    """
    return get_client().request(
        "POST",
        f"/queues/{queueId}/localFields",
        json=given(
            name=name,
            id=id,
            category=category,
            type=type,
            optionsProvider=optionsProvider,
            order=order,
            description=description,
            readonly=readonly,
            visible=visible,
            hidden=hidden,
            container=container,
        ),
    )


@tool
def tracker_get_local_fields(
    queueId: Annotated[
        NonEmptyStr, Field(description="Queue ID or key. The queue key is case-sensitive.")
    ],
) -> Any:
    """Get the local issue fields linked to a queue.

    GET /v3/queues/{queueId}/localFields
    https://yandex.ru/support/tracker/en/api/queues/get-local-fields.md
    """
    return get_client().request("GET", f"/queues/{queueId}/localFields")


@tool
def tracker_get_local_field(
    queueId: Annotated[
        NonEmptyStr, Field(description="Queue ID or key. The queue key is case-sensitive.")
    ],
    fieldKey: Annotated[
        NonEmptyStr,
        Field(
            description=(
                "Local field key. Get it with GET /v3/queues/{queueId}/localFields."
            )
        ),
    ],
) -> Any:
    """Get information about one local queue field.

    GET /v3/queues/{queueId}/localFields/{fieldKey}
    https://yandex.ru/support/tracker/en/api/queues/get-info-local-field.md
    """
    return get_client().request("GET", f"/queues/{queueId}/localFields/{fieldKey}")


@tool
def tracker_patch_local_field(
    queueId: Annotated[
        NonEmptyStr, Field(description="Queue ID or key. The queue key is case-sensitive.")
    ],
    fieldKey: Annotated[
        NonEmptyStr,
        Field(
            description=(
                "Local field key. Get it with GET /v3/queues/{queueId}/localFields."
            )
        ),
    ],
    name: Annotated[
        dict | None,
        Field(description="Local field name: `en` in English, `ru` in Russian."),
    ] = None,
    category: Annotated[
        str | None,
        Field(
            description=(
                "Field category ID. Get the list of categories with "
                "GET /v3/fields/categories."
            )
        ),
    ] = None,
    order: Annotated[
        int | None,
        Field(description="Sequence number in the list of organization fields."),
    ] = None,
    description: Annotated[str | None, Field(description="Local field description.")] = None,
    optionsProvider: Annotated[
        dict | None,
        Field(
            description=(
                "Drop-down list items: `type` (`FixedListOptionsProvider` or "
                "`FixedUserListOptionsProvider`) and `values` (array of list values)."
            )
        ),
    ] = None,
    readonly: Annotated[
        bool | None,
        Field(description="Whether the field value is non-editable: `true` or `false`."),
    ] = None,
    visible: Annotated[
        bool | None,
        Field(
            description=(
                "Whether the field always appears in issues, even when it has no value."
            )
        ),
    ] = None,
    hidden: Annotated[
        bool | None,
        Field(
            description=(
                "Whether the field is hidden completely, even when it contains a value."
            )
        ),
    ] = None,
) -> Any:
    """Edit a local issue field linked to a queue.

    PATCH /v3/queues/{queueId}/localFields/{fieldKey}
    https://yandex.ru/support/tracker/en/api/queues/edit-local-field.md
    """
    return get_client().request(
        "PATCH",
        f"/queues/{queueId}/localFields/{fieldKey}",
        json=given(
            name=name,
            category=category,
            order=order,
            description=description,
            optionsProvider=optionsProvider,
            readonly=readonly,
            visible=visible,
            hidden=hidden,
        ),
    )


@tool
def tracker_create_workflow(
    name: Annotated[NonEmptyStr, Field(description="Workflow name.")],
    initialAction: Annotated[
        dict,
        Field(
            description=(
                "Initial action that sets the status assigned to an issue when it is "
                "created: `name` (localized object) and `target` (status key, ID or "
                "object) are required, plus optional `id`, `description`, `screen`, "
                "`conditions` and `functions`."
            )
        ),
    ],
    steps: Annotated[
        list,
        Field(
            description=(
                "Workflow steps, one per status: `status` (key, ID or object) is required, "
                "plus optional `description` (localized object), `actions` (array of "
                "transitions), `metaAction` and `statusType` (`NEW`, `IN_PROGRESS`, "
                "`PAUSED`, `DONE`, `CANCELLED`)."
            )
        ),
    ],
    id: Annotated[
        str | None,
        Field(
            description=(
                "Workflow ID. Generated in the `W...` format when not specified."
            )
        ),
    ] = None,
    queue: Annotated[
        str | int | dict | None,
        Field(
            description=(
                "Queue the workflow is linked to: key, ID or an object "
                '(`{\"key\": ...}`, `{\"id\": ...}`, `{\"name\": ...}`). Omit it to create '
                "a shared workflow."
            )
        ),
    ] = None,
    type: Annotated[
        str | None,
        Field(description="Workflow type. Pass `VISUAL`; the API returns `visual`."),
    ] = None,
    issueTypeResolutions: Annotated[
        list | None,
        Field(
            description=(
                "Resolution settings per issue type: `issueType` (key or ID) and "
                "`resolutions` (array of resolution keys or IDs)."
            )
        ),
    ] = None,
) -> Any:
    """Create a workflow.

    POST /v3/workflows
    https://yandex.ru/support/tracker/en/api/queues/workflows/post-workflow.md
    """
    return get_client().request(
        "POST",
        "/workflows",
        json=given(
            name=name,
            initialAction=initialAction,
            steps=steps,
            id=id,
            queue=queue,
            type=type,
            issueTypeResolutions=issueTypeResolutions,
        ),
    )


@tool
def tracker_get_workflows() -> Any:
    """Get the list of all workflows in the organization.

    GET /v3/workflows
    https://yandex.ru/support/tracker/en/api/queues/workflows/get-workflows.md
    """
    return get_client().request("GET", "/workflows")


@tool
def tracker_get_workflow(
    workflowId: Annotated[NonEmptyStr, Field(description="Workflow ID.")],
) -> Any:
    """Get information about a workflow by its ID.

    GET /v3/workflows/{workflowId}
    https://yandex.ru/support/tracker/en/api/queues/workflows/get-workflow.md
    """
    return get_client().request("GET", f"/workflows/{workflowId}")


@tool
def tracker_patch_workflow(
    workflowId: Annotated[NonEmptyStr, Field(description="Workflow ID.")],
    version: Annotated[
        int | None,
        Field(
            description=(
                "Current workflow version, to prevent conflicts during concurrent "
                "changes. Get it with the request for a workflow."
            )
        ),
    ] = None,
    name: Annotated[str | None, Field(description="New workflow name.")] = None,
    type: Annotated[
        str | None,
        Field(description="Workflow type. Pass `VISUAL`; the API returns `visual`."),
    ] = None,
    initialAction: Annotated[
        dict | None,
        Field(
            description=(
                "New initial action, in the format described under Creating a workflow."
            )
        ),
    ] = None,
    steps: Annotated[
        list | None,
        Field(
            description=(
                "Updated workflow steps, in the format described under Creating a workflow."
            )
        ),
    ] = None,
    issueTypeResolutions: Annotated[
        list | None,
        Field(
            description=(
                "Resolution settings per issue type: `issueType` and `resolutions`."
            )
        ),
    ] = None,
) -> Any:
    """Edit a workflow: its name, initial action, steps, type and resolution settings.

    PATCH /v3/workflows/{workflowId}
    https://yandex.ru/support/tracker/en/api/queues/workflows/patch-workflow.md

    Send only the parameters you want to change.
    """
    return get_client().request(
        "PATCH",
        f"/workflows/{workflowId}",
        params=given(version=version),
        json=given(
            name=name,
            type=type,
            initialAction=initialAction,
            steps=steps,
            issueTypeResolutions=issueTypeResolutions,
        ),
    )


@tool
def tracker_patch_workflow_action(
    workflowId: Annotated[NonEmptyStr, Field(description="Workflow ID.")],
    status: Annotated[
        NonEmptyStr,
        Field(
            description=(
                "Key of the status (step) that contains the action, for example `open`, "
                "`inProgress` or `closed`."
            )
        ),
    ],
    actionId: Annotated[
        NonEmptyStr,
        Field(description="ID of the action inside the step, for example `inProgress`."),
    ],
    version: Annotated[
        int | None,
        Field(
            description=(
                "Current workflow version, used to control concurrent changes. Get it "
                "with the request for a workflow."
            )
        ),
    ] = None,
    id: Annotated[str | None, Field(description="Action ID.")] = None,
    name: Annotated[
        dict | None,
        Field(description="Action name as a localized object, for example `{\"en\": ...}`."),
    ] = None,
    description: Annotated[
        dict | None, Field(description="Action description as a localized object.")
    ] = None,
    target: Annotated[
        str | int | dict | None,
        Field(
            description=(
                "Target status the action moves the issue to: key, ID or an object "
                '(`{\"key\": ...}`, `{\"id\": ...}`, `{\"name\": ...}`).'
            )
        ),
    ] = None,
    screen: Annotated[
        dict | None,
        Field(
            description=(
                "Transition screen with the fields that can be filled in when performing "
                "the action."
            )
        ),
    ] = None,
    conditions: Annotated[
        list | None, Field(description="Conditions for performing the action.")
    ] = None,
    functions: Annotated[
        list | None, Field(description="Functions executed during the transition.")
    ] = None,
) -> Any:
    """Edit one action (transition) of a workflow step.

    PATCH /v3/workflows/{workflowId}/steps/{status}/actions/{actionId}
    https://yandex.ru/support/tracker/en/api/queues/workflows/patch-workflow-action.md
    """
    return get_client().request(
        "PATCH",
        f"/workflows/{workflowId}/steps/{status}/actions/{actionId}",
        params=given(version=version),
        json=given(
            id=id,
            name=name,
            description=description,
            target=target,
            screen=screen,
            conditions=conditions,
            functions=functions,
        ),
    )


@tool
def tracker_delete_workflow(
    workflowId: Annotated[NonEmptyStr, Field(description="Workflow ID.")],
) -> Any:
    """Delete a workflow.

    DELETE /v3/workflows/{workflowId}
    https://yandex.ru/support/tracker/en/api/queues/workflows/delete-workflow.md
    """
    return get_client().request("DELETE", f"/workflows/{workflowId}")


@tool
def tracker_create_autoaction(
    queueId: Annotated[
        NonEmptyStr, Field(description="Queue ID or key. The queue key is case-sensitive.")
    ],
    name: Annotated[NonEmptyStr, Field(description="Auto action name.")],
    actions: Annotated[
        list,
        Field(
            description=(
                "Actions performed on the issues, for example "
                '`{\"type\": \"Transition\", \"status\": {\"key\": \"needInfo\"}}`. The '
                "action objects are described at "
                "https://yandex.ru/support/tracker/en/api/queues/change-trigger-actions.md."
            )
        ),
    ],
    filter: Annotated[
        dict | list | None,
        Field(
            description=(
                "Issue field filtering conditions that trigger the auto action, as field "
                'key to array of values, for example `{\"status\": [\"inProgress\"]}`. '
                "Specify at least one of `filter` and `query`."
            )
        ),
    ] = None,
    query: Annotated[
        str | None,
        Field(
            description=(
                "Query-language filter selecting the issues that trigger the auto action. "
                "Specify at least one of `filter` and `query`."
            )
        ),
    ] = None,
    active: Annotated[
        bool | None,
        Field(description="Auto action status: `true` active, `false` inactive."),
    ] = None,
    enableNotifications: Annotated[
        bool | None,
        Field(description="Whether to send notifications: `true` or `false`."),
    ] = None,
    intervalMillis: Annotated[
        int | None,
        Field(
            description=(
                "Auto action start frequency in milliseconds. Default `3600000` (hourly)."
            )
        ),
    ] = None,
    calendar: Annotated[
        dict | None,
        Field(
            description=(
                "Period for which the auto action is active, as `{\"id\": <work schedule "
                "ID>}`."
            )
        ),
    ] = None,
) -> Any:
    """Create an auto action in a queue.

    POST /v3/queues/{queueId}/autoactions
    https://yandex.ru/support/tracker/en/api/queues/create-autoaction.md
    """
    return get_client().request(
        "POST",
        f"/queues/{queueId}/autoactions",
        json=given(
            name=name,
            actions=actions,
            filter=filter,
            query=query,
            active=active,
            enableNotifications=enableNotifications,
            intervalMillis=intervalMillis,
            calendar=calendar,
        ),
    )


@tool
def tracker_get_autoaction(
    queueId: Annotated[
        NonEmptyStr, Field(description="Queue ID or key. The queue key is case-sensitive.")
    ],
    autoactionId: Annotated[NonEmptyStr, Field(description="Auto action ID.")],
) -> Any:
    """Get the parameters of an auto action.

    GET /v3/queues/{queueId}/autoactions/{autoactionId}
    https://yandex.ru/support/tracker/en/api/queues/get-autoaction.md
    """
    return get_client().request("GET", f"/queues/{queueId}/autoactions/{autoactionId}")


@tool
def tracker_get_autoaction_logs(
    queueId: Annotated[
        NonEmptyStr, Field(description="Queue ID or key. The queue key is case-sensitive.")
    ],
    autoactionId: Annotated[NonEmptyStr, Field(description="Auto action ID.")],
) -> Any:
    """Get the log of all runs of an auto action.

    GET /v3/queues/{queueId}/autoactions/{autoactionId}/logs
    https://yandex.ru/support/tracker/en/api/queues/view-autoaction-logs.md

    Logs exist only for auto actions that configure automatic issue updates.
    Each entry carries the run `id` to pass to tracker_get_autoaction_run_log.
    """
    return get_client().request("GET", f"/queues/{queueId}/autoactions/{autoactionId}/logs")


@tool
def tracker_get_autoaction_run_log(
    queueId: Annotated[
        NonEmptyStr, Field(description="Queue ID or key. The queue key is case-sensitive.")
    ],
    autoactionId: Annotated[NonEmptyStr, Field(description="Auto action ID.")],
    runId: Annotated[NonEmptyStr, Field(description="ID of the auto action run.")],
) -> Any:
    """Get the log of one auto action run with the list of issues it found.

    GET /v3/queues/{queueId}/autoactions/{autoactionId}/logs/{runId}
    https://yandex.ru/support/tracker/en/api/queues/view-autoaction-logs.md
    """
    return get_client().request(
        "GET", f"/queues/{queueId}/autoactions/{autoactionId}/logs/{runId}"
    )


@tool
def tracker_create_trigger(
    queueId: Annotated[
        NonEmptyStr, Field(description="Queue ID or key. The queue key is case-sensitive.")
    ],
    name: Annotated[NonEmptyStr, Field(description="Trigger name.")],
    actions: Annotated[
        list,
        Field(
            description=(
                "Trigger actions, described at "
                "https://yandex.ru/support/tracker/en/api/queues/change-trigger-actions.md, "
                'for example `{\"type\": \"Transition\", \"status\": {\"key\": \"open\"}}`.'
            )
        ),
    ],
    conditions: Annotated[
        list | None,
        Field(
            description=(
                "Trigger conditions, described at "
                "https://yandex.ru/support/tracker/en/api/queues/change-trigger-conditions.md, "
                'for example `{\"type\": \"CommentFullyMatchCondition\", \"word\": \"Open\"}`.'
            )
        ),
    ] = None,
    active: Annotated[
        bool | None, Field(description="Trigger status: `true` active, `false` inactive.")
    ] = None,
) -> Any:
    """Create a trigger in a queue.

    POST /v3/queues/{queueId}/triggers
    https://yandex.ru/support/tracker/en/api/queues/create-trigger.md
    """
    return get_client().request(
        "POST",
        f"/queues/{queueId}/triggers",
        json=given(name=name, actions=actions, conditions=conditions, active=active),
    )


@tool
def tracker_get_triggers(
    queueId: Annotated[
        NonEmptyStr, Field(description="Queue ID or key. The queue key is case-sensitive.")
    ],
    perPage: Annotated[int | None, Field(description="Number of triggers per page.")] = None,
    id: Annotated[
        int | None,
        Field(description="ID of the last trigger of the previous page."),
    ] = None,
) -> Any:
    """Get the list of all triggers created in a queue.

    GET /v3/queues/{queueId}/triggers
    https://yandex.ru/support/tracker/en/api/queues/get-triggers.md

    The request uses relative pagination: results are sorted by ascending
    trigger ID, so pass the ID of the last trigger of a page as `id` to get the
    next one.
    """
    return get_client().request(
        "GET", f"/queues/{queueId}/triggers", params=given(perPage=perPage, id=id)
    )


@tool
def tracker_get_trigger(
    queueId: Annotated[
        NonEmptyStr, Field(description="Queue ID or key. The queue key is case-sensitive.")
    ],
    triggerId: Annotated[NonEmptyStr, Field(description="Trigger ID.")],
) -> Any:
    """Get the parameters of a queue trigger.

    GET /v3/queues/{queueId}/triggers/{triggerId}
    https://yandex.ru/support/tracker/en/api/queues/get-trigger.md
    """
    return get_client().request("GET", f"/queues/{queueId}/triggers/{triggerId}")


@tool
def tracker_patch_trigger(
    queueId: Annotated[
        NonEmptyStr, Field(description="Queue ID or key. The queue key is case-sensitive.")
    ],
    triggerId: Annotated[NonEmptyStr, Field(description="Trigger ID.")],
    version: Annotated[
        int,
        Field(
            description=(
                "Current trigger version. Get it with the request for trigger parameters."
            )
        ),
    ],
    name: Annotated[str | None, Field(description="Trigger name.")] = None,
    actions: Annotated[
        list | None,
        Field(
            description=(
                "Trigger actions, described at "
                "https://yandex.ru/support/tracker/en/api/queues/change-trigger-actions.md."
            )
        ),
    ] = None,
    conditions: Annotated[
        list | dict | None,
        Field(
            description=(
                "Trigger conditions, described at "
                "https://yandex.ru/support/tracker/en/api/queues/change-trigger-conditions.md. "
                "An array means all conditions must be met; to combine them differently "
                'pass `{\"type\": \"Or\"|\"And\", \"conditions\": [...]}`.'
            )
        ),
    ] = None,
    active: Annotated[
        bool | None, Field(description="Trigger status: `true` active, `false` inactive.")
    ] = None,
    before: Annotated[
        int | None,
        Field(description="ID of the trigger before which to place this trigger."),
    ] = None,
) -> Any:
    """Update a queue trigger.

    PATCH /v3/queues/{queueId}/triggers/{triggerId}
    https://yandex.ru/support/tracker/en/api/queues/change-trigger.md
    """
    return get_client().request(
        "PATCH",
        f"/queues/{queueId}/triggers/{triggerId}",
        params=given(version=version),
        json=given(
            name=name,
            actions=actions,
            conditions=conditions,
            active=active,
            before=before,
        ),
    )


@tool
def tracker_get_trigger_webhook_log(
    queueId: Annotated[
        NonEmptyStr, Field(description="Queue ID or key. The queue key is case-sensitive.")
    ],
    triggerId: Annotated[NonEmptyStr, Field(description="Trigger ID.")],
    issueId: Annotated[
        str | None,
        Field(description="ID of the issue where the trigger was activated."),
    ] = None,
    limit: Annotated[
        int | None,
        Field(description="Number of log entries in the response. Default 10, maximum 100."),
    ] = None,
    from_: Annotated[
        str | None,
        Field(
            description=(
                "Start of the log filter time range in "
                "`YYYY-MM-DDThh:mm:ss.sss±hhmm` format."
            )
        ),
    ] = None,
    to: Annotated[
        str | None,
        Field(
            description=(
                "End of the log filter time range in `YYYY-MM-DDThh:mm:ss.sss±hhmm` format."
            )
        ),
    ] = None,
) -> Any:
    """Get the HTTP request action logs of a queue trigger.

    GET /v3/queues/{queueId}/triggers/{triggerId}/webhooks/log
    https://yandex.ru/support/tracker/en/api/queues/view-trigger-logs.md
    """
    params = given(issueId=issueId, limit=limit, to=to)
    if from_ is not None:
        # `from` is a Python keyword, so the argument is named from_.
        params["from"] = from_
    return get_client().request(
        "GET", f"/queues/{queueId}/triggers/{triggerId}/webhooks/log", params=params
    )


@tool
def tracker_get_components() -> Any:
    """Get the list of all components created by the organization users.

    GET /v3/components
    https://yandex.ru/support/tracker/en/api/queues/get-components.md

    This is the organization-wide list. For the components of a single queue,
    call tracker_get_queue with `expand=components`.
    """
    return get_client().request("GET", "/components")


@tool
def tracker_create_component(
    name: Annotated[NonEmptyStr, Field(description="Component name.")],
    queue: Annotated[
        NonEmptyStr, Field(description="Key of the queue where the component is created.")
    ],
    description: Annotated[str | None, Field(description="Component description.")] = None,
    lead: Annotated[str | None, Field(description="Username of the component owner.")] = None,
    assignAuto: Annotated[
        bool | None,
        Field(
            description=(
                "Default assignee attribute: `true` assigns the owner as the default "
                "assignee, `false` assigns nobody."
            )
        ),
    ] = None,
) -> Any:
    """Create a component.

    POST /v3/components
    https://yandex.ru/support/tracker/en/api/queues/post-component.md
    """
    return get_client().request(
        "POST",
        "/components",
        json=given(
            name=name,
            queue=queue,
            description=description,
            lead=lead,
            assignAuto=assignAuto,
        ),
    )


@tool
def tracker_patch_component(
    componentId: Annotated[NonEmptyStr, Field(description="Component ID.")],
    version: Annotated[int, Field(description="Current component version number.")],
    name: Annotated[str | None, Field(description="Component name.")] = None,
    description: Annotated[str | None, Field(description="Component description.")] = None,
    lead: Annotated[str | None, Field(description="Username of the component owner.")] = None,
    assignAuto: Annotated[
        bool | None,
        Field(
            description=(
                "Default assignee attribute: `true` assigns the owner as the default "
                "assignee, `false` assigns nobody."
            )
        ),
    ] = None,
) -> Any:
    """Change the parameters of a component.

    PATCH /v3/components/{componentId}
    https://yandex.ru/support/tracker/en/api/queues/patch-component.md
    """
    return get_client().request(
        "PATCH",
        f"/components/{componentId}",
        params=given(version=version),
        json=given(
            name=name,
            description=description,
            lead=lead,
            assignAuto=assignAuto,
        ),
    )


@tool
def tracker_get_component_user_access(
    componentId: Annotated[NonEmptyStr, Field(description="Component ID.")],
    userId: Annotated[
        NonEmptyStr, Field(description="Unique ID of the account or the user login.")
    ],
) -> Any:
    """Get the permissions of one user for a component.

    GET /v3/components/{componentId}/permissions/users/{userId}
    https://yandex.ru/support/tracker/en/api/queues/get-component-user-access.md
    """
    return get_client().request("GET", f"/components/{componentId}/permissions/users/{userId}")


@tool
def tracker_get_component_group_access(
    componentId: Annotated[NonEmptyStr, Field(description="Component ID.")],
    groupId: Annotated[
        NonEmptyStr, Field(description="Unique group ID in the organization.")
    ],
) -> Any:
    """Get the permissions of one group for a component.

    GET /v3/components/{componentId}/permissions/groups/{groupId}
    https://yandex.ru/support/tracker/en/api/queues/get-component-group-access.md
    """
    return get_client().request(
        "GET", f"/components/{componentId}/permissions/groups/{groupId}"
    )
