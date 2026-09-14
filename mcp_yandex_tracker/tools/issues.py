"""Issues, comments, checklists, attachments, worklog and fields — https://yandex.ru/support/tracker/en/api/issues/get-issue.md"""

from __future__ import annotations

from typing import Annotated, Any

from pydantic import Field

from ..client import given
from ..server import NonEmptyStr, get_client, tool


@tool
def tracker_create_issue(
    summary: Annotated[NonEmptyStr, Field(description="Issue summary.")],
    queue: Annotated[
        str | int | dict,
        Field(
            description="Queue to create the issue in: a string (queue key), a number "
            "(queue ID), or an object with `id` and/or `key`."
        ),
    ],
    notify: Annotated[
        bool | None,
        Field(
            description="Send a notification about the issue being created to users "
            "subscribed to this event. The notification is sent by default."
        ),
    ] = None,
    parent: Annotated[
        str | dict | None,
        Field(description="Parent issue: its key, or an object with `id` and/or `key`."),
    ] = None,
    description: Annotated[str | None, Field(description="Issue description.")] = None,
    markupType: Annotated[
        str | None,
        Field(
            description="Type of text markup. Specify `md` when the description uses YFM markup."
        ),
    ] = None,
    sprint: Annotated[
        list | int | str | None,
        Field(description="Block with information about sprints: array of objects or strings."),
    ] = None,
    type: Annotated[
        str | int | dict | None,
        Field(
            description="Issue type: a string (type key), a number (type ID), or an object "
            "with `id` and/or `key`."
        ),
    ] = None,
    priority: Annotated[
        str | int | dict | None,
        Field(
            description="Issue priority: a string (priority key), a number (priority ID), or "
            "an object with `id` and/or `key`."
        ),
    ] = None,
    followers: Annotated[
        list | None,
        Field(description="IDs or usernames of issue followers."),
    ] = None,
    assignee: Annotated[
        str | int | None, Field(description="Login or ID of the issue assignee.")
    ] = None,
    author: Annotated[
        str | int | dict | None, Field(description="ID or username of the issue author.")
    ] = None,
    project: Annotated[
        dict | None,
        Field(
            description="Block with information about issue projects: `primary` (shortId of the "
            "main project) and `secondary` (array of shortIds)."
        ),
    ] = None,
    links: Annotated[
        list | None,
        Field(
            description="Links to other issues. Each object has `issue` (ID or key of the linked "
            "issue) and `relationship`: `relates`, `is dependent by`, `depends on`, "
            "`is subtask for`, `is parent task for`, `duplicates`, `is duplicated by`, "
            "`is epic of`, `has epic`."
        ),
    ] = None,
    unique: Annotated[
        str | None,
        Field(
            description="Value that must be unique within the organization. Reusing it returns "
            "error 409 instead of creating a duplicate issue."
        ),
    ] = None,
    attachmentIds: Annotated[
        list | None,
        Field(description="IDs of temporary files to attach to the issue description."),
    ] = None,
    tags: Annotated[list | None, Field(description="Issue tags.")] = None,
    access: Annotated[
        list | None,
        Field(description="IDs or logins of users listed in the Access field."),
    ] = None,
    affectedVersions: Annotated[
        list | None,
        Field(
            description="IDs of versions listed in the Found in versions field. The versions "
            "must exist in the queue."
        ),
    ] = None,
    boards: Annotated[
        list | None, Field(description="IDs of boards to add the issue to.")
    ] = None,
    components: Annotated[
        list | None, Field(description="Names or IDs of queue components added to the issue.")
    ] = None,
    createdBy: Annotated[
        str | int | None, Field(description="Login or ID of the issue author.")
    ] = None,
    deadline: Annotated[
        str | None, Field(description="Issue deadline in the YYYY-MM-DD format.")
    ] = None,
    descriptionAttachmentIds: Annotated[
        list | None,
        Field(description="IDs of temporary files to add to the issue description."),
    ] = None,
    emailCc: Annotated[list | None, Field(description='Email recipients in the "Cc" field.')] = None,
    emailCreatedBy: Annotated[
        str | None, Field(description="Email address the email was created on behalf of.")
    ] = None,
    emailFrom: Annotated[str | None, Field(description="Email sender address.")] = None,
    emailTo: Annotated[str | None, Field(description="Email recipients.")] = None,
    end: Annotated[
        str | None, Field(description="Date of issue completion in the YYYY-MM-DD format.")
    ] = None,
    epic: Annotated[
        str | None, Field(description="Key or ID of the epic the issue belongs to.")
    ] = None,
    estimation: Annotated[
        str | None,
        Field(
            description="Estimate in workdays, hours or minutes, as `<number><unit>` — "
            "for example `1d`, `2h`, `30m`."
        ),
    ] = None,
    fixVersions: Annotated[
        list | None,
        Field(
            description="IDs of versions listed in the Fix in versions field. The versions must "
            "exist in the queue."
        ),
    ] = None,
    linkedGoals: Annotated[
        dict | int | str | None,
        Field(
            description="Goal ID (it becomes the primary goal) or an object with `primary` and "
            "`secondary` goal IDs."
        ),
    ] = None,
    originalEstimation: Annotated[
        str | None,
        Field(
            description="Original estimate in workdays, hours or minutes, as `<number><unit>` — "
            "for example `1d`, `2h`, `30m`."
        ),
    ] = None,
    pendingReplyFrom: Annotated[
        list | None, Field(description="Logins or IDs of users a reply is expected from.")
    ] = None,
    possibleSpam: Annotated[
        bool | None,
        Field(description="Indication that the issue was created from an email that is spam."),
    ] = None,
    qaEngineer: Annotated[
        str | int | None, Field(description="Login or ID of the QA engineer.")
    ] = None,
    receivedReplyFor: Annotated[
        str | int | None,
        Field(description="Login or ID of the user a reply was received for."),
    ] = None,
    start: Annotated[
        str | None,
        Field(description="Start date of work on the issue in the YYYY-MM-DD format."),
    ] = None,
    storyPoints: Annotated[
        int | None, Field(description="Issue estimate in story points.")
    ] = None,
    fields: Annotated[
        dict | None,
        Field(
            description="Custom global fields and queue local fields, keyed by field ID. Merged "
            "into the request body last."
        ),
    ] = None,
) -> Any:
    """Create an issue.

    POST /v3/issues/
    https://yandex.ru/support/tracker/en/api/issues/create-issue.md

    How every field value is shaped is described in
    https://yandex.ru/support/tracker/en/api/issues/request-fields.md, and the
    shape of the issue you get back in
    https://yandex.ru/support/tracker/en/api/issues/response-fields.md.
    """
    return get_client().request(
        "POST",
        "/issues/",
        params=given(notify=notify),
        json={
            **given(
                summary=summary,
                queue=queue,
                parent=parent,
                description=description,
                markupType=markupType,
                sprint=sprint,
                type=type,
                priority=priority,
                followers=followers,
                assignee=assignee,
                author=author,
                project=project,
                links=links,
                unique=unique,
                attachmentIds=attachmentIds,
                tags=tags,
                access=access,
                affectedVersions=affectedVersions,
                boards=boards,
                components=components,
                createdBy=createdBy,
                deadline=deadline,
                descriptionAttachmentIds=descriptionAttachmentIds,
                emailCc=emailCc,
                emailCreatedBy=emailCreatedBy,
                emailFrom=emailFrom,
                emailTo=emailTo,
                end=end,
                epic=epic,
                estimation=estimation,
                fixVersions=fixVersions,
                linkedGoals=linkedGoals,
                originalEstimation=originalEstimation,
                pendingReplyFrom=pendingReplyFrom,
                possibleSpam=possibleSpam,
                qaEngineer=qaEngineer,
                receivedReplyFor=receivedReplyFor,
                start=start,
                storyPoints=storyPoints,
            ),
            **(fields or {}),
        },
    )


