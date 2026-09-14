"""Projects, portfolios and goals — https://yandex.ru/support/tracker/en/api/entities/about-entities.md"""

from __future__ import annotations

from typing import Annotated, Any

from pydantic import Field

from ..client import given
from ..server import NonEmptyStr, get_client, tool


@tool
def tracker_create_entity(
    entityType: Annotated[
        NonEmptyStr,
        Field(description="Entity type: project, portfolio, goal."),
    ],
    summary: Annotated[NonEmptyStr, Field(description="Name (required field).")],
    queues: Annotated[
        str | None,
        Field(
            description=(
                "Queue (required for the project if the teamAccess field isn't specified)."
            )
        ),
    ] = None,
    teamAccess: Annotated[
        bool | None,
        Field(
            description=(
                "Access (required for the project if the queues field isn't specified)."
            )
        ),
    ] = None,
    description: Annotated[str | None, Field(description="Description.")] = None,
    markupType: Annotated[
        str | None,
        Field(
            description=(
                "Text markup type. If you use YFM markup in a comment or entity "
                "description, specify the `md` value."
            )
        ),
    ] = None,
    author: Annotated[str | None, Field(description="Author (user ID).")] = None,
    lead: Annotated[str | None, Field(description="Lead (user ID).")] = None,
    teamUsers: Annotated[
        list | None, Field(description="Participants (array of user IDs).")
    ] = None,
    clients: Annotated[
        list | None, Field(description="Customers (array of user IDs).")
    ] = None,
    followers: Annotated[
        list | None, Field(description="Followers (array of user IDs).")
    ] = None,
    start: Annotated[
        str | None, Field(description="Start date in `YYYY-MM-DDThh:mm:ss.sss±hhmm` format.")
    ] = None,
    end: Annotated[
        str | None, Field(description="Deadline in `YYYY-MM-DDThh:mm:ss.sss±hhmm` format.")
    ] = None,
    tags: Annotated[list | None, Field(description="Tags.")] = None,
    parentEntity: Annotated[
        dict | None,
        Field(
            description=(
                "Parent entity data: primary (ID of the main portfolio for projects and "
                "portfolios, or of the parent goal for goals) and secondary (IDs of "
                "additional portfolios; goals don't support secondary)."
            )
        ),
    ] = None,
    entityStatus: Annotated[
        str | None,
        Field(
            description=(
                "Status. For projects or portfolios: draft, draft2, in_progress, "
                "according_to_plan, postponed, at_risk, blocked, launched, cancelled. "
                "For goals: draft, according_to_plan, at_risk, blocked, achieved, "
                "partially_achieved, not_achieved, exceeded, cancelled."
            )
        ),
    ] = None,
    links: Annotated[
        list | None,
        Field(
            description=(
                "Array of objects with settings of links to other entities: relationship "
                "(link type) and entity (ID of the linked entity)."
            )
        ),
    ] = None,
    fields: Annotated[
        str | None,
        Field(description="Additional entity fields to include in the response."),
    ] = None,
) -> Any:
    """Create a new entity: a goal, project, or project portfolio.

    POST /v3/entities/{entityType}
    https://yandex.ru/support/tracker/en/api/entities/create-entity.md
    """
    return get_client().request(
        "POST",
        f"/entities/{entityType}",
        params=given(fields=fields),
        json={
            "fields": given(
                summary=summary,
                queues=queues,
                teamAccess=teamAccess,
                description=description,
                markupType=markupType,
                author=author,
                lead=lead,
                teamUsers=teamUsers,
                clients=clients,
                followers=followers,
                start=start,
                end=end,
                tags=tags,
                parentEntity=parentEntity,
                entityStatus=entityStatus,
            ),
            **given(links=links),
        },
    )


@tool
def tracker_get_entity(
    entityType: Annotated[
        NonEmptyStr,
        Field(description="Entity type: project, portfolio, goal."),
    ],
    entityId: Annotated[
        NonEmptyStr,
        Field(description="Entity ID. You can use the `id` or `shortId` parameter as the ID."),
    ],
    fields: Annotated[
        str | None,
        Field(description="Additional entity fields to include in the response."),
    ] = None,
    expand: Annotated[
        str | None,
        Field(
            description=(
                "Additional information to include in the response: `attachments` "
                "(attached files)."
            )
        ),
    ] = None,
) -> Any:
    """Get information about an entity: a goal, project, or project portfolio.

    GET /v3/entities/{entityType}/{entityId}
    https://yandex.ru/support/tracker/en/api/entities/get-entity.md
    """
    return get_client().request(
        "GET",
        f"/entities/{entityType}/{entityId}",
        params=given(fields=fields, expand=expand),
    )


