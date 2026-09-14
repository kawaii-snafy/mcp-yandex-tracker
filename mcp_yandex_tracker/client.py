"""Transport for the Yandex Tracker REST API v3.

Everything in this module is a direct expression of the official documentation —
index at https://yandex.ru/support/tracker/en/llms.txt, every page available as
markdown by appending `.md`. No SDK, no undocumented endpoints, no guesses.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import requests
from requests.adapters import HTTPAdapter, Retry

# common-format.md: v3 is the current version and carries every method update.
API_VERSION = "v3"

# The SDK this server used to wrap retried 10 times by default. Keep comparable
# resilience for requests that are safe to repeat. error-codes.md documents 429
# but specifies neither a quota nor a Retry-After header, so back off on our own.
_RETRY_STATUSES = (429, 500, 502, 503, 504)
_RETRY_METHODS = frozenset({"GET", "HEAD", "OPTIONS", "DELETE"})

_DOWNLOAD_CHUNK = 8192


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
            base_url=_strip_api_version(values.get("YANDEX_TRACKER_BASE_URL", cls.base_url)),
            auth_scheme=values.get("YANDEX_TRACKER_AUTH_SCHEME", cls.auth_scheme),
            timeout=float(values.get("YANDEX_TRACKER_TIMEOUT", cls.timeout)),
        )

    @property
    def api_root(self) -> str:
        return f"{_strip_api_version(self.base_url)}/{API_VERSION}"

    def headers(self) -> dict[str, str]:
        # common-format.md: `OAuth <token>` for OAuth tokens, `Bearer <token>` for
        # IAM ones, plus X-Cloud-Org-ID (Identity Hub) or X-Org-ID (Yandex 360).
        # Exactly one org header goes on the wire; cloud wins when both are set.
        headers = {"Authorization": f"{self.auth_scheme} {self.token}"}
        if self.cloud_org_id:
            headers["X-Cloud-Org-Id"] = self.cloud_org_id
        elif self.org_id:
            headers["X-Org-Id"] = self.org_id
        return headers


def _strip_api_version(base_url: str) -> str:
    # The version lives in the path this client builds, not in the configured
    # host. Older configs carry a `/v2` or `/v3` suffix; drop it silently.
    base_url = base_url.rstrip("/")
    for suffix in (f"/{API_VERSION}", "/v2"):
        if base_url.endswith(suffix):
            return base_url[: -len(suffix)]
    return base_url


def if_match(version: Any) -> dict[str, str] | None:
    """Build the optimistic-locking header some endpoints document.

    Those pages show `If-Match: "<version>"` in their request example: the edit
    only lands if the object is still at that version, otherwise Tracker answers
    409/412. Returns None when the caller did not ask for the check.
    """
    if version is None:
        return None
    return {"If-Match": f'"{version}"'}


def given(**values: Any) -> dict[str, Any]:
    """Drop the arguments the caller left unset.

    Every tool builds its query string and its request body with this, so an
    omitted optional parameter is simply absent from the request instead of
    being sent as null. `False` and `""` are values and survive.
    """
    return {key: value for key, value in values.items() if value is not None}


class Tracker:
    """The only way out to Yandex Tracker. There is nothing else in this layer."""

    def __init__(
        self,
        config: TrackerConfig | None = None,
        session: Any | None = None,
    ) -> None:
        self.config = config or TrackerConfig.from_env()
        self._session = session if session is not None else _build_session(self.config)

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any | None = None,
        files: Any | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        """Call one documented endpoint and return its decoded body."""
        response = self._send(
            method,
            self.config.api_root + path,
            params=_wire_params(params),
            json=json,
            files=files,
            headers=headers or None,
        )
        return _decode(response)

    def upload(
        self,
        path: str,
        file_path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """POST a local file as multipart/form-data (the part is named `file`)."""
        # Validate up front so a missing or unreadable path is a clean argument
        # error rather than being mislabeled as a transport failure.
        if not os.path.isfile(file_path):
            raise ValueError(f"File not found: {file_path}")
        if not os.access(file_path, os.R_OK):
            raise ValueError(f"File is not readable: {file_path}")
        with open(file_path, "rb") as handle:
            return self.request(
                "POST",
                path,
                params=params,
                files={"file": (os.path.basename(file_path), handle)},
            )

    def download(self, path: str, dest_dir: str, filename: str) -> dict[str, Any]:
        """Stream a binary endpoint into `dest_dir` and return where it landed."""
        # basename guards against path traversal through a Tracker-supplied or
        # caller-supplied name.
        name = os.path.basename(str(filename)) or "attachment"
        response = self._send("GET", self.config.api_root + path, stream=True)
        os.makedirs(dest_dir, exist_ok=True)
        dest_path = os.path.join(dest_dir, name)
        size = 0
        try:
            with open(dest_path, "wb") as handle:
                for chunk in response.iter_content(_DOWNLOAD_CHUNK):
                    handle.write(chunk)
                    size += len(chunk)
        finally:
            response.close()
        return {"path": dest_path, "name": name, "size": size}

    def _send(self, method: str, url: str, **kwargs: Any) -> Any:
        try:
            response = self._session.request(
                method, url, timeout=self.config.timeout, **kwargs
            )
        except (requests.RequestException, OSError) as exc:
            raise TrackerApiError(0, f"Failed to reach Yandex Tracker: {exc}") from exc
        if response.status_code >= 400:
            raise _api_error(response)
        return response


def _build_session(config: TrackerConfig) -> requests.Session:
    session = requests.Session()
    session.headers.update(config.headers())
    retry = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=_RETRY_STATUSES,
        allowed_methods=_RETRY_METHODS,
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def _wire_params(params: dict[str, Any] | None) -> dict[str, Any] | None:
    """Spell query values the way the API reads them.

    requests urlencodes a Python bool as `True`/`False`; every documented boolean
    parameter (`notify`, `full`, `localized`, …) is a JSON boolean, so it has to
    go out lowercase. Lists are left alone apart from their items — a repeated
    key is how `createdAt=from:…&createdAt=to:…` is expressed.
    """
    if not params:
        return None
    return {key: _wire_value(value) for key, value in params.items()}


def _wire_value(value: Any) -> Any:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list):
        return [_wire_value(item) for item in value]
    return value


def _decode(response: Any) -> Any:
    # error-codes.md: 204 means the DELETE went through and carries no body.
    if response.status_code == 204 or not response.content:
        return None
    try:
        return response.json()
    except ValueError:
        return response.text


def _api_error(response: Any) -> TrackerApiError:
    payload = None
    if response.content:
        try:
            payload = response.json()
        except ValueError:
            payload = None
    message = (
        _error_message(payload)
        or (response.text or "").strip()
        or response.reason
        or "request failed"
    )
    return TrackerApiError(response.status_code, message, payload)


def _error_message(payload: Any) -> str | None:
    # The error body shape is *not* documented anywhere in the API reference, so
    # this stays best effort: read the fields Tracker actually sends, and let the
    # caller fall back to the raw body when it sends something else.
    if not isinstance(payload, dict):
        return None
    messages = payload.get("errorMessages")
    if isinstance(messages, list) and messages:
        return "; ".join(str(item) for item in messages)
    errors = payload.get("errors")
    if isinstance(errors, dict) and errors:
        return "; ".join(f"{key}: {value}" for key, value in errors.items())
    return None
