"""Users — https://yandex.ru/support/tracker/en/api/users/get-users.md"""

from __future__ import annotations

from typing import Annotated, Any

from pydantic import Field

from ..client import given
from ..server import NonEmptyStr, get_client, tool


@tool
def tracker_get_myself() -> Any:
    """Get the Yandex Tracker user the token belongs to.

    GET /v3/myself
    https://yandex.ru/support/tracker/en/api/users/get-user-info.md
    """
    return get_client().request("GET", "/myself")


@tool
def tracker_get_users(
    perPage: Annotated[
        int | None,
        Field(description="Users per page. The result is paginated; default 50."),
    ] = None,
    page: Annotated[int | None, Field(description="Page number. Default 1.")] = None,
) -> Any:
    """Get the list of Yandex Tracker users in the organization.

    GET /v3/users
    https://yandex.ru/support/tracker/en/api/users/get-users.md

    The endpoint page documents no filters — `perPage` and `page` are the
    organization-wide pagination parameters from common-format.md. To search by
    login, name or email, page through the list and filter the result yourself.
    """
    return get_client().request("GET", "/users", params=given(perPage=perPage, page=page))


@tool
def tracker_get_user(
    userId: Annotated[
        NonEmptyStr,
        Field(description="User login or uid. A numeric login must be passed as login:12345."),
    ],
) -> Any:
    """Get one Yandex Tracker user by login or uid.

    GET /v3/users/{userId}
    https://yandex.ru/support/tracker/en/api/users/get-user.md
    """
    return get_client().request("GET", f"/users/{userId}")


@tool
def tracker_get_users_relative(
    perPage: Annotated[int | None, Field(description="Users per page, 1 to 100.")] = None,
    id: Annotated[int | None, Field(description="User uid to start the page from.")] = None,
    expand: Annotated[
        str | None, Field(description="Additional fields. `groups` adds group membership.")
    ] = None,
) -> Any:
    """List users with relative pagination, sorted by ascending uid.

    GET /v3/users/_relative
    https://yandex.ru/support/tracker/en/api/users/get-users-relative.md

    Returns {users, hasNext}; pass the last uid as `id` to get the next page.
    Unlike tracker_get_users this has no offset limit, so it is the one to use
    when walking the whole organization.
    """
    return get_client().request(
        "GET", "/users/_relative", params=given(perPage=perPage, id=id, expand=expand)
    )
