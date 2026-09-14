import json
import re
import unittest

from mcp.server.mcpserver.exceptions import ResourceError, ToolError

import mcp_yandex_tracker  # noqa: F401 - importing the package registers the tools
from mcp_yandex_tracker import Tracker, TrackerApiError, TrackerConfigError
from mcp_yandex_tracker import server


class FakeTracker:
    """Records the HTTP call a tool asks for, without making one."""

    def __init__(self, result=None):
        self.calls = []
        self.result = {"ok": True} if result is None else result

    def request(self, method, path, *, params=None, json=None, files=None, headers=None):
        self.calls.append(
            {
                "method": method,
                "path": path,
                # Mirror the real transport, which turns an empty mapping into no
                # query string / no header at all.
                "params": params or None,
                "json": json,
                "files": files,
                "headers": headers or None,
            }
        )
        return self.result

    def upload(self, path, file_path, *, params=None):
        self.calls.append(
            {"method": "POST", "path": path, "params": params, "filePath": file_path}
        )
        return self.result

    def download(self, path, dest_dir, filename):
        self.calls.append(
            {"method": "GET", "path": path, "destDir": dest_dir, "fileName": filename}
        )
        return {"path": f"{dest_dir}/{filename}", "name": filename, "size": 0}

    @property
    def last(self):
        return self.calls[-1]


def _use_client(client):
    """Point the server's lazy singleton at a specific (fake) client.

    This must patch `mcp_yandex_tracker.server`, the module `get_client` actually
    reads its globals from — patching the package would silently leave the real
    client in place and send the suite at a live Tracker.
    """
    server._client = None
    server._client_factory = lambda: client


# Every tool docstring ends with the endpoint it wraps and the page it was
# written from. Both are load-bearing: the tests below hold the code to them.
_ENDPOINT = re.compile(r"^(GET|POST|PATCH|DELETE) (/v3/\S*)$", re.MULTILINE)
_DOC_URL = re.compile(
    r"^https://yandex\.ru/support/tracker/en/api/[\w/-]+\.md$", re.MULTILINE
)


def _sample(name, schema):
    # A stand-in value for a required argument, derived from its declared type.
    # Strings become `<name>` so a path placeholder is recognisable in the URL.
    kind = schema.get("type")
    if kind is None:
        for option in schema.get("anyOf", []):
            if option.get("type") not in (None, "null"):
                kind = option["type"]
                break
    if kind in ("integer", "number"):
        return 1
    if kind == "boolean":
        return True
    if kind == "array":
        return []
    if kind == "object":
        return {}
    return f"<{name}>"


def _required_arguments(tool):
    schema = tool.input_schema
    properties = schema.get("properties", {})
    return {
        name: _sample(name, properties.get(name, {}))
        for name in schema.get("required", [])
    }


class ToolContractTests(unittest.IsolatedAsyncioTestCase):
    """The tool surface must be exactly the documented API surface.

    Rather than restating every endpoint in a fixture, these read the endpoint out
    of each tool's own docstring and then check the tool really issues it. A tool
    whose docstring drifts from its code fails here, and so does one that reaches
    a path nobody documented.
    """

    def setUp(self):
        self.fake = FakeTracker()
        _use_client(self.fake)

    def tearDown(self):
        server._client = None
        server._client_factory = Tracker

    async def test_every_tool_names_its_endpoint_and_its_doc_page(self):
        for tool in await server.mcp.list_tools():
            with self.subTest(tool=tool.name):
                self.assertTrue(tool.name.startswith("tracker_"))
                self.assertIsNotNone(
                    _ENDPOINT.search(tool.description or ""),
                    "docstring must carry a `<METHOD> /v3/<path>` line",
                )
                self.assertIsNotNone(
                    _DOC_URL.search(tool.description or ""),
                    "docstring must link to the documentation page it came from",
                )

    async def test_every_tool_calls_the_endpoint_its_docstring_claims(self):
        for tool in await server.mcp.list_tools():
            with self.subTest(tool=tool.name):
                method, doc_path = _ENDPOINT.search(tool.description).groups()
                arguments = _required_arguments(tool)
                self.fake.calls.clear()
                result = await server.mcp.call_tool(tool.name, arguments)
                self.assertFalse(result.is_error, result.content[0].text if result.content else "")
                self.assertEqual(len(self.fake.calls), 1, "one tool, one request")
                expected = doc_path[len("/v3") :].format(
                    **{k: v for k, v in arguments.items() if isinstance(v, str)}
                )
                self.assertEqual(self.fake.last["method"], method)
                self.assertEqual(self.fake.last["path"], expected)

    async def test_tools_have_no_output_schema(self):
        # structured_output=False: one compact JSON text block, no duplicating
        # structuredContent and no output schema to pay for in every tools/list.
        for tool in await server.mcp.list_tools():
            with self.subTest(tool=tool.name):
                self.assertIsNone(tool.output_schema)

    async def test_optional_arguments_are_omitted_from_the_request(self):
        # `given()` drops unset arguments so Tracker never receives `null` for a
        # parameter the caller simply did not use.
        await server.mcp.call_tool("tracker_get_users", {})
        self.assertIsNone(self.fake.last["params"])
        self.assertIsNone(self.fake.last["json"])

    async def test_optional_arguments_are_sent_when_supplied(self):
        await server.mcp.call_tool("tracker_get_users", {"perPage": 10})
        self.assertEqual(self.fake.last["params"], {"perPage": 10})

    async def test_every_tool_module_is_registered(self):
        # tools/__init__.py registers by importing; a module dropped from that
        # list would silently vanish from the server.
        import importlib

        for module in ("issues", "queues", "boards", "entities", "admin", "users"):
            with self.subTest(module=module):
                names = {
                    name
                    for name in importlib.import_module(
                        f"mcp_yandex_tracker.tools.{module}"
                    ).__dict__
                    if name.startswith("tracker_")
                }
                self.assertTrue(names, f"{module} defines no tools")
                registered = {tool.name for tool in await server.mcp.list_tools()}
                self.assertLessEqual(names, registered)


