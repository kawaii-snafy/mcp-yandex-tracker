import unittest

from yandex_tracker_mcp_server.client import (
    TrackerConfig,
    TrackerConfigError,
    YandexTrackerClient,
    _tracker_client_kwargs,
)


class FakeCollection:
    def __init__(self, items=None):
        self.items = items or {}
        self.created = []
        self.find_calls = []

    def __getitem__(self, key):
        return self.items[key]

    def create(self, **kwargs):
        self.created.append(kwargs)
        return kwargs

    def find(self, **kwargs):
        self.find_calls.append(kwargs)
        return [{"key": "TEST-1"}]


class FakeTransition:
    def __init__(self, transition_id, display, to):
        self.id = transition_id
        self.display = display
        self.to = to
        self.executions = []

    def execute(self, **kwargs):
        self.executions.append(kwargs)
        return [{"id": "next", "to": {"key": "closed"}}]

    def as_dict(self):
        return {"id": self.id, "display": self.display, "to": self.to}


class FakeTransitionCollection:
    def __init__(self, transitions):
        self.transitions = {transition.id: transition for transition in transitions}

    def __getitem__(self, key):
        return self.transitions[key]

    def get_all(self):
        return list(self.transitions.values())


class FakeComments:
    def __init__(self):
        self.created = []

    def create(self, **kwargs):
        self.created.append(kwargs)
        return {"id": 1, **kwargs}

    def get_all(self):
        return [{"id": 1, "text": "hello"}]


class FakeIssue:
    def __init__(self, key, transitions=None):
        self.key = key
        self.comments = FakeComments()
        self.transitions = FakeTransitionCollection(transitions or [])
        self.updated = []

    def update(self, **kwargs):
        self.updated.append(kwargs)
        return {"key": self.key, **kwargs}

    def as_dict(self):
        return {"key": self.key}


class FakeSdkClient:
    def __init__(self, issue):
        self.issue = issue
        self.issues = FakeCollection({issue.key: issue})


class ClientTests(unittest.TestCase):
    def test_env_config_requires_token_and_org(self):
        with self.assertRaises(TrackerConfigError):
            TrackerConfig.from_env({})
        with self.assertRaises(TrackerConfigError):
            TrackerConfig.from_env({"YANDEX_TRACKER_TOKEN": "secret"})

    def test_env_config_accepts_tracker_env(self):
        config = TrackerConfig.from_env(
            {
                "YANDEX_TRACKER_TOKEN": "secret",
                "YANDEX_TRACKER_CLOUD_ORG_ID": "cloud",
                "YANDEX_TRACKER_BASE_URL": "https://tracker.test/v2/",
                "YANDEX_TRACKER_AUTH_SCHEME": "Bearer",
                "YANDEX_TRACKER_TIMEOUT": "12.5",
            }
        )

        self.assertEqual(config.token, "secret")
        self.assertEqual(config.cloud_org_id, "cloud")
        self.assertEqual(config.base_url, "https://tracker.test/v2")
        self.assertEqual(config.auth_scheme, "Bearer")
        self.assertEqual(config.timeout, 12.5)

    def test_tracker_client_kwargs_preserve_auth_and_base_url(self):
        config = TrackerConfig(
            token="secret",
            cloud_org_id="cloud",
            base_url="https://tracker.test/v2",
            auth_scheme="Bearer",
            timeout=12.5,
        )

        self.assertEqual(
            _tracker_client_kwargs(config),
            {
                "iam_token": "secret",
                "cloud_org_id": "cloud",
                "base_url": "https://tracker.test",
                "api_version": "v2",
                "timeout": 12.5,
            },
        )

    def test_get_issue_reads_from_official_sdk_collection(self):
        issue = FakeIssue("TEST-1")
        client = YandexTrackerClient(tracker_client=FakeSdkClient(issue))

        self.assertEqual(client.get_issue("TEST-1"), {"key": "TEST-1"})

    def test_search_issues_uses_official_sdk_find(self):
        issue = FakeIssue("TEST-1")
        sdk_client = FakeSdkClient(issue)
        client = YandexTrackerClient(tracker_client=sdk_client)

        result = client.search_issues(query="Queue: TEST", filter={"status": "open"}, per_page=5, page=2)

        self.assertEqual(result, [{"key": "TEST-1"}])
        self.assertEqual(
            sdk_client.issues.find_calls,
            [
                {
                    "query": "Queue: TEST",
                    "filter": {"status": "open"},
                    "order": None,
                    "keys": None,
                    "per_page": 5,
                    "page": 2,
                }
            ],
        )

    def test_update_issue_uses_official_sdk_issue_update(self):
        issue = FakeIssue("TEST-1")
        client = YandexTrackerClient(tracker_client=FakeSdkClient(issue))

        self.assertEqual(client.update_issue("TEST-1", {"summary": "new"}), {"key": "TEST-1", "summary": "new"})
        self.assertEqual(issue.updated, [{"summary": "new"}])

    def test_comments_use_official_sdk_issue_comments(self):
        issue = FakeIssue("TEST-1")
        client = YandexTrackerClient(tracker_client=FakeSdkClient(issue))

        self.assertEqual(client.add_comment("TEST-1", "hello"), {"id": 1, "text": "hello"})
        self.assertEqual(client.list_comments("TEST-1"), [{"id": 1, "text": "hello"}])
        self.assertEqual(issue.comments.created, [{"text": "hello"}])

    def test_move_issue_status_executes_matching_transition(self):
        start = FakeTransition(
            "start_progress",
            "Start progress",
            {"key": "inProgress", "display": "In progress"},
        )
        issue = FakeIssue("TEST-1", [FakeTransition("close", "Close", {"key": "closed"}), start])
        client = YandexTrackerClient(tracker_client=FakeSdkClient(issue))

        result = client.move_issue_status(
            "TEST-1",
            "In progress",
            fields={"comment": "starting"},
        )

        self.assertEqual(result, [{"id": "next", "to": {"key": "closed"}}])
        self.assertEqual(start.executions, [{"comment": "starting"}])

    def test_execute_transition_uses_official_sdk_transition(self):
        close = FakeTransition("close", "Close", {"key": "closed"})
        issue = FakeIssue("TEST-1", [close])
        client = YandexTrackerClient(tracker_client=FakeSdkClient(issue))

        client.execute_transition("TEST-1", "close", {"resolution": "fixed"})

        self.assertEqual(close.executions, [{"resolution": "fixed"}])


if __name__ == "__main__":
    unittest.main()