@tool
def tracker_get_issue(
    issueId: Annotated[NonEmptyStr, Field(description="ID or key of the issue.")],
    fields: Annotated[
        str | None,
        Field(
            description="Issue fields to include in the response, comma-separated — for example "
            "`status,assignee,summary`. Without it the response includes all basic fields."
        ),
    ] = None,
    expand: Annotated[
        str | None,
        Field(
            description="Additional fields to include: `links`, `comments`, `transitions`, "
            "`attachments`."
        ),
    ] = None,
) -> Any:
    """Get the parameters of one issue.

    GET /v3/issues/{issueId}
    https://yandex.ru/support/tracker/en/api/issues/get-issue.md
    """
    return get_client().request(
        "GET", f"/issues/{issueId}", params=given(fields=fields, expand=expand)
    )


@tool
def tracker_patch_issue(
    issueId: Annotated[NonEmptyStr, Field(description="ID or key of the issue.")],
    version: Annotated[
        int | None,
        Field(description="Issue version. Changes are only made to the current version."),
    ] = None,
    summary: Annotated[str | None, Field(description="Issue name.")] = None,
    parent: Annotated[
        str | dict | None,
        Field(description="Parent issue: its key, or an object with `id` and/or `key`."),
    ] = None,
    description: Annotated[str | None, Field(description="Issue description.")] = None,
    markupType: Annotated[
        str | None,
        Field(
            description="Type of text markup. Specify `md` when the description uses YFM markup."
        ),
    ] = None,
    sprint: Annotated[
        list | int | str | None,
        Field(
            description="Block with information about sprints: array of objects with `id`, or "
            "of strings."
        ),
    ] = None,
    type: Annotated[
        str | int | dict | None,
        Field(
            description="Issue type: a string (type key), a number (type ID), or an object with "
            "`id` and/or `key`."
        ),
    ] = None,
    priority: Annotated[
        str | int | dict | None,
        Field(
            description="Issue priority: a string (priority key), a number (priority ID), or an "
            "object with `id` and/or `key`."
        ),
    ] = None,
    followers: Annotated[
        list | None, Field(description="IDs or usernames of issue followers.")
    ] = None,
    project: Annotated[
        dict | None,
        Field(
            description="Block with information about issue projects: `primary` (shortId of the "
            "main project) and `secondary` (array of shortIds)."
        ),
    ] = None,
    attachmentIds: Annotated[
        list | None, Field(description="IDs of temporary files to add as attachments.")
    ] = None,
    descriptionAttachmentIds: Annotated[
        list | None,
        Field(description="IDs of temporary files to add to the issue description."),
    ] = None,
    tags: Annotated[list | None, Field(description="Issue tags.")] = None,
    access: Annotated[
        list | None, Field(description="IDs or logins of users listed in the Access field.")
    ] = None,
    affectedVersions: Annotated[
        list | None,
        Field(
            description="IDs of versions listed in the Found in versions field. The versions "
            "must exist in the queue."
        ),
    ] = None,
    assignee: Annotated[
        str | int | None, Field(description="Login or ID of the issue assignee.")
    ] = None,
    boards: Annotated[
        list | None, Field(description="IDs of boards to add the issue to.")
    ] = None,
    components: Annotated[
        list | None, Field(description="Names or IDs of queue components added to the issue.")
    ] = None,
    createdBy: Annotated[
        str | int | None, Field(description="Login or ID of the issue author.")
    ] = None,
    deadline: Annotated[
        str | None, Field(description="Issue deadline in the YYYY-MM-DD format.")
    ] = None,
    emailCc: Annotated[list | None, Field(description='Email recipients in the "Cc" field.')] = None,
    emailCreatedBy: Annotated[
        str | None, Field(description="Email address the email was created on behalf of.")
    ] = None,
    emailFrom: Annotated[str | None, Field(description="Email sender address.")] = None,
    emailTo: Annotated[str | None, Field(description="Email recipients.")] = None,
    end: Annotated[
        str | None, Field(description="Date of issue completion in the YYYY-MM-DD format.")
    ] = None,
    epic: Annotated[
        str | None, Field(description="Key or ID of the epic the issue belongs to.")
    ] = None,
    estimation: Annotated[
        str | None,
        Field(
            description="Estimate in workdays, hours or minutes, as `<number><unit>` — "
            "for example `1d`, `2h`, `30m`."
        ),
    ] = None,
    fixVersions: Annotated[
        list | None,
        Field(
            description="IDs of versions listed in the Fix in versions field. The versions must "
            "exist in the queue."
        ),
    ] = None,
    linkedGoals: Annotated[
        dict | int | str | None,
        Field(
            description="Goal ID (it becomes the primary goal) or an object with `primary` and "
            "`secondary` goal IDs."
        ),
    ] = None,
    links: Annotated[
        list | None,
        Field(
            description="List of linked issues. Each object has `issue` (ID or key) and "
            "`relationship`: `relates`, `is dependent by`, `depends on`, `is subtask for`, "
            "`is parent task for`, `duplicates`, `is duplicated by`, `is epic of`, `has epic`."
        ),
    ] = None,
    originalEstimation: Annotated[
        str | None,
        Field(
            description="Original estimate in workdays, hours or minutes, as `<number><unit>` — "
            "for example `1d`, `2h`, `30m`."
        ),
    ] = None,
    pendingReplyFrom: Annotated[
        list | None, Field(description="Logins or IDs of users a reply is expected from.")
    ] = None,
    possibleSpam: Annotated[
        bool | None,
        Field(description="Indication that the issue was created from an email that is spam."),
    ] = None,
    qaEngineer: Annotated[
        str | int | None, Field(description="Login or ID of the QA engineer.")
    ] = None,
    receivedReplyFor: Annotated[
        str | int | None, Field(description="Login or ID of the user a reply was received for.")
    ] = None,
    start: Annotated[
        str | None, Field(description="Start date of work on the issue in the YYYY-MM-DD format.")
    ] = None,
    storyPoints: Annotated[int | None, Field(description="Issue estimate in story points.")] = None,
    unique: Annotated[
        str | None,
        Field(description="Value that must be unique within the organization."),
    ] = None,
    fields: Annotated[
        dict | None,
        Field(
            description="Custom global fields, queue local fields, and fields set through the "
            "`set`/`add`/`remove` operators. Merged into the request body last."
        ),
    ] = None,
) -> Any:
    """Edit an issue.

    PATCH /v3/issues/{issueId}
    https://yandex.ru/support/tracker/en/api/issues/patch-issue.md

    The status is the one field this cannot change — use tracker_new_transition.
    Array fields also accept the `set`/`add`/`remove` operators instead of a plain
    value (see https://yandex.ru/support/tracker/en/api/common-format.md#body);
    pass those through `fields`. How every field value is shaped is described in
    https://yandex.ru/support/tracker/en/api/issues/request-fields.md, and the
    shape of the issue you get back in
    https://yandex.ru/support/tracker/en/api/issues/response-fields.md.
    """
    return get_client().request(
        "PATCH",
        f"/issues/{issueId}",
        params=given(version=version),
        json={
            **given(
                summary=summary,
                parent=parent,
                description=description,
                markupType=markupType,
                sprint=sprint,
                type=type,
                priority=priority,
                followers=followers,
                project=project,
                attachmentIds=attachmentIds,
                descriptionAttachmentIds=descriptionAttachmentIds,
                tags=tags,
                access=access,
                affectedVersions=affectedVersions,
                assignee=assignee,
                boards=boards,
                components=components,
                createdBy=createdBy,
                deadline=deadline,
                emailCc=emailCc,
                emailCreatedBy=emailCreatedBy,
                emailFrom=emailFrom,
                emailTo=emailTo,
                end=end,
                epic=epic,
                estimation=estimation,
                fixVersions=fixVersions,
                linkedGoals=linkedGoals,
                links=links,
                originalEstimation=originalEstimation,
                pendingReplyFrom=pendingReplyFrom,
                possibleSpam=possibleSpam,
                qaEngineer=qaEngineer,
                receivedReplyFor=receivedReplyFor,
                start=start,
                storyPoints=storyPoints,
                unique=unique,
            ),
            **(fields or {}),
        },
    )


