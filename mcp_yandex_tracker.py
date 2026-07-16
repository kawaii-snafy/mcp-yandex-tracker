"""Yandex Tracker MCP server (single-file stdio server built on FastMCP)."""

from __future__ import annotations

import functools
import json
import os
import threading
from collections.abc import Callable
from dataclasses import dataclass
from typing import Annotated, Any

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ResourceError, ToolError
from pydantic import Field

# Keep this a plain string literal: pyproject reads it statically (setuptools
# dynamic version via AST, no import) as the package version. A computed
# expression would force setuptools to import this module at build time, pulling
# in the runtime deps (mcp, pydantic, …).
__version__ = "0.6.0"


# ===========================================================================
# SDK client layer — everything Yandex Tracker, via the official SDK
# ===========================================================================
class TrackerConfigError(RuntimeError):
    """Raised when the Yandex Tracker client is missing required settings."""


class TrackerApiError(RuntimeError):
    """Raised when Yandex Tracker returns an unsuccessful response."""

    def __init__(self, status: int, message: str, payload: Any | None = None) -> None:
        super().__init__(f"Yandex Tracker API error {status}: {message}")
        self.status = status
        self.payload = payload


@dataclass(frozen=True)
class TrackerConfig:
    token: str
    org_id: str | None = None
    cloud_org_id: str | None = None
    base_url: str = "https://api.tracker.yandex.net"
    auth_scheme: str = "OAuth"
    timeout: float = 30.0

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> "TrackerConfig":
        values = env if env is not None else os.environ
        token = values.get("YANDEX_TRACKER_TOKEN")
        if not token:
            raise TrackerConfigError(
                "Set YANDEX_TRACKER_TOKEN with an OAuth or IAM token for Yandex Tracker."
            )

        org_id = values.get("YANDEX_TRACKER_ORG_ID")
        cloud_org_id = values.get("YANDEX_TRACKER_CLOUD_ORG_ID")
        if not org_id and not cloud_org_id:
            raise TrackerConfigError(
                "Set YANDEX_TRACKER_ORG_ID or YANDEX_TRACKER_CLOUD_ORG_ID."
            )

        return cls(
            token=token,
            org_id=org_id,
            cloud_org_id=cloud_org_id,
            base_url=values.get("YANDEX_TRACKER_BASE_URL", cls.base_url).rstrip("/"),
            auth_scheme=values.get("YANDEX_TRACKER_AUTH_SCHEME", cls.auth_scheme),
            timeout=float(values.get("YANDEX_TRACKER_TIMEOUT", cls.timeout)),
        )


