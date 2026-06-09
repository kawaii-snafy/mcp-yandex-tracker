import io
import json
import unittest

from yandex_tracker_mcp_server.client import TrackerConfigError
from yandex_tracker_mcp_server.server import McpServer, serve_stdio


class FakeClient:
    def __init__(self):
        self.calls = []

    def get_issue(self, issue_key):
        self.calls.append(("get_issue", issue_key))
        return {"key": issue_key}

    def search_issues(self, **kwargs):
        self.calls.append(("search_issues", kwargs))
        return [{"key": "TEST-1"}]

    def create_issue(self, **kwargs):
        self.calls.append(("create_issue", kwargs))
        return {"key": "TEST-2"}

    def update_issue(self, issue_key, fields):
        self.calls.append(("update_issue", issue_key, fields))
        return {"key": issue_key, **fields}

    def add_comment(self, issue_key, text):
        self.calls.append(("add_comment", issue_key, text))
        return {"id": 1, "text": text}

    def list_comments(self, issue_key):
        self.calls.append(("list_comments", issue_key))
        return [{"id": 1}]

    def list_transitions(self, issue_key):
        self.calls.append(("list_transitions", issue_key))
        return [{"id": "start", "display": "Start progress", "to": {"key": "inProgress"}}]

    def move_issue_status(self, issue_key, status, fields=None):
        self.calls.append(("move_issue_status", issue_key, status, fields))
        return [{"id": "close", "to": {"key": "closed"}}]

    def execute_transition(self, issue_key, transition_id, fields=None):
        self.calls.append(("execute_transition", issue_key, transition_id, fields))
        return {"transition": transition_id}


class ServerTests(unittest.TestCase):
    def test_initialize_declares_tools_capability(self):
        server = McpServer(client_factory=FakeClient)

        response = server.handle_message(
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
        )

        result = response["result"]
        self.assertEqual(result["serverInfo"]["name"], "yandex-tracker-mcp")
        self.assertIn("tools", result["capabilities"])

    def test_tools_list_exposes_tracker_tools(self):
        server = McpServer(client_factory=FakeClient)

        response = server.handle_message({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})

        names = {tool["name"] for tool in response["result"]["tools"]}
        self.assertIn("tracker_get_issue", names)
        self.assertIn("tracker_search_issues", names)
        self.assertIn("tracker_add_comment", names)
        self.assertIn("tracker_list_transitions", names)
        self.assertIn("tracker_move_issue_status", names)

    def test_tools_call_returns_text_result(self):
        fake = FakeClient()
        server = McpServer(client_factory=lambda: fake)

        response = server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "tracker_get_issue",
                    "arguments": {"issue_key": "TEST-1"},
                },
            }
        )

        self.assertFalse(response["result"]["isError"])
        self.assertIn('"key": "TEST-1"', response["result"]["content"][0]["text"])
        self.assertEqual(fake.calls, [("get_issue", "TEST-1")])

    def test_tool_argument_errors_are_tool_errors(self):
        server = McpServer(client_factory=FakeClient)

        response = server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {"name": "tracker_get_issue", "arguments": {}},
            }
        )

        self.assertTrue(response["result"]["isError"])
        self.assertIn("Missing required argument", response["result"]["content"][0]["text"])

    def test_client_configuration_errors_are_tool_errors(self):
        def broken_client_factory():
            raise TrackerConfigError("missing token")

        server = McpServer(client_factory=broken_client_factory)

        response = server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 5,
                "method": "tools/call",
                "params": {
                    "name": "tracker_get_issue",
                    "arguments": {"issue_key": "TEST-1"},
                },
            }
        )

        self.assertNotIn("error", response)
        self.assertTrue(response["result"]["isError"])
        self.assertIn("missing token", response["result"]["content"][0]["text"])

    def test_move_issue_status_calls_client(self):
        fake = FakeClient()
        server = McpServer(client_factory=lambda: fake)

        response = server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 6,
                "method": "tools/call",
                "params": {
                    "name": "tracker_move_issue_status",
                    "arguments": {
                        "issue_key": "TEST-1",
                        "status": "inProgress",
                        "fields": {"comment": "starting"},
                    },
                },
            }
        )

        self.assertFalse(response["result"]["isError"])
        self.assertEqual(
            fake.calls,
            [("move_issue_status", "TEST-1", "inProgress", {"comment": "starting"})],
        )

    def test_stdio_uses_newline_delimited_json_rpc(self):
        input_stream = io.StringIO(
            json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}) + "\n"
        )
        output_stream = io.StringIO()

        serve_stdio(input_stream, output_stream, McpServer(client_factory=FakeClient))

        response = json.loads(output_stream.getvalue())
        self.assertEqual(response["jsonrpc"], "2.0")
        self.assertEqual(response["id"], 1)
        self.assertIn("tools", response["result"])

    def test_stdio_batch_invalid_item_does_not_suppress_valid_response(self):
        input_stream = io.StringIO(
            json.dumps(
                [
                    {"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
                    1,
                ]
            )
            + "\n"
        )
        output_stream = io.StringIO()

        serve_stdio(input_stream, output_stream, McpServer(client_factory=FakeClient))

        response = json.loads(output_stream.getvalue())
        self.assertEqual(len(response), 2)
        self.assertEqual(response[0]["id"], 1)
        self.assertIn("tools", response[0]["result"])
        self.assertEqual(response[1]["id"], None)
        self.assertEqual(response[1]["error"]["code"], -32600)

    def test_notifications_do_not_emit_response(self):
        input_stream = io.StringIO(
            json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n"
        )
        output_stream = io.StringIO()

        serve_stdio(input_stream, output_stream, McpServer(client_factory=FakeClient))

        self.assertEqual(output_stream.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