@tool
def tracker_move_issue(
    issueId: Annotated[NonEmptyStr, Field(description="ID or key of the issue.")],
    queue: Annotated[NonEmptyStr, Field(description="Key of the queue to move the issue to.")],
    notify: Annotated[
        bool | None,
        Field(
            description="Notify the users specified in the issue fields about the change. "
            "`true` by default."
        ),
    ] = None,
    notifyAuthor: Annotated[
        bool | None, Field(description="Notify the issue reporter. `false` by default.")
    ] = None,
    moveAllFields: Annotated[
        bool | None,
        Field(
            description="Move the issue's versions, components and projects if the new queue has "
            "similar ones. `false` by default, which clears them."
        ),
    ] = None,
    initialStatus: Annotated[
        bool | None,
        Field(
            description="Reset the issue status to the initial one — needed when the new queue "
            "has a different workflow. `false` by default."
        ),
    ] = None,
    expand: Annotated[
        str | None,
        Field(
            description="Additional fields to include in the response: `attachments`, "
            "`comments`, `workflow`, `transitions`."
        ),
    ] = None,
    fields: Annotated[
        dict | None,
        Field(
            description="Issue parameters to change while moving. Same body format as editing an "
            "issue — see https://yandex.ru/support/tracker/en/api/issues/patch-issue.md."
        ),
    ] = None,
) -> Any:
    """Move an issue to another queue.

    POST /v3/issues/{issueId}/_move
    https://yandex.ru/support/tracker/en/api/issues/move-issue.md

    Nothing is moved when the issue's type or status does not exist in the target
    queue; local field values are always reset by the move.
    """
    return get_client().request(
        "POST",
        f"/issues/{issueId}/_move",
        params=given(
            queue=queue,
            notify=notify,
            notifyAuthor=notifyAuthor,
            moveAllFields=moveAllFields,
            initialStatus=initialStatus,
            expand=expand,
        ),
        json=fields,
    )


@tool
def tracker_search_issues(
    expand: Annotated[
        str | None,
        Field(
            description="Additional fields to include in the response: `transitions`, "
            "`attachments`."
        ),
    ] = None,
    perPage: Annotated[
        int | None, Field(description="Number of issues per response page. Default 50.")
    ] = None,
    page: Annotated[
        int | None,
        Field(description="Page number of the paginated output. Default 1."),
    ] = None,
    scrollType: Annotated[
        str | None,
        Field(
            description="Scrolling type, used only in the first request of a scrollable "
            "sequence: `sorted` (use the sorting from the request) or `unsorted`. Not allowed "
            "together with `queue` or `keys`."
        ),
    ] = None,
    perScroll: Annotated[
        int | None,
        Field(
            description="Maximum number of issues per scrollable response. Default 100, maximum "
            "1000. Used only in the first request of a scrollable sequence."
        ),
    ] = None,
    scrollTTLMillis: Annotated[
        int | None,
        Field(description="Scroll context lifetime in milliseconds. Default 60000."),
    ] = None,
    scrollId: Annotated[
        str | None,
        Field(
            description="Page ID, taken from the `X-Scroll-Id` header of the previous response. "
            "Specified only in the second and following requests of a scrollable sequence."
        ),
    ] = None,
    queue: Annotated[str | None, Field(description="Queue to search in.")] = None,
    keys: Annotated[
        str | list | None, Field(description="Issue key or list of issue keys.")
    ] = None,
    filter: Annotated[
        dict | None,
        Field(description="Issue filtering parameters: any issue field name and a value."),
    ] = None,
    query: Annotated[str | None, Field(description="Filter using the query language.")] = None,
    query2: Annotated[
        dict | None,
        Field(
            description="Filter using query language 2.0 as an MLJ (Mongo-like JSON) object — "
            "see https://yandex.ru/support/tracker/en/api/issues/query2.md."
        ),
    ] = None,
    order: Annotated[
        str | None,
        Field(
            description="Sorting direction and field as `[+/-]<field_key>`. Only works together "
            "with `filter`."
        ),
    ] = None,
) -> Any:
    """Find the issues that meet the given criteria.

    POST /v3/issues/_search
    https://yandex.ru/support/tracker/en/api/issues/search-issues.md

    `queue`, `keys`, `filter` and `query` are mutually exclusive — combining them
    returns error 400. Use paginated output below 10,000 rows and the scroll
    parameters above it; release a scroll snapshot with tracker_clear_scroll.
    `perPage` and `page` are the paginated-output parameters this page links to
    in https://yandex.ru/support/tracker/en/api/common-format.md.
    """
    return get_client().request(
        "POST",
        "/issues/_search",
        params=given(
            expand=expand,
            perPage=perPage,
            page=page,
            scrollType=scrollType,
            perScroll=perScroll,
            scrollTTLMillis=scrollTTLMillis,
            scrollId=scrollId,
        ),
        json=given(
            queue=queue, keys=keys, filter=filter, query=query, query2=query2, order=order
        ),
    )


@tool
def tracker_count_issues(
    filter: Annotated[
        dict | None,
        Field(description="Issue filtering parameters: any issue field name and a value."),
    ] = None,
    query: Annotated[str | None, Field(description="Filter using the query language.")] = None,
) -> Any:
    """Count the issues that meet the given criteria.

    POST /v3/issues/_count
    https://yandex.ru/support/tracker/en/api/issues/count-issues.md
    """
    return get_client().request(
        "POST", "/issues/_count", json=given(filter=filter, query=query)
    )