@tool
def tracker_update_entity(
    entityType: Annotated[
        NonEmptyStr,
        Field(description="Entity type: project, portfolio, goal."),
    ],
    entityId: Annotated[
        NonEmptyStr,
        Field(description="Entity ID. You can use the `id` or `shortId` parameter as the ID."),
    ],
    summary: Annotated[str | None, Field(description="Name.")] = None,
    queues: Annotated[
        str | None,
        Field(
            description=(
                "Queue (required for the project if the teamAccess field isn't specified)."
            )
        ),
    ] = None,
    teamAccess: Annotated[
        bool | None,
        Field(
            description=(
                "Access (required for the project if the queues field isn't specified)."
            )
        ),
    ] = None,
    description: Annotated[str | None, Field(description="Description.")] = None,
    markupType: Annotated[
        str | None,
        Field(
            description=(
                "Text markup type. If you use YFM markup in a comment or entity "
                "description, specify the `md` value."
            )
        ),
    ] = None,
    author: Annotated[str | None, Field(description="Author (user ID).")] = None,
    lead: Annotated[str | None, Field(description="Lead (user ID).")] = None,
    teamUsers: Annotated[
        list | None, Field(description="Participants (array of user IDs).")
    ] = None,
    clients: Annotated[
        list | None, Field(description="Customers (array of user IDs).")
    ] = None,
    followers: Annotated[
        list | None, Field(description="Followers (array of user IDs).")
    ] = None,
    start: Annotated[
        str | None, Field(description="Start date in `YYYY-MM-DDThh:mm:ss.sss±hhmm` format.")
    ] = None,
    end: Annotated[
        str | None, Field(description="Deadline in `YYYY-MM-DDThh:mm:ss.sss±hhmm` format.")
    ] = None,
    tags: Annotated[list | None, Field(description="Tags.")] = None,
    parentEntity: Annotated[
        dict | None,
        Field(
            description=(
                "Parent entity data: primary (ID of the main portfolio for projects and "
                "portfolios, or of the parent goal for goals) and secondary (IDs of "
                "additional portfolios; goals don't support secondary)."
            )
        ),
    ] = None,
    entityStatus: Annotated[
        str | None,
        Field(
            description=(
                "Status. For projects or portfolios: draft, draft2, in_progress, "
                "according_to_plan, postponed, at_risk, blocked, launched, cancelled. "
                "For goals: draft, according_to_plan, at_risk, blocked, achieved, "
                "partially_achieved, not_achieved, exceeded, cancelled."
            )
        ),
    ] = None,
    checklistItems: Annotated[
        list | None,
        Field(
            description=(
                "Checklist of a project or portfolio; each object: id, text, checked, "
                "assignee, deadline, checklistItemType. Replaces the whole checklist."
            )
        ),
    ] = None,
    metricItems: Annotated[
        list | None,
        Field(
            description=(
                "Metrics; each object: text (metric name, required) and url (widget URL "
                "for an iframe). Replaces the whole list of metrics."
            )
        ),
    ] = None,
    keyResultItems: Annotated[
        list | None,
        Field(
            description=(
                "Key results of a goal; each object: type (`value` or `binary`, required), "
                "text (required), assignee, deadline, progress (start/end/current, required "
                "when type is `value`), achieved. Replaces the whole list of key results."
            )
        ),
    ] = None,
    comment: Annotated[str | None, Field(description="Comment.")] = None,
    links: Annotated[
        list | None,
        Field(
            description=(
                "Array of objects with settings of links to other entities: relationship "
                "(link type) and entity (ID of the linked entity)."
            )
        ),
    ] = None,
    fields: Annotated[
        str | None,
        Field(description="Additional entity fields to include in the response."),
    ] = None,
    expand: Annotated[
        str | None,
        Field(
            description=(
                "Additional information to include in the response: `attachments` "
                "(attached files)."
            )
        ),
    ] = None,
) -> Any:
    """Update information about an entity: a goal, project, or project portfolio.

    PATCH /v3/entities/{entityType}/{entityId}
    https://yandex.ru/support/tracker/en/api/entities/update-entity.md

    This is also the request that edits a goal's key results and an entity's
    metrics — see keyResultItems and metricItems:
    https://yandex.ru/support/tracker/en/api/entities/keyresults.md
    https://yandex.ru/support/tracker/en/api/entities/metric.md
    """
    return get_client().request(
        "PATCH",
        f"/entities/{entityType}/{entityId}",
        params=given(fields=fields, expand=expand),
        json={
            **given(
                fields=given(
                    summary=summary,
                    queues=queues,
                    teamAccess=teamAccess,
                    description=description,
                    markupType=markupType,
                    author=author,
                    lead=lead,
                    teamUsers=teamUsers,
                    clients=clients,
                    followers=followers,
                    start=start,
                    end=end,
                    tags=tags,
                    parentEntity=parentEntity,
                    entityStatus=entityStatus,
                    checklistItems=checklistItems,
                    metricItems=metricItems,
                    keyResultItems=keyResultItems,
                )
                or None
            ),
            **given(comment=comment, links=links),
        },
    )


@tool
def tracker_delete_entity(
    entityType: Annotated[
        NonEmptyStr,
        Field(description="Entity type: project, portfolio, goal."),
    ],
    entityId: Annotated[
        NonEmptyStr,
        Field(description="Entity ID. You can use the `id` or `shortId` parameter as the ID."),
    ],
    withBoard: Annotated[
        bool | None, Field(description="Delete together with the board.")
    ] = None,
) -> Any:
    """Delete an entity: a goal, project, or project portfolio.

    DELETE /v3/entities/{entityType}/{entityId}
    https://yandex.ru/support/tracker/en/api/entities/delete-entity.md
    """
    return get_client().request(
        "DELETE",
        f"/entities/{entityType}/{entityId}",
        params=given(withBoard=withBoard),
    )


@tool
def tracker_search_entities(
    entityType: Annotated[
        NonEmptyStr,
        Field(description="Entity type: project, portfolio, goal."),
    ],
    input: Annotated[
        str | None, Field(description="Substring in the entity name.")
    ] = None,
    filter: Annotated[
        dict | None,
        Field(
            description=(
                "Filtering parameters. The parameter can specify any field key and value "
                "for filtering."
            )
        ),
    ] = None,
    orderBy: Annotated[
        str | None,
        Field(
            description="Sorting parameters. The parameter can specify any field key for sorting."
        ),
    ] = None,
    orderAsc: Annotated[bool | None, Field(description="Sorting direction.")] = None,
    rootOnly: Annotated[
        bool | None, Field(description="Output only entities that are not nested.")
    ] = None,
    fields: Annotated[
        str | None, Field(description="Additional fields to include in the response.")
    ] = None,
    perPage: Annotated[
        int | None,
        Field(description="Number of issues per response page. The default value is 50."),
    ] = None,
    page: Annotated[
        int | None, Field(description="Page with search results. The default value is 1.")
    ] = None,
) -> Any:
    """Get a list of entities that meet specific criteria.

    POST /v3/entities/{entityType}/_search
    https://yandex.ru/support/tracker/en/api/entities/search-entities.md

    Entity field keys and value keys, e.g., statuses, sometimes differ from
    similar issue keys.
    """
    return get_client().request(
        "POST",
        f"/entities/{entityType}/_search",
        params=given(fields=fields, perPage=perPage, page=page),
        json=given(
            input=input,
            filter=filter,
            orderBy=orderBy,
            orderAsc=orderAsc,
            rootOnly=rootOnly,
        ),
    )


