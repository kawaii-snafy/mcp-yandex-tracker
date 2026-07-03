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
                "include_total": {
                    "type": "boolean",
                    "description": "Also return the total match count (extra request). "
                    "Response becomes {issues, total, page, per_page}.",
                },
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
    {
        "name": "tracker_link_issues",
        "description": "Create a link between two Yandex Tracker issues. "
        "Use tracker_list_link_types to discover valid relationship values.",
        "inputSchema": _schema(
            {
                "issue_key": {"type": "string", "description": "Source issue, e.g. TEST-1."},
                "relationship": {
                    "type": "string",
                    "description": "Link type, e.g. relates, depends on, "
                    "is dependent by, is subtask for, is parent task for, duplicates.",
                },
                "target_issue": {"type": "string", "description": "Issue to link to, e.g. TEST-2."},
            },
            ["issue_key", "relationship", "target_issue"],
        ),
    },
    {
        "name": "tracker_list_links",
        "description": "List links of a Yandex Tracker issue (each carries an id for tracker_unlink_issues).",
        "inputSchema": _schema(
            {"issue_key": {"type": "string"}},
            ["issue_key"],
        ),
    },
    {
        "name": "tracker_unlink_issues",
        "description": "Remove a link from a Yandex Tracker issue by its link id "
        "(get ids from tracker_list_links).",
        "inputSchema": _schema(
            {
                "issue_key": {"type": "string"},
                "link_id": {"type": "string", "description": "Link id from tracker_list_links."},
            },
            ["issue_key", "link_id"],
        ),
    },
    {
        "name": "tracker_list_queues",
        "description": "List Yandex Tracker queues.",
        "inputSchema": _schema({}),
    },
    {
        "name": "tracker_list_users",
        "description": "List Yandex Tracker users (for assignee, followers, and other user fields).",
        "inputSchema": _schema({}),
    },
    {
        "name": "tracker_list_statuses",
        "description": "List the global Yandex Tracker status dictionary.",
        "inputSchema": _schema({}),
    },
    {
        "name": "tracker_list_issue_types",
        "description": "List the global Yandex Tracker issue-type dictionary.",
        "inputSchema": _schema({}),
    },
    {
        "name": "tracker_list_priorities",
        "description": "List the global Yandex Tracker priority dictionary.",
        "inputSchema": _schema({}),
    },
    {
        "name": "tracker_list_fields",
        "description": "List Yandex Tracker fields, including custom fields.",
        "inputSchema": _schema({}),
    },
    {
        "name": "tracker_list_link_types",
        "description": "List Yandex Tracker link types (valid relationship values for tracker_link_issues).",
        "inputSchema": _schema({}),
    },
    {
        "name": "tracker_list_queue_versions",
        "description": "List versions defined in a specific Yandex Tracker queue.",
        "inputSchema": _schema(
            {"queue": {"type": "string", "description": "Queue key, e.g. TEST."}},
            ["queue"],
        ),
    },
    {
        "name": "tracker_list_queue_components",
        "description": "List components defined in a specific Yandex Tracker queue.",
        "inputSchema": _schema(
            {"queue": {"type": "string", "description": "Queue key, e.g. TEST."}},
            ["queue"],
        ),
    },
    {
        "name": "tracker_get_changelog",
        "description": "Get the change history of a Yandex Tracker issue.",
        "inputSchema": _schema(
            {"issue_key": {"type": "string"}},
            ["issue_key"],
        ),
    },
    {
        "name": "tracker_list_worklog",
        "description": "List worklog (time-tracking) records of a Yandex Tracker issue.",
        "inputSchema": _schema(
            {"issue_key": {"type": "string"}},
            ["issue_key"],
        ),
    },
    {
        "name": "tracker_add_worklog",
        "description": "Add a worklog (time spent) record to a Yandex Tracker issue.",
        "inputSchema": _schema(
            {
                "issue_key": {"type": "string"},
                "duration": {
                    "type": "string",
                    "description": "ISO 8601 duration, e.g. PT1H30M for 1h30m.",
                },
                "comment": {"type": "string"},
                "start": {
                    "type": "string",
                    "description": "ISO 8601 start datetime, e.g. 2026-07-03T10:00:00.000+0000.",
                },
            },
            ["issue_key", "duration"],
        ),
    },
    {
        "name": "tracker_list_checklist",
        "description": "List checklist items of a Yandex Tracker issue.",
        "inputSchema": _schema(
            {"issue_key": {"type": "string"}},
            ["issue_key"],
        ),
    },
    {
        "name": "tracker_add_checklist_item",
        "description": "Add a checklist item to a Yandex Tracker issue.",
        "inputSchema": _schema(
            {
                "issue_key": {"type": "string"},
                "text": {"type": "string"},
                "checked": {"type": "boolean", "description": "Initial checked state."},
            },
            ["issue_key", "text"],
        ),
    },
    {
        "name": "tracker_list_attachments",
        "description": "List attachment metadata (id, name, size, url) of a Yandex Tracker issue. "
        "Use tracker_download_attachment to fetch the bytes.",
        "inputSchema": _schema(
            {"issue_key": {"type": "string"}},
            ["issue_key"],
        ),
    },
    {
        "name": "tracker_download_attachment",
        "description": "Download an issue attachment to a local directory and return the saved "
        "file path. Tracker attachment URLs need authentication, so this proxies the download "
        "through the server. Ask the user where to save before calling.",
        "inputSchema": _schema(
            {
                "issue_key": {"type": "string"},
                "attachment_id": {
                    "type": "string",
                    "description": "Attachment id from tracker_list_attachments.",
                },
                "dest_dir": {
                    "type": "string",
                    "description": "Absolute directory path to save the file into.",
                },
                "filename": {
                    "type": "string",
                    "description": "Optional override for the saved file name.",
                },
            },
            ["issue_key", "attachment_id", "dest_dir"],
        ),
    },
    {
        "name": "tracker_upload_attachment",
        "description": "Upload a local file as an attachment on a Yandex Tracker issue.",
        "inputSchema": _schema(
            {
                "issue_key": {"type": "string"},
                "file_path": {
                    "type": "string",
                    "description": "Absolute path to the local file to upload.",
                },
                "filename": {
                    "type": "string",
                    "description": "Optional name to store the attachment under in Tracker.",
                },
            },
            ["issue_key", "file_path"],
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
                "serverInfo": {"name": "mcp-yandex-tracker", "version": __version__},
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
                per_page=_int_arg(a, "per_page", 20),
                page=_int_arg(a, "page", 1),
                include_total=bool(a.get("include_total", False)),
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
            "tracker_link_issues": lambda c, a: c.link_issue(
                _required(a, "issue_key"),
                _required(a, "relationship"),
                _required(a, "target_issue"),
            ),
            "tracker_list_links": lambda c, a: c.list_links(_required(a, "issue_key")),
            "tracker_unlink_issues": lambda c, a: c.unlink_issue(
                _required(a, "issue_key"),
                _required(a, "link_id"),
            ),
            "tracker_list_queues": lambda c, a: c.list_queues(),
            "tracker_list_users": lambda c, a: c.list_users(),
            "tracker_list_statuses": lambda c, a: c.list_statuses(),
            "tracker_list_issue_types": lambda c, a: c.list_issue_types(),
            "tracker_list_priorities": lambda c, a: c.list_priorities(),
            "tracker_list_fields": lambda c, a: c.list_fields(),
            "tracker_list_link_types": lambda c, a: c.list_link_types(),
            "tracker_list_queue_versions": lambda c, a: c.list_queue_versions(
                _required(a, "queue")
            ),
            "tracker_list_queue_components": lambda c, a: c.list_queue_components(
                _required(a, "queue")
            ),
            "tracker_get_changelog": lambda c, a: c.get_changelog(_required(a, "issue_key")),
            "tracker_list_worklog": lambda c, a: c.list_worklog(_required(a, "issue_key")),
            "tracker_add_worklog": lambda c, a: c.add_worklog(
                _required(a, "issue_key"),
                _required(a, "duration"),
                comment=a.get("comment"),
                start=a.get("start"),
            ),
            "tracker_list_checklist": lambda c, a: c.list_checklist(_required(a, "issue_key")),
            "tracker_add_checklist_item": lambda c, a: c.add_checklist_item(
                _required(a, "issue_key"),
                _required(a, "text"),
                checked=bool(a.get("checked", False)),
            ),
            "tracker_list_attachments": lambda c, a: c.list_attachments(_required(a, "issue_key")),
            "tracker_download_attachment": lambda c, a: c.download_attachment(
                _required(a, "issue_key"),
                _required(a, "attachment_id"),
                _required(a, "dest_dir"),
                filename=a.get("filename"),
            ),
            "tracker_upload_attachment": lambda c, a: c.upload_attachment(
                _required(a, "issue_key"),
                _required(a, "file_path"),
                filename=a.get("filename"),
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


def _int_arg(arguments: dict[str, Any], name: str, default: int) -> int:
    value = arguments.get(name, default)
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValueError(f"Argument {name!r} must be an integer, got {value!r}.")


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
            responses = [_handle_stdio_item(server, item) for item in items]
            responses = [response for response in responses if response is not None]
            if not responses:
                continue
            payload = responses if batch else responses[0]
        except Exception as exc:
            payload = {"jsonrpc": JSONRPC_VERSION, "id": None, "error": _error_payload(exc)}
        output_stream.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")
        output_stream.flush()


def _handle_stdio_item(server: McpServer, item: Any) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return {
            "jsonrpc": JSONRPC_VERSION,
            "id": None,
            "error": {"code": -32600, "message": "Invalid Request"},
        }
    try:
        return server.handle_message(item)
    except Exception as exc:
        return {"jsonrpc": JSONRPC_VERSION, "id": item.get("id"), "error": _error_payload(exc)}