@tool
def tracker_get_suggest(
    input: Annotated[
        NonEmptyStr,
        Field(
            description="Text to filter issues by summary. A space between words also matches "
            "any text in place of the space."
        ),
    ],
    queue: Annotated[
        str | None, Field(description="Key of the queue to search issues in.")
    ] = None,
    full: Annotated[
        bool | None,
        Field(
            description="Return detailed information for each issue. Default `false`. Required "
            "to enable `fields`, `expand` and `embed`."
        ),
    ] = None,
    fields: Annotated[
        str | None,
        Field(description="Additional issue fields to return. Requires `full=true`."),
    ] = None,
    expand: Annotated[
        str | None,
        Field(
            description="Additional information to include: `all`, `html`, `attachments`, "
            "`comments`, `links`, `localLinkRefs`, `aliases`, `transitions`, `permissions`, "
            "`sla`, `update_limits`. Requires `full=true`."
        ),
    ] = None,
    embed: Annotated[
        str | None,
        Field(
            description="More detail for the parameters named in `expand`: `attachments`, "
            "`comments`, `transitions`, `sla`. Requires `full=true`."
        ),
    ] = None,
) -> Any:
    """Get the issue suggestions shown when searching by summary.

    GET /v3/issues/_suggest
    https://yandex.ru/support/tracker/en/api/issues/get-suggest.md
    """
    return get_client().request(
        "GET",
        "/issues/_suggest",
        params=given(
            input=input, queue=queue, full=full, fields=fields, expand=expand, embed=embed
        ),
    )


@tool
def tracker_clear_scroll(
    fields: Annotated[
        dict,
        Field(
            description="One `<scrollId>: <scrollToken>` pair per result page, taken from the "
            "`X-Scroll-Id` and `X-Scroll-Token` headers of the scrollable search responses."
        ),
    ],
) -> Any:
    """Release the resources of a scrollable issue search snapshot.

    POST /v3/system/search/scroll/_clear
    https://yandex.ru/support/tracker/en/api/issues/search-release.md
    """
    return get_client().request("POST", "/system/search/scroll/_clear", json=fields)


@tool
def tracker_get_changelog(
    issueId: Annotated[NonEmptyStr, Field(description="ID or key of the issue.")],
    id: Annotated[
        str | None, Field(description="ID of the change the requested changes follow.")
    ] = None,
    perPage: Annotated[
        int | None, Field(description="Number of changes per page. Default 50.")
    ] = None,
    field: Annotated[
        str | None,
        Field(
            description="ID of the changed issue parameter — for example `checklistItems` or "
            "`status`."
        ),
    ] = None,
    type: Annotated[
        str | None,
        Field(
            description="Key of the change type: `IssueUpdated`, `IssueCreated`, `IssueMoved`, "
            "`IssueCloned`, `IssueCommentAdded`, `IssueCommentUpdated`, `IssueCommentRemoved`, "
            "`IssueWorklogAdded`, `IssueWorklogUpdated`, `IssueWorklogRemoved`, "
            "`IssueCommentReactionAdded`, `IssueCommentReactionRemoved`, `IssueVoteAdded`, "
            "`IssueVoteRemoved`, `IssueLinked`, `IssueLinkChanged`, `IssueUnlinked`, "
            "`RelatedIssueResolutionChanged`, `IssueAttachmentAdded`, "
            "`IssueAttachmentRemoved`, `IssueWorkflow`."
        ),
    ] = None,
) -> Any:
    """Get the history of changes to an issue.

    GET /v3/issues/{issueId}/changelog
    https://yandex.ru/support/tracker/en/api/issues/get-changelog.md
    """
    return get_client().request(
        "GET",
        f"/issues/{issueId}/changelog",
        params=given(id=id, perPage=perPage, field=field, type=type),
    )


@tool
def tracker_link_issue(
    issueId: Annotated[NonEmptyStr, Field(description="ID or key of the current issue.")],
    relationship: Annotated[
        NonEmptyStr,
        Field(
            description="Link type between the issues: `relates` — simple link; "
            "`is dependent by` — the current issue blocks the linked issue; `depends on` — the "
            "current issue depends on the linked issue; `is subtask for` — the current issue is "
            "a subtask of the linked issue; `is parent task for` — the current issue is a parent "
            "task for the linked issue; `duplicates` — the current issue is a duplicate of the "
            "linked issue; `is duplicated by` — the linked issue is a duplicate of the current "
            "issue; `is epic of` — the current issue is an epic for the linked issue (only for "
            'issues of the "Epic" type); `has epic` — the linked issue is an epic for the '
            'current issue (only for issues of the "Epic" type).'
        ),
    ],
    issue: Annotated[NonEmptyStr, Field(description="ID or key of the linked issue.")],
) -> Any:
    """Create a link between two issues.

    POST /v3/issues/{issueId}/links
    https://yandex.ru/support/tracker/en/api/issues/link-issue.md
    """
    return get_client().request(
        "POST",
        f"/issues/{issueId}/links",
        json=given(relationship=relationship, issue=issue),
    )


@tool
def tracker_get_links(
    issueId: Annotated[NonEmptyStr, Field(description="ID or key of the issue.")],
) -> Any:
    """Get the links of an issue.

    GET /v3/issues/{issueId}/links
    https://yandex.ru/support/tracker/en/api/issues/get-links.md
    """
    return get_client().request("GET", f"/issues/{issueId}/links")


@tool
def tracker_delete_link(
    issueId: Annotated[NonEmptyStr, Field(description="ID or key of the current issue.")],
    linkId: Annotated[
        NonEmptyStr,
        Field(description="ID of the link with another issue, from tracker_get_links."),
    ],
) -> Any:
    """Unlink an issue from another issue.

    DELETE /v3/issues/{issueId}/links/{linkId}
    https://yandex.ru/support/tracker/en/api/issues/delete-link-issue.md
    """
    return get_client().request("DELETE", f"/issues/{issueId}/links/{linkId}")


@tool
def tracker_get_external_links(
    issueId: Annotated[NonEmptyStr, Field(description="ID or key of the issue.")],
) -> Any:
    """Get the issue's links to external application objects.

    GET /v3/issues/{issueId}/remotelinks
    https://yandex.ru/support/tracker/en/api/issues/get-external-links.md
    """
    return get_client().request("GET", f"/issues/{issueId}/remotelinks")


@tool
def tracker_add_external_link(
    issueId: Annotated[NonEmptyStr, Field(description="ID or key of the current issue.")],
    relationship: Annotated[
        NonEmptyStr, Field(description="Link type. `RELATES` is the recommended value.")
    ],
    key: Annotated[NonEmptyStr, Field(description="Key of the external application object.")],
    origin: Annotated[
        NonEmptyStr,
        Field(description="ID of the application whose object the link points to."),
    ],
    backlink: Annotated[
        bool | None,
        Field(
            description="Set `true` to have Tracker ask the external application to create the "
            "duplicate link on its side."
        ),
    ] = None,
) -> Any:
    """Create a link to an object in an external application.

    POST /v3/issues/{issueId}/remotelinks
    https://yandex.ru/support/tracker/en/api/issues/add-external-link.md
    """
    return get_client().request(
        "POST",
        f"/issues/{issueId}/remotelinks",
        params=given(backlink=backlink),
        json=given(relationship=relationship, key=key, origin=origin),
    )


@tool
def tracker_delete_external_link(
    issueId: Annotated[NonEmptyStr, Field(description="ID or key of the current issue.")],
    externalLinkId: Annotated[
        NonEmptyStr,
        Field(description="External link ID, from tracker_get_external_links."),
    ],
) -> Any:
    """Delete an issue's link to an external application object.

    DELETE /v3/issues/{issueId}/remotelinks/{externalLinkId}
    https://yandex.ru/support/tracker/en/api/issues/delete-external-link.md
    """
    return get_client().request(
        "DELETE", f"/issues/{issueId}/remotelinks/{externalLinkId}"
    )


