from __future__ import annotations

import json
import sys
import traceback
from collections.abc import Callable
from typing import Any

from . import __version__
from .client import TrackerApiError, TrackerConfigError, YandexTrackerClient


JSONRPC_VERSION = "2.0"
PROTOCOL_VERSION = "2025-03-26"


def _schema(properties: dict[str, Any], required: list[str] | None = None) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": properties,
        "required": required or [],
        "additionalProperties": False,
    }


TOOLS: list[dict[str, Any]] = [
    {
        "name": "tracker_get_issue",
        "description": "Get a Yandex Tracker issue by key.",
        "inputSchema": _schema(
            {"issue_key": {"type": "string", "description": "Issue key, for example TEST-123."}},
            ["issue_key"],
        ),
    },
    {
        "name": "tracker_search_issues",
        "description": "Search Yandex Tracker issues using query language, filter fields, or keys.",
        "inputSchema": _schema(
            {
                "query": {"type": "string"},
                "filter": {"type": "object"},
                "order": {"type": "string"},
                "keys": {"type": "array", "items": {"type": "string"}},
                "per_page": {"type": "integer", "minimum": 1, "maximum": 100},
                "page": {"type": "integer", "minimum": 1},
            }
        ),
    },
    {
        "name": "tracker_create_issue",
        "description": "Create a Yandex Tracker issue.",
        "inputSchema": _schema(
            {
                "queue": {"type": "string"},
                "summary": {"type": "string"},
                "description": {"type": "string"},
                "fields": {"type": "object", "description": "Additional Tracker issue fields."},
            },
            ["queue", "summary"],
        ),
    },
    {
        "name": "tracker_update_issue",
        "description": "Update fields on a Yandex Tracker issue.",
        "inputSchema": _schema(
            {
                "issue_key": {"type": "string"},
                "fields": {"type": "object", "description": "Fields to patch."},
            },
            ["issue_key", "fields"],
        ),
    },
    {
        "name": "tracker_add_comment",
        "description": "Add a comment to a Yandex Tracker issue.",
        "inputSchema": _schema(
            {
                "issue_key": {"type": "string"},
                "text": {"type": "string"},
            },
            ["issue_key", "text"],
        ),
    },
    {
        "name": "tracker_list_comments",
        "description": "List comments for a Yandex Tracker issue.",
        "inputSchema": _schema(
            {"issue_key": {"type": "string"}},
            ["issue_key"],
        ),
    },
    {
        "name": "tracker_list_transitions",
        "description": "List available workflow transitions for a Yandex Tracker issue.",
        "inputSchema": _schema(
            {"issue_key": {"type": "string"}},
            ["issue_key"],
        ),
    },
    {
        "name": "tracker_move_issue_status",
        "description": "Move a Yandex Tracker issue to a status by matching an available transition.",
        "inputSchema": _schema(
            {
                "issue_key": {"type": "string"},
                "status": {
                    "type": "string",
                    "description": "Transition id/display or destination status id/key/display.",
                },
                "fields": {
                    "type": "object",
                    "description": "Optional fields for the transition screen, such as comment.",
                },
            },
            ["issue_key", "status"],
        ),
    },
    {
        "name": "tracker_execute_transition",
        "description": "Execute a Yandex Tracker workflow transition.",
        "inputSchema": _schema(
            {
                "issue_key": {"type": "string"},
                "transition_id": {"type": "string"},
                "fields": {"type": "object"},
            },
            ["issue_key", "transition_id"],
        ),
    },
]


