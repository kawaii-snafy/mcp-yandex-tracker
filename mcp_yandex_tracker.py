"""Yandex Tracker MCP server (single-file stdio server built on MCPServer)."""

from __future__ import annotations

import functools
import json
import os
import threading
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Annotated, Any

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ResourceError, ToolError
from mcp.types import ToolAnnotations
from pydantic import Field

# Keep this a plain string literal: pyproject reads it statically (setuptools
# dynamic version via AST, no import) as the package version. A computed
# expression would force setuptools to import this module at build time, pulling
# in the runtime deps (mcp, pydantic, …).
__version__ = "0.8.0"


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


# Hard caps on how many items a list call returns. Every Tracker collection is
# cursor-paginated and its iterator follows each "next" link to exhaustion, so
# materializing one with list() is unbounded by construction: a call to
# list_comments on a busy issue, or list_users on a large org, walks every page.
# Each call site goes through _take instead, which stops at the cap and never
# fetches the page after it.
_DEFAULT_LIMIT = 50
# Reference dictionaries are the exception: silently truncating one would make
# the agent conclude a status or field does not exist. This is a runaway guard,
# not a page size — high enough that a real organization never reaches it.
_DICTIONARY_LIMIT = 500


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
        full: bool = False,
    ) -> Any:
        payload = {"queue": queue, "summary": summary}
        if description is not None:
            payload["description"] = description
        if fields:
            payload.update(fields)
        created = _to_plain(self._call_sdk(lambda client: client.issues.create(**payload)))
        if full:
            return created
        # Echo the extra fields (custom values the server may have normalized),
        # not summary/description — the caller just sent those verbatim.
        return _issue_receipt(created, fields or ())

    def update_issue(
        self,
        issue_key: str,
        fields: dict[str, Any],
        full: bool = False,
    ) -> Any:
        def update(client: Any) -> Any:
            issue = client.issues[issue_key]
            return issue.update(**fields)

        updated = _to_plain(self._call_sdk(update))
        return updated if full else _issue_receipt(updated, fields)

    def add_comment(self, issue_key: str, text: str) -> Any:
        def add(client: Any) -> Any:
            issue = client.issues[issue_key]
            return issue.comments.create(text=text)

        # Write receipt only: the response echoes the text the caller just sent
        # plus a full user object, and neither tells the agent anything new.
        return _project(_to_plain(self._call_sdk(add)), _COMMENT_RECEIPT_FIELDS)

    def list_comments(self, issue_key: str, limit: int = _DEFAULT_LIMIT) -> Any:
        def get_all(client: Any) -> Any:
            issue = client.issues[issue_key]
            return _take(issue.comments.get_all(), limit)

        return _to_plain(self._call_sdk(get_all))

    def update_comment(self, issue_key: str, comment_id: str, text: str) -> Any:
        def update(client: Any) -> Any:
            comment = client.issues[issue_key].comments[str(comment_id)]
            return comment.update(text=text)

        # Receipt only: the caller sent the text, so what is worth returning is
        # that the edit landed and who Tracker recorded for it.
        return _project(
            _to_plain(self._call_sdk(update)), _COMMENT_EDIT_RECEIPT_FIELDS
        )

    def delete_comment(self, issue_key: str, comment_id: str) -> Any:
        def delete(client: Any) -> Any:
            comment = client.issues[issue_key].comments[str(comment_id)]
            comment.delete()
            return {"deleted": str(comment_id), "issue": issue_key}

        return _to_plain(self._call_sdk(delete))

    def list_transitions(self, issue_key: str) -> Any:
        def get_all(client: Any) -> Any:
            issue = client.issues[issue_key]
            return _take(issue.transitions.get_all(), _DICTIONARY_LIMIT)

        return _to_plain(self._call_sdk(get_all))

    def move_issue_status(
        self,
        issue_key: str,
        status: str,
        fields: dict[str, Any] | None = None,
    ) -> Any:
        def move(client: Any) -> Any:
            issue = client.issues[issue_key]
            transitions = _take(issue.transitions.get_all(), _DICTIONARY_LIMIT)
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

        return _slim_link(_to_plain(self._call_sdk(link)))

    def list_links(
        self,
        issue_key: str,
        limit: int = _DEFAULT_LIMIT,
        full: bool = False,
    ) -> Any:
        def get_all(client: Any) -> Any:
            issue = client.issues[issue_key]
            return _take(issue.links, limit)

        links = _to_plain(self._call_sdk(get_all))
        return links if full else _slim_link(links)

    def unlink_issue(self, issue_key: str, link_id: str) -> Any:
        def unlink(client: Any) -> Any:
            issue = client.issues[issue_key]
            target = str(link_id)
            # A lookup, not a listing — but issue.links is still a paginated
            # collection, so bound the scan like every other call site.
            for link in _take(issue.links, _DICTIONARY_LIMIT):
                if str(_field(link, "id")) == target:
                    client._connection.delete(path=link._path)
                    return {"deleted": target, "issue": issue_key}
            raise ValueError(f"No link {link_id!r} on issue {issue_key}.")

        return _to_plain(self._call_sdk(unlink))

    def list_queues(self, limit: int = _DEFAULT_LIMIT) -> Any:
        return _to_plain(
            self._call_sdk(lambda client: _take(client.queues.get_all(), limit))
        )

    def list_users(
        self,
        email: str | None = None,
        group: str | None = None,
        limit: int = _DEFAULT_LIMIT,
    ) -> Any:
        # email (exact match) and group are the server-side filters the Tracker
        # users endpoint supports; the SDK passes them through get_all(**params).
        # perPage is only the page size — on its own the iterator still walks the
        # whole directory — so _take is what turns `limit` into a real cap.
        params: dict[str, Any] = {"perPage": min(limit, 100)}
        if email is not None:
            params["email"] = email
        if group is not None:
            params["group"] = group
        return _to_plain(
            self._call_sdk(lambda client: _take(client.users.get_all(**params), limit))
        )

    def get_user(self, login_or_uid: str) -> Any:
        return _to_plain(
            self._call_sdk(lambda client: client.users[str(login_or_uid)])
        )

    def get_current_user(self) -> Any:
        return _to_plain(self._call_sdk(lambda client: client.myself))

    def list_statuses(self) -> Any:
        return _to_plain(
            self._call_sdk(lambda client: _take(client.statuses.get_all(), _DICTIONARY_LIMIT))
        )

    def list_issue_types(self) -> Any:
        return _to_plain(
            self._call_sdk(lambda client: _take(client.issue_types.get_all(), _DICTIONARY_LIMIT))
        )

    def list_priorities(self) -> Any:
        return _to_plain(
            self._call_sdk(lambda client: _take(client.priorities.get_all(), _DICTIONARY_LIMIT))
        )

    def list_fields(self) -> Any:
        return _to_plain(
            self._call_sdk(lambda client: _take(client.fields.get_all(), _DICTIONARY_LIMIT))
        )

    def list_link_types(self) -> Any:
        return _to_plain(
            self._call_sdk(lambda client: _take(client.linktypes.get_all(), _DICTIONARY_LIMIT))
        )

    def list_queue_versions(self, queue: str) -> Any:
        return _to_plain(
            self._call_sdk(
                lambda client: _take(client.queues[queue].versions, _DICTIONARY_LIMIT)
            )
        )

    def list_queue_components(self, queue: str) -> Any:
        return _to_plain(
            self._call_sdk(
                lambda client: _take(client.queues[queue].components, _DICTIONARY_LIMIT)
            )
        )

    def list_queue_local_fields(self, queue: str) -> Any:
        return _to_plain(
            self._call_sdk(
                lambda client: _take(client.queues[queue].local_fields, _DICTIONARY_LIMIT)
            )
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
        limit: int = _DEFAULT_LIMIT,
    ) -> Any:
        # field/type are native changelog get-params. perPage is only the page
        # size — the SDK iterator follows every cursor past it — so _take is what
        # bounds the result.
        params: dict[str, Any] = {"perPage": min(limit, 100)}
        if field is not None:
            params["field"] = field
        if change_type is not None:
            params["type"] = change_type

        def changelog(client: Any) -> Any:
            return _take(client.issues[issue_key].changelog.get_all(**params), limit)

        return _to_plain(self._call_sdk(changelog))

    def list_worklog(self, issue_key: str, limit: int = _DEFAULT_LIMIT) -> Any:
        return _to_plain(
            self._call_sdk(lambda client: _take(client.issues[issue_key].worklog, limit))
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

        # Write receipt only: the full record embeds the whole parent issue.
        return _project(_to_plain(self._call_sdk(add)), _WORKLOG_RECEIPT_FIELDS)

    def list_checklist(self, issue_key: str, limit: int = _DEFAULT_LIMIT) -> Any:
        return _to_plain(
            self._call_sdk(
                lambda client: _take(client.issues[issue_key].checklist_items, limit)
            )
        )

    def add_checklist_item(self, issue_key: str, text: str, checked: bool = False) -> Any:
        def add(client: Any) -> Any:
            issue = client.issues[issue_key]
            created = issue.checklist_items.create(text=text, checked=checked)
            # The SDK's checklistItems.create() discards the API response (it
            # never returns super().create(...)), which would leave the caller
            # with a bare null and no id for the item it just added. Re-read the
            # checklist in that case.
            if created is None:
                return _take(issue.checklist_items, _DICTIONARY_LIMIT)
            return created

        return _project(_to_plain(self._call_sdk(add)), _SLIM_CHECKLIST_FIELDS)

    def update_checklist_item(
        self,
        issue_key: str,
        item_id: str,
        text: str | None = None,
        checked: bool | None = None,
    ) -> Any:
        payload: dict[str, Any] = {}
        if text is not None:
            payload["text"] = text
        if checked is not None:
            payload["checked"] = checked
        if not payload:
            raise ValueError("Pass text and/or checked to update a checklist item.")

        def update(client: Any) -> Any:
            return _checklist_item(client, issue_key, item_id).update(**payload)

        return _project(_to_plain(self._call_sdk(update)), _SLIM_CHECKLIST_FIELDS)

    def delete_checklist_item(self, issue_key: str, item_id: str) -> Any:
        def delete(client: Any) -> Any:
            _checklist_item(client, issue_key, item_id).delete()
            return {"deleted": str(item_id), "issue": issue_key}

        return _to_plain(self._call_sdk(delete))

    def list_attachments(self, issue_key: str, limit: int = _DEFAULT_LIMIT) -> Any:
        return _to_plain(
            self._call_sdk(
                lambda client: _take(client.issues[issue_key].attachments, limit)
            )
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


def _checklist_item(client: Any, issue_key: str, item_id: str) -> Any:
    # Tracker documents PATCH and DELETE on a single checklist item but not GET,
    # so the item cannot be addressed directly the way a comment can. Locate it
    # in the list instead — the SDK resource that comes back carries its own
    # path, which is all update()/delete() need. Same shape as unlink_issue.
    target = str(item_id)
    for item in _take(client.issues[issue_key].checklist_items, _DICTIONARY_LIMIT):
        if str(_field(item, "id")) == target:
            return item
    raise ValueError(f"No checklist item {item_id!r} on issue {issue_key}.")


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


# A link's `type` keeps inward/outward rather than collapsing to a bare ref:
# the id alone ("dependency") does not say which way the relationship reads.
_SLIM_LINK_FIELDS = ("id", "direction", "status")
_SLIM_LINK_TYPE_KEYS = ("id", "inward", "outward")
_SLIM_CHECKLIST_FIELDS = ("id", "text", "checked", "assignee", "deadline")

# Write receipts. A create response is worth exactly two things to the caller:
# proof the write landed, and any value the server assigned or normalized. The
# rest — the echoed text it just sent, the full author object, the entire parent
# issue embedded in a worklog record — is bulk it already has or never needed.
_COMMENT_RECEIPT_FIELDS = ("id", "createdBy", "createdAt")
_COMMENT_EDIT_RECEIPT_FIELDS = ("id", "updatedBy", "updatedAt")
_WORKLOG_RECEIPT_FIELDS = ("id", "duration", "start", "createdBy", "createdAt")


def _slim_ref(value: Any) -> Any:
    # Collapse a nested Tracker reference (user, status, queue...) to just its
    # identifying keys, dropping self URLs and other bulk.
    if isinstance(value, dict):
        return {key: value[key] for key in _SLIM_REF_KEYS if key in value}
    if isinstance(value, list):
        return [_slim_ref(item) for item in value]
    return value


def _project(value: Any, fields: tuple[str, ...]) -> Any:
    # Keep only `fields`, collapsing every nested reference to its identifying
    # keys. Lists map elementwise; anything that is not a dict passes through.
    if isinstance(value, list):
        return [_project(item, fields) for item in value]
    if not isinstance(value, dict):
        return value
    return {name: _slim_ref(value[name]) for name in fields if name in value}


def _slim_issue(issue: Any) -> Any:
    return _project(issue, _SLIM_ISSUE_FIELDS)


def _issue_receipt(issue: Any, patched: Iterable[str] = ()) -> Any:
    """Post-write view of an issue: the compact projection plus what changed.

    Returning the whole issue after a PATCH is what made update the single most
    expensive tool here — a full object is ~29 fields, most of them untouched by
    the write. The two things the caller actually needs are proof the write
    landed and the server's canonical value of the fields that moved, so echo
    the patched keys even when they fall outside the projection (custom fields,
    description). `version` rides along because Tracker's optimistic locking
    keys off it.
    """
    if not isinstance(issue, dict):
        return issue
    slim = _project(issue, _SLIM_ISSUE_FIELDS + ("version",))
    for name in patched:
        if name in issue and name not in slim:
            slim[name] = _slim_ref(issue[name])
    return slim


def _slim_link(link: Any) -> Any:
    # A link's `object` is a *complete* issue object in the API response, which
    # is what makes a list of links cost far more than the relationships it
    # describes. Collapse it to an issue ref and keep the type's inward/outward
    # wording.
    if isinstance(link, list):
        return [_slim_link(item) for item in link]
    if not isinstance(link, dict):
        return link
    slim = _project(link, _SLIM_LINK_FIELDS)
    link_type = link.get("type")
    if isinstance(link_type, dict):
        slim["type"] = {
            key: link_type[key] for key in _SLIM_LINK_TYPE_KEYS if key in link_type
        }
    if "object" in link:
        slim["object"] = _slim_ref(link["object"])
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
# MCP server layer — MCPServer tools over the client above
# ===========================================================================
mcp = MCPServer("mcp-yandex-tracker", version=__version__)


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

    functools.wraps preserves the handler signature so MCPServer still derives the
    input schema from its typed parameters.
    """

    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> str:
        try:
            return _dump(fn(*args, **kwargs))
        except _DOMAIN_ERRORS as exc:
            raise error_cls(str(exc)) from exc

    return wrapper


def _tool(annotations: ToolAnnotations) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Build a registration decorator carrying a fixed set of tool annotations.

    The handler's raw return value becomes a single compact JSON text block
    (structured_output=False keeps MCPServer from also emitting a duplicating
    structuredContent block and an output schema), and domain errors surface as
    clean isError tool results instead of internal errors.
    """

    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        return mcp.tool(structured_output=False, annotations=annotations)(
            _json_safe(fn, ToolError)
        )

    return decorator


# Three flavours, so every tool states at its definition site what it does to the
# user's Tracker. Hosts read these hints to decide how much friction a call
# deserves: `readOnlyHint` is what lets a client auto-approve a lookup instead of
# prompting for each one, and `destructiveHint` separates "adds something" from
# "overwrites or removes something".
#
# Only the two hints that carry information are emitted. `idempotentHint` and
# `openWorldHint` are deliberately left off: every tool here talks to the same
# external service, so open-world is uniform and says nothing, and idempotency
# for Tracker writes depends on queue workflow rather than on the tool.
read_tool = _tool(ToolAnnotations(read_only_hint=True))
# Additive: creates something new and leaves existing data alone.
additive_tool = _tool(ToolAnnotations(read_only_hint=False, destructive_hint=False))
# Overwrites a value or removes data. Deletes, patches, and status transitions
# all land here — the previous value does not survive the call.
destructive_tool = _tool(ToolAnnotations(read_only_hint=False, destructive_hint=True))


NonEmptyStr = Annotated[str, Field(min_length=1)]
# Every Tracker collection is cursor-paginated and iterating one follows each
# "next" link to the end, so a list tool without a cap is unbounded. This is a
# hard cap on items returned, not a page size.
Limit = Annotated[
    int,
    Field(ge=1, le=1000, description="Max items to return (hard cap, not a page size). Default 50."),
]
Full = Annotated[
    bool,
    Field(description="Return complete objects instead of the compact projection. Off by default to keep responses small."),
]


# --- Issues -----------------------------------------------------------------
@read_tool
def tracker_get_issue(issue_key: NonEmptyStr) -> Any:
    """Get a Yandex Tracker issue by key."""
    return get_client().get_issue(issue_key)


@read_tool
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


@additive_tool
def tracker_create_issue(
    queue: NonEmptyStr,
    summary: NonEmptyStr,
    description: str | None = None,
    fields: Annotated[dict | None, Field(description="Additional Tracker issue fields.")] = None,
    full: Full = False,
) -> Any:
    """Create a Yandex Tracker issue.

    Returns a compact receipt — the new issue's key plus its identifying fields,
    version, and any extra `fields` as the server stored them. Pass full=true for
    the complete issue object.
    """
    return get_client().create_issue(
        queue=queue, summary=summary, description=description, fields=fields, full=full
    )


@destructive_tool
def tracker_update_issue(
    issue_key: NonEmptyStr,
    fields: Annotated[dict, Field(description="Fields to patch (raw Tracker API field names and values).")],
    full: Full = False,
) -> Any:
    """Update fields on a Yandex Tracker issue.

    Returns a compact receipt — the issue's identifying fields, its new version,
    and every patched field as the server stored it — rather than the whole
    issue. Pass full=true for the complete object.

    fields is a raw Tracker PATCH body, so it also covers: tags via
    {"tags": {"add": [...], "remove": [...]}} (or a full array to replace);
    components the same way (id or name); parent reassignment via
    {"parent": {"key": "TEST-2"}}. Epic association is a link, not a field — use
    tracker_link_issues for that.
    """
    return get_client().update_issue(issue_key, fields, full=full)


# --- Comments ---------------------------------------------------------------
@additive_tool
def tracker_add_comment(issue_key: NonEmptyStr, text: NonEmptyStr) -> Any:
    """Add a comment to a Yandex Tracker issue.

    Returns a receipt (comment id, author, timestamp), not the echoed text.
    """
    return get_client().add_comment(issue_key, text)


@read_tool
def tracker_list_comments(issue_key: NonEmptyStr, limit: Limit = 50) -> Any:
    """List comments for a Yandex Tracker issue, oldest first, at most `limit`."""
    return get_client().list_comments(issue_key, limit=limit)


@destructive_tool
def tracker_update_comment(
    issue_key: NonEmptyStr,
    comment_id: Annotated[str, Field(min_length=1, description="Comment id from tracker_list_comments.")],
    text: NonEmptyStr,
) -> Any:
    """Replace the text of an existing comment (get ids from tracker_list_comments).

    Returns a receipt (comment id, editor, timestamp), not the echoed text.
    """
    return get_client().update_comment(issue_key, comment_id, text)


@destructive_tool
def tracker_delete_comment(
    issue_key: NonEmptyStr,
    comment_id: Annotated[str, Field(min_length=1, description="Comment id from tracker_list_comments.")],
) -> Any:
    """Delete a comment from a Yandex Tracker issue by its comment id (get ids from tracker_list_comments)."""
    return get_client().delete_comment(issue_key, comment_id)


# --- Transitions ------------------------------------------------------------
@read_tool
def tracker_list_transitions(issue_key: NonEmptyStr) -> Any:
    """List available workflow transitions for a Yandex Tracker issue."""
    return get_client().list_transitions(issue_key)


@destructive_tool
def tracker_move_issue_status(
    issue_key: NonEmptyStr,
    status: Annotated[str, Field(min_length=1, description="Transition id/display or destination status id/key/display.")],
    fields: Annotated[dict | None, Field(description="Optional fields for the transition screen, such as comment.")] = None,
) -> Any:
    """Move a Yandex Tracker issue to a status by matching an available transition."""
    return get_client().move_issue_status(issue_key, status, fields)


@destructive_tool
def tracker_execute_transition(
    issue_key: NonEmptyStr,
    transition_id: NonEmptyStr,
    fields: dict | None = None,
) -> Any:
    """Execute a Yandex Tracker workflow transition."""
    return get_client().execute_transition(issue_key, transition_id, fields)


# --- Links ------------------------------------------------------------------
@additive_tool
def tracker_link_issues(
    issue_key: Annotated[str, Field(min_length=1, description="Source issue, e.g. TEST-1.")],
    relationship: Annotated[
        str,
        Field(description="Link type, e.g. relates, depends on, is dependent by, is subtask for, is parent task for, duplicates."),
    ],
    target_issue: Annotated[str, Field(min_length=1, description="Issue to link to, e.g. TEST-2.")],
) -> Any:
    """Create a link between two Yandex Tracker issues.

    Use tracker_list_link_types to discover valid relationship values. Returns
    the new link in the same compact shape as tracker_list_links.
    """
    return get_client().link_issue(issue_key, relationship, target_issue)


@read_tool
def tracker_list_links(
    issue_key: NonEmptyStr,
    limit: Limit = 50,
    full: Full = False,
) -> Any:
    """List links of a Yandex Tracker issue (each carries an id for tracker_unlink_issues).

    Each link is returned compactly — id, type (with its inward/outward wording),
    direction, status, and the linked issue trimmed to key/summary. The raw API
    embeds a complete issue object per link; pass full=true if you need it.
    """
    return get_client().list_links(issue_key, limit=limit, full=full)


@destructive_tool
def tracker_unlink_issues(
    issue_key: NonEmptyStr,
    link_id: Annotated[str, Field(min_length=1, description="Link id from tracker_list_links.")],
) -> Any:
    """Remove a link from a Yandex Tracker issue by its link id (get ids from tracker_list_links)."""
    return get_client().unlink_issue(issue_key, link_id)


# --- Queues & users ---------------------------------------------------------
@read_tool
def tracker_list_queues(limit: Limit = 50) -> Any:
    """List Yandex Tracker queues, at most `limit`."""
    return get_client().list_queues(limit=limit)


@read_tool
def tracker_list_users(
    email: Annotated[str | None, Field(description="Filter by exact email match.")] = None,
    group: Annotated[str | None, Field(description="Filter by group id.")] = None,
    limit: Limit = 50,
) -> Any:
    """List Yandex Tracker users (for assignee, followers, and other user fields).

    Supports server-side filters: email (exact match) and group. Note: Tracker
    has no server-side search by login or name — fetch and filter client-side
    for that, and raise `limit` if the directory is larger than the default.
    """
    return get_client().list_users(email=email, group=group, limit=limit)


@read_tool
def tracker_get_user(
    login_or_uid: Annotated[str, Field(min_length=1, description="User login (e.g. jsmith) or numeric uid.")],
) -> Any:
    """Get a single Yandex Tracker user by login or uid."""
    return get_client().get_user(login_or_uid)


@read_tool
def tracker_get_current_user() -> Any:
    """Get the currently authenticated Yandex Tracker user (the token owner)."""
    return get_client().get_current_user()


# --- Reference dictionaries -------------------------------------------------
@read_tool
def tracker_list_statuses() -> Any:
    """List the global Yandex Tracker status dictionary."""
    return get_client().list_statuses()


@read_tool
def tracker_list_issue_types() -> Any:
    """List the global Yandex Tracker issue-type dictionary."""
    return get_client().list_issue_types()


@read_tool
def tracker_list_priorities() -> Any:
    """List the global Yandex Tracker priority dictionary."""
    return get_client().list_priorities()


@read_tool
def tracker_list_fields() -> Any:
    """List Yandex Tracker fields, including custom fields."""
    return get_client().list_fields()


@read_tool
def tracker_list_link_types() -> Any:
    """List Yandex Tracker link types (valid relationship values for tracker_link_issues)."""
    return get_client().list_link_types()


@read_tool
def tracker_list_queue_versions(
    queue: Annotated[str, Field(min_length=1, description="Queue key, e.g. TEST.")],
) -> Any:
    """List versions defined in a specific Yandex Tracker queue."""
    return get_client().list_queue_versions(queue)


@read_tool
def tracker_list_queue_components(
    queue: Annotated[str, Field(min_length=1, description="Queue key, e.g. TEST.")],
) -> Any:
    """List components defined in a specific Yandex Tracker queue."""
    return get_client().list_queue_components(queue)


@read_tool
def tracker_list_queue_local_fields(
    queue: Annotated[str, Field(min_length=1, description="Queue key, e.g. TEST.")],
) -> Any:
    """List local (queue-specific custom) fields of a Yandex Tracker queue.

    Unlike tracker_list_fields, these are scoped to the queue.
    """
    return get_client().list_queue_local_fields(queue)


@read_tool
def tracker_list_queue_tags(
    queue: Annotated[str, Field(min_length=1, description="Queue key, e.g. TEST.")],
) -> Any:
    """List tags defined in a specific Yandex Tracker queue."""
    return get_client().list_queue_tags(queue)


# --- Activity ---------------------------------------------------------------
@read_tool
def tracker_get_changelog(
    issue_key: NonEmptyStr,
    field: Annotated[str | None, Field(description="Filter to changes of a single field id, e.g. status.")] = None,
    # `type` shadows the builtin on purpose: it mirrors the Tracker changelog
    # get-param name; the body forwards it as change_type.
    type: Annotated[str | None, Field(description="Filter by change type, e.g. IssueWorkflow, IssueUpdated.")] = None,
    limit: Limit = 50,
) -> Any:
    """Get the change history of a Yandex Tracker issue, oldest first, at most `limit`.

    Optionally filter by field and change type.
    """
    return get_client().get_changelog(issue_key, field=field, change_type=type, limit=limit)


@read_tool
def tracker_list_worklog(issue_key: NonEmptyStr, limit: Limit = 50) -> Any:
    """List worklog (time-tracking) records of a Yandex Tracker issue, at most `limit`."""
    return get_client().list_worklog(issue_key, limit=limit)


@additive_tool
def tracker_add_worklog(
    issue_key: NonEmptyStr,
    duration: Annotated[str, Field(min_length=1, description="ISO 8601 duration, e.g. PT1H30M for 1h30m.")],
    comment: str | None = None,
    start: Annotated[str | None, Field(description="ISO 8601 start datetime, e.g. 2026-07-03T10:00:00.000+0000.")] = None,
) -> Any:
    """Add a worklog (time spent) record to a Yandex Tracker issue.

    Returns a receipt (record id, duration, start, author, timestamp).
    """
    return get_client().add_worklog(issue_key, duration, comment=comment, start=start)


# --- Checklist --------------------------------------------------------------
@read_tool
def tracker_list_checklist(issue_key: NonEmptyStr, limit: Limit = 50) -> Any:
    """List checklist items of a Yandex Tracker issue, at most `limit`."""
    return get_client().list_checklist(issue_key, limit=limit)


@additive_tool
def tracker_add_checklist_item(
    issue_key: NonEmptyStr,
    text: NonEmptyStr,
    checked: Annotated[bool, Field(description="Initial checked state.")] = False,
) -> Any:
    """Add a checklist item to a Yandex Tracker issue.

    Returns the item (or the resulting checklist) with its id, text, and state.
    """
    return get_client().add_checklist_item(issue_key, text, checked=checked)


@destructive_tool
def tracker_update_checklist_item(
    issue_key: NonEmptyStr,
    item_id: Annotated[str, Field(min_length=1, description="Checklist item id from tracker_list_checklist.")],
    text: Annotated[str | None, Field(description="New text. Omit to leave unchanged.")] = None,
    checked: Annotated[bool | None, Field(description="New checked state. Omit to leave unchanged.")] = None,
) -> Any:
    """Update a checklist item's text and/or checked state.

    This is how an item gets ticked off. Pass at least one of text / checked.
    """
    return get_client().update_checklist_item(issue_key, item_id, text=text, checked=checked)


@destructive_tool
def tracker_delete_checklist_item(
    issue_key: NonEmptyStr,
    item_id: Annotated[str, Field(min_length=1, description="Checklist item id from tracker_list_checklist.")],
) -> Any:
    """Delete a checklist item from a Yandex Tracker issue by its item id."""
    return get_client().delete_checklist_item(issue_key, item_id)


# --- Attachments ------------------------------------------------------------
@read_tool
def tracker_list_attachments(issue_key: NonEmptyStr, limit: Limit = 50) -> Any:
    """List attachment metadata (id, name, size, url) of a Yandex Tracker issue.

    Returns at most `limit` items. Use tracker_download_attachment to fetch the
    bytes.
    """
    return get_client().list_attachments(issue_key, limit=limit)


@destructive_tool
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


@additive_tool
def tracker_upload_attachment(
    issue_key: NonEmptyStr,
    file_path: Annotated[str, Field(min_length=1, description="Absolute path to the local file to upload.")],
    filename: Annotated[str | None, Field(description="Optional name to store the attachment under in Tracker.")] = None,
) -> Any:
    """Upload a local file as an attachment on a Yandex Tracker issue."""
    return get_client().upload_attachment(issue_key, file_path, filename=filename)


@destructive_tool
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

    The body's return value becomes a compact JSON resource. Note: MCPServer's
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