@tool
def tracker_get_transitions(
    issueId: Annotated[NonEmptyStr, Field(description="ID or key of the issue.")],
) -> Any:
    """Get the status transitions available for an issue.

    GET /v3/issues/{issueId}/transitions
    https://yandex.ru/support/tracker/en/api/issues/get-transitions.md
    """
    return get_client().request("GET", f"/issues/{issueId}/transitions")


@tool
def tracker_new_transition(
    issueId: Annotated[NonEmptyStr, Field(description="ID or key of the issue.")],
    transitionId: Annotated[
        NonEmptyStr,
        Field(description="Transition ID, from tracker_get_transitions."),
    ],
    comment: Annotated[str | None, Field(description="Comment on the issue.")] = None,
    fields: Annotated[
        dict | None,
        Field(
            description="Issue parameters to change along with the transition, when the "
            "transition settings allow it — see "
            "https://yandex.ru/support/tracker/en/api/issues/request-fields.md. Custom global "
            "fields and queue local fields go here too."
        ),
    ] = None,
) -> Any:
    """Switch an issue to a new status.

    POST /v3/issues/{issueId}/transitions/{transitionId}/_execute
    https://yandex.ru/support/tracker/en/api/issues/new-transition.md

    The response lists the transitions available in the NEW status, not the
    updated issue.
    """
    return get_client().request(
        "POST",
        f"/issues/{issueId}/transitions/{transitionId}/_execute",
        json={**given(comment=comment), **(fields or {})},
    )


@tool
def tracker_add_comment(
    issueId: Annotated[NonEmptyStr, Field(description="ID or key of the issue.")],
    text: Annotated[NonEmptyStr, Field(description="Comment on the issue.")],
    isAddToFollowers: Annotated[
        bool | None,
        Field(
            description="Add the user who made the comment to the issue followers. `true` by "
            "default."
        ),
    ] = None,
    attachmentIds: Annotated[
        list | None,
        Field(
            description="IDs of temporary files to attach to the comment. They also appear on "
            "the issue's Attachments tab."
        ),
    ] = None,
    summonees: Annotated[
        list | None, Field(description="IDs or usernames of summoned users.")
    ] = None,
    maillistSummonees: Annotated[
        list | None, Field(description="Mailing lists mentioned in the comment.")
    ] = None,
    markupType: Annotated[
        str | None,
        Field(description="Type of text markup. Specify `md` when the comment uses YFM markup."),
    ] = None,
) -> Any:
    """Add a comment to an issue.

    POST /v3/issues/{issueId}/comments
    https://yandex.ru/support/tracker/en/api/issues/add-comment.md
    """
    return get_client().request(
        "POST",
        f"/issues/{issueId}/comments",
        params=given(isAddToFollowers=isAddToFollowers),
        json=given(
            text=text,
            attachmentIds=attachmentIds,
            summonees=summonees,
            maillistSummonees=maillistSummonees,
            markupType=markupType,
        ),
    )


@tool
def tracker_get_comments(
    issueId: Annotated[NonEmptyStr, Field(description="ID or key of the issue.")],
    expand: Annotated[
        str | None,
        Field(
            description="Additional fields to include: `attachments`, `html` (comment HTML "
            "markup), `all`."
        ),
    ] = None,
    perPage: Annotated[
        int | None, Field(description="Number of comments per page. Default 50.")
    ] = None,
    id: Annotated[
        str | None, Field(description="Comment `id` the requested page starts after.")
    ] = None,
) -> Any:
    """Get the comments on an issue.

    GET /v3/issues/{issueId}/comments
    https://yandex.ru/support/tracker/en/api/issues/get-comments.md
    """
    return get_client().request(
        "GET",
        f"/issues/{issueId}/comments",
        params=given(expand=expand, perPage=perPage, id=id),
    )


@tool
def tracker_edit_comment(
    issueId: Annotated[NonEmptyStr, Field(description="ID or key of the issue.")],
    commentId: Annotated[
        NonEmptyStr,
        Field(description="Unique ID of the comment, numeric (id) or string (longId)."),
    ],
    text: Annotated[NonEmptyStr, Field(description="Edited issue comment.")],
    attachmentIds: Annotated[
        list | None, Field(description="IDs of temporary files to add as attachments.")
    ] = None,
    summonees: Annotated[
        list | None, Field(description="IDs or usernames of summoned users.")
    ] = None,
    markupType: Annotated[
        str | None,
        Field(description="Type of text markup. Specify `md` when the comment uses YFM markup."),
    ] = None,
) -> Any:
    """Edit a comment on an issue.

    PATCH /v3/issues/{issueId}/comments/{commentId}
    https://yandex.ru/support/tracker/en/api/issues/edit-comment.md
    """
    return get_client().request(
        "PATCH",
        f"/issues/{issueId}/comments/{commentId}",
        json=given(
            text=text,
            attachmentIds=attachmentIds,
            summonees=summonees,
            markupType=markupType,
        ),
    )


@tool
def tracker_delete_comment(
    issueId: Annotated[NonEmptyStr, Field(description="ID or key of the issue.")],
    commentId: Annotated[
        NonEmptyStr,
        Field(description="Unique ID of the comment, numeric (id) or string (longId)."),
    ],
) -> Any:
    """Delete a comment on an issue.

    DELETE /v3/issues/{issueId}/comments/{commentId}
    https://yandex.ru/support/tracker/en/api/issues/delete-comment.md
    """
    return get_client().request("DELETE", f"/issues/{issueId}/comments/{commentId}")


@tool
def tracker_add_reaction_to_comment(
    issueId: Annotated[NonEmptyStr, Field(description="Issue ID or key.")],
    commentId: Annotated[
        NonEmptyStr,
        Field(description="Unique ID of the comment, numeric (id) or string (longId)."),
    ],
    reactionName: Annotated[
        NonEmptyStr,
        Field(
            description="Reaction name: `LIKE`, `DISLIKE`, `LAUGH`, `HOORAY`, `CONFUSED`, "
            "`HEART`, `ROCKET`, `EYES`, `FIRE`, `OK`, `FACEPALM`, `CHECK`."
        ),
    ],
) -> Any:
    """React to a comment on an issue.

    POST /v3/issues/{issueId}/comments/{commentId}/reactions/{reactionName}
    https://yandex.ru/support/tracker/en/api/issues/add-reaction-to-comment.md
    """
    return get_client().request(
        "POST", f"/issues/{issueId}/comments/{commentId}/reactions/{reactionName}"
    )


@tool
def tracker_add_checklist_item(
    issueId: Annotated[NonEmptyStr, Field(description="Issue ID or key.")],
    text: Annotated[NonEmptyStr, Field(description="Text of the item.")],
    checked: Annotated[
        bool | None, Field(description="Mark the item as completed.")
    ] = None,
    assignee: Annotated[
        str | None,
        Field(description="ID or username of the user the checklist item is assigned to."),
    ] = None,
    deadline: Annotated[
        dict | None,
        Field(
            description="Deadline for the checklist item: `date` in "
            "`YYYY-MM-DDThh:mm:ss.sss±hhmm` format and `deadlineType`."
        ),
    ] = None,
) -> Any:
    """Create a checklist on an issue or add an item to it.

    POST /v3/issues/{issueId}/checklistItems
    https://yandex.ru/support/tracker/en/api/issues/add-checklist-item.md

    The response is the whole issue, not the created item.
    """
    return get_client().request(
        "POST",
        f"/issues/{issueId}/checklistItems",
        json=given(text=text, checked=checked, assignee=assignee, deadline=deadline),
    )


