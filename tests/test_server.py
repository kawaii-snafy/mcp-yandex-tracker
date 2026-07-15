import json
import unittest

from mcp.server.fastmcp.exceptions import ResourceError, ToolError

import mcp_yandex_tracker as server
from mcp_yandex_tracker import TrackerApiError, TrackerConfigError, YandexTrackerClient


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


def _use_client(client):
    """Point the server's lazy singleton at a specific (fake) client."""
    server._client = None
    server._client_factory = lambda: client


class ServerTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.fake = FakeClient()
        _use_client(self.fake)

    def tearDown(self):
        server._client = None
        server._client_factory = YandexTrackerClient

    async def _text(self, name, arguments):
        content = await server.mcp.call_tool(name, arguments)
        # structured_output=False makes every tool return a single text block.
        self.assertEqual(len(content), 1)
        self.assertEqual(content[0].type, "text")
        return content[0].text

    # --- Discovery ---------------------------------------------------------
    async def test_exposes_all_tracker_tools(self):
        tools = await server.mcp.list_tools()
        names = {tool.name for tool in tools}
        self.assertEqual(len(tools), 35)
        for name in (
            "tracker_get_issue",
            "tracker_search_issues",
            "tracker_add_comment",
            "tracker_list_transitions",
            "tracker_move_issue_status",
            "tracker_link_issues",
            "tracker_list_links",
            "tracker_unlink_issues",
            "tracker_list_queues",
            "tracker_list_users",
            "tracker_list_link_types",
            "tracker_list_queue_versions",
            "tracker_list_queue_components",
            "tracker_get_changelog",
            "tracker_list_worklog",
            "tracker_add_worklog",
            "tracker_list_checklist",
            "tracker_add_checklist_item",
            "tracker_list_attachments",
            "tracker_download_attachment",
            "tracker_upload_attachment",
            "tracker_get_user",
            "tracker_get_current_user",
            "tracker_delete_comment",
            "tracker_delete_attachment",
            "tracker_list_queue_local_fields",
            "tracker_list_queue_tags",
        ):
            self.assertIn(name, names)

    async def test_tools_have_no_output_schema(self):
        # Token optimization: text-only responses (structured_output=False) must
        # not publish an output schema or a duplicating structuredContent block.
        tools = await server.mcp.list_tools()
        with_schema = [tool.name for tool in tools if tool.outputSchema is not None]
        self.assertEqual(with_schema, [])

    async def test_required_arguments_are_declared(self):
        tools = {tool.name: tool for tool in await server.mcp.list_tools()}
        self.assertEqual(
            tools["tracker_get_issue"].inputSchema.get("required"), ["issue_key"]
        )
        self.assertEqual(
            tools["tracker_create_issue"].inputSchema.get("required"),
            ["queue", "summary"],
        )

    # --- Routing -----------------------------------------------------------
    async def test_get_issue_returns_compact_text(self):
        text = await self._text("tracker_get_issue", {"issue_key": "TEST-1"})
        self.assertIn('"key":"TEST-1"', text)
        self.assertEqual(self.fake.calls, [("get_issue", "TEST-1")])

    async def test_tools_route_to_client(self):
        cases = [
            ("tracker_get_user", {"login_or_uid": "jsmith"}, ("get_user", "jsmith")),
            ("tracker_get_current_user", {}, ("get_current_user",)),
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
            ("tracker_list_queue_tags", {"queue": "TEST"}, ("list_queue_tags", "TEST")),
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
            (
                "tracker_link_issues",
                {"issue_key": "TEST-1", "relationship": "relates", "target_issue": "TEST-2"},
                ("link_issue", "TEST-1", "relates", "TEST-2"),
            ),
            (
                "tracker_unlink_issues",
                {"issue_key": "TEST-1", "link_id": "100"},
                ("unlink_issue", "TEST-1", "100"),
            ),
            (
                "tracker_list_queue_versions",
                {"queue": "TEST"},
                ("list_queue_versions", "TEST"),
            ),
            (
                "tracker_move_issue_status",
                {"issue_key": "TEST-1", "status": "inProgress", "fields": {"comment": "starting"}},
                ("move_issue_status", "TEST-1", "inProgress", {"comment": "starting"}),
            ),
            (
                "tracker_add_worklog",
                {"issue_key": "TEST-1", "duration": "PT1H", "comment": "x"},
                ("add_worklog", "TEST-1", "PT1H", "x", None),
            ),
            (
                "tracker_upload_attachment",
                {"issue_key": "TEST-1", "file_path": "/tmp/up.txt"},
                ("upload_attachment", "TEST-1", "/tmp/up.txt", None),
            ),
            (
                "tracker_download_attachment",
                {"issue_key": "TEST-1", "attachment_id": "att1", "dest_dir": "/tmp/dl"},
                ("download_attachment", "TEST-1", "att1", "/tmp/dl", None),
            ),
        ]
        for tool_name, arguments, expected_call in cases:
            with self.subTest(tool=tool_name):
                fake = FakeClient()
                _use_client(fake)
                await server.mcp.call_tool(tool_name, arguments)
                self.assertEqual(fake.calls, [expected_call])

    async def test_cyrillic_text_survives_round_trip(self):
        # ensure_ascii=False keeps Cyrillic intact in the response payload.
        text = "клик по лого → сброс дашборда «на главную»"
        result = await self._text(
            "tracker_add_comment", {"issue_key": "TEST-1", "text": text}
        )
        self.assertEqual(json.loads(result)["text"], text)

    # --- Resources ---------------------------------------------------------
    async def test_resources_and_template_listed(self):
        static = {str(r.uri) for r in await server.mcp.list_resources()}
        templates = {t.uriTemplate for t in await server.mcp.list_resource_templates()}
        self.assertEqual(
            static,
            {
                "tracker://queues",
                "tracker://statuses",
                "tracker://priorities",
                "tracker://issue-types",
                "tracker://fields",
                "tracker://link-types",
            },
        )
        self.assertIn("tracker://issue/{key}", templates)

    async def test_issue_resource_reads_via_client(self):
        contents = list(await server.mcp.read_resource("tracker://issue/TEST-1"))
        self.assertEqual(contents[0].mime_type, "application/json")
        self.assertIn('"key":"TEST-1"', contents[0].content)
        self.assertEqual(self.fake.calls, [("get_issue", "TEST-1")])

    async def test_reference_resource_reads_via_client(self):
        contents = list(await server.mcp.read_resource("tracker://statuses"))
        self.assertEqual(json.loads(contents[0].content), [{"key": "open"}])
        self.assertEqual(self.fake.calls, [("list_statuses",)])

    async def test_resource_error_surfaces_message(self):
        # The resource wrapper maps a domain error to ResourceError, so the read
        # carries a clean message instead of leaking the raw internal error.
        class Boom:
            def list_statuses(self):
                raise TrackerApiError(500, "boom")

        _use_client(Boom())
        with self.assertRaises(ResourceError) as ctx:
            await server.mcp.read_resource("tracker://statuses")
        self.assertIn("boom", str(ctx.exception))

    # --- Errors ------------------------------------------------------------
    async def test_missing_required_argument_is_tool_error(self):
        with self.assertRaises(ToolError):
            await server.mcp.call_tool("tracker_get_issue", {})

    async def test_invalid_per_page_is_tool_error(self):
        with self.assertRaises(ToolError):
            await server.mcp.call_tool(
                "tracker_search_issues", {"query": "Queue: TEST", "per_page": "abc"}
            )

    async def test_api_error_surfaces_message(self):
        class Boom:
            def get_issue(self, issue_key):
                raise TrackerApiError(404, "not found")

        _use_client(Boom())
        with self.assertRaises(ToolError) as ctx:
            await server.mcp.call_tool("tracker_get_issue", {"issue_key": "TEST-1"})
        self.assertIn("not found", str(ctx.exception))

    async def test_client_configuration_error_surfaces_message(self):
        def broken_factory():
            raise TrackerConfigError("missing token")

        server._client = None
        server._client_factory = broken_factory
        with self.assertRaises(ToolError) as ctx:
            await server.mcp.call_tool("tracker_get_issue", {"issue_key": "TEST-1"})
        self.assertIn("missing token", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