@tool
def tracker_bulkchange_entities(
    entityType: Annotated[
        NonEmptyStr,
        Field(description="Entity type: project, portfolio, goal."),
    ],
    metaEntities: Annotated[list, Field(description="List of entity IDs.")],
    values: Annotated[
        dict,
        Field(
            description=(
                "Object with settings for bulk entity changes: fields (object with "
                "key-value pairs), comment, links (array of objects with relationship "
                "and entity)."
            )
        ),
    ],
) -> Any:
    """Update multiple goals, projects, or project portfolios at once.

    POST /v3/entities/{entityType}/bulkchange/_update
    https://yandex.ru/support/tracker/en/api/entities/bulkchange-entities.md
    """
    return get_client().request(
        "POST",
        f"/entities/{entityType}/bulkchange/_update",
        json=given(metaEntities=metaEntities, values=values),
    )


@tool
def tracker_get_entity_events(
    entityType: Annotated[
        NonEmptyStr,
        Field(description="Entity type: project, portfolio, goal."),
    ],
    entityId: Annotated[
        NonEmptyStr,
        Field(description="Entity ID. You can use the `id` or `shortId` parameter as the ID."),
    ],
    perPage: Annotated[
        int | None,
        Field(
            description=(
                "Sets the maximum number of events in the response. The default value is 50."
            )
        ),
    ] = None,
    from_: Annotated[
        str | None,
        Field(
            description=(
                "ID of the event after which the list starts to be generated. The event "
                "itself is not included in the list. Not used together with `selected`."
            )
        ),
    ] = None,
    selected: Annotated[
        str | None,
        Field(
            description=(
                "ID of the event around which the list is generated. Not specified "
                "together with the `from` parameter."
            )
        ),
    ] = None,
    newEventsOnTop: Annotated[
        bool | None,
        Field(
            description="Reverses the order of events in the list. The default value is `false`."
        ),
    ] = None,
    direction: Annotated[
        str | None,
        Field(
            description=(
                "Sets the order of events in the list: `forward` (default), or `backward`, "
                "which inverts the `newEventsOnTop` parameter value."
            )
        ),
    ] = None,
) -> Any:
    """Get a paginated entity event history.

    GET /v3/entities/{entityType}/{entityId}/events/_relative
    https://yandex.ru/support/tracker/en/api/entities/get-events-relative.md
    """
    params = given(
        perPage=perPage,
        selected=selected,
        newEventsOnTop=newEventsOnTop,
        direction=direction,
    )
    if from_ is not None:
        # `from` is a Python keyword, so the argument is named from_.
        params["from"] = from_
    return get_client().request(
        "GET", f"/entities/{entityType}/{entityId}/events/_relative", params=params
    )


@tool
def tracker_entity_add_comment(
    entityType: Annotated[
        NonEmptyStr,
        Field(description="Entity type: project, portfolio, goal."),
    ],
    entityId: Annotated[
        NonEmptyStr,
        Field(description="Entity ID. You can use the `id` or `shortId` parameter as the ID."),
    ],
    text: Annotated[NonEmptyStr, Field(description="Text of the comment.")],
    attachmentIds: Annotated[
        list | None,
        Field(description="IDs of temporary files that will be added as attachments."),
    ] = None,
    summonees: Annotated[
        list | None, Field(description="IDs or usernames of summoned users.")
    ] = None,
    maillistSummonees: Annotated[
        list | None, Field(description="List of mailing lists mentioned in the comment.")
    ] = None,
    isAddToFollowers: Annotated[
        bool | None,
        Field(
            description="Adding a comment author to followers. The default value is `true`."
        ),
    ] = None,
    notify: Annotated[
        bool | None,
        Field(
            description=(
                "Notify the users specified in the Author, Lead, Participants, Customers, "
                "and Followers fields. The default value is `true`."
            )
        ),
    ] = None,
    notifyAuthor: Annotated[
        bool | None,
        Field(description="Notify the author of the changes. The default value is `false`."),
    ] = None,
    expand: Annotated[
        str | None,
        Field(
            description=(
                "Additional information to include in the response: `all`, `html` "
                "(comment HTML markup), `attachments`, `reactions`."
            )
        ),
    ] = None,
) -> Any:
    """Add a comment to an entity.

    POST /v3/entities/{entityType}/{entityId}/comments
    https://yandex.ru/support/tracker/en/api/entities/comments/add-comment.md
    """
    return get_client().request(
        "POST",
        f"/entities/{entityType}/{entityId}/comments",
        params=given(
            isAddToFollowers=isAddToFollowers,
            notify=notify,
            notifyAuthor=notifyAuthor,
            expand=expand,
        ),
        json=given(
            text=text,
            attachmentIds=attachmentIds,
            summonees=summonees,
            maillistSummonees=maillistSummonees,
        ),
    )