@tool
def tracker_get_checklist(
    issueId: Annotated[NonEmptyStr, Field(description="Issue ID or key.")],
) -> Any:
    """Get the checklist of an issue.

    GET /v3/issues/{issueId}/checklistItems
    https://yandex.ru/support/tracker/en/api/issues/get-checklist.md
    """
    return get_client().request("GET", f"/issues/{issueId}/checklistItems")


@tool
def tracker_edit_checklist_item(
    issueId: Annotated[NonEmptyStr, Field(description="Issue ID or key.")],
    checklistItemId: Annotated[
        NonEmptyStr,
        Field(description="Checklist item ID, from tracker_get_checklist."),
    ],
    text: Annotated[NonEmptyStr, Field(description="Text of the checklist item.")],
    checked: Annotated[
        bool | None, Field(description="Mark the item as completed.")
    ] = None,
    assignee: Annotated[
        str | None,
        Field(description="ID or username of the user the checklist item is assigned to."),
    ] = None,
    deadline: Annotated[
        dict | None,
        Field(
            description="Deadline for the checklist item: `date` in "
            "`YYYY-MM-DDThh:mm:ss.sss±hhmm` format and `deadlineType`."
        ),
    ] = None,
) -> Any:
    """Edit an item of an issue's checklist.

    PATCH /v3/issues/{issueId}/checklistItems/{checklistItemId}
    https://yandex.ru/support/tracker/en/api/issues/edit-checklist.md

    The response is the whole issue with its full checklist. (The page
    contradicts itself: its parameter table describes one item, its example shows
    an array of every item. This follows the table, which matches the item id in
    the path, and that is what the endpoint accepts.)
    """
    return get_client().request(
        "PATCH",
        f"/issues/{issueId}/checklistItems/{checklistItemId}",
        json=given(text=text, checked=checked, assignee=assignee, deadline=deadline),
    )


@tool
def tracker_delete_checklist(
    issueId: Annotated[NonEmptyStr, Field(description="Issue ID or key.")],
) -> Any:
    """Delete the whole checklist from an issue.

    DELETE /v3/issues/{issueId}/checklistItems
    https://yandex.ru/support/tracker/en/api/issues/delete-checklist.md
    """
    return get_client().request("DELETE", f"/issues/{issueId}/checklistItems")


@tool
def tracker_delete_checklist_item(
    issueId: Annotated[NonEmptyStr, Field(description="Issue ID or key.")],
    checklistItemId: Annotated[
        NonEmptyStr,
        Field(description="Checklist item ID, from tracker_get_checklist."),
    ],
) -> Any:
    """Delete one item from an issue's checklist.

    DELETE /v3/issues/{issueId}/checklistItems/{checklistItemId}
    https://yandex.ru/support/tracker/en/api/issues/delete-checklist-item.md
    """
    return get_client().request(
        "DELETE", f"/issues/{issueId}/checklistItems/{checklistItemId}"
    )


@tool
def tracker_get_attachments(
    issueId: Annotated[NonEmptyStr, Field(description="Issue ID or key.")],
) -> Any:
    """Get the files attached to an issue and to the comments below it.

    GET /v3/issues/{issueId}/attachments
    https://yandex.ru/support/tracker/en/api/issues/get-attachments-list.md
    """
    return get_client().request("GET", f"/issues/{issueId}/attachments")


@tool
def tracker_get_attachment(
    issueId: Annotated[NonEmptyStr, Field(description="Issue ID or key.")],
    fileId: Annotated[
        NonEmptyStr, Field(description="Unique file ID, from tracker_get_attachments.")
    ],
    fileName: Annotated[
        NonEmptyStr,
        Field(description="File name, from tracker_get_attachments. Part of the request path."),
    ],
    destDir: Annotated[
        NonEmptyStr, Field(description="Local directory to save the downloaded file in.")
    ],
    saveAs: Annotated[
        str | None,
        Field(description="Name to save the file under locally. Defaults to `fileName`."),
    ] = None,
) -> Any:
    """Download a file attached to an issue.

    GET /v3/issues/{issueId}/attachments/{fileId}/{fileName}
    https://yandex.ru/support/tracker/en/api/issues/get-attachment.md

    Writes the file to `destDir` and returns {"path", "name", "size"}.
    """
    return get_client().download(
        f"/issues/{issueId}/attachments/{fileId}/{fileName}", destDir, saveAs or fileName
    )


@tool
def tracker_get_attachment_preview(
    issueId: Annotated[NonEmptyStr, Field(description="Issue ID or key.")],
    fileId: Annotated[
        NonEmptyStr,
        Field(description="Unique ID of the attached file, from tracker_get_attachments."),
    ],
    destDir: Annotated[
        NonEmptyStr, Field(description="Local directory to save the thumbnail in.")
    ],
    saveAs: Annotated[
        str | None,
        Field(description="Name to save the thumbnail under locally. Defaults to `fileId`."),
    ] = None,
) -> Any:
    """Download the thumbnail of an image file attached to an issue.

    GET /v3/issues/{issueId}/thumbnails/{fileId}
    https://yandex.ru/support/tracker/en/api/issues/get-attachment-preview.md

    Writes the thumbnail to `destDir` and returns {"path", "name", "size"}.
    """
    return get_client().download(
        f"/issues/{issueId}/thumbnails/{fileId}", destDir, saveAs or fileId
    )


@tool
def tracker_post_attachment(
    issueId: Annotated[NonEmptyStr, Field(description="Issue ID or key.")],
    filePath: Annotated[
        NonEmptyStr,
        Field(description="Path to the local file to upload. Maximum size 1024 MB."),
    ],
    filename: Annotated[
        str | None,
        Field(
            description="New name to store the file under on the server. The local file name is "
            "used when omitted."
        ),
    ] = None,
) -> Any:
    """Attach a file to an issue.

    POST /v3/issues/{issueId}/attachments/
    https://yandex.ru/support/tracker/en/api/issues/post-attachment.md

    The file appears on the issue's Attachments tab.
    """
    return get_client().upload(
        f"/issues/{issueId}/attachments/", filePath, params=given(filename=filename)
    )


@tool
def tracker_post_temp_attachment(
    filePath: Annotated[
        NonEmptyStr,
        Field(description="Path to the local file to upload. Maximum size 1024 MB."),
    ],
    filename: Annotated[
        str | None,
        Field(
            description="New name to store the file under on the server. The local file name is "
            "used when omitted."
        ),
    ] = None,
) -> Any:
    """Upload a temporary file.

    POST /v3/attachments/
    https://yandex.ru/support/tracker/en/api/issues/temp-attachment.md

    Pass the returned ID in `attachmentIds` when creating an issue or adding a
    comment. Each temporary file ID can be used only once.
    """
    return get_client().upload("/attachments/", filePath, params=given(filename=filename))