class McpServer:
    def __init__(self, client_factory: Callable[[], YandexTrackerClient] | None = None) -> None:
        self._client_factory = client_factory or YandexTrackerClient

    def handle_message(self, message: dict[str, Any]) -> dict[str, Any] | None:
        if "id" not in message:
            self._handle_notification(message.get("method"), message.get("params") or {})
            return None

        request_id = message.get("id")
        method = message.get("method")
        params = message.get("params") or {}
        try:
            result = self._dispatch(method, params)
            return {"jsonrpc": JSONRPC_VERSION, "id": request_id, "result": result}
        except Exception as exc:
            return {
                "jsonrpc": JSONRPC_VERSION,
                "id": request_id,
                "error": _error_payload(exc),
            }

    def _dispatch(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        if method == "initialize":
            return {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {
                    "tools": {"listChanged": False},
                    "resources": {},
                    "prompts": {},
                },
                "serverInfo": {"name": "yandex-tracker-mcp", "version": __version__},
            }
        if method == "ping":
            return {}
        if method == "tools/list":
            return {"tools": TOOLS}
        if method == "tools/call":
            return self._call_tool(params)
        if method == "resources/list":
            return {"resources": []}
        if method == "prompts/list":
            return {"prompts": []}
        raise ValueError(f"Unsupported MCP method: {method}")

    def _handle_notification(self, method: str | None, params: dict[str, Any]) -> None:
        if method in {"notifications/initialized", "notifications/cancelled"}:
            return
        print(f"Ignoring MCP notification {method!r}: {params!r}", file=sys.stderr)

    def _call_tool(self, params: dict[str, Any]) -> dict[str, Any]:
        name = params.get("name")
        arguments = params.get("arguments") or {}
        if not isinstance(arguments, dict):
            raise ValueError("tools/call params.arguments must be an object.")

        handlers: dict[str, Callable[[YandexTrackerClient, dict[str, Any]], Any]] = {
            "tracker_get_issue": lambda c, a: c.get_issue(_required(a, "issue_key")),
            "tracker_search_issues": lambda c, a: c.search_issues(
                query=a.get("query"),
                filter=a.get("filter"),
                order=a.get("order"),
                keys=a.get("keys"),
                per_page=int(a.get("per_page", 20)),
                page=int(a.get("page", 1)),
            ),
            "tracker_create_issue": lambda c, a: c.create_issue(
                queue=_required(a, "queue"),
                summary=_required(a, "summary"),
                description=a.get("description"),
                fields=a.get("fields"),
            ),
            "tracker_update_issue": lambda c, a: c.update_issue(
                _required(a, "issue_key"),
                _required(a, "fields"),
            ),
            "tracker_add_comment": lambda c, a: c.add_comment(
                _required(a, "issue_key"),
                _required(a, "text"),
            ),
            "tracker_list_comments": lambda c, a: c.list_comments(_required(a, "issue_key")),
            "tracker_list_transitions": lambda c, a: c.list_transitions(_required(a, "issue_key")),
            "tracker_move_issue_status": lambda c, a: c.move_issue_status(
                _required(a, "issue_key"),
                _required(a, "status"),
                a.get("fields"),
            ),
            "tracker_execute_transition": lambda c, a: c.execute_transition(
                _required(a, "issue_key"),
                _required(a, "transition_id"),
                a.get("fields"),
            ),
        }
        if name not in handlers:
            raise ValueError(f"Unknown tool: {name}")

        try:
            client = self._client_factory()
            payload = handlers[name](client, arguments)
            return _tool_result(payload)
        except (TrackerApiError, TrackerConfigError, ValueError) as exc:
            return _tool_error(str(exc))


def _required(arguments: dict[str, Any], name: str) -> Any:
    value = arguments.get(name)
    if value is None or value == "":
        raise ValueError(f"Missing required argument: {name}")
    return value


def _tool_result(payload: Any) -> dict[str, Any]:
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(payload, ensure_ascii=False, indent=2),
            }
        ],
        "isError": False,
    }


def _tool_error(message: str) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": message}], "isError": True}


def _error_payload(exc: Exception) -> dict[str, Any]:
    if isinstance(exc, json.JSONDecodeError):
        return {"code": -32700, "message": "Parse error", "data": str(exc)}
    if isinstance(exc, ValueError):
        return {"code": -32602, "message": str(exc)}
    return {
        "code": -32603,
        "message": "Internal error",
        "data": "".join(traceback.format_exception_only(type(exc), exc)).strip(),
    }


def serve_stdio(
    input_stream: Any = sys.stdin,
    output_stream: Any = sys.stdout,
    server: McpServer | None = None,
) -> None:
    server = server or McpServer()
    for line in input_stream:
        line = line.strip()
        if not line:
            continue
        try:
            messages = json.loads(line)
            batch = isinstance(messages, list)
            items = messages if batch else [messages]
            responses = [server.handle_message(item) for item in items]
            responses = [response for response in responses if response is not None]
            if not responses:
                continue
            payload = responses if batch else responses[0]
        except Exception as exc:
            payload = {"jsonrpc": JSONRPC_VERSION, "id": None, "error": _error_payload(exc)}
        output_stream.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")
        output_stream.flush()