@tool
def tracker_entity_patch_comment(
    entityType: Annotated[
        NonEmptyStr,
        Field(description="Entity type: project, portfolio, goal."),
    ],
    entityId: Annotated[NonEmptyStr, Field(description="Entity ID.")],
    commentId: Annotated[NonEmptyStr, Field(description="Comment's unique ID.")],
    text: Annotated[str | None, Field(description="Text of the comment.")] = None,
    attachmentIds: Annotated[
        list | None,
        Field(description="IDs of temporary files that will be added as attachments."),
    ] = None,
    summonees: Annotated[
        list | None, Field(description="IDs or usernames of summoned users.")
    ] = None,
    maillistSummonees: Annotated[
        list | None, Field(description="List of mailing lists mentioned in the comment.")
    ] = None,
    isAddToFollowers: Annotated[
        bool | None,
        Field(
            description="Adding a comment author to followers. The default value is `true`."
        ),
    ] = None,
    notify: Annotated[
        bool | None,
        Field(
            description=(
                "Notify the users specified in the Author, Lead, Participants, Customers, "
                "and Followers fields. The default value is `true`."
            )
        ),
    ] = None,
    notifyAuthor: Annotated[
        bool | None,
        Field(description="Notify the author of the changes. The default value is `false`."),
    ] = None,
    expand: Annotated[
        str | None,
        Field(
            description=(
                "Additional information to include in the response: `all`, `html` "
                "(comment HTML markup), `attachments`, `reactions`."
            )
        ),
    ] = None,
) -> Any:
    """Edit an entity comment.

    PATCH /v3/entities/{entityType}/{entityId}/comments/{commentId}
    https://yandex.ru/support/tracker/en/api/entities/comments/patch-comment.md

    The page's summary line omits the comment ID, but its Resource table and its
    request example both address one comment, so the ID is part of the path.
    """
    return get_client().request(
        "PATCH",
        f"/entities/{entityType}/{entityId}/comments/{commentId}",
        params=given(
            isAddToFollowers=isAddToFollowers,
            notify=notify,
            notifyAuthor=notifyAuthor,
            expand=expand,
        ),
        json=given(
            text=text,
            attachmentIds=attachmentIds,
            summonees=summonees,
            maillistSummonees=maillistSummonees,
        ),
    )


@tool
def tracker_entity_get_comments(
    entityType: Annotated[
        NonEmptyStr,
        Field(description="Entity type: project, portfolio, goal."),
    ],
    entityId: Annotated[
        NonEmptyStr,
        Field(description="Entity ID. You can use the `id` or `shortId` parameter as the ID."),
    ],
    expand: Annotated[
        str | None,
        Field(
            description=(
                "Additional information to include in the response: `all`, `html` "
                "(comment HTML markup), `attachments`, `reactions`."
            )
        ),
    ] = None,
) -> Any:
    """Get the list of comments for an entity.

    GET /v3/entities/{entityType}/{entityId}/comments
    https://yandex.ru/support/tracker/en/api/entities/comments/get-all-comments.md
    """
    return get_client().request(
        "GET",
        f"/entities/{entityType}/{entityId}/comments",
        params=given(expand=expand),
    )


@tool
def tracker_entity_get_comments_relative(
    entityType: Annotated[
        NonEmptyStr,
        Field(description="Entity type: project, portfolio, goal."),
    ],
    entityId: Annotated[
        NonEmptyStr,
        Field(description="Entity ID. You can use the `id` or `shortId` parameter as the ID."),
    ],
    perPage: Annotated[
        int | None,
        Field(
            description=(
                "Defines the maximum number of comments in a response. The default value is 50."
            )
        ),
    ] = None,
    from_: Annotated[
        str | None,
        Field(
            description=(
                "ID of the comment after which the list starts to be generated. The comment "
                "itself is not included in the list. Not used together with `selected`."
            )
        ),
    ] = None,
    selected: Annotated[
        str | None,
        Field(
            description=(
                "ID of the comment around which the list is generated. Not specified "
                "together with the `from` parameter."
            )
        ),
    ] = None,
    newCommentsOnTop: Annotated[
        bool | None,
        Field(
            description=(
                "Reverses the order of comments in the list. The default value is `false`."
            )
        ),
    ] = None,
    direction: Annotated[
        str | None,
        Field(
            description=(
                "Determines the order of comments in the list: `forward` (default), or "
                "`backward`, which inverts the `newCommentsOnTop` parameter value."
            )
        ),
    ] = None,
) -> Any:
    """Get entity comments page by page.

    GET /v3/entities/{entityType}/{entityId}/comments/_relative
    https://yandex.ru/support/tracker/en/api/entities/comments/get-all-comments.md
    """
    params = given(
        perPage=perPage,
        selected=selected,
        newCommentsOnTop=newCommentsOnTop,
        direction=direction,
    )
    if from_ is not None:
        # `from` is a Python keyword, so the argument is named from_.
        params["from"] = from_
    return get_client().request(
        "GET", f"/entities/{entityType}/{entityId}/comments/_relative", params=params
    )


@tool
def tracker_entity_get_comment(
    entityType: Annotated[
        NonEmptyStr,
        Field(description="Entity type: project, portfolio, goal."),
    ],
    entityId: Annotated[NonEmptyStr, Field(description="Entity ID.")],
    commentId: Annotated[NonEmptyStr, Field(description="Comment's unique ID.")],
    expand: Annotated[
        str | None,
        Field(
            description=(
                "Additional information to include in the response: `all`, `html` "
                "(comment HTML markup), `attachments`, `reactions`."
            )
        ),
    ] = None,
) -> Any:
    """Get one entity comment.

    GET /v3/entities/{entityType}/{entityId}/comments/{commentId}
    https://yandex.ru/support/tracker/en/api/entities/comments/get-comment.md
    """
    return get_client().request(
        "GET",
        f"/entities/{entityType}/{entityId}/comments/{commentId}",
        params=given(expand=expand),
    )


