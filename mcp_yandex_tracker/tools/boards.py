"""Boards, columns and sprints — https://yandex.ru/support/tracker/en/api/boards/get-boards.md"""

from __future__ import annotations

from typing import Annotated, Any

from pydantic import Field

from ..client import given, if_match
from ..server import NonEmptyStr, get_client, tool


@tool
def tracker_get_boards() -> Any:
    """Get the parameters of all issue boards created by the organization users.

    GET /v3/boards
    https://yandex.ru/support/tracker/en/api/boards/get-boards.md
    """
    return get_client().request("GET", "/boards")


@tool
def tracker_get_boards_paginate(
    perPage: Annotated[
        int | None, Field(description="The number of items per page, no more than 500.")
    ] = None,
    id: Annotated[
        int | None,
        Field(description="The board ID to start the next page of results from."),
    ] = None,
) -> Any:
    """Get the parameters of all boards with relative pagination support.

    GET /v3/boards/_paginate
    https://yandex.ru/support/tracker/en/api/boards/get-boards-paginate.md

    Boards are sorted by ascending ID and no more than 500 records are
    returned; pass the ID of the last board of a page as `id` to get the next.
    """
    return get_client().request("GET", "/boards/_paginate", params=given(perPage=perPage, id=id))


@tool
def tracker_get_board(
    boardId: Annotated[NonEmptyStr, Field(description="Board ID.")],
) -> Any:
    """Get the parameters of an issue board.

    GET /v3/boards/{boardId}
    https://yandex.ru/support/tracker/en/api/boards/get-board.md
    """
    return get_client().request("GET", f"/boards/{boardId}")


@tool
def tracker_create_board(
    name: Annotated[NonEmptyStr, Field(description="Board name.")],
    defaultQueue: Annotated[
        str | int | dict,
        Field(
            description=(
                "Default queue for creating issues. An object with `id` and `key`, "
                "a string (queue key), or a number (queue ID)."
            )
        ),
    ],
    boardType: Annotated[
        str | None,
        Field(
            description="Board type: `default` (basic), `scrum`, or `kanban`.",
        ),
    ] = None,
    filter: Annotated[
        dict | None,
        Field(
            description=(
                "Filter conditions for selecting board issues, as field key to value or "
                "array of values. Incompatible with `query`."
            )
        ),
    ] = None,
    orderBy: Annotated[
        str | None, Field(description="Key of the field used to sort board issues.")
    ] = None,
    orderAsc: Annotated[
        bool | None,
        Field(description="Sort direction: `true` ascending, `false` descending."),
    ] = None,
    query: Annotated[
        str | None,
        Field(
            description=(
                "Filter for selecting board issues, in the query language. "
                "Incompatible with `filter`, `orderBy` and `orderAsc`."
            )
        ),
    ] = None,
    useRanking: Annotated[
        bool | None,
        Field(description="Whether the order of issues on the board can be changed."),
    ] = None,
    country: Annotated[
        dict | None,
        Field(
            description=(
                "Country whose business calendar the burndown chart uses, as {\"id\": \"<ID>\"}. "
                "Get the IDs with GET /v3/countries."
            )
        ),
    ] = None,
) -> Any:
    """Create an issue board.

    POST /v3/boards/
    https://yandex.ru/support/tracker/en/api/boards/post-board.md
    """
    return get_client().request(
        "POST",
        "/boards/",
        json=given(
            name=name,
            defaultQueue=defaultQueue,
            boardType=boardType,
            filter=filter,
            orderBy=orderBy,
            orderAsc=orderAsc,
            query=query,
            useRanking=useRanking,
            country=country,
        ),
    )


@tool
def tracker_patch_board(
    boardId: Annotated[NonEmptyStr, Field(description="Board ID.")],
    name: Annotated[str | None, Field(description="Board name.")] = None,
    columns: Annotated[
        list | None,
        Field(
            description=(
                "New board columns, each with `id`, `name` and `statuses` "
                "(keys of the issue statuses shown in the column)."
            )
        ),
    ] = None,
    filter: Annotated[
        dict | None,
        Field(
            description=(
                "Filter conditions for selecting board issues, as field key to value or "
                "array of values. Incompatible with `query`."
            )
        ),
    ] = None,
    orderBy: Annotated[
        str | None, Field(description="Key of the field used to sort board issues.")
    ] = None,
    orderAsc: Annotated[
        bool | None,
        Field(description="Sort direction: `true` ascending, `false` descending."),
    ] = None,
    query: Annotated[
        str | None,
        Field(
            description=(
                "Filter for selecting board issues, in the query language. "
                "Incompatible with `filter`, `orderBy` and `orderAsc`."
            )
        ),
    ] = None,
    useRanking: Annotated[
        bool | None,
        Field(description="Whether the order of issues on the board can be changed."),
    ] = None,
    country: Annotated[
        dict | None,
        Field(
            description=(
                "Country whose business calendar the burndown chart uses, as {\"id\": \"<ID>\"}. "
                "Get the IDs with GET /v3/countries."
            )
        ),
    ] = None,
    version: Annotated[
        int | None,
        Field(
            description=(
                "Current board version. The change is applied only if the board is "
                "still at this version."
            )
        ),
    ] = None,
) -> Any:
    """Edit the parameters of an issue board.

    PATCH /v3/boards/{boardId}
    https://yandex.ru/support/tracker/en/api/boards/patch-board.md

    The current version is the `version` field returned by tracker_get_board.
    """
    return get_client().request(
        "PATCH",
        f"/boards/{boardId}",
        json=given(
            name=name,
            columns=columns,
            filter=filter,
            orderBy=orderBy,
            orderAsc=orderAsc,
            query=query,
            useRanking=useRanking,
            country=country,
        ),
        headers=if_match(version),
    )


