import json
import os
import tempfile
import unittest

import requests

from mcp_yandex_tracker import Tracker, TrackerApiError, TrackerConfig, TrackerConfigError
from mcp_yandex_tracker.client import given


class FakeResponse:
    """Stands in for requests.Response — only what the transport actually reads."""

    def __init__(self, status_code=200, json_body=None, text=None, chunks=None, reason="OK"):
        self.status_code = status_code
        self.reason = reason
        self._json_body = json_body
        self._chunks = chunks or []
        if text is not None:
            self.text = text
        elif json_body is not None:
            self.text = json.dumps(json_body)
        else:
            self.text = ""
        self.content = b"".join(self._chunks) if self._chunks else self.text.encode()
        self.closed = False

    def json(self):
        if self._json_body is None:
            raise ValueError("no json")
        return self._json_body

    def iter_content(self, chunk_size):
        return iter(self._chunks)

    def close(self):
        self.closed = True


class FakeSession:
    """Records every call and replays queued responses in order."""

    def __init__(self, *responses):
        self.headers = {}
        self.calls = []
        self._responses = list(responses) or [FakeResponse(json_body={})]

    def request(self, method, url, **kwargs):
        self.calls.append({"method": method, "url": url, **kwargs})
        if len(self._responses) > 1:
            return self._responses.pop(0)
        return self._responses[0]

    @property
    def last(self):
        return self.calls[-1]


def _config(**overrides):
    values = {"token": "tkn", "org_id": "42"}
    values.update(overrides)
    return TrackerConfig(**values)


def _client(*responses, config=None):
    session = FakeSession(*responses)
    return Tracker(config=config or _config(), session=session), session


class ConfigTests(unittest.TestCase):
    def test_requires_token_and_one_org_id(self):
        with self.assertRaises(TrackerConfigError):
            TrackerConfig.from_env({})
        with self.assertRaises(TrackerConfigError):
            TrackerConfig.from_env({"YANDEX_TRACKER_TOKEN": "tkn"})

    def test_reads_every_supported_variable(self):
        config = TrackerConfig.from_env(
            {
                "YANDEX_TRACKER_TOKEN": "tkn",
                "YANDEX_TRACKER_CLOUD_ORG_ID": "cloud-1",
                "YANDEX_TRACKER_AUTH_SCHEME": "Bearer",
                "YANDEX_TRACKER_BASE_URL": "https://tracker.example/",
                "YANDEX_TRACKER_TIMEOUT": "5",
            }
        )
        self.assertEqual(config.token, "tkn")
        self.assertEqual(config.cloud_org_id, "cloud-1")
        self.assertEqual(config.auth_scheme, "Bearer")
        self.assertEqual(config.base_url, "https://tracker.example")
        self.assertEqual(config.timeout, 5.0)

    def test_api_root_always_targets_v3(self):
        # A /v2 or /v3 suffix left over in an old config is dropped: the version
        # belongs to the path this client builds, not to the configured host.
        for base in ("https://api.tracker.yandex.net", "https://api.tracker.yandex.net/v2"):
            self.assertEqual(
                _config(base_url=base).api_root, "https://api.tracker.yandex.net/v3"
            )

    def test_oauth_scheme_and_org_header(self):
        headers = _config().headers()
        self.assertEqual(headers["Authorization"], "OAuth tkn")
        self.assertEqual(headers["X-Org-Id"], "42")
        self.assertNotIn("X-Cloud-Org-Id", headers)

    def test_cloud_org_wins_and_bearer_scheme_passes_through(self):
        headers = _config(cloud_org_id="cloud-1", auth_scheme="Bearer").headers()
        self.assertEqual(headers["Authorization"], "Bearer tkn")
        self.assertEqual(headers["X-Cloud-Org-Id"], "cloud-1")
        self.assertNotIn("X-Org-Id", headers)


class GivenTests(unittest.TestCase):
    def test_drops_only_none(self):
        self.assertEqual(
            given(a=1, b=None, c=False, d=""),
            {"a": 1, "c": False, "d": ""},
        )


class RequestTests(unittest.TestCase):
    def test_builds_a_v3_url_and_passes_the_timeout(self):
        client, session = _client(FakeResponse(json_body={"key": "TEST-1"}))
        self.assertEqual(client.request("GET", "/issues/TEST-1"), {"key": "TEST-1"})
        self.assertEqual(session.last["method"], "GET")
        self.assertEqual(session.last["url"], "https://api.tracker.yandex.net/v3/issues/TEST-1")
        self.assertEqual(session.last["timeout"], 30.0)

    def test_sends_params_and_body(self):
        client, session = _client()
        client.request("POST", "/issues/_search", params={"perPage": 5}, json={"queue": "TEST"})
        self.assertEqual(session.last["params"], {"perPage": 5})
        self.assertEqual(session.last["json"], {"queue": "TEST"})

    def test_booleans_go_out_lowercase(self):
        # requests would urlencode a Python bool as True/False; every documented
        # boolean parameter is a JSON boolean.
        client, session = _client()
        client.request("POST", "/issues/", params={"notify": False})
        self.assertEqual(session.last["params"], {"notify": "false"})
        client.request("GET", "/priorities", params={"localized": True})
        self.assertEqual(session.last["params"], {"localized": "true"})

    def test_booleans_inside_a_repeated_key_are_converted_too(self):
        client, session = _client()
        client.request("GET", "/worklog", params={"createdAt": ["from:x", True]})
        self.assertEqual(session.last["params"], {"createdAt": ["from:x", "true"]})

    def test_empty_params_are_not_sent(self):
        client, session = _client()
        client.request("GET", "/users")
        self.assertIsNone(session.last["params"])

    def test_no_content_decodes_to_none(self):
        client, _ = _client(FakeResponse(status_code=204))
        self.assertIsNone(client.request("DELETE", "/issues/TEST-1/comments/1"))

    def test_non_json_body_falls_back_to_text(self):
        client, _ = _client(FakeResponse(text="plain"))
        self.assertEqual(client.request("GET", "/whatever"), "plain")

    def test_session_carries_the_auth_headers(self):
        # The real session is built once and reused, so the headers must live on
        # it rather than being rebuilt per request.
        client = Tracker(config=_config(cloud_org_id="cloud-1"))
        self.assertEqual(client._session.headers["X-Cloud-Org-Id"], "cloud-1")