class DeviationTests(unittest.IsolatedAsyncioTestCase):
    """The handful of places a tool cannot mirror its endpoint byte for byte.

    Each of these is listed in docs/TOOLS.md; they are the only ones, so they are
    pinned here rather than left to the generic contract test above.
    """

    def setUp(self):
        self.fake = FakeTracker()
        _use_client(self.fake)

    def tearDown(self):
        server._client = None
        server._client_factory = Tracker

    async def test_from_underscore_reaches_tracker_as_from(self):
        # `from` is a Python keyword, so the argument is spelled from_ — but the
        # query string must still say `from`.
        await server.mcp.call_tool(
            "tracker_get_entity_events",
            {"entityType": "project", "entityId": "1", "from_": "2026-01-01"},
        )
        self.assertEqual(self.fake.last["params"].get("from"), "2026-01-01")
        self.assertNotIn("from_", self.fake.last["params"])

    async def test_if_match_carries_the_version_of_a_board_edit(self):
        # The board, column and sprint pages document optimistic locking as a
        # header rather than a parameter.
        await server.mcp.call_tool("tracker_patch_board", {"boardId": "42", "version": 7})
        self.assertEqual(self.fake.last["headers"], {"If-Match": '"7"'})

    async def test_omitting_the_version_sends_no_if_match(self):
        await server.mcp.call_tool("tracker_patch_board", {"boardId": "42", "name": "Board"})
        self.assertIsNone(self.fake.last["headers"])

    async def test_query_parameter_version_stays_a_query_parameter(self):
        # Where a page documents `version` as a real query parameter, it must not
        # become a header.
        await server.mcp.call_tool("tracker_patch_issue", {"issueId": "TEST-1", "version": 3})
        self.assertEqual(self.fake.last["params"], {"version": 3})
        self.assertIsNone(self.fake.last["headers"])

    async def test_download_streams_to_the_requested_directory(self):
        result = await server.mcp.call_tool(
            "tracker_get_attachment",
            {"issueId": "TEST-1", "fileId": "7", "fileName": "report.txt", "destDir": "/tmp/x"},
        )
        self.assertEqual(self.fake.last["path"], "/issues/TEST-1/attachments/7/report.txt")
        self.assertEqual(self.fake.last["destDir"], "/tmp/x")
        self.assertEqual(self.fake.last["fileName"], "report.txt")
        self.assertEqual(json.loads(result.content[0].text)["name"], "report.txt")

    async def test_download_honours_a_local_name_override(self):
        await server.mcp.call_tool(
            "tracker_get_attachment",
            {
                "issueId": "TEST-1",
                "fileId": "7",
                "fileName": "report.txt",
                "destDir": "/tmp/x",
                "saveAs": "local.txt",
            },
        )
        self.assertEqual(self.fake.last["fileName"], "local.txt")
        # The remote path still uses the name Tracker knows the file by.
        self.assertTrue(self.fake.last["path"].endswith("/report.txt"))

    async def test_upload_sends_the_local_path_and_the_rename_parameter(self):
        await server.mcp.call_tool(
            "tracker_post_attachment",
            {"issueId": "TEST-1", "filePath": "/tmp/a.txt", "filename": "b.txt"},
        )
        self.assertEqual(self.fake.last["path"], "/issues/TEST-1/attachments/")
        self.assertEqual(self.fake.last["filePath"], "/tmp/a.txt")
        self.assertEqual(self.fake.last["params"], {"filename": "b.txt"})


class ProtocolTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.fake = FakeTracker()
        _use_client(self.fake)

    def tearDown(self):
        server._client = None
        server._client_factory = Tracker

    async def _text(self, name, arguments):
        result = await server.mcp.call_tool(name, arguments)
        # structured_output=False makes every tool return a single text block.
        self.assertFalse(result.is_error)
        self.assertEqual(len(result.content), 1)
        self.assertEqual(result.content[0].type, "text")
        return result.content[0].text

    async def test_tool_returns_the_payload_untouched(self):
        # No projection, no field stripping: whatever Tracker sent is what the
        # agent sees, `self` links and all.
        payload = {"self": "https://api.tracker.yandex.net/v3/issues/TEST-1", "key": "TEST-1"}
        _use_client(FakeTracker(payload))
        text = await self._text("tracker_get_issue", {"issueId": "TEST-1"})
        self.assertEqual(json.loads(text), payload)

    async def test_cyrillic_survives_the_round_trip(self):
        _use_client(FakeTracker({"summary": "Тестовая задача"}))
        text = await self._text("tracker_get_issue", {"issueId": "TEST-1"})
        self.assertIn("Тестовая задача", text)
        self.assertEqual(json.loads(text)["summary"], "Тестовая задача")

    async def test_missing_required_argument_is_rejected(self):
        with self.assertRaises(Exception):
            await server.mcp.call_tool("tracker_get_issue", {})

    async def test_empty_required_string_is_rejected(self):
        with self.assertRaises(Exception):
            await server.mcp.call_tool("tracker_get_issue", {"issueId": ""})

    async def test_api_error_surfaces_as_a_tool_error(self):
        class Boom:
            def request(self, *args, **kwargs):
                raise TrackerApiError(404, "Issue not found")

        _use_client(Boom())
        with self.assertRaises(ToolError) as ctx:
            await server.mcp.call_tool("tracker_get_issue", {"issueId": "TEST-1"})
        self.assertIn("Issue not found", str(ctx.exception))

    async def test_config_error_surfaces_as_a_tool_error(self):
        def broken_factory():
            raise TrackerConfigError("missing token")

        server._client = None
        server._client_factory = broken_factory
        with self.assertRaises(ToolError) as ctx:
            await server.mcp.call_tool("tracker_get_issue", {"issueId": "TEST-1"})
        self.assertIn("missing token", str(ctx.exception))


class ResourceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.fake = FakeTracker()
        _use_client(self.fake)

    def tearDown(self):
        server._client = None
        server._client_factory = Tracker

    async def test_lists_the_static_resources_and_the_issue_template(self):
        uris = {str(resource.uri) for resource in await server.mcp.list_resources()}
        self.assertEqual(
            uris,
            {
                "tracker://queues",
                "tracker://statuses",
                "tracker://priorities",
                "tracker://issue-types",
                "tracker://fields",
            },
        )
        templates = {str(item.uri_template) for item in await server.mcp.list_resource_templates()}
        self.assertIn("tracker://issue/{key}", templates)

    async def test_reading_a_resource_hits_the_documented_endpoint(self):
        _use_client(FakeTracker([{"key": "TEST"}]))
        contents = await server.mcp.read_resource("tracker://statuses")
        self.assertEqual(json.loads(list(contents)[0].content), [{"key": "TEST"}])

    async def test_resource_error_surfaces_the_tracker_message(self):
        class Boom:
            def request(self, *args, **kwargs):
                raise TrackerApiError(500, "boom")

        _use_client(Boom())
        with self.assertRaises(ResourceError) as ctx:
            await server.mcp.read_resource("tracker://statuses")
        self.assertIn("boom", str(ctx.exception))


class StdioTests(unittest.IsolatedAsyncioTestCase):
    async def test_stdio_transport_preserves_cyrillic(self):
        # End-to-end guard for the UTF-8 stdio path (MCPServer's stdio_server pins
        # UTF-8). Spawns the real server and round-trips a Cyrillic tool name
        # through the byte transport — it must come back intact in the error
        # message. Needs no Tracker credentials since an unknown-tool call never
        # reaches the API.
        import sys

        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        name = "задача_кириллица_проверка"
        params = StdioServerParameters(command=sys.executable, args=["-m", "mcp_yandex_tracker"])
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(name, {})
        self.assertTrue(result.is_error)
        self.assertIn(name, result.content[0].text)


if __name__ == "__main__":
    unittest.main()