@tool
def tracker_delete_board(
    boardId: Annotated[NonEmptyStr, Field(description="Board ID.")],
) -> Any:
    """Delete an issue board.

    DELETE /v3/boards/{boardId}
    https://yandex.ru/support/tracker/en/api/boards/delete-board.md
    """
    return get_client().request("DELETE", f"/boards/{boardId}")


@tool
def tracker_get_board_columns(
    boardId: Annotated[NonEmptyStr, Field(description="Board ID.")],
) -> Any:
    """Get the parameters of all columns of a board.

    GET /v3/boards/{boardId}/columns
    https://yandex.ru/support/tracker/en/api/boards/get-columns.md
    """
    return get_client().request("GET", f"/boards/{boardId}/columns")


@tool
def tracker_get_board_column(
    boardId: Annotated[NonEmptyStr, Field(description="Board ID.")],
    columnId: Annotated[NonEmptyStr, Field(description="Column ID.")],
) -> Any:
    """Get the parameters of one column of a board.

    GET /v3/boards/{boardId}/columns/{columnId}
    https://yandex.ru/support/tracker/en/api/boards/get-column.md
    """
    return get_client().request("GET", f"/boards/{boardId}/columns/{columnId}")


@tool
def tracker_create_board_column(
    boardId: Annotated[NonEmptyStr, Field(description="Board ID.")],
    name: Annotated[NonEmptyStr, Field(description="Column name.")],
    statuses: Annotated[
        list,
        Field(description="Keys of the issue statuses to be included in the column."),
    ],
    version: Annotated[
        int | None,
        Field(
            description=(
                "Current board version. The change is applied only if the board is "
                "still at this version."
            )
        ),
    ] = None,
) -> Any:
    """Create a column on an issue board.

    POST /v3/boards/{boardId}/columns/
    https://yandex.ru/support/tracker/en/api/boards/post-column.md

    The current version is the `version` field returned by tracker_get_board.
    """
    return get_client().request(
        "POST",
        f"/boards/{boardId}/columns/",
        json=given(name=name, statuses=statuses),
        headers=if_match(version),
    )


@tool
def tracker_patch_board_column(
    boardId: Annotated[NonEmptyStr, Field(description="Board ID.")],
    columnId: Annotated[NonEmptyStr, Field(description="Column ID.")],
    name: Annotated[str | None, Field(description="Column name.")] = None,
    statuses: Annotated[
        list | None,
        Field(description="Keys of the issue statuses to be included in the column."),
    ] = None,
    version: Annotated[
        int | None,
        Field(
            description=(
                "Current board version. The change is applied only if the board is "
                "still at this version."
            )
        ),
    ] = None,
) -> Any:
    """Edit the parameters of a board column.

    PATCH /v3/boards/{boardId}/columns/{columnId}
    https://yandex.ru/support/tracker/en/api/boards/patch-column.md

    The current version is the `version` field returned by tracker_get_board.
    """
    return get_client().request(
        "PATCH",
        f"/boards/{boardId}/columns/{columnId}",
        json=given(name=name, statuses=statuses),
        headers=if_match(version),
    )


@tool
def tracker_delete_board_column(
    boardId: Annotated[NonEmptyStr, Field(description="Board ID.")],
    columnId: Annotated[NonEmptyStr, Field(description="Column ID.")],
    version: Annotated[
        int | None,
        Field(
            description=(
                "Current board version. The change is applied only if the board is "
                "still at this version."
            )
        ),
    ] = None,
) -> Any:
    """Delete a board column.

    DELETE /v3/boards/{boardId}/columns/{columnId}
    https://yandex.ru/support/tracker/en/api/boards/delete-column.md

    The current version is the `version` field returned by tracker_get_board.
    """
    return get_client().request(
        "DELETE",
        f"/boards/{boardId}/columns/{columnId}",
        headers=if_match(version),
    )


