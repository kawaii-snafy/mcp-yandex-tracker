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

    def delete_comment(self, issue_key, comment_id):
        self.calls.append(("delete_comment", issue_key, comment_id))
        return {"deleted": comment_id, "issue": issue_key}

    def list_transitions(self, issue_key):
        self.calls.append(("list_transitions", issue_key))
        return [{"id": "start", "display": "Start progress", "to": {"key": "inProgress"}}]

    def move_issue_status(self, issue_key, status, fields=None):
        self.calls.append(("move_issue_status", issue_key, status, fields))
        return [{"id": "close", "to": {"key": "closed"}}]

    def execute_transition(self, issue_key, transition_id, fields=None):
        self.calls.append(("execute_transition", issue_key, transition_id, fields))
        return {"transition": transition_id}

    def link_issue(self, issue_key, relationship, target_issue):
        self.calls.append(("link_issue", issue_key, relationship, target_issue))
        return {"linked": target_issue}

    def list_links(self, issue_key):
        self.calls.append(("list_links", issue_key))
        return [{"id": "100"}]

    def unlink_issue(self, issue_key, link_id):
        self.calls.append(("unlink_issue", issue_key, link_id))
        return {"deleted": link_id}

    def list_queues(self):
        self.calls.append(("list_queues",))
        return [{"key": "TEST"}]

    def list_users(self, email=None, group=None, per_page=None):
        self.calls.append(("list_users", email, group, per_page))
        return [{"id": "user1"}]

    def get_user(self, login_or_uid):
        self.calls.append(("get_user", login_or_uid))
        return {"login": login_or_uid}

    def get_current_user(self):
        self.calls.append(("get_current_user",))
        return {"login": "me"}

    def list_statuses(self):
        self.calls.append(("list_statuses",))
        return [{"key": "open"}]

    def list_issue_types(self):
        self.calls.append(("list_issue_types",))
        return [{"key": "bug"}]

    def list_priorities(self):
        self.calls.append(("list_priorities",))
        return [{"key": "normal"}]

    def list_fields(self):
        self.calls.append(("list_fields",))
        return [{"id": "summary"}]

    def list_link_types(self):
        self.calls.append(("list_link_types",))
        return [{"id": "relates"}]

    def list_queue_versions(self, queue):
        self.calls.append(("list_queue_versions", queue))
        return [{"id": "v1"}]

    def list_queue_components(self, queue):
        self.calls.append(("list_queue_components", queue))
        return [{"id": "c1"}]

    def list_queue_local_fields(self, queue):
        self.calls.append(("list_queue_local_fields", queue))
        return [{"id": "customField"}]

    def list_queue_tags(self, queue):
        self.calls.append(("list_queue_tags", queue))
        return ["backend", "urgent"]

    def get_changelog(self, issue_key, field=None, change_type=None, per_page=None):
        self.calls.append(("get_changelog", issue_key, field, change_type, per_page))
        return [{"id": "cl1"}]

    def list_worklog(self, issue_key):
        self.calls.append(("list_worklog", issue_key))
        return [{"id": "wl1"}]

    def add_worklog(self, issue_key, duration, comment=None, start=None):
        self.calls.append(("add_worklog", issue_key, duration, comment, start))
        return {"id": "wl", "duration": duration}

    def list_checklist(self, issue_key):
        self.calls.append(("list_checklist", issue_key))
        return [{"id": "ci1"}]

    def add_checklist_item(self, issue_key, text, checked=False):
        self.calls.append(("add_checklist_item", issue_key, text, checked))
        return {"id": "ci", "text": text}

    def list_attachments(self, issue_key):
        self.calls.append(("list_attachments", issue_key))
        return [{"id": "att1"}]

    def download_attachment(self, issue_key, attachment_id, dest_dir, filename=None):
        self.calls.append(("download_attachment", issue_key, attachment_id, dest_dir, filename))
        return {"path": f"{dest_dir}/a.txt"}

    def upload_attachment(self, issue_key, file_path, filename=None):
        self.calls.append(("upload_attachment", issue_key, file_path, filename))
        return {"id": "att-new"}

    def delete_attachment(self, issue_key, attachment_id):
        self.calls.append(("delete_attachment", issue_key, attachment_id))
        return {"deleted": attachment_id, "issue": issue_key}