class YandexTrackerClient:
    def __init__(
        self,
        config: TrackerConfig | None = None,
        tracker_client: Any | None = None,
        tracker_client_factory: Any | None = None,
    ) -> None:
        self.config = config
        self._client = tracker_client or self._build_tracker_client(config, tracker_client_factory)

    def get_issue(self, issue_key: str) -> Any:
        return _to_plain(self._call_sdk(lambda client: client.issues[issue_key]))

    def search_issues(
        self,
        query: str | None = None,
        filter: dict[str, Any] | None = None,
        order: str | list[str] | None = None,
        keys: list[str] | None = None,
        per_page: int = 20,
        page: int = 1,
        include_total: bool = False,
        full: bool = False,
    ) -> Any:
        def search(client: Any) -> Any:
            issues = client.issues.find(
                query=query,
                filter=filter,
                order=order,
                keys=keys,
                per_page=per_page,
                page=page,
            )
            # per_page is only the API page size; iterating the SDK result to
            # exhaustion follows every "next" page. Cap at per_page so it is a
            # real limit on returned issues (and HTTP round-trips), not a floor.
            materialized = _take(issues, per_page)
            if not include_total:
                return materialized
            total = client.issues.find(
                query=query,
                filter=filter,
                keys=keys,
                count_only=True,
            )
            return {
                "issues": materialized,
                "total": total,
                "page": page,
                "per_page": per_page,
            }

        result = _to_plain(self._call_sdk(search))
        if full:
            return result
        # Default to a compact projection: full issue objects carry ~29 fields
        # each (description, nested user refs, boards, sprint...), so a page of
        # results can be hundreds of KB. Callers pass full=true for everything.
        if isinstance(result, dict):
            issues = result.get("issues")
            if isinstance(issues, list):
                result["issues"] = [_slim_issue(item) for item in issues]
            return result
        if isinstance(result, list):
            return [_slim_issue(item) for item in result]
        return result

    def create_issue(
        self,
        queue: str,
        summary: str,
        description: str | None = None,
        fields: dict[str, Any] | None = None,
    ) -> Any:
        payload = {"queue": queue, "summary": summary}
        if description is not None:
            payload["description"] = description
        if fields:
            payload.update(fields)
        return _to_plain(self._call_sdk(lambda client: client.issues.create(**payload)))

    def update_issue(self, issue_key: str, fields: dict[str, Any]) -> Any:
        def update(client: Any) -> Any:
            issue = client.issues[issue_key]
            return issue.update(**fields)

        return _to_plain(self._call_sdk(update))

    def add_comment(self, issue_key: str, text: str) -> Any:
        def add(client: Any) -> Any:
            issue = client.issues[issue_key]
            return issue.comments.create(text=text)

        return _to_plain(self._call_sdk(add))

    def list_comments(self, issue_key: str) -> Any:
        def get_all(client: Any) -> Any:
            issue = client.issues[issue_key]
            return list(issue.comments.get_all())

        return _to_plain(self._call_sdk(get_all))

    def delete_comment(self, issue_key: str, comment_id: str) -> Any:
        def delete(client: Any) -> Any:
            comment = client.issues[issue_key].comments[str(comment_id)]
            comment.delete()
            return {"deleted": str(comment_id), "issue": issue_key}

        return _to_plain(self._call_sdk(delete))

    def list_transitions(self, issue_key: str) -> Any:
        def get_all(client: Any) -> Any:
            issue = client.issues[issue_key]
            return list(issue.transitions.get_all())

        return _to_plain(self._call_sdk(get_all))

    def move_issue_status(
        self,
        issue_key: str,
        status: str,
        fields: dict[str, Any] | None = None,
    ) -> Any:
        def move(client: Any) -> Any:
            issue = client.issues[issue_key]
            transitions = list(issue.transitions.get_all())
            transition = self._select_transition(transitions, status)
            return transition.execute(**(fields or {}))

        return _to_plain(self._call_sdk(move))

    def execute_transition(
        self,
        issue_key: str,
        transition_id: str,
        fields: dict[str, Any] | None = None,
    ) -> Any:
        def execute(client: Any) -> Any:
            issue = client.issues[issue_key]
            return issue.transitions[transition_id].execute(**(fields or {}))

        return _to_plain(self._call_sdk(execute))

    def link_issue(
        self,
        issue_key: str,
        relationship: str,
        target_issue: str,
    ) -> Any:
        def link(client: Any) -> Any:
            issue = client.issues[issue_key]
            return issue.links.create(relationship=relationship, issue=target_issue)

        return _to_plain(self._call_sdk(link))

    def list_links(self, issue_key: str) -> Any:
        def get_all(client: Any) -> Any:
            issue = client.issues[issue_key]
            return list(issue.links)

        return _to_plain(self._call_sdk(get_all))

    def unlink_issue(self, issue_key: str, link_id: str) -> Any:
        def unlink(client: Any) -> Any:
            issue = client.issues[issue_key]
            target = str(link_id)
            for link in issue.links:
                if str(_field(link, "id")) == target:
                    client._connection.delete(path=link._path)
                    return {"deleted": target, "issue": issue_key}
            raise ValueError(f"No link {link_id!r} on issue {issue_key}.")

        return _to_plain(self._call_sdk(unlink))

    def list_queues(self) -> Any:
        return _to_plain(self._call_sdk(lambda client: list(client.queues.get_all())))

    def list_users(
        self,
        email: str | None = None,
        group: str | None = None,
        per_page: int | None = None,
    ) -> Any:
        # email (exact match) and group are the server-side filters the Tracker
        # users endpoint supports; the SDK passes them through get_all(**params).
        params: dict[str, Any] = {}
        if email is not None:
            params["email"] = email
        if group is not None:
            params["group"] = group
        if per_page is not None:
            params["perPage"] = per_page
        return _to_plain(
            self._call_sdk(lambda client: list(client.users.get_all(**params)))
        )

    def get_user(self, login_or_uid: str) -> Any:
        return _to_plain(
            self._call_sdk(lambda client: client.users[str(login_or_uid)])
        )

    def get_current_user(self) -> Any:
        return _to_plain(self._call_sdk(lambda client: client.myself))

    def list_statuses(self) -> Any:
        return _to_plain(self._call_sdk(lambda client: list(client.statuses.get_all())))

    def list_issue_types(self) -> Any:
        return _to_plain(self._call_sdk(lambda client: list(client.issue_types.get_all())))

    def list_priorities(self) -> Any:
        return _to_plain(self._call_sdk(lambda client: list(client.priorities.get_all())))

    def list_fields(self) -> Any:
        return _to_plain(self._call_sdk(lambda client: list(client.fields.get_all())))

    def list_link_types(self) -> Any:
        return _to_plain(self._call_sdk(lambda client: list(client.linktypes.get_all())))

    def list_queue_versions(self, queue: str) -> Any:
        return _to_plain(
            self._call_sdk(lambda client: list(client.queues[queue].versions))
        )

    def list_queue_components(self, queue: str) -> Any:
        return _to_plain(
            self._call_sdk(lambda client: list(client.queues[queue].components))
        )

    def list_queue_local_fields(self, queue: str) -> Any:
        return _to_plain(
            self._call_sdk(lambda client: list(client.queues[queue].local_fields))
        )

    def list_queue_tags(self, queue: str) -> Any:
        # The SDK has no wrapper for queue tags, so hit the endpoint through the
        # raw connection the same way the SDK's own queue sub-resources do.
        def get_tags(client: Any) -> Any:
            queue_obj = client.queues[queue]
            return client._connection.get(path=queue_obj._path + "/tags")

        return _to_plain(self._call_sdk(get_tags))

    def get_changelog(
        self,
        issue_key: str,
        field: str | None = None,
        change_type: str | None = None,
        per_page: int | None = None,
    ) -> Any:
        # field/type filters and perPage are native changelog get-params; the SDK
        # iterator handles cursor pagination when the result is materialized.
        params: dict[str, Any] = {}
        if field is not None:
            params["field"] = field
        if change_type is not None:
            params["type"] = change_type
        if per_page is not None:
            params["perPage"] = per_page

        def changelog(client: Any) -> Any:
            return list(client.issues[issue_key].changelog.get_all(**params))

        return _to_plain(self._call_sdk(changelog))

    def list_worklog(self, issue_key: str) -> Any:
        return _to_plain(
            self._call_sdk(lambda client: list(client.issues[issue_key].worklog))
        )

    def add_worklog(
        self,
        issue_key: str,
        duration: str,
        comment: str | None = None,
        start: str | None = None,
    ) -> Any:
        def add(client: Any) -> Any:
            issue = client.issues[issue_key]
            payload: dict[str, Any] = {"duration": duration}
            if comment is not None:
                payload["comment"] = comment
            if start is not None:
                payload["start"] = start
            return issue.worklog.create(**payload)

        return _to_plain(self._call_sdk(add))

    def list_checklist(self, issue_key: str) -> Any:
        return _to_plain(
            self._call_sdk(lambda client: list(client.issues[issue_key].checklist_items))
        )

    def add_checklist_item(self, issue_key: str, text: str, checked: bool = False) -> Any:
        def add(client: Any) -> Any:
            issue = client.issues[issue_key]
            return issue.checklist_items.create(text=text, checked=checked)

        return _to_plain(self._call_sdk(add))

    def list_attachments(self, issue_key: str) -> Any:
        return _to_plain(
            self._call_sdk(lambda client: list(client.issues[issue_key].attachments))
        )

    def download_attachment(
        self,
        issue_key: str,
        attachment_id: str,
        dest_dir: str,
        filename: str | None = None,
    ) -> Any:
        def download(client: Any) -> Any:
            attachments = client.issues[issue_key].attachments
            attachment = attachments[attachment_id]
            raw_name = filename or _field(attachment, "name") or str(attachment_id)
            # basename guards against path traversal via the attachment name.
            name = os.path.basename(str(raw_name)) or str(attachment_id)
            os.makedirs(dest_dir, exist_ok=True)
            dest_path = os.path.join(dest_dir, name)
            with open(dest_path, "wb") as handle:
                for chunk in attachments.read(attachment):
                    handle.write(chunk)
            return {
                "path": dest_path,
                "name": name,
                "size": _field(attachment, "size"),
            }

        return _to_plain(self._call_sdk(download))

    def upload_attachment(
        self,
        issue_key: str,
        file_path: str,
        filename: str | None = None,
    ) -> Any:
        # Validate the local file up front so a missing/unreadable path is a clean
        # tool error rather than being mislabeled as a transport failure.
        if not os.path.isfile(file_path):
            raise ValueError(f"File not found: {file_path}")
        if not os.access(file_path, os.R_OK):
            raise ValueError(f"File is not readable: {file_path}")

        def upload(client: Any) -> Any:
            attachments = client.issues[issue_key].attachments
            params = {"filename": filename} if filename else None
            return attachments.create(file_path, params=params)

        return _to_plain(self._call_sdk(upload))

    def delete_attachment(self, issue_key: str, attachment_id: str) -> Any:
        def delete(client: Any) -> Any:
            attachment = client.issues[issue_key].attachments[str(attachment_id)]
            attachment.delete()
            return {"deleted": str(attachment_id), "issue": issue_key}

        return _to_plain(self._call_sdk(delete))

    @staticmethod
    def _build_tracker_client(
        config: TrackerConfig | None,
        tracker_client_factory: Any | None,
    ) -> Any:
        config = config or TrackerConfig.from_env()
        factory = tracker_client_factory or _load_tracker_client_factory()
        kwargs = _tracker_client_kwargs(config)
        return factory(**kwargs)

    def _call_sdk(self, action: Any) -> Any:
        try:
            return action(self._client)
        except ValueError:
            raise
        except Exception as exc:
            module = exc.__class__.__module__
            if module.startswith("yandex_tracker_client"):
                status = getattr(exc, "status_code", getattr(exc, "status", 0)) or 0
                payload = getattr(exc, "payload", None)
                raise TrackerApiError(status, str(exc), payload) from exc
            # Direct transport failures (requests/urllib3/socket) not wrapped by
            # the SDK: surface them as Tracker API errors so callers get a clean
            # tool error instead of an opaque internal error.
            if isinstance(exc, OSError) or module.split(".", 1)[0] in {
                "requests",
                "urllib3",
                "http",
                "socket",
                "ssl",
            }:
                raise TrackerApiError(0, f"Failed to reach Yandex Tracker: {exc}") from exc
            raise

    @staticmethod
    def _select_transition(transitions: list[Any], status: str) -> Any:
        target = _normalize_transition_value(status)
        matches = []
        seen_ids = set()
        for transition in transitions:
            transition_id = _field(transition, "id")
            if transition_id is None:
                continue
            if _transition_matches(transition, target):
                transition_id = str(transition_id)
                if transition_id not in seen_ids:
                    seen_ids.add(transition_id)
                    matches.append(transition)

        if not matches:
            available = _format_available_transitions(transitions)
            raise ValueError(
                f"No available transition matches status {status!r}."
                f" Available transitions: {available}"
            )
        if len(matches) > 1:
            ids = ", ".join(str(_field(match, "id")) for match in matches)
            raise ValueError(f"Status {status!r} matches multiple transitions: {ids}.")
        return matches[0]


