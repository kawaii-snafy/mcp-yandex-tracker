"""Read-only context the user can @-mention in a host.

Resources are a *user*-facing surface (pulled into a prompt via @-mention and
attached as context), not something the agent reads autonomously mid-task — the
tools remain the agent's path to the same data. These add a natural way to drop
an issue snapshot or a reference dictionary into the conversation.
"""

from __future__ import annotations

from typing import Any

from .server import NonEmptyStr, get_client, resource


@resource("tracker://issue/{key}", mime_type="application/json")
def issue_resource(key: NonEmptyStr) -> Any:
    """A single Yandex Tracker issue by key (e.g. tracker://issue/TEST-123)."""
    return get_client().request("GET", f"/issues/{key}")


@resource("tracker://queues", mime_type="application/json")
def queues_resource() -> Any:
    """The Yandex Tracker queue list."""
    return get_client().request("GET", "/queues/")


@resource("tracker://statuses", mime_type="application/json")
def statuses_resource() -> Any:
    """The global Yandex Tracker status dictionary."""
    return get_client().request("GET", "/statuses")


@resource("tracker://priorities", mime_type="application/json")
def priorities_resource() -> Any:
    """The global Yandex Tracker priority dictionary."""
    return get_client().request("GET", "/priorities")


@resource("tracker://issue-types", mime_type="application/json")
def issue_types_resource() -> Any:
    """The global Yandex Tracker issue-type dictionary."""
    return get_client().request("GET", "/issuetypes")


@resource("tracker://fields", mime_type="application/json")
def fields_resource() -> Any:
    """Yandex Tracker fields, including custom fields."""
    return get_client().request("GET", "/fields")
