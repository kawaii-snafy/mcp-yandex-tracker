"""Reference dictionaries — https://yandex.ru/support/tracker/en/api/admin/get-statuses.md"""

from __future__ import annotations

from typing import Annotated, Any

from pydantic import Field

from ..client import given
from ..server import NonEmptyStr, get_client, tool


@tool
def tracker_get_issuetypes() -> Any:
    """Get the list of available issue types.

    GET /v3/issuetypes
    https://yandex.ru/support/tracker/en/api/admin/get-issue-types.md
    """
    return get_client().request("GET", "/issuetypes")


@tool
def tracker_create_issuetype(
    key: Annotated[NonEmptyStr, Field(description="Key of the issue type.")],
    name: Annotated[
        dict,
        Field(description='Issue type name per language: {"ru": "Клиент", "en": "Customer"}.'),
    ],
) -> Any:
    """Create a new issue type.

    POST /v3/issuetypes/
    https://yandex.ru/support/tracker/en/api/admin/create-issue-type.md

    Requires Administrator rights in the organization.
    """
    return get_client().request("POST", "/issuetypes/", json=given(key=key, name=name))


@tool
def tracker_patch_issuetype(
    issueTypeId: Annotated[
        NonEmptyStr,
        Field(description="Unique ID of the issue type in Yandex Tracker, or the issue type key."),
    ],
    version: Annotated[
        int | None,
        Field(
            description=(
                "Version of the issue type. Changes apply only to the current version "
                "of the issue type."
            )
        ),
    ] = None,
    name: Annotated[
        dict | None,
        Field(description='Issue type name per language: {"ru": "Покупатель", "en": "Customer"}.'),
    ] = None,
) -> Any:
    """Modify an existing issue type.

    PATCH /v3/issuetypes/{issueTypeId}
    https://yandex.ru/support/tracker/en/api/admin/patch-issue-type.md

    Requires Administrator rights. Call tracker_get_issuetypes to read the
    current `version`.
    """
    return get_client().request(
        "PATCH",
        f"/issuetypes/{issueTypeId}",
        params=given(version=version),
        json=given(name=name),
    )


@tool
def tracker_get_statuses() -> Any:
    """Get the list of issue statuses.

    GET /v3/statuses
    https://yandex.ru/support/tracker/en/api/admin/get-statuses.md
    """
    return get_client().request("GET", "/statuses")


@tool
def tracker_create_status(
    key: Annotated[
        NonEmptyStr,
        Field(
            description=(
                "Status key (ID). Use Latin characters only, starting with a lowercase letter."
            )
        ),
    ],
    name: Annotated[
        dict,
        Field(description='Status name per language: {"ru": "Мой статус", "en": "My status"}.'),
    ],
    type: Annotated[
        NonEmptyStr,
        Field(
            description=(
                "Status type. Acceptable values include: `new`, `inProgress`, `paused`, "
                "`done`, `cancelled`."
            )
        ),
    ],
) -> Any:
    """Create a new issue status.

    POST /v3/statuses/
    https://yandex.ru/support/tracker/en/api/admin/create-status.md

    Requires Administrator rights in the organization.
    """
    return get_client().request("POST", "/statuses/", json=given(key=key, name=name, type=type))


@tool
def tracker_patch_status(
    statusId: Annotated[
        NonEmptyStr,
        Field(description="Unique ID of the issue status in Yandex Tracker, or the status key."),
    ],
    version: Annotated[
        int | None,
        Field(
            description=(
                "Version of the issue status. Changes are only made to the current version."
            )
        ),
    ] = None,
    name: Annotated[
        dict | None,
        Field(description='Status name per language: {"ru": "Мой статус", "en": "My status"}.'),
    ] = None,
    description: Annotated[str | None, Field(description="Status description.")] = None,
    order: Annotated[
        int | None,
        Field(
            description=(
                "Status weight. This parameter affects the order of status display "
                "in the interface."
            )
        ),
    ] = None,
    type: Annotated[
        str | None,
        Field(
            description=(
                "Status type. Acceptable values include: `new`, `inProgress`, `paused`, "
                "`done`, `cancelled`."
            )
        ),
    ] = None,
) -> Any:
    """Change an existing issue status.

    PATCH /v3/statuses/{statusId}
    https://yandex.ru/support/tracker/en/api/admin/patch-status.md

    Requires Administrator rights. Call tracker_get_statuses to read the
    current `version`.
    """
    return get_client().request(
        "PATCH",
        f"/statuses/{statusId}",
        params=given(version=version),
        json=given(name=name, description=description, order=order, type=type),
    )