def _load_tracker_client_factory() -> Any:
    try:
        from yandex_tracker_client import TrackerClient
    except ImportError as exc:
        raise TrackerConfigError(
            "Install yandex_tracker_client to use the Yandex Tracker MCP server."
        ) from exc
    return TrackerClient


def _tracker_client_kwargs(config: TrackerConfig) -> dict[str, Any]:
    base_url, api_version = _split_base_url(config.base_url)
    kwargs: dict[str, Any] = {
        "org_id": config.org_id,
        "cloud_org_id": config.cloud_org_id,
        "base_url": base_url,
        "api_version": api_version,
        "timeout": config.timeout,
    }
    if config.auth_scheme.casefold() == "bearer":
        kwargs["iam_token"] = config.token
    else:
        kwargs["token"] = config.token
    return {key: value for key, value in kwargs.items() if value is not None}


def _split_base_url(base_url: str) -> tuple[str, str]:
    for version in ("v2", "v3"):
        suffix = f"/{version}"
        if base_url.endswith(suffix):
            return base_url[: -len(suffix)], version
    return base_url, "v2"


def _transition_matches(transition: Any, target: str) -> bool:
    candidates = [_field(transition, "id"), _field(transition, "display")]
    to_status = _field(transition, "to")
    candidates.extend([_field(to_status, "id"), _field(to_status, "key"), _field(to_status, "display")])
    return any(
        _normalize_transition_value(candidate) == target
        for candidate in candidates
        if candidate is not None
    )