@tool
def tracker_entity_delete_comment(
    entityType: Annotated[
        NonEmptyStr,
        Field(description="Entity type: project, portfolio, goal."),
    ],
    entityId: Annotated[NonEmptyStr, Field(description="Entity ID.")],
    commentId: Annotated[NonEmptyStr, Field(description="Comment's unique ID.")],
    notify: Annotated[
        bool | None,
        Field(
            description=(
                "Notify the users specified in the Author, Lead, Participants, Customers, "
                "and Followers fields. The default value is `true`."
            )
        ),
    ] = None,
    notifyAuthor: Annotated[
        bool | None,
        Field(description="Notify the author of the changes. The default value is `false`."),
    ] = None,
) -> Any:
    """Delete an entity comment.

    DELETE /v3/entities/{entityType}/{entityId}/comments/{commentId}
    https://yandex.ru/support/tracker/en/api/entities/comments/delete-comment.md
    """
    return get_client().request(
        "DELETE",
        f"/entities/{entityType}/{entityId}/comments/{commentId}",
        params=given(notify=notify, notifyAuthor=notifyAuthor),
    )


@tool
def tracker_entity_add_checklist_item(
    entityType: Annotated[
        NonEmptyStr,
        Field(description="Entity type: project, portfolio."),
    ],
    entityId: Annotated[
        NonEmptyStr,
        Field(description="Entity ID. You can use the `id` or `shortId` parameter as the ID."),
    ],
    text: Annotated[NonEmptyStr, Field(description="Text of the checklist item.")],
    checked: Annotated[
        bool | None,
        Field(
            description=(
                "Item completion flag: `true` marks the item as completed, `false` doesn't."
            )
        ),
    ] = None,
    assignee: Annotated[
        str | None,
        Field(description="ID or username of the user that the checklist item is assigned to."),
    ] = None,
    deadline: Annotated[
        dict | None,
        Field(
            description=(
                "Deadline for the checklist item: date (`YYYY-MM-DDThh:mm:ss.sss±hhmm`) "
                "and deadlineType."
            )
        ),
    ] = None,
    notify: Annotated[
        bool | None,
        Field(
            description=(
                "Notify the users specified in the Author, Responsible, Participants, "
                "Customers, and Followers fields. The default value is `true`."
            )
        ),
    ] = None,
    notifyAuthor: Annotated[
        bool | None,
        Field(description="Notify the author of the changes. The default value is `false`."),
    ] = None,
    fields: Annotated[
        str | None,
        Field(description="Additional entity fields to include in the response."),
    ] = None,
    expand: Annotated[
        str | None,
        Field(
            description=(
                "Additional information to include in the response: `attachments` "
                "(attached files)."
            )
        ),
    ] = None,
) -> Any:
    """Create a checklist in a project or portfolio, or add an item to it.

    POST /v3/entities/{entityType}/{entityId}/checklistItems
    https://yandex.ru/support/tracker/en/api/entities/checklists/add-checklist.md

    New items are added to the end of the list.
    """
    return get_client().request(
        "POST",
        f"/entities/{entityType}/{entityId}/checklistItems",
        params=given(
            notify=notify, notifyAuthor=notifyAuthor, fields=fields, expand=expand
        ),
        json=given(text=text, checked=checked, assignee=assignee, deadline=deadline),
    )


@tool
def tracker_entity_patch_checklist(
    entityType: Annotated[
        NonEmptyStr,
        Field(description="Entity type: project, portfolio."),
    ],
    entityId: Annotated[
        NonEmptyStr,
        Field(description="Entity ID. You can use the `id` or `shortId` parameter as the ID."),
    ],
    checklistItems: Annotated[
        list,
        Field(
            description=(
                "Checklist items to edit; each object takes id and text (both required) "
                "plus checked, assignee and deadline. An additional parameter left out is "
                "reset to its default value, so repeat the values you did not change."
            )
        ),
    ],
    notify: Annotated[
        bool | None,
        Field(
            description=(
                "Notify the users specified in the Author, Responsible, Participants, "
                "Customers, and Followers fields. The default value is `true`."
            )
        ),
    ] = None,
    notifyAuthor: Annotated[
        bool | None,
        Field(description="Notify the author of the changes. The default value is `false`."),
    ] = None,
    fields: Annotated[
        str | None,
        Field(description="Additional entity fields to include in the response."),
    ] = None,
    expand: Annotated[
        str | None,
        Field(
            description=(
                "Additional information to include in the response: `attachments` "
                "(attached files)."
            )
        ),
    ] = None,
) -> Any:
    """Edit checklist items in a project or portfolio.

    PATCH /v3/entities/{entityType}/{entityId}/checklistItems
    https://yandex.ru/support/tracker/en/api/entities/checklists/patch-checklist.md

    The number of items cannot change here — add or delete items with the
    dedicated requests instead.
    """
    return get_client().request(
        "PATCH",
        f"/entities/{entityType}/{entityId}/checklistItems",
        params=given(
            notify=notify, notifyAuthor=notifyAuthor, fields=fields, expand=expand
        ),
        json=checklistItems,
    )