@tool
def tracker_get_resolutions() -> Any:
    """Get the list of resolutions.

    GET /v3/resolutions
    https://yandex.ru/support/tracker/en/api/admin/get-resolutions.md
    """
    return get_client().request("GET", "/resolutions")


@tool
def tracker_create_resolution(
    key: Annotated[
        NonEmptyStr,
        Field(
            description=(
                "Resolution key (ID). Use Latin characters only, starting with a lowercase letter."
            )
        ),
    ],
    name: Annotated[
        dict,
        Field(
            description=(
                'Resolution name per language: {"ru": "Моя резолюция", "en": "My resolution"}.'
            )
        ),
    ],
) -> Any:
    """Create a new resolution.

    POST /v3/resolutions/
    https://yandex.ru/support/tracker/en/api/admin/create-resolution.md

    Requires Administrator rights in the organization.
    """
    return get_client().request("POST", "/resolutions/", json=given(key=key, name=name))


@tool
def tracker_patch_resolution(
    resolutionId: Annotated[
        NonEmptyStr,
        Field(description="Unique ID of the resolution in Yandex Tracker, or the resolution key."),
    ],
    version: Annotated[
        int | None,
        Field(
            description=(
                "Resolution version. Changes only apply to the current resolution version."
            )
        ),
    ] = None,
    name: Annotated[
        dict | None,
        Field(
            description=(
                'Resolution name per language: {"ru": "Моя резолюция", "en": "My resolution"}.'
            )
        ),
    ] = None,
    description: Annotated[str | None, Field(description="Resolution description.")] = None,
    order: Annotated[
        int | None,
        Field(
            description=(
                "Resolution weight. This parameter affects the order of resolution display "
                "in the interface."
            )
        ),
    ] = None,
) -> Any:
    """Make changes to a resolution.

    PATCH /v3/resolutions/{resolutionId}
    https://yandex.ru/support/tracker/en/api/admin/patch-resolution.md

    Requires Administrator rights. Call tracker_get_resolutions to read the
    current `version`.
    """
    return get_client().request(
        "PATCH",
        f"/resolutions/{resolutionId}",
        params=given(version=version),
        json=given(name=name, description=description, order=order),
    )


@tool
def tracker_get_priorities(
    localized: Annotated[
        bool | None,
        Field(
            description=(
                "Shows if the response contains translations. `true`: the response only "
                "contains priority descriptions in the user's language (default). `false`: "
                "the response contains priority descriptions in all supported languages."
            )
        ),
    ] = None,
) -> Any:
    """Get the list of priorities for an issue.

    GET /v3/priorities
    https://yandex.ru/support/tracker/en/api/admin/get-priorities.md
    """
    return get_client().request("GET", "/priorities", params=given(localized=localized))


@tool
def tracker_create_priority(
    name: Annotated[
        dict,
        Field(
            description=(
                'Priority name per language: {"en": "English name", "ru": "Название на русском"}.'
            )
        ),
    ],
    key: Annotated[NonEmptyStr, Field(description="Priority key.")],
    order: Annotated[
        int,
        Field(
            description=(
                "Priority weight. This parameter affects the order in which the priority "
                "is displayed in the interface."
            )
        ),
    ],
    description: Annotated[str, Field(description="Priority description.")],
) -> Any:
    """Create a new priority for issues.

    POST /v3/priorities/
    https://yandex.ru/support/tracker/en/api/admin/create-priority.md

    Requires Administrator rights in the organization.
    """
    return get_client().request(
        "POST",
        "/priorities/",
        json=given(name=name, key=key, order=order, description=description),
    )


@tool
def tracker_patch_priority(
    priorityId: Annotated[
        NonEmptyStr,
        Field(description="The unique ID of the priority in Tracker, or the priority key."),
    ],
    version: Annotated[
        int | None,
        Field(
            description=(
                "The priority version. Changes are only applied to the current priority version."
            )
        ),
    ] = None,
    name: Annotated[
        dict | None,
        Field(
            description=(
                'Priority name per language: {"en": "English name", "ru": "Название на русском"}.'
            )
        ),
    ] = None,
    description: Annotated[str | None, Field(description="Priority description.")] = None,
) -> Any:
    """Update a priority.

    PATCH /v3/priorities/{priorityId}
    https://yandex.ru/support/tracker/en/api/admin/patch-priority.md

    Requires Administrator rights. This request cannot change a priority icon in
    the Tracker interface. Call tracker_get_priorities to read the current
    `version`.
    """
    return get_client().request(
        "PATCH",
        f"/priorities/{priorityId}",
        params=given(version=version),
        json=given(name=name, description=description),
    )
