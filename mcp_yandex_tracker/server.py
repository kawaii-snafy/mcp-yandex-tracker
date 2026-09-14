"""MCP surface: the server object, the tool/resource wrappers, and main()."""

from __future__ import annotations

import functools
import json
import threading
from collections.abc import Callable
from typing import Annotated, Any

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ResourceError, ToolError
from pydantic import Field

from ._version import __version__
from .client import Tracker, TrackerApiError, TrackerConfigError

mcp = MCPServer("mcp-yandex-tracker", version=__version__)


# One client per process, built lazily. requests.Session opens a connection pool
# on construction; reusing a single instance keeps HTTP keep-alive across tool
# calls instead of rebuilding it every time. _client_factory stays swappable so
# tests can inject a fake.
_client: Tracker | None = None
_client_factory: Callable[[], Tracker] = Tracker
_client_lock = threading.Lock()


def get_client() -> Tracker:
    global _client
    if _client is None:
        with _client_lock:
            if _client is None:
                _client = _client_factory()
    return _client


def _dump(payload: Any) -> str:
    # Compact separators: pretty-printing adds whitespace tokens to every line of
    # every response for no benefit — the model reads compact JSON just as well.
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


# Domain exceptions a handler may raise; both surfaces remap them to a clean MCP
# error instead of leaking an internal one.
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


def tool(fn: Callable[..., Any]) -> Callable[..., Any]:
    """Register one Yandex Tracker endpoint as a tool.

    The handler's raw return value becomes a single compact JSON text block
    (structured_output=False keeps MCPServer from also emitting a duplicating
    structuredContent block and an output schema), and domain errors surface as
    clean isError tool results instead of internal errors.
    """
    return mcp.tool(structured_output=False)(_json_safe(fn, ToolError))


def resource(uri: str, **kwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Register a read-only Tracker resource.

    The body's return value becomes a compact JSON resource, and a domain error
    becomes a `ResourceError`, which MCPServer re-raises untouched — so this
    mapping, not just the serialization, is what carries the Tracker message to
    the client. (That pass-through is why the dependency floor is mcp 2.1: 2.0
    replaced every handler error with a generic "Error reading resource {uri}".)
    """

    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        return mcp.resource(uri, **kwargs)(_json_safe(fn, ResourceError))

    return decorator


NonEmptyStr = Annotated[str, Field(min_length=1)]


def main() -> None:
    mcp.run(transport="stdio")