@tool
def tracker_entity_patch_checklist_item(
    entityType: Annotated[
        NonEmptyStr,
        Field(description="Entity type: project, portfolio."),
    ],
    entityId: Annotated[
        NonEmptyStr,
        Field(description="Entity ID. You can use the `id` or `shortId` parameter as the ID."),
    ],
    checklistItemId: Annotated[NonEmptyStr, Field(description="Checklist item ID.")],
    text: Annotated[str | None, Field(description="Text of the checklist item.")] = None,
    checked: Annotated[
        bool | None,
        Field(
            description=(
                "Item completion flag: `true` marks the item as completed, `false` doesn't."
            )
        ),
    ] = None,
    assignee: Annotated[
        str | None,
        Field(description="ID or username of the user that the checklist item is assigned to."),
    ] = None,
    deadline: Annotated[
        dict | None,
        Field(
            description=(
                "Deadline for the checklist item: date (`YYYY-MM-DDThh:mm:ss.sss±hhmm`) "
                "and deadlineType."
            )
        ),
    ] = None,
    notify: Annotated[
        bool | None,
        Field(
            description=(
                "Notify the users specified in the Author, Responsible, Participants, "
                "Customers, and Followers fields. The default value is `true`."
            )
        ),
    ] = None,
    notifyAuthor: Annotated[
        bool | None,
        Field(description="Notify the author of the changes. The default value is `false`."),
    ] = None,
    fields: Annotated[
        str | None,
        Field(description="Additional entity fields to include in the response."),
    ] = None,
    expand: Annotated[
        str | None,
        Field(
            description=(
                "Additional information to include in the response: `attachments` "
                "(attached files)."
            )
        ),
    ] = None,
) -> Any:
    """Update information about a specific checklist item in a project or portfolio.

    PATCH /v3/entities/{entityType}/{entityId}/checklistItems/{checklistItemId}
    https://yandex.ru/support/tracker/en/api/entities/checklists/patch-checklist-item.md
    """
    return get_client().request(
        "PATCH",
        f"/entities/{entityType}/{entityId}/checklistItems/{checklistItemId}",
        params=given(
            notify=notify, notifyAuthor=notifyAuthor, fields=fields, expand=expand
        ),
        json=given(text=text, checked=checked, assignee=assignee, deadline=deadline),
    )


@tool
def tracker_entity_move_checklist_item(
    entityType: Annotated[
        NonEmptyStr,
        Field(description="Entity type: project, portfolio."),
    ],
    entityId: Annotated[
        NonEmptyStr,
        Field(description="Entity ID. You can use the `id` or `shortId` parameter as the ID."),
    ],
    checklistItemId: Annotated[NonEmptyStr, Field(description="Checklist item ID.")],
    before: Annotated[
        NonEmptyStr,
        Field(description="ID of the checklist item to be preceded by the inserted one."),
    ],
    notify: Annotated[
        bool | None,
        Field(
            description=(
                "Notify the users specified in the Author, Responsible, Participants, "
                "Customers, and Followers fields. The default value is `true`."
            )
        ),
    ] = None,
    notifyAuthor: Annotated[
        bool | None,
        Field(description="Notify the author of the changes. The default value is `false`."),
    ] = None,
    fields: Annotated[
        str | None,
        Field(description="Additional entity fields to include in the response."),
    ] = None,
    expand: Annotated[
        str | None,
        Field(
            description=(
                "Additional information to include in the response: `attachments` "
                "(attached files)."
            )
        ),
    ] = None,
) -> Any:
    """Move a checklist item across projects and portfolios.

    POST /v3/entities/{entityType}/{entityId}/checklistItems/{checklistItemId}/_move
    https://yandex.ru/support/tracker/en/api/entities/checklists/move-checklist-item.md
    """
    return get_client().request(
        "POST",
        f"/entities/{entityType}/{entityId}/checklistItems/{checklistItemId}/_move",
        params=given(
            notify=notify, notifyAuthor=notifyAuthor, fields=fields, expand=expand
        ),
        json=given(before=before),
    )


@tool
def tracker_entity_delete_checklist(
    entityType: Annotated[
        NonEmptyStr,
        Field(description="Entity type: project, portfolio."),
    ],
    entityId: Annotated[
        NonEmptyStr,
        Field(description="Entity ID. You can use the `id` or `shortId` parameter as the ID."),
    ],
    notify: Annotated[
        bool | None,
        Field(
            description=(
                "Notify the users specified in the Author, Responsible, Participants, "
                "Customers, and Followers fields. The default value is `true`."
            )
        ),
    ] = None,
    notifyAuthor: Annotated[
        bool | None,
        Field(description="Notify the author of the changes. The default value is `false`."),
    ] = None,
    fields: Annotated[
        str | None,
        Field(description="Additional entity fields to include in the response."),
    ] = None,
    expand: Annotated[
        str | None,
        Field(
            description=(
                "Additional information to include in the response: `attachments` "
                "(attached files)."
            )
        ),
    ] = None,
) -> Any:
    """Delete all checklist items from a project or portfolio.

    DELETE /v3/entities/{entityType}/{entityId}/checklistItems
    https://yandex.ru/support/tracker/en/api/entities/checklists/delete-checklist.md

    The action cannot be undone.
    """
    return get_client().request(
        "DELETE",
        f"/entities/{entityType}/{entityId}/checklistItems",
        params=given(
            notify=notify, notifyAuthor=notifyAuthor, fields=fields, expand=expand
        ),
    )


@tool
def tracker_entity_delete_checklist_item(
    entityType: Annotated[
        NonEmptyStr,
        Field(description="Entity type: project, portfolio."),
    ],
    entityId: Annotated[
        NonEmptyStr,
        Field(description="Entity ID. You can use the `id` or `shortId` parameter as the ID."),
    ],
    checklistItemId: Annotated[NonEmptyStr, Field(description="Checklist item ID.")],
    notify: Annotated[
        bool | None,
        Field(
            description=(
                "Notify the users specified in the Author, Responsible, Participants, "
                "Customers, and Followers fields. The default value is `true`."
            )
        ),
    ] = None,
    notifyAuthor: Annotated[
        bool | None,
        Field(description="Notify the author of the changes. The default value is `false`."),
    ] = None,
    fields: Annotated[
        str | None,
        Field(description="Additional entity fields to include in the response."),
    ] = None,
    expand: Annotated[
        str | None,
        Field(
            description=(
                "Additional information to include in the response: `attachments` "
                "(attached files)."
            )
        ),
    ] = None,
) -> Any:
    """Delete an item from a project or portfolio's checklist.

    DELETE /v3/entities/{entityType}/{entityId}/checklistItems/{checklistItemId}
    https://yandex.ru/support/tracker/en/api/entities/checklists/delete-checklist-item.md

    The action cannot be undone.
    """
    return get_client().request(
        "DELETE",
        f"/entities/{entityType}/{entityId}/checklistItems/{checklistItemId}",
        params=given(
            notify=notify, notifyAuthor=notifyAuthor, fields=fields, expand=expand
        ),
    )