@tool
def tracker_delete_attachment(
    issueId: Annotated[NonEmptyStr, Field(description="Issue ID or key.")],
    fileId: Annotated[
        NonEmptyStr, Field(description="Unique file ID, from tracker_get_attachments.")
    ],
) -> Any:
    """Delete a file attached to an issue.

    DELETE /v3/issues/{issueId}/attachments/{fileId}/
    https://yandex.ru/support/tracker/en/api/issues/delete-attachment.md
    """
    return get_client().request("DELETE", f"/issues/{issueId}/attachments/{fileId}/")


@tool
def tracker_new_worklog(
    issueId: Annotated[NonEmptyStr, Field(description="Issue ID or key.")],
    start: Annotated[
        NonEmptyStr,
        Field(
            description="Date and time when work on the issue started, in "
            "`YYYY-MM-DDThh:mm:ss.sss±hhmm` format."
        ),
    ],
    duration: Annotated[
        NonEmptyStr,
        Field(
            description="Time spent in ISO 8601 `PnYnMnDTnHnMnS` or `PnW` format — for example "
            "`P6W` (6 weeks), `PT300M` (300 minutes), `P0Y0M30DT2H10M25S`."
        ),
    ],
    comment: Annotated[
        str | None,
        Field(
            description="Text of the comment on the record, saved to the Report on time spent."
        ),
    ] = None,
) -> Any:
    """Add a record of time spent on an issue.

    POST /v3/issues/{issueId}/worklog
    https://yandex.ru/support/tracker/en/api/issues/new-worklog.md

    Time spent is measured in business weeks (5 days) and business days (8 hours),
    so a submitted `P5D` comes back as `P1W`.
    """
    return get_client().request(
        "POST",
        f"/issues/{issueId}/worklog",
        json=given(start=start, duration=duration, comment=comment),
    )


@tool
def tracker_get_issue_worklog(
    issueId: Annotated[NonEmptyStr, Field(description="Issue ID or key.")],
) -> Any:
    """Get all the records of time spent on an issue.

    GET /v3/issues/{issueId}/worklog
    https://yandex.ru/support/tracker/en/api/issues/issue-worklog.md
    """
    return get_client().request("GET", f"/issues/{issueId}/worklog")


@tool
def tracker_patch_worklog(
    issueId: Annotated[NonEmptyStr, Field(description="Issue ID or key.")],
    recordId: Annotated[
        NonEmptyStr, Field(description="ID of the record of time spent.")
    ],
    duration: Annotated[
        NonEmptyStr,
        Field(
            description="Time spent in ISO 8601 `PnYnMnDTnHnMnS` or `PnW` format — for example "
            "`P6W` (6 weeks), `PT300M` (300 minutes), `P0Y0M30DT2H10M25S`."
        ),
    ],
    comment: Annotated[
        str | None,
        Field(
            description="Text of the comment on the record, saved to the Report on time spent."
        ),
    ] = None,
) -> Any:
    """Edit a record of time spent on an issue.

    PATCH /v3/issues/{issueId}/worklog/{recordId}
    https://yandex.ru/support/tracker/en/api/issues/patch-worklog.md

    Time spent is measured in business weeks (5 days) and business days (8 hours),
    so a submitted `P5D` comes back as `P1W`.
    """
    return get_client().request(
        "PATCH",
        f"/issues/{issueId}/worklog/{recordId}",
        json=given(duration=duration, comment=comment),
    )


@tool
def tracker_delete_worklog(
    issueId: Annotated[NonEmptyStr, Field(description="Issue ID or key.")],
    recordId: Annotated[
        NonEmptyStr, Field(description="ID of the record of time spent.")
    ],
) -> Any:
    """Delete a record of time spent on an issue.

    DELETE /v3/issues/{issueId}/worklog/{recordId}
    https://yandex.ru/support/tracker/en/api/issues/delete-worklog.md
    """
    return get_client().request("DELETE", f"/issues/{issueId}/worklog/{recordId}")


@tool
def tracker_get_worklog(
    createdBy: Annotated[
        str | None, Field(description="ID or username of the record author.")
    ] = None,
    from_: Annotated[
        str | None,
        Field(
            description="Start of the interval the records were created in, in "
            "`YYYY-MM-DDThh:mm:ss.sss±hhmm` format. Sent as `createdAt=from:<start>`; requires "
            "`createdBy`."
        ),
    ] = None,
    to: Annotated[
        str | None,
        Field(
            description="End of the interval the records were created in, in "
            "`YYYY-MM-DDThh:mm:ss.sss±hhmm` format. Sent as `createdAt=to:<end>`; requires "
            "`createdBy`."
        ),
    ] = None,
) -> Any:
    """Select records of time spent by author and creation date.

    GET /v3/worklog
    https://yandex.ru/support/tracker/en/api/issues/get-worklog.md
    """
    params = given(createdBy=createdBy)
    createdAt = []
    if from_ is not None:
        # `from` is a Python keyword, so the argument is named from_.
        createdAt.append(f"from:{from_}")
    if to is not None:
        createdAt.append(f"to:{to}")
    if createdAt:
        params["createdAt"] = createdAt
    return get_client().request("GET", "/worklog", params=params)


@tool
def tracker_search_worklog(
    createdBy: Annotated[
        str | None, Field(description="ID or username of the record author.")
    ] = None,
    createdAt: Annotated[
        dict | None,
        Field(
            description="Record creation date and time: `from` and `to`, both in "
            "`YYYY-MM-DDThh:mm:ss.sss±hhmm` format."
        ),
    ] = None,
) -> Any:
    """Select records of time spent by author and creation date.

    POST /v3/worklog/_search
    https://yandex.ru/support/tracker/en/api/issues/get-worklog.md
    """
    return get_client().request(
        "POST", "/worklog/_search", json=given(createdBy=createdBy, createdAt=createdAt)
    )


@tool
def tracker_get_global_fields() -> Any:
    """Get all the global issue fields of the organization.

    GET /v3/fields
    https://yandex.ru/support/tracker/en/api/issues/get-global-fields.md
    """
    return get_client().request("GET", "/fields")