def _normalize_transition_value(value: Any) -> str:
    return str(value).strip().casefold()


def _format_available_transitions(transitions: list[Any]) -> str:
    values = []
    for transition in transitions:
        transition_id = _field(transition, "id")
        to_status = _field(transition, "to")
        status = _field(to_status, "key") or _field(to_status, "display") or _field(to_status, "id")
        values.append(f"{transition_id}->{status}" if status else str(transition_id))
    return ", ".join(values) if values else "<none>"


def _field(value: Any, name: str) -> Any:
    if value is None:
        return None
    if isinstance(value, dict):
        return value.get(name)
    try:
        return value[name]
    except (KeyError, TypeError):
        return getattr(value, name, None)


def _take(iterable: Any, limit: int) -> list[Any]:
    # Stop iterating a (lazily cursor-paginated) SDK result once `limit` items
    # are collected, so later pages are never fetched.
    items: list[Any] = []
    if limit <= 0:
        return items
    for item in iterable:
        items.append(item)
        if len(items) >= limit:
            break
    return items


_SLIM_REF_KEYS = ("key", "id", "display", "name")
_SLIM_ISSUE_FIELDS = (
    "key",
    "summary",
    "status",
    "type",
    "priority",
    "assignee",
    "queue",
    "parent",
    "epic",
    "sprint",
    "tags",
    "updatedAt",
    "createdAt",
)