@tool
def tracker_entity_get_attachments(
    entityType: Annotated[
        NonEmptyStr,
        Field(description="Entity type: project, portfolio, goal."),
    ],
    entityId: Annotated[
        NonEmptyStr,
        Field(description="Entity ID. You can use the `id` or `shortId` parameter as the ID."),
    ],
) -> Any:
    """Get the list of files attached to an entity.

    GET /v3/entities/{entityType}/{entityId}/attachments
    https://yandex.ru/support/tracker/en/api/entities/attachments/get-all-attachments.md
    """
    return get_client().request("GET", f"/entities/{entityType}/{entityId}/attachments")


@tool
def tracker_entity_get_attachment(
    entityType: Annotated[
        NonEmptyStr,
        Field(description="Entity type: project, portfolio, goal."),
    ],
    entityId: Annotated[NonEmptyStr, Field(description="Entity ID.")],
    fileId: Annotated[NonEmptyStr, Field(description="File's unique ID.")],
) -> Any:
    """Get information about a file attached to an entity.

    GET /v3/entities/{entityType}/{entityId}/attachments/{fileId}
    https://yandex.ru/support/tracker/en/api/entities/attachments/get-attachment.md

    Returns the attachment's metadata, not its contents.
    """
    return get_client().request(
        "GET", f"/entities/{entityType}/{entityId}/attachments/{fileId}"
    )


@tool
def tracker_entity_add_attachment(
    entityType: Annotated[
        NonEmptyStr,
        Field(description="Entity type: project, portfolio, goal."),
    ],
    entityId: Annotated[NonEmptyStr, Field(description="Entity ID.")],
    fileId: Annotated[
        NonEmptyStr,
        Field(description="ID of a temporary file preloaded into Tracker."),
    ],
    notify: Annotated[
        bool | None,
        Field(
            description=(
                "Notify the users specified in the Author, Lead, Participants, Customers, "
                "and Followers fields. The default value is `true`."
            )
        ),
    ] = None,
    notifyAuthor: Annotated[
        bool | None,
        Field(description="Notify the author of the changes. The default value is `false`."),
    ] = None,
    fields: Annotated[
        str | None,
        Field(description="Additional entity fields to include in the response."),
    ] = None,
    expand: Annotated[
        str | None,
        Field(
            description=(
                "Additional information to include in the response: `all`, `attachments` "
                "(attached files)."
            )
        ),
    ] = None,
) -> Any:
    """Attach an already-uploaded temporary file to an entity.

    POST /v3/entities/{entityType}/{entityId}/attachments/{fileId}
    https://yandex.ru/support/tracker/en/api/entities/attachments/add-attachment.md

    This sends no file contents: upload the file first with POST /v3/attachments/
    (tracker_post_temp_attachment) and pass the temporary file ID it returns as
    fileId.
    """
    return get_client().request(
        "POST",
        f"/entities/{entityType}/{entityId}/attachments/{fileId}",
        params=given(
            notify=notify, notifyAuthor=notifyAuthor, fields=fields, expand=expand
        ),
    )


@tool
def tracker_entity_delete_attachment(
    entityType: Annotated[
        NonEmptyStr,
        Field(description="Entity type: project, portfolio, goal."),
    ],
    entityId: Annotated[NonEmptyStr, Field(description="Entity ID.")],
    fileId: Annotated[NonEmptyStr, Field(description="File's unique ID.")],
) -> Any:
    """Delete a file attached to an entity.

    DELETE /v3/entities/{entityType}/{entityId}/attachments/{fileId}
    https://yandex.ru/support/tracker/en/api/entities/attachments/delete-attachment.md
    """
    return get_client().request(
        "DELETE", f"/entities/{entityType}/{entityId}/attachments/{fileId}"
    )


@tool
def tracker_entity_add_links(
    entityType: Annotated[
        NonEmptyStr,
        Field(description="Entity type: project, portfolio, goal."),
    ],
    entityId: Annotated[
        NonEmptyStr,
        Field(description="Entity ID. You can use the `id` or `shortId` parameter as the ID."),
    ],
    relationship: Annotated[
        NonEmptyStr,
        Field(
            description=(
                "Link type. For projects and portfolios: `depends on` (the current entity "
                "depends on the linked one), `is dependent by` (the current entity blocks "
                "the linked one), `works towards` (project link to a goal). For goals: "
                "`parent entity` (parent goal), `child entity` (subgoal), `depends on`, "
                "`is dependent by`, `is supported by` (link to a project)."
            )
        ),
    ],
    entity: Annotated[NonEmptyStr, Field(description="ID of the linked entity.")],
) -> Any:
    """Create a link between the entity in the path and another entity.

    POST /v3/entities/{entityType}/{entityId}/links
    https://yandex.ru/support/tracker/en/api/entities/links/add-links.md

    To add a parent entity for a project or portfolio, edit the parentEntity
    field with tracker_update_entity instead.
    """
    return get_client().request(
        "POST",
        f"/entities/{entityType}/{entityId}/links",
        json=given(relationship=relationship, entity=entity),
    )