@tool
def tracker_get_board_sprints(
    boardId: Annotated[NonEmptyStr, Field(description="Board ID.")],
) -> Any:
    """Get the parameters of all sprints of a board.

    GET /v3/boards/{boardId}/sprints
    https://yandex.ru/support/tracker/en/api/boards/get-sprints.md

    Each sprint carries a `status`: `draft` (open), `in_progress` (in
    progress), `released` (resolved) or `archived`. The sprint currently
    running is the one with `status: in_progress`.
    """
    return get_client().request("GET", f"/boards/{boardId}/sprints")


@tool
def tracker_get_sprint(
    sprintId: Annotated[NonEmptyStr, Field(description="Sprint ID.")],
) -> Any:
    """Get the parameters of a sprint.

    GET /v3/sprints/{sprintId}
    https://yandex.ru/support/tracker/en/api/boards/get-sprint.md
    """
    return get_client().request("GET", f"/sprints/{sprintId}")


@tool
def tracker_create_sprint(
    name: Annotated[NonEmptyStr, Field(description="Sprint name.")],
    board: Annotated[
        dict,
        Field(
            description=(
                "Board whose issues the sprint refers to, as {\"id\": \"<board_ID>\"}."
            )
        ),
    ],
    startDate: Annotated[
        NonEmptyStr, Field(description="Sprint start date in YYYY-MM-DD format.")
    ],
    endDate: Annotated[
        NonEmptyStr, Field(description="Sprint end date in YYYY-MM-DD format.")
    ],
) -> Any:
    """Create a sprint.

    POST /v3/sprints
    https://yandex.ru/support/tracker/en/api/boards/post-sprint.md
    """
    return get_client().request(
        "POST",
        "/sprints",
        json=given(name=name, board=board, startDate=startDate, endDate=endDate),
    )


@tool
def tracker_patch_sprint(
    sprintId: Annotated[NonEmptyStr, Field(description="Sprint ID.")],
    name: Annotated[str | None, Field(description="Sprint name.")] = None,
    startDate: Annotated[
        str | None, Field(description="Sprint start date in YYYY-MM-DD format.")
    ] = None,
    endDate: Annotated[
        str | None, Field(description="Sprint end date in YYYY-MM-DD format.")
    ] = None,
    status: Annotated[
        str | None,
        Field(
            description=(
                "Sprint status: `draft` (open), `in_progress` (in progress), "
                "`released` (released) or `archived` (archived)."
            )
        ),
    ] = None,
    version: Annotated[
        int | None,
        Field(
            description=(
                "Sprint version. Specify it to avoid losing changes during "
                "simultaneous editing."
            )
        ),
    ] = None,
) -> Any:
    """Edit the parameters of a sprint.

    PATCH /v3/sprints/{sprintId}
    https://yandex.ru/support/tracker/en/api/boards/patch-sprint.md

    The current version is the `version` field returned by tracker_get_sprint.
    """
    return get_client().request(
        "PATCH",
        f"/sprints/{sprintId}",
        json=given(name=name, startDate=startDate, endDate=endDate, status=status),
        headers=if_match(version),
    )


@tool
def tracker_start_sprint(
    sprintId: Annotated[NonEmptyStr, Field(description="Sprint ID.")],
    version: Annotated[
        int | None,
        Field(
            description=(
                "Sprint version. Specify it to avoid losing changes during "
                "simultaneous editing."
            )
        ),
    ] = None,
) -> Any:
    """Start a sprint, changing its status to `in_progress`.

    POST /v3/sprints/{sprintId}/_start
    https://yandex.ru/support/tracker/en/api/boards/start-sprint.md

    The current version is the `version` field returned by tracker_get_sprint.
    """
    return get_client().request(
        "POST",
        f"/sprints/{sprintId}/_start",
        headers=if_match(version),
    )


@tool
def tracker_archive_sprint(
    sprintId: Annotated[NonEmptyStr, Field(description="Sprint ID.")],
    version: Annotated[
        int | None,
        Field(
            description=(
                "Sprint version. Specify it to avoid losing changes during "
                "simultaneous editing."
            )
        ),
    ] = None,
) -> Any:
    """Archive a sprint.

    POST /v3/sprints/{sprintId}/_archive
    https://yandex.ru/support/tracker/en/api/boards/archive-sprint.md

    The current version is the `version` field returned by tracker_get_sprint.
    """
    return get_client().request(
        "POST",
        f"/sprints/{sprintId}/_archive",
        headers=if_match(version),
    )


@tool
def tracker_delete_sprint(
    sprintId: Annotated[NonEmptyStr, Field(description="Sprint ID.")],
) -> Any:
    """Delete a sprint.

    DELETE /v3/sprints/{sprintId}
    https://yandex.ru/support/tracker/en/api/boards/delete-sprint.md
    """
    return get_client().request("DELETE", f"/sprints/{sprintId}")
