from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any


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
            materialized = list(issues)
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

        return _to_plain(self._call_sdk(search))

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

    def list_users(self) -> Any:
        return _to_plain(self._call_sdk(lambda client: list(client.users.get_all())))

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

    def get_changelog(self, issue_key: str) -> Any:
        return _to_plain(
            self._call_sdk(lambda client: list(client.issues[issue_key].changelog))
        )

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


def _to_plain(value: Any) -> Any:
    if hasattr(value, "as_dict"):
        return _to_plain(value.as_dict())
    if isinstance(value, dict):
        return {key: _to_plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_to_plain(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)