def _slim_ref(value: Any) -> Any:
    # Collapse a nested Tracker reference (user, status, queue...) to just its
    # identifying keys, dropping self URLs and other bulk.
    if isinstance(value, dict):
        return {key: value[key] for key in _SLIM_REF_KEYS if key in value}
    if isinstance(value, list):
        return [_slim_ref(item) for item in value]
    return value


def _slim_issue(issue: Any) -> Any:
    if not isinstance(issue, dict):
        return issue
    slim: dict[str, Any] = {}
    for field in _SLIM_ISSUE_FIELDS:
        if field in issue:
            slim[field] = _slim_ref(issue[field])
    return slim


# Keys stripped from every serialized object: pure transport/metadata noise the
# model never needs. `self` is the resource URL present on every Tracker object
# and nested ref (~55 chars each); `cloudUid`/`passportUid` are internal Yandex
# user identifiers duplicated alongside the human-readable `id`/`display`.
# Dropping them recursively cuts a typical issue payload by roughly half with no
# information loss.
_NOISE_KEYS = frozenset({"self", "cloudUid", "passportUid"})


def _to_plain(value: Any) -> Any:
    if hasattr(value, "as_dict"):
        return _to_plain(value.as_dict())
    if isinstance(value, dict):
        return {
            key: _to_plain(item)
            for key, item in value.items()
            if key not in _NOISE_KEYS
        }
    if isinstance(value, (list, tuple, set)):
        return [_to_plain(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


# ===========================================================================
# MCP server layer — FastMCP tools over the client above
# ===========================================================================
mcp = FastMCP("mcp-yandex-tracker")
# FastMCP doesn't accept a version, so serverInfo would otherwise advertise the
# mcp package version instead of ours. Set it on the low-level server. This
# reaches a private SDK attribute, so a future mcp upgrade could change its
# shape — test_initialize_advertises_our_version guards against that.
mcp._mcp_server.version = __version__


# One client per process, built lazily. The Yandex Tracker SDK opens a
# requests.Session (connection pool) on construction; reusing a single instance
# keeps HTTP keep-alive across tool calls instead of rebuilding it every time.
# _client_factory stays swappable so tests can inject a fake client.
_client: YandexTrackerClient | None = None
_client_factory: Callable[[], YandexTrackerClient] = YandexTrackerClient
_client_lock = threading.Lock()


def get_client() -> YandexTrackerClient:
    global _client
    if _client is None:
        with _client_lock:
            if _client is None:
                _client = _client_factory()
    return _client


def _dump(payload: Any) -> str:
    # Compact separators: pretty-printing adds whitespace tokens to every line
    # of every response for no benefit — the model reads compact JSON just as
    # well.
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


# Domain exceptions a handler may raise; both surfaces remap them to a clean
# MCP error instead of leaking an internal error.
_DOMAIN_ERRORS = (TrackerApiError, TrackerConfigError, ValueError)


def _json_safe(fn: Callable[..., Any], error_cls: type[Exception]) -> Callable[..., Any]:
    """Serialize a handler's return value to compact JSON and map domain errors.

    functools.wraps preserves the handler signature so FastMCP still derives the
    input schema from its typed parameters.
    """

    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> str:
        try:
            return _dump(fn(*args, **kwargs))
        except _DOMAIN_ERRORS as exc:
            raise error_cls(str(exc)) from exc

    return wrapper


def tool(fn: Callable[..., Any]) -> Callable[..., Any]:
    """Register a Yandex Tracker tool.

    The handler's raw return value becomes a single compact JSON text block
    (structured_output=False keeps FastMCP from also emitting a duplicating
    structuredContent block and an output schema), and domain errors surface as
    clean isError tool results instead of internal errors.
    """
    return mcp.tool(structured_output=False)(_json_safe(fn, ToolError))


NonEmptyStr = Annotated[str, Field(min_length=1)]


# --- Issues -----------------------------------------------------------------
@tool
def tracker_get_issue(issue_key: NonEmptyStr) -> Any:
    """Get a Yandex Tracker issue by key."""
    return get_client().get_issue(issue_key)


@tool
def tracker_search_issues(
    query: str | None = None,
    # `filter` shadows the builtin on purpose: the arg name mirrors the Tracker
    # API field, and the body only forwards it.
    filter: dict | None = None,
    order: str | None = None,
    keys: list[str] | None = None,
    per_page: Annotated[
        int,
        Field(ge=1, le=100, description="Max issues to return (hard cap, not just page size). Default 20."),
    ] = 20,
    page: Annotated[int, Field(ge=1)] = 1,
    include_total: Annotated[
        bool,
        Field(description="Also return the total match count (extra request). Response becomes {issues, total, page, per_page}."),
    ] = False,
    full: Annotated[
        bool,
        Field(description="Return complete issue objects instead of the compact projection. Off by default to keep responses small."),
    ] = False,
) -> Any:
    """Search Yandex Tracker issues using query language, filter fields, or keys.

    Returns a compact projection of each issue (key, summary, status, type,
    priority, assignee, queue, parent, epic, sprint, tags, timestamps) — pass
    full=true for the complete issue objects. per_page is a hard cap on how many
    issues are returned.
    """
    return get_client().search_issues(
        query=query,
        filter=filter,
        order=order,
        keys=keys,
        per_page=per_page,
        page=page,
        include_total=include_total,
        full=full,
    )


@tool
def tracker_create_issue(
    queue: NonEmptyStr,
    summary: NonEmptyStr,
    description: str | None = None,
    fields: Annotated[dict | None, Field(description="Additional Tracker issue fields.")] = None,
) -> Any:
    """Create a Yandex Tracker issue."""
    return get_client().create_issue(
        queue=queue, summary=summary, description=description, fields=fields
    )


@tool
def tracker_update_issue(
    issue_key: NonEmptyStr,
    fields: Annotated[dict, Field(description="Fields to patch (raw Tracker API field names and values).")],
) -> Any:
    """Update fields on a Yandex Tracker issue.

    fields is a raw Tracker PATCH body, so it also covers: tags via
    {"tags": {"add": [...], "remove": [...]}} (or a full array to replace);
    components the same way (id or name); parent reassignment via
    {"parent": {"key": "TEST-2"}}. Epic association is a link, not a field — use
    tracker_link_issues for that.
    """
    return get_client().update_issue(issue_key, fields)


# --- Comments ---------------------------------------------------------------
@tool
def tracker_add_comment(issue_key: NonEmptyStr, text: NonEmptyStr) -> Any:
    """Add a comment to a Yandex Tracker issue."""
    return get_client().add_comment(issue_key, text)


@tool
def tracker_list_comments(issue_key: NonEmptyStr) -> Any:
    """List comments for a Yandex Tracker issue."""
    return get_client().list_comments(issue_key)


@tool
def tracker_delete_comment(
    issue_key: NonEmptyStr,
    comment_id: Annotated[str, Field(min_length=1, description="Comment id from tracker_list_comments.")],
) -> Any:
    """Delete a comment from a Yandex Tracker issue by its comment id (get ids from tracker_list_comments)."""
    return get_client().delete_comment(issue_key, comment_id)


# --- Transitions ------------------------------------------------------------
@tool
def tracker_list_transitions(issue_key: NonEmptyStr) -> Any:
    """List available workflow transitions for a Yandex Tracker issue."""
    return get_client().list_transitions(issue_key)


@tool
def tracker_move_issue_status(
    issue_key: NonEmptyStr,
    status: Annotated[str, Field(min_length=1, description="Transition id/display or destination status id/key/display.")],
    fields: Annotated[dict | None, Field(description="Optional fields for the transition screen, such as comment.")] = None,
) -> Any:
    """Move a Yandex Tracker issue to a status by matching an available transition."""
    return get_client().move_issue_status(issue_key, status, fields)


@tool
def tracker_execute_transition(
    issue_key: NonEmptyStr,
    transition_id: NonEmptyStr,
    fields: dict | None = None,
) -> Any:
    """Execute a Yandex Tracker workflow transition."""
    return get_client().execute_transition(issue_key, transition_id, fields)


# --- Links ------------------------------------------------------------------
@tool
def tracker_link_issues(
    issue_key: Annotated[str, Field(min_length=1, description="Source issue, e.g. TEST-1.")],
    relationship: Annotated[
        str,
        Field(description="Link type, e.g. relates, depends on, is dependent by, is subtask for, is parent task for, duplicates."),
    ],
    target_issue: Annotated[str, Field(min_length=1, description="Issue to link to, e.g. TEST-2.")],
) -> Any:
    """Create a link between two Yandex Tracker issues.

    Use tracker_list_link_types to discover valid relationship values.
    """
    return get_client().link_issue(issue_key, relationship, target_issue)


@tool
def tracker_list_links(issue_key: NonEmptyStr) -> Any:
    """List links of a Yandex Tracker issue (each carries an id for tracker_unlink_issues)."""
    return get_client().list_links(issue_key)


@tool
def tracker_unlink_issues(
    issue_key: NonEmptyStr,
    link_id: Annotated[str, Field(min_length=1, description="Link id from tracker_list_links.")],
) -> Any:
    """Remove a link from a Yandex Tracker issue by its link id (get ids from tracker_list_links)."""
    return get_client().unlink_issue(issue_key, link_id)


# --- Queues & users ---------------------------------------------------------
@tool
def tracker_list_queues() -> Any:
    """List Yandex Tracker queues."""
    return get_client().list_queues()


@tool
def tracker_list_users(
    email: Annotated[str | None, Field(description="Filter by exact email match.")] = None,
    group: Annotated[str | None, Field(description="Filter by group id.")] = None,
    per_page: Annotated[int | None, Field(ge=1, le=100)] = None,
) -> Any:
    """List Yandex Tracker users (for assignee, followers, and other user fields).

    Supports server-side filters: email (exact match) and group. Note: Tracker
    has no server-side search by login or name — fetch and filter client-side
    for that.
    """
    return get_client().list_users(email=email, group=group, per_page=per_page)


@tool
def tracker_get_user(
    login_or_uid: Annotated[str, Field(min_length=1, description="User login (e.g. jsmith) or numeric uid.")],
) -> Any:
    """Get a single Yandex Tracker user by login or uid."""
    return get_client().get_user(login_or_uid)


@tool
def tracker_get_current_user() -> Any:
    """Get the currently authenticated Yandex Tracker user (the token owner)."""
    return get_client().get_current_user()


# --- Reference dictionaries -------------------------------------------------
@tool
def tracker_list_statuses() -> Any:
    """List the global Yandex Tracker status dictionary."""
    return get_client().list_statuses()


@tool
def tracker_list_issue_types() -> Any:
    """List the global Yandex Tracker issue-type dictionary."""
    return get_client().list_issue_types()


@tool
def tracker_list_priorities() -> Any:
    """List the global Yandex Tracker priority dictionary."""
    return get_client().list_priorities()


@tool
def tracker_list_fields() -> Any:
    """List Yandex Tracker fields, including custom fields."""
    return get_client().list_fields()


@tool
def tracker_list_link_types() -> Any:
    """List Yandex Tracker link types (valid relationship values for tracker_link_issues)."""
    return get_client().list_link_types()


@tool
def tracker_list_queue_versions(
    queue: Annotated[str, Field(min_length=1, description="Queue key, e.g. TEST.")],
) -> Any:
    """List versions defined in a specific Yandex Tracker queue."""
    return get_client().list_queue_versions(queue)


@tool
def tracker_list_queue_components(
    queue: Annotated[str, Field(min_length=1, description="Queue key, e.g. TEST.")],
) -> Any:
    """List components defined in a specific Yandex Tracker queue."""
    return get_client().list_queue_components(queue)


@tool
def tracker_list_queue_local_fields(
    queue: Annotated[str, Field(min_length=1, description="Queue key, e.g. TEST.")],
) -> Any:
    """List local (queue-specific custom) fields of a Yandex Tracker queue.

    Unlike tracker_list_fields, these are scoped to the queue.
    """
    return get_client().list_queue_local_fields(queue)


@tool
def tracker_list_queue_tags(
    queue: Annotated[str, Field(min_length=1, description="Queue key, e.g. TEST.")],
) -> Any:
    """List tags defined in a specific Yandex Tracker queue."""
    return get_client().list_queue_tags(queue)


# --- Activity ---------------------------------------------------------------
@tool
def tracker_get_changelog(
    issue_key: NonEmptyStr,
    field: Annotated[str | None, Field(description="Filter to changes of a single field id, e.g. status.")] = None,
    # `type` shadows the builtin on purpose: it mirrors the Tracker changelog
    # get-param name; the body forwards it as change_type.
    type: Annotated[str | None, Field(description="Filter by change type, e.g. IssueWorkflow, IssueUpdated.")] = None,
    per_page: Annotated[int | None, Field(ge=1, le=100)] = None,
) -> Any:
    """Get the change history of a Yandex Tracker issue.

    Optionally filter by field and change type.
    """
    return get_client().get_changelog(issue_key, field=field, change_type=type, per_page=per_page)


@tool
def tracker_list_worklog(issue_key: NonEmptyStr) -> Any:
    """List worklog (time-tracking) records of a Yandex Tracker issue."""
    return get_client().list_worklog(issue_key)


@tool
def tracker_add_worklog(
    issue_key: NonEmptyStr,
    duration: Annotated[str, Field(min_length=1, description="ISO 8601 duration, e.g. PT1H30M for 1h30m.")],
    comment: str | None = None,
    start: Annotated[str | None, Field(description="ISO 8601 start datetime, e.g. 2026-07-03T10:00:00.000+0000.")] = None,
) -> Any:
    """Add a worklog (time spent) record to a Yandex Tracker issue."""
    return get_client().add_worklog(issue_key, duration, comment=comment, start=start)


# --- Checklist --------------------------------------------------------------
@tool
def tracker_list_checklist(issue_key: NonEmptyStr) -> Any:
    """List checklist items of a Yandex Tracker issue."""
    return get_client().list_checklist(issue_key)


@tool
def tracker_add_checklist_item(
    issue_key: NonEmptyStr,
    text: NonEmptyStr,
    checked: Annotated[bool, Field(description="Initial checked state.")] = False,
) -> Any:
    """Add a checklist item to a Yandex Tracker issue."""
    return get_client().add_checklist_item(issue_key, text, checked=checked)


# --- Attachments ------------------------------------------------------------
@tool
def tracker_list_attachments(issue_key: NonEmptyStr) -> Any:
    """List attachment metadata (id, name, size, url) of a Yandex Tracker issue.

    Use tracker_download_attachment to fetch the bytes.
    """
    return get_client().list_attachments(issue_key)


@tool
def tracker_download_attachment(
    issue_key: NonEmptyStr,
    attachment_id: Annotated[str, Field(min_length=1, description="Attachment id from tracker_list_attachments.")],
    dest_dir: Annotated[str, Field(min_length=1, description="Absolute directory path to save the file into.")],
    filename: Annotated[str | None, Field(description="Optional override for the saved file name.")] = None,
) -> Any:
    """Download an issue attachment to a local directory and return the saved file path.

    Tracker attachment URLs need authentication, so this proxies the download
    through the server. Ask the user where to save before calling.
    """
    return get_client().download_attachment(issue_key, attachment_id, dest_dir, filename=filename)


@tool
def tracker_upload_attachment(
    issue_key: NonEmptyStr,
    file_path: Annotated[str, Field(min_length=1, description="Absolute path to the local file to upload.")],
    filename: Annotated[str | None, Field(description="Optional name to store the attachment under in Tracker.")] = None,
) -> Any:
    """Upload a local file as an attachment on a Yandex Tracker issue."""
    return get_client().upload_attachment(issue_key, file_path, filename=filename)


@tool
def tracker_delete_attachment(
    issue_key: NonEmptyStr,
    attachment_id: Annotated[str, Field(min_length=1, description="Attachment id from tracker_list_attachments.")],
) -> Any:
    """Delete an attachment from a Yandex Tracker issue by its attachment id (get ids from tracker_list_attachments)."""
    return get_client().delete_attachment(issue_key, attachment_id)


# ===========================================================================
# Resources — read-only context the user can @-mention in Claude Code
# ===========================================================================
# Resources are a *user*-facing surface (pulled into a prompt via @-mention and
# attached as context), not something the agent reads autonomously mid-task —
# the tools above stay the agent's path to the same data. These add a natural
# way to drop an issue snapshot or a reference dictionary into the conversation.
def resource(uri: str, **kwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Register a read-only Tracker resource.

    The body's return value becomes a compact JSON resource. Note: FastMCP's
    resource read path already wraps any handler error into a `ResourceError`
    itself, so passing `ResourceError` to the shared `_json_safe` here is only
    for parity with `tool` — the final error type comes from the SDK regardless.
    The wrapper's real job for resources is the compact serialization.
    """

    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        return mcp.resource(uri, **kwargs)(_json_safe(fn, ResourceError))

    return decorator


@resource("tracker://issue/{key}", mime_type="application/json")
def issue_resource(key: NonEmptyStr) -> Any:
    """A single Yandex Tracker issue by key (e.g. tracker://issue/TEST-123)."""
    return get_client().get_issue(key)


@resource("tracker://queues", mime_type="application/json")
def queues_resource() -> Any:
    """The Yandex Tracker queue list."""
    return get_client().list_queues()


@resource("tracker://statuses", mime_type="application/json")
def statuses_resource() -> Any:
    """The global Yandex Tracker status dictionary."""
    return get_client().list_statuses()


@resource("tracker://priorities", mime_type="application/json")
def priorities_resource() -> Any:
    """The global Yandex Tracker priority dictionary."""
    return get_client().list_priorities()


@resource("tracker://issue-types", mime_type="application/json")
def issue_types_resource() -> Any:
    """The global Yandex Tracker issue-type dictionary."""
    return get_client().list_issue_types()


@resource("tracker://fields", mime_type="application/json")
def fields_resource() -> Any:
    """Yandex Tracker fields, including custom fields."""
    return get_client().list_fields()


@resource("tracker://link-types", mime_type="application/json")
def link_types_resource() -> Any:
    """Yandex Tracker link types (valid relationship values for links)."""
    return get_client().list_link_types()


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