@tool
def tracker_create_field(
    name: Annotated[
        dict,
        Field(description="Field name: `en` in English and `ru` in Russian."),
    ],
    id: Annotated[NonEmptyStr, Field(description="Field ID.")],
    category: Annotated[
        NonEmptyStr,
        Field(
            description="ID of the field category. Get the list of categories with "
            "`GET /v3/fields/categories`."
        ),
    ],
    type: Annotated[
        NonEmptyStr,
        Field(
            description="Field type: `ru.yandex.startrek.core.fields.DateFieldType` (date), "
            "`ru.yandex.startrek.core.fields.DateTimeFieldType` (date/time), "
            "`ru.yandex.startrek.core.fields.StringFieldType` (one-line text), "
            "`ru.yandex.startrek.core.fields.TextFieldType` (multi-line text), "
            "`ru.yandex.startrek.core.fields.FloatFieldType` (fractional number), "
            "`ru.yandex.startrek.core.fields.IntegerFieldType` (integer), "
            "`ru.yandex.startrek.core.fields.UserFieldType` (user's name), "
            "`ru.yandex.startrek.core.fields.UriFieldType` (link)."
        ),
    ],
    optionsProvider: Annotated[
        dict | None,
        Field(
            description="Drop-down list settings: `type` (`FixedListOptionsProvider` for strings "
            "or numbers, `FixedUserListOptionsProvider` for users) and `values` (up to 3000 "
            "entries)."
        ),
    ] = None,
    order: Annotated[
        int | None,
        Field(description="Sequence number in the list of organization fields."),
    ] = None,
    description: Annotated[str | None, Field(description="Field description.")] = None,
    readonly: Annotated[
        bool | None,
        Field(description="`true` makes the field value non-editable, `false` editable."),
    ] = None,
    visible: Annotated[
        bool | None,
        Field(description="`true` keeps the field always visible in the interface."),
    ] = None,
    hidden: Annotated[
        bool | None,
        Field(description="`true` hides the field in the interface even when it is not empty."),
    ] = None,
    container: Annotated[
        bool | None,
        Field(
            description="`true` allows multiple values in the field, as in Tags. Applies to "
            "`StringFieldType`, `UserFieldType` and drop-down lists."
        ),
    ] = None,
) -> Any:
    """Create a global issue field.

    POST /v3/fields
    https://yandex.ru/support/tracker/en/api/issues/create-field.md
    """
    return get_client().request(
        "POST",
        "/fields",
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
def tracker_get_field(
    fieldId: Annotated[NonEmptyStr, Field(description="Issue field ID.")],
) -> Any:
    """Get the parameters and possible values of one issue field.

    GET /v3/fields/{fieldId}
    https://yandex.ru/support/tracker/en/api/issues/get-issue-fields.md
    """
    return get_client().request("GET", f"/fields/{fieldId}")


@tool
def tracker_patch_field(
    fieldId: Annotated[NonEmptyStr, Field(description="Issue field ID.")],
    version: Annotated[
        str | None,
        Field(description="Current version of the issue field. Changes apply only to it."),
    ] = None,
    name: Annotated[
        dict | None,
        Field(description="Field name: `en` in English and `ru` in Russian."),
    ] = None,
    category: Annotated[
        str | None,
        Field(
            description="ID of the field category. Get the list of categories with "
            "`GET /v3/fields/categories`."
        ),
    ] = None,
    order: Annotated[
        int | None,
        Field(description="Sequence number in the list of organization fields."),
    ] = None,
    description: Annotated[str | None, Field(description="Field description.")] = None,
    readonly: Annotated[
        bool | None,
        Field(description="`true` makes the field value non-editable, `false` editable."),
    ] = None,
    hidden: Annotated[
        bool | None,
        Field(description="`true` hides the field in the interface even when it is not empty."),
    ] = None,
    visible: Annotated[
        bool | None,
        Field(description="`true` keeps the field always visible in the interface."),
    ] = None,
    optionsProvider: Annotated[
        dict | None,
        Field(
            description="Allowed field values: `type` (type of field values) and `values` "
            "(array of field values)."
        ),
    ] = None,
) -> Any:
    """Edit an issue field: its name, and its possible values and settings.

    PATCH /v3/fields/{fieldId}
    https://yandex.ru/support/tracker/en/api/issues/patch-issue-field-name.md
    https://yandex.ru/support/tracker/en/api/issues/patch-issue-field-value.md

    The two pages describe the same endpoint — renaming a field and editing its
    values — and the arguments below are the union of what they document.
    """
    return get_client().request(
        "PATCH",
        f"/fields/{fieldId}",
        params=given(version=version),
        json=given(
            name=name,
            category=category,
            order=order,
            description=description,
            readonly=readonly,
            hidden=hidden,
            visible=visible,
            optionsProvider=optionsProvider,
        ),
    )


@tool
def tracker_create_field_category(
    name: Annotated[
        dict,
        Field(description="Category name: `en` in English and `ru` in Russian."),
    ],
    order: Annotated[
        int,
        Field(
            description="Weight of the field in the interface. Lower weights are displayed above "
            "higher ones."
        ),
    ],
    description: Annotated[str | None, Field(description="Category description.")] = None,
) -> Any:
    """Create a category for issue fields.

    POST /v3/fields/categories
    https://yandex.ru/support/tracker/en/api/issues/create-issue-field-category.md
    """
    return get_client().request(
        "POST",
        "/fields/categories",
        json=given(name=name, order=order, description=description),
    )


@tool
def tracker_patch_field_category(
    categoryId: Annotated[NonEmptyStr, Field(description="ID of the issue field category.")],
    name: Annotated[
        dict,
        Field(description="Category name: `en` in English and `ru` in Russian."),
    ],
    order: Annotated[
        int,
        Field(
            description="Weight of the field in the interface. Lower weights are displayed above "
            "higher ones."
        ),
    ],
    description: Annotated[str | None, Field(description="Category description.")] = None,
    version: Annotated[
        int | None,
        Field(description="Category version. Changes apply only to the current version."),
    ] = None,
) -> Any:
    """Edit a category of issue fields.

    PATCH /v3/fields/categories/{categoryId}
    https://yandex.ru/support/tracker/en/api/issues/patch-issue-field-category.md
    """
    return get_client().request(
        "PATCH",
        f"/fields/categories/{categoryId}",
        params=given(version=version),
        json=given(name=name, order=order, description=description),
    )


@tool
def tracker_get_applications() -> Any:
    """Get the external applications an issue can be linked to.

    GET /v3/applications
    https://yandex.ru/support/tracker/en/api/issues/get-applications.md
    """
    return get_client().request("GET", "/applications")


@tool
def tracker_create_report(
    fields: Annotated[
        dict,
        Field(
            description="Report parameters: `summary` (report name) and `parameters` with "
            "`type` (`issueFilterExport`), `format` (`xlsx`, `xml` or `csv`), `filter` "
            "(one of `query`, `filter` or `filterId`, plus `sorts` with `orderBy`/`orderAsc`) "
            "and `fields` (issue fields to include)."
        ),
    ],
) -> Any:
    """Generate a report of the issues matching the given search criteria.

    POST /v3/entities/report/
    https://yandex.ru/support/tracker/en/api/issues/create-report.md
    """
    return get_client().request("POST", "/entities/report/", json=given(fields=fields))


@tool
def tracker_search_reports(
    filter: Annotated[
        dict | None,
        Field(
            description="Report filter. Only `id` (report ID), `shortId` (short report ID) and "
            "`author` (the `id` of the report's `createdBy`) can be filtered on."
        ),
    ] = None,
    orderBy: Annotated[
        str | None,
        Field(
            description="Field to sort reports by: `id`, `shortId`, `createdBy`, `createdAt`, "
            "`updatedAt`, `self`."
        ),
    ] = None,
    orderAsc: Annotated[
        bool | None,
        Field(description="Sort direction: `true` ascending, `false` descending."),
    ] = None,
    perPage: Annotated[
        int | None, Field(description="Number of reports per response page. Default 50.")
    ] = None,
    page: Annotated[int | None, Field(description="Page number. Default 1.")] = None,
) -> Any:
    """Find the issue reports matching the given criteria.

    POST /v3/entities/report/_search
    https://yandex.ru/support/tracker/en/api/issues/search-reports.md
    """
    return get_client().request(
        "POST",
        "/entities/report/_search",
        params=given(perPage=perPage, page=page),
        json=given(filter=filter, orderBy=orderBy, orderAsc=orderAsc),
    )