@tool
def tracker_entity_get_links(
    entityType: Annotated[
        NonEmptyStr,
        Field(description="Entity type: project, portfolio, goal."),
    ],
    entityId: Annotated[
        NonEmptyStr,
        Field(description="Entity ID. You can use the `id` or `shortId` parameter as the ID."),
    ],
    fields: Annotated[
        str | None,
        Field(description="Fields of the linked entities to include in the response."),
    ] = None,
) -> Any:
    """Get information about an entity's links with other entities.

    GET /v3/entities/{entityType}/{entityId}/links
    https://yandex.ru/support/tracker/en/api/entities/links/get-links.md
    """
    return get_client().request(
        "GET", f"/entities/{entityType}/{entityId}/links", params=given(fields=fields)
    )


@tool
def tracker_entity_delete_link(
    entityType: Annotated[
        NonEmptyStr,
        Field(description="Entity type: project, portfolio, goal."),
    ],
    entityId: Annotated[
        NonEmptyStr,
        Field(description="Entity ID. You can use the `id` or `shortId` parameter as the ID."),
    ],
    right: Annotated[
        NonEmptyStr, Field(description="ID of the entity whose link is deleted.")
    ],
) -> Any:
    """Delete the link between the entity in the path and the entity in `right`.

    DELETE /v3/entities/{entityType}/{entityId}/links
    https://yandex.ru/support/tracker/en/api/entities/links/delete-link.md
    """
    return get_client().request(
        "DELETE", f"/entities/{entityType}/{entityId}/links", params=given(right=right)
    )


@tool
def tracker_entity_get_permissions(
    entityType: Annotated[
        NonEmptyStr,
        Field(description="Entity type: project, portfolio, goal."),
    ],
    entityId: Annotated[
        NonEmptyStr,
        Field(description="Entity ID. You can use the `id` or `shortId` parameter as the ID."),
    ],
) -> Any:
    """Get an entity's permissions in the `acl` object format.

    GET /v3/entities/{entityType}/{entityId}/permissions
    https://yandex.ru/support/tracker/en/api/entities/get-access.md

    Unlike tracker_entity_get_extended_permissions, this does not return
    permissionSources, the parent entity the current one inherits access from.
    """
    return get_client().request("GET", f"/entities/{entityType}/{entityId}/permissions")


@tool
def tracker_entity_get_extended_permissions(
    entityType: Annotated[
        NonEmptyStr,
        Field(description="Entity type: project, portfolio, goal."),
    ],
    entityId: Annotated[
        NonEmptyStr,
        Field(description="Entity ID. You can use the `id` or `shortId` parameter as the ID."),
    ],
) -> Any:
    """Get an entity's access settings, including inherited ones.

    GET /v3/entities/{entityType}/{entityId}/extendedPermissions
    https://yandex.ru/support/tracker/en/api/entities/get-access.md

    Adds permissionSources — the parent entity the current one inherits access
    settings from — to the `acl` object.
    """
    return get_client().request(
        "GET", f"/entities/{entityType}/{entityId}/extendedPermissions"
    )


@tool
def tracker_entity_patch_permissions(
    entityType: Annotated[
        NonEmptyStr,
        Field(description="Entity type: project, portfolio, goal."),
    ],
    entityId: Annotated[
        NonEmptyStr,
        Field(description="Entity ID. You can use the `id` or `shortId` parameter as the ID."),
    ],
    grant: Annotated[
        dict | None,
        Field(
            description=(
                "Permissions to grant, keyed by access type — READ, WRITE or GRANT — each "
                "an object with users (IDs or usernames), groups (group IDs) and roles "
                "(AUTHOR, OWNER, CLIENT, FOLLOWER, MEMBER)."
            )
        ),
    ] = None,
    revoke: Annotated[
        dict | None,
        Field(
            description=(
                "Permissions to revoke, keyed by access type — READ, WRITE or GRANT — each "
                "an object with users (IDs or usernames), groups (group IDs) and roles "
                "(AUTHOR, OWNER, CLIENT, FOLLOWER, MEMBER)."
            )
        ),
    ] = None,
) -> Any:
    """Grant or revoke access to an entity.

    PATCH /v3/entities/{entityType}/{entityId}/permissions
    https://yandex.ru/support/tracker/en/api/entities/patch-access.md

    The body is the `acl` object itself, so permissionSources cannot be set here —
    use tracker_entity_patch_extended_permissions for that. Access inheritance
    must be off before permissions can be changed.
    """
    return get_client().request(
        "PATCH",
        f"/entities/{entityType}/{entityId}/permissions",
        json=given(grant=grant, revoke=revoke),
    )


@tool
def tracker_entity_patch_extended_permissions(
    entityType: Annotated[
        NonEmptyStr,
        Field(description="Entity type: project, portfolio, goal."),
    ],
    entityId: Annotated[
        NonEmptyStr,
        Field(description="Entity ID. You can use the `id` or `shortId` parameter as the ID."),
    ],
    permissionSources: Annotated[
        str | list | None,
        Field(
            description=(
                "ID of the parent entity the current one inherits access settings from: the "
                "main portfolio for projects and portfolios, or the parent goal for goals. "
                "Pass an empty array to disable access inheritance."
            )
        ),
    ] = None,
    acl: Annotated[
        dict | None,
        Field(
            description=(
                "Permissions to change: grant and revoke objects, each keyed by access type "
                "— READ, WRITE or GRANT — with users (IDs or usernames), groups (group IDs) "
                "and roles (AUTHOR, OWNER, CLIENT, FOLLOWER, MEMBER)."
            )
        ),
    ] = None,
) -> Any:
    """Grant or revoke access to an entity, including access inheritance.

    PATCH /v3/entities/{entityType}/{entityId}/extendedPermissions
    https://yandex.ru/support/tracker/en/api/entities/patch-access.md

    While permissionSources is non-empty, acl is rejected and the entity's
    teamAccess parameter is ignored — disable inheritance first.
    """
    return get_client().request(
        "PATCH",
        f"/entities/{entityType}/{entityId}/extendedPermissions",
        json=given(permissionSources=permissionSources, acl=acl),
    )