class ErrorTests(unittest.TestCase):
    def test_error_messages_field_becomes_the_message(self):
        body = {"errorMessages": ["Issue not found"], "statusCode": 404}
        client, _ = _client(FakeResponse(status_code=404, json_body=body, reason="Not Found"))
        with self.assertRaises(TrackerApiError) as ctx:
            client.request("GET", "/issues/NOPE-1")
        self.assertEqual(ctx.exception.status, 404)
        self.assertIn("Issue not found", str(ctx.exception))
        self.assertEqual(ctx.exception.payload, body)

    def test_errors_map_becomes_the_message(self):
        body = {"errors": {"summary": "must not be empty"}}
        client, _ = _client(FakeResponse(status_code=422, json_body=body))
        with self.assertRaises(TrackerApiError) as ctx:
            client.request("POST", "/issues/")
        self.assertIn("summary: must not be empty", str(ctx.exception))

    def test_unknown_error_shape_falls_back_to_the_raw_body(self):
        # The error body shape is not documented, so an unexpected one must still
        # reach the caller instead of being swallowed.
        client, _ = _client(FakeResponse(status_code=500, text="gateway exploded"))
        with self.assertRaises(TrackerApiError) as ctx:
            client.request("GET", "/issues/TEST-1")
        self.assertIn("gateway exploded", str(ctx.exception))

    def test_empty_error_body_falls_back_to_the_reason(self):
        client, _ = _client(FakeResponse(status_code=403, text="", reason="Forbidden"))
        with self.assertRaises(TrackerApiError) as ctx:
            client.request("GET", "/issues/TEST-1")
        self.assertIn("Forbidden", str(ctx.exception))

    def test_transport_failure_becomes_a_status_zero_api_error(self):
        class Broken:
            headers = {}

            def request(self, *args, **kwargs):
                raise requests.ConnectionError("no route to host")

        client = Tracker(config=_config(), session=Broken())
        with self.assertRaises(TrackerApiError) as ctx:
            client.request("GET", "/issues/TEST-1")
        self.assertEqual(ctx.exception.status, 0)
        self.assertIn("Failed to reach Yandex Tracker", str(ctx.exception))


class DownloadTests(unittest.TestCase):
    def test_streams_to_disk_and_reports_where_it_landed(self):
        client, session = _client(FakeResponse(chunks=[b"abc", b"de"]))
        with tempfile.TemporaryDirectory() as tmp:
            result = client.download("/issues/TEST-1/attachments/7/report.txt", tmp, "report.txt")
            self.assertEqual(result, {"path": os.path.join(tmp, "report.txt"), "name": "report.txt", "size": 5})
            with open(result["path"], "rb") as handle:
                self.assertEqual(handle.read(), b"abcde")
        self.assertTrue(session.last["stream"])

    def test_a_traversing_file_name_cannot_escape_the_destination(self):
        client, _ = _client(FakeResponse(chunks=[b"x"]))
        with tempfile.TemporaryDirectory() as tmp:
            result = client.download("/issues/TEST-1/attachments/7/evil", tmp, "../evil.txt")
            self.assertEqual(os.path.dirname(result["path"]), tmp)
            self.assertEqual(result["name"], "evil.txt")

    def test_creates_the_destination_directory(self):
        client, _ = _client(FakeResponse(chunks=[b"x"]))
        with tempfile.TemporaryDirectory() as tmp:
            nested = os.path.join(tmp, "a", "b")
            result = client.download("/issues/TEST-1/attachments/7/f.txt", nested, "f.txt")
            self.assertTrue(os.path.isfile(result["path"]))


class UploadTests(unittest.TestCase):
    def test_posts_the_file_under_the_documented_part_name(self):
        client, session = _client(FakeResponse(json_body={"id": "7"}))
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "notes.txt")
            with open(path, "wb") as handle:
                handle.write(b"hello")
            client.upload("/issues/TEST-1/attachments/", path, params={"filename": "renamed.txt"})
        self.assertEqual(session.last["method"], "POST")
        self.assertEqual(session.last["params"], {"filename": "renamed.txt"})
        name, handle = session.last["files"]["file"]
        self.assertEqual(name, "notes.txt")

    def test_a_missing_file_is_an_argument_error_not_a_transport_error(self):
        client, session = _client()
        with self.assertRaises(ValueError):
            client.upload("/issues/TEST-1/attachments/", "/no/such/file")
        self.assertEqual(session.calls, [])


if __name__ == "__main__":
    unittest.main()