class ServerTests(unittest.TestCase):
    def test_initialize_declares_tools_capability(self):
        server = McpServer(client_factory=FakeClient)

        response = server.handle_message(
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
        )

        result = response["result"]
        self.assertEqual(result["serverInfo"]["name"], "mcp-yandex-tracker")
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

    def test_tools_list_exposes_link_and_dictionary_tools(self):
        server = McpServer(client_factory=FakeClient)

        response = server.handle_message({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})

        names = {tool["name"] for tool in response["result"]["tools"]}
        for name in (
            "tracker_link_issues",
            "tracker_list_links",
            "tracker_unlink_issues",
            "tracker_list_queues",
            "tracker_list_users",
            "tracker_list_link_types",
            "tracker_list_queue_versions",
            "tracker_list_queue_components",
        ):
            self.assertIn(name, names)

    def test_tools_list_exposes_activity_tools(self):
        server = McpServer(client_factory=FakeClient)

        response = server.handle_message({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})

        names = {tool["name"] for tool in response["result"]["tools"]}
        for name in (
            "tracker_get_changelog",
            "tracker_list_worklog",
            "tracker_add_worklog",
            "tracker_list_checklist",
            "tracker_add_checklist_item",
            "tracker_list_attachments",
            "tracker_download_attachment",
            "tracker_upload_attachment",
        ):
            self.assertIn(name, names)

    def test_tools_list_exposes_native_sdk_tools(self):
        server = McpServer(client_factory=FakeClient)

        response = server.handle_message({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})

        names = {tool["name"] for tool in response["result"]["tools"]}
        for name in (
            "tracker_get_user",
            "tracker_get_current_user",
            "tracker_delete_comment",
            "tracker_delete_attachment",
            "tracker_list_queue_local_fields",
            "tracker_list_queue_tags",
        ):
            self.assertIn(name, names)

    def test_native_sdk_tools_route_to_client(self):
        cases = [
            (
                "tracker_get_user",
                {"login_or_uid": "jsmith"},
                ("get_user", "jsmith"),
            ),
            (
                "tracker_get_current_user",
                {},
                ("get_current_user",),
            ),
            (
                "tracker_delete_comment",
                {"issue_key": "TEST-1", "comment_id": "5"},
                ("delete_comment", "TEST-1", "5"),
            ),
            (
                "tracker_delete_attachment",
                {"issue_key": "TEST-1", "attachment_id": "att1"},
                ("delete_attachment", "TEST-1", "att1"),
            ),
            (
                "tracker_list_queue_local_fields",
                {"queue": "TEST"},
                ("list_queue_local_fields", "TEST"),
            ),
            (
                "tracker_list_queue_tags",
                {"queue": "TEST"},
                ("list_queue_tags", "TEST"),
            ),
            (
                "tracker_list_users",
                {"email": "a@b.c", "group": "42", "per_page": 50},
                ("list_users", "a@b.c", "42", 50),
            ),
            (
                "tracker_get_changelog",
                {"issue_key": "TEST-1", "field": "status", "type": "IssueWorkflow"},
                ("get_changelog", "TEST-1", "status", "IssueWorkflow", None),
            ),
        ]
        for tool_name, arguments, expected_call in cases:
            with self.subTest(tool=tool_name):
                fake = FakeClient()
                server = McpServer(client_factory=lambda fake=fake: fake)

                response = server.handle_message(
                    {
                        "jsonrpc": "2.0",
                        "id": 20,
                        "method": "tools/call",
                        "params": {"name": tool_name, "arguments": arguments},
                    }
                )

                self.assertFalse(response["result"]["isError"])
                self.assertEqual(fake.calls, [expected_call])

    def test_upload_attachment_routes_to_client(self):
        fake = FakeClient()
        server = McpServer(client_factory=lambda: fake)

        response = server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 13,
                "method": "tools/call",
                "params": {
                    "name": "tracker_upload_attachment",
                    "arguments": {"issue_key": "TEST-1", "file_path": "/tmp/up.txt"},
                },
            }
        )

        self.assertFalse(response["result"]["isError"])
        self.assertEqual(
            fake.calls,
            [("upload_attachment", "TEST-1", "/tmp/up.txt", None)],
        )

    def test_download_attachment_routes_to_client(self):
        fake = FakeClient()
        server = McpServer(client_factory=lambda: fake)

        response = server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 12,
                "method": "tools/call",
                "params": {
                    "name": "tracker_download_attachment",
                    "arguments": {
                        "issue_key": "TEST-1",
                        "attachment_id": "att1",
                        "dest_dir": "/tmp/dl",
                    },
                },
            }
        )

        self.assertFalse(response["result"]["isError"])
        self.assertEqual(
            fake.calls,
            [("download_attachment", "TEST-1", "att1", "/tmp/dl", None)],
        )

    def test_search_invalid_per_page_is_tool_error(self):
        server = McpServer(client_factory=FakeClient)

        response = server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 10,
                "method": "tools/call",
                "params": {
                    "name": "tracker_search_issues",
                    "arguments": {"query": "Queue: TEST", "per_page": "abc"},
                },
            }
        )

        self.assertNotIn("error", response)
        self.assertTrue(response["result"]["isError"])
        self.assertIn("must be an integer", response["result"]["content"][0]["text"])

    def test_add_worklog_routes_to_client(self):
        fake = FakeClient()
        server = McpServer(client_factory=lambda: fake)

        response = server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 11,
                "method": "tools/call",
                "params": {
                    "name": "tracker_add_worklog",
                    "arguments": {"issue_key": "TEST-1", "duration": "PT1H", "comment": "x"},
                },
            }
        )

        self.assertFalse(response["result"]["isError"])
        self.assertEqual(fake.calls, [("add_worklog", "TEST-1", "PT1H", "x", None)])

    def test_link_issues_routes_to_client(self):
        fake = FakeClient()
        server = McpServer(client_factory=lambda: fake)

        response = server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 7,
                "method": "tools/call",
                "params": {
                    "name": "tracker_link_issues",
                    "arguments": {
                        "issue_key": "TEST-1",
                        "relationship": "relates",
                        "target_issue": "TEST-2",
                    },
                },
            }
        )

        self.assertFalse(response["result"]["isError"])
        self.assertEqual(fake.calls, [("link_issue", "TEST-1", "relates", "TEST-2")])

    def test_unlink_issues_routes_to_client(self):
        fake = FakeClient()
        server = McpServer(client_factory=lambda: fake)

        response = server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 8,
                "method": "tools/call",
                "params": {
                    "name": "tracker_unlink_issues",
                    "arguments": {"issue_key": "TEST-1", "link_id": "100"},
                },
            }
        )

        self.assertFalse(response["result"]["isError"])
        self.assertEqual(fake.calls, [("unlink_issue", "TEST-1", "100")])

    def test_list_queue_versions_routes_to_client(self):
        fake = FakeClient()
        server = McpServer(client_factory=lambda: fake)

        response = server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 9,
                "method": "tools/call",
                "params": {
                    "name": "tracker_list_queue_versions",
                    "arguments": {"queue": "TEST"},
                },
            }
        )

        self.assertFalse(response["result"]["isError"])
        self.assertEqual(fake.calls, [("list_queue_versions", "TEST")])

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

    def test_stdio_preserves_cyrillic_over_non_utf8_locale_streams(self):
        # Regression: on Windows, sys.stdin/sys.stdout default to the locale
        # code page (e.g. cp1251). The MCP transport is UTF-8, so a Cyrillic
        # payload must survive even when the stream objects were created with a
        # non-UTF-8 encoding. serve_stdio pins them to UTF-8.
        text = "клик по лого → сброс дашборда «на главную»"
        request = (
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 7,
                    "method": "tools/call",
                    "params": {
                        "name": "tracker_add_comment",
                        "arguments": {"issue_key": "TEST-1", "text": text},
                    },
                },
                ensure_ascii=False,
            )
            + "\n"
        ).encode("utf-8")

        input_stream = io.TextIOWrapper(io.BytesIO(request), encoding="cp1251", newline="")
        out_bytes = io.BytesIO()
        output_stream = io.TextIOWrapper(out_bytes, encoding="cp1251", newline="")

        serve_stdio(input_stream, output_stream, McpServer(client_factory=FakeClient))
        output_stream.flush()

        # Wire bytes must be valid UTF-8 and preserve the original text.
        response = json.loads(out_bytes.getvalue().decode("utf-8"))
        inner = json.loads(response["result"]["content"][0]["text"])
        self.assertEqual(inner["text"], text)


if __name__ == "__main__":
    unittest.main()
