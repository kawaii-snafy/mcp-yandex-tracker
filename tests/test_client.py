import unittest

from mcp_yandex_tracker import (
    TrackerApiError,
    TrackerConfig,
    TrackerConfigError,
    YandexTrackerClient,
    _tracker_client_kwargs,
)


class FakeCollection:
    def __init__(self, items=None, find_result=None, count_result=0):
        self.items = items or {}
        self.find_result = find_result
        self.count_result = count_result
        self.created = []
        self.find_calls = []

    def __getitem__(self, key):
        return self.items[key]

    def create(self, **kwargs):
        self.created.append(kwargs)
        return kwargs

    def find(self, **kwargs):
        self.find_calls.append(kwargs)
        if kwargs.get("count_only"):
            return self.count_result
        if self.find_result is not None:
            return self.find_result
        return [{"key": "TEST-1"}]


class FakeDictCollection:
    def __init__(self, items):
        self._items = list(items)
        self.get_all_calls = []

    def get_all(self, **kwargs):
        self.get_all_calls.append(kwargs)
        return list(self._items)

    def __getitem__(self, key):
        for item in self._items:
            if str(item.get("id")) == str(key) or str(item.get("login")) == str(key):
                return item
        raise KeyError(key)


class FakeConnection:
    def __init__(self, tags=None):
        self.deleted = []
        self.gets = []
        self._tags = list(tags if tags is not None else ["backend", "urgent"])

    def delete(self, path):
        self.deleted.append(path)
        return {"deleted": path}

    def get(self, path, params=None):
        self.gets.append(path)
        if path.endswith("/tags"):
            return list(self._tags)
        return None


class FakeLink:
    def __init__(self, link_id, obj):
        self.id = link_id
        self.object = obj
        self._path = f"/v2/issues/links/{link_id}"

    def as_dict(self):
        return {"id": self.id, "object": self.object}


class FakeLinks:
    def __init__(self, links=None):
        self.links = list(links or [])
        self.created = []

    def __iter__(self):
        return iter(self.links)

    def create(self, **kwargs):
        self.created.append(kwargs)
        return {"id": "new", **kwargs}


_UNSET = object()


class FakeCreatableList:
    """Iterable collection that also records create() calls (worklog, checklist)."""

    def __init__(self, items=None, create_result=_UNSET):
        self.items = list(items or [])
        self.created = []
        self._create_result = create_result

    def __iter__(self):
        return iter(self.items)

    def create(self, **kwargs):
        self.created.append(kwargs)
        if self._create_result is not _UNSET:
            return self._create_result
        return {"id": "new", **kwargs}


class FakeSilentChecklist(FakeCreatableList):
    """Mirrors the real SDK, whose checklistItems.create() returns None.

    yandex_tracker_client's checklistItems.create calls super().create(...) and
    never returns it, so the API response is discarded.
    """

    def create(self, **kwargs):
        super().create(**kwargs)
        self.items.append({"self": "https://api/…", "id": "ci2", **kwargs})
        return None


class FakeEndlessCollection:
    """Stands in for an SDK cursor-paginated collection.

    Iterating one follows every "next" link, so it ends only when the data does.
    Materializing it with list() is exactly what made the list_* calls unbounded.
    """

    def __init__(self):
        self.yielded = 0
        self.get_all_calls = []

    def __iter__(self):
        while True:
            self.yielded += 1
            yield {"id": f"item{self.yielded}"}

    def get_all(self, **params):
        self.get_all_calls.append(params)
        return self


class FakeAttachment:
    def __init__(self, attachment_id, name, size=12, chunks=None):
        self.id = attachment_id
        self.name = name
        self.size = size
        self.content = f"/v2/issues/TEST-1/attachments/{attachment_id}/{name}"
        self.chunks = chunks or [b"chunk1", b"chunk2"]
        self.deleted_calls = 0

    def delete(self):
        self.deleted_calls += 1

    def as_dict(self):
        return {"id": self.id, "name": self.name, "size": self.size}


class FakeAttachments:
    def __init__(self, items=None):
        self._items = list(items or [FakeAttachment("att1", "a.txt")])
        self.created = []

    def __iter__(self):
        return iter(self._items)

    def __getitem__(self, key):
        for attachment in self._items:
            if str(attachment.id) == str(key):
                return attachment
        raise KeyError(key)

    def read(self, attachment):
        return iter(attachment.chunks)

    def create(self, file, params=None):
        self.created.append({"file": file, "params": params})
        return {"id": "att-new", "name": (params or {}).get("filename") or file}


class FakeQueue:
    def __init__(self, key, versions=None, components=None, local_fields=None):
        self.key = key
        self.versions = list(versions or [])
        self.components = list(components or [])
        self.local_fields = list(local_fields or [])
        self._path = f"/v2/queues/{key}"

    def as_dict(self):
        return {"key": self.key}


class FakeQueues:
    def __init__(self, queues):
        self._queues = {queue.key: queue for queue in queues}

    def __getitem__(self, key):
        return self._queues[key]

    def get_all(self):
        return list(self._queues.values())


class FakeSeekablePaginatedList:
    def __iter__(self):
        return iter([FakeIssue("TEST-1")])

    def __str__(self):
        return "<SeekablePaginatedList>"


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


class FakeComment:
    def __init__(self, comment_id, collection):
        self.id = comment_id
        self._collection = collection

    def update(self, **kwargs):
        self._collection.updated.append((self.id, kwargs))
        return {
            "self": "https://api/…",
            "id": self.id,
            "text": kwargs.get("text"),
            "createdBy": {"self": "https://api/…", "id": "42", "display": "J. Smith"},
            "updatedBy": {
                "self": "https://api/…",
                "id": "42",
                "display": "J. Smith",
                "cloudUid": "abc",
            },
            "createdAt": "2026-07-01T10:00:00.000+0000",
            "updatedAt": "2026-08-23T11:00:00.000+0000",
            "version": 2,
        }

    def delete(self):
        self._collection.deleted.append(self.id)


class FakeChecklistItem:
    """An SDK resource: carries its own path and the injected update/delete."""

    def __init__(self, item_id, text, checked=False):
        self.id = item_id
        self.text = text
        self.checked = checked
        self.deleted = False

    def update(self, **kwargs):
        self.__dict__.update(kwargs)
        return self

    def delete(self):
        self.deleted = True

    def as_dict(self):
        return {
            "self": "https://api/…",
            "id": self.id,
            "text": self.text,
            "checked": self.checked,
        }


class FakeComments:
    def __init__(self):
        self.created = []
        self.deleted = []
        self.updated = []

    def __getitem__(self, key):
        return FakeComment(str(key), self)

    def create(self, **kwargs):
        self.created.append(kwargs)
        return {"id": 1, **kwargs}

    def get_all(self):
        return [{"id": 1, "text": "hello"}]


class FakeChangelog:
    def __init__(self, items=None):
        self._items = list(items or [{"id": "cl1"}])
        self.get_all_calls = []

    def get_all(self, **kwargs):
        self.get_all_calls.append(kwargs)
        return list(self._items)


class FakeIssue:
    def __init__(self, key, transitions=None, links=None):
        self.key = key
        self.comments = FakeComments()
        self.transitions = FakeTransitionCollection(transitions or [])
        self.links = FakeLinks(links)
        self.changelog = FakeChangelog()
        self.worklog = FakeCreatableList([{"id": "wl1"}])
        self.checklist_items = FakeCreatableList([{"id": "ci1"}])
        self.attachments = FakeAttachments()
        self.updated = []

    def update(self, **kwargs):
        self.updated.append(kwargs)
        return {"key": self.key, **kwargs}

    def as_dict(self):
        return {"key": self.key}


class FakeSdkClient:
    def __init__(self, issue, find_result=None, queues=None):
        self.issue = issue
        self.issues = FakeCollection({issue.key: issue}, find_result=find_result)
        self._connection = FakeConnection()
        self.myself = {"self": "https://tracker/me", "login": "me", "uid": 42}
        self.users = FakeDictCollection([{"id": "user1"}])
        self.statuses = FakeDictCollection([{"key": "open"}])
        self.issue_types = FakeDictCollection([{"key": "bug"}])
        self.priorities = FakeDictCollection([{"key": "normal"}])
        self.fields = FakeDictCollection([{"id": "summary"}])
        self.linktypes = FakeDictCollection([{"id": "relates"}])
        self.queues = FakeQueues(
            queues
            or [FakeQueue("TEST", versions=[{"id": "v1"}], components=[{"id": "c1"}])]
        )


# A Tracker issue as the API really returns it: ~20 fields, nested refs with
# `self` URLs, and a description that dwarfs everything else.
FULL_ISSUE_PAYLOAD = {
    "self": "https://api.tracker.yandex.net/v2/issues/TEST-1",
    "id": "issue-1",
    "key": "TEST-1",
    "version": 12,
    "summary": "Новое название",
    "description": "тело задачи " * 200,
    "status": {"self": "https://api/…", "id": "2", "key": "inProgress", "display": "В работе"},
    "type": {"self": "https://api/…", "id": "2", "key": "task", "display": "Задача"},
    "priority": {"self": "https://api/…", "id": "3", "key": "normal", "display": "Средний"},
    "assignee": {"self": "https://api/…", "id": "42", "display": "J. Smith", "cloudUid": "abc"},
    "queue": {"self": "https://api/…", "id": "1", "key": "TEST", "display": "Test"},
    "createdAt": "2026-07-01T10:00:00.000+0000",
    "updatedAt": "2026-08-23T10:00:00.000+0000",
    "createdBy": {"self": "https://api/…", "id": "42", "display": "J. Smith"},
    "followers": [{"self": "https://api/…", "id": "7", "display": "A"}],
    "boards": [{"id": "b1", "name": "Board"}],
    "boardStatus": "review",
    "statusStartTime": "2026-08-23T09:00:00.000+0000",
}

# The API embeds a *complete* issue object in every link's `object`.
LINK_PAYLOAD = {
    "self": "https://api.tracker.yandex.net/v2/issues/TEST-1/links/100",
    "id": 100,
    "type": {
        "self": "https://api/…",
        "id": "depends",
        "inward": "Зависит от",
        "outward": "Блокирует",
    },
    "direction": "outward",
    "object": dict(FULL_ISSUE_PAYLOAD, key="TEST-2", id="issue-2", display="Починить логин"),
    "status": {"self": "https://api/…", "id": "1", "key": "open", "display": "Открыт"},
    "createdBy": {"self": "https://api/…", "id": "42", "display": "J. Smith", "cloudUid": "abc"},
    "createdAt": "2026-07-01T10:00:00.000+0000",
    "updatedAt": "2026-07-01T10:00:00.000+0000",
}


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

    def test_search_issues_materializes_sdk_paginated_list(self):
        issue = FakeIssue("TEST-1")
        client = YandexTrackerClient(
            tracker_client=FakeSdkClient(issue, find_result=FakeSeekablePaginatedList())
        )

        result = client.search_issues(per_page=1)

        self.assertEqual(result, [{"key": "TEST-1"}])

    def test_update_issue_uses_official_sdk_issue_update(self):
        issue = FakeIssue("TEST-1")
        client = YandexTrackerClient(tracker_client=FakeSdkClient(issue))

        self.assertEqual(client.update_issue("TEST-1", {"summary": "new"}), {"key": "TEST-1", "summary": "new"})
        self.assertEqual(issue.updated, [{"summary": "new"}])

    def test_comments_use_official_sdk_issue_comments(self):
        issue = FakeIssue("TEST-1")
        client = YandexTrackerClient(tracker_client=FakeSdkClient(issue))

        # add_comment answers with a receipt: the caller already has the text.
        self.assertEqual(client.add_comment("TEST-1", "hello"), {"id": 1})
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

    def test_search_issues_include_total_adds_count(self):
        issue = FakeIssue("TEST-1")
        sdk_client = FakeSdkClient(issue)
        sdk_client.issues.count_result = 7
        client = YandexTrackerClient(tracker_client=sdk_client)

        result = client.search_issues(query="Queue: TEST", per_page=5, page=2, include_total=True)

        self.assertEqual(
            result,
            {"issues": [{"key": "TEST-1"}], "total": 7, "page": 2, "per_page": 5},
        )
        self.assertTrue(any(call.get("count_only") for call in sdk_client.issues.find_calls))

    def test_search_issues_caps_results_at_per_page(self):
        issue = FakeIssue("TEST-1")
        many = [{"key": f"TEST-{n}"} for n in range(10)]
        sdk_client = FakeSdkClient(issue, find_result=many)
        client = YandexTrackerClient(tracker_client=sdk_client)

        result = client.search_issues(per_page=3)

        # per_page is a hard cap even though find() yields 10 issues.
        self.assertEqual(result, [{"key": "TEST-0"}, {"key": "TEST-1"}, {"key": "TEST-2"}])

    def test_search_issues_stops_iterating_after_per_page(self):
        issue = FakeIssue("TEST-1")
        consumed = []

        def counting_pages():
            for n in range(10):
                consumed.append(n)
                yield {"key": f"TEST-{n}"}

        sdk_client = FakeSdkClient(issue, find_result=counting_pages())
        client = YandexTrackerClient(tracker_client=sdk_client)

        client.search_issues(per_page=2)

        # Iteration halts at the cap, so later (paginated) items are never pulled.
        self.assertEqual(consumed, [0, 1])

    def test_search_issues_returns_compact_projection_by_default(self):
        issue = FakeIssue("TEST-1")
        full_issue = {
            "key": "TEST-9",
            "summary": "Do the thing",
            "description": "a very long body " * 100,
            "status": {"self": "https://api/…", "id": "1", "key": "open", "display": "Открыт"},
            "assignee": {"self": "https://api/…", "id": "42", "display": "J. Smith"},
            "followers": [{"id": "7"}, {"id": "8"}],
            "boards": [{"id": "b1", "name": "Board"}],
            "epic": {"self": "https://api/…", "id": "100", "key": "TEST-1", "display": "Epic"},
        }
        sdk_client = FakeSdkClient(issue, find_result=[full_issue])
        client = YandexTrackerClient(tracker_client=sdk_client)

        result = client.search_issues(per_page=5)

        self.assertEqual(
            result,
            [
                {
                    "key": "TEST-9",
                    "summary": "Do the thing",
                    "status": {"id": "1", "key": "open", "display": "Открыт"},
                    "assignee": {"id": "42", "display": "J. Smith"},
                    "epic": {"id": "100", "key": "TEST-1", "display": "Epic"},
                }
            ],
        )

    def test_search_issues_full_returns_complete_objects(self):
        issue = FakeIssue("TEST-1")
        full_issue = {
            "key": "TEST-9",
            "summary": "Do the thing",
            "description": "body",
            "status": {"self": "https://api/…", "id": "1", "key": "open"},
        }
        sdk_client = FakeSdkClient(issue, find_result=[full_issue])
        client = YandexTrackerClient(tracker_client=sdk_client)

        result = client.search_issues(per_page=5, full=True)

        # full=True keeps every field but transport noise (`self`) is still stripped.
        self.assertEqual(
            result,
            [
                {
                    "key": "TEST-9",
                    "summary": "Do the thing",
                    "description": "body",
                    "status": {"id": "1", "key": "open"},
                }
            ],
        )

    def test_link_issue_creates_link_via_sdk(self):
        issue = FakeIssue("TEST-1")
        client = YandexTrackerClient(tracker_client=FakeSdkClient(issue))

        client.link_issue("TEST-1", "relates", "TEST-2")

        self.assertEqual(issue.links.created, [{"relationship": "relates", "issue": "TEST-2"}])

    def test_list_links_returns_issue_links(self):
        link = FakeLink("100", {"key": "TEST-2"})
        issue = FakeIssue("TEST-1", links=[link])
        client = YandexTrackerClient(tracker_client=FakeSdkClient(issue))

        self.assertEqual(client.list_links("TEST-1"), [{"id": "100", "object": {"key": "TEST-2"}}])

    def test_unlink_issue_deletes_matching_link(self):
        issue = FakeIssue("TEST-1", links=[FakeLink("100", {"key": "TEST-2"})])
        sdk_client = FakeSdkClient(issue)
        client = YandexTrackerClient(tracker_client=sdk_client)

        result = client.unlink_issue("TEST-1", "100")

        self.assertEqual(sdk_client._connection.deleted, ["/v2/issues/links/100"])
        self.assertEqual(result, {"deleted": "100", "issue": "TEST-1"})

    def test_unlink_issue_unknown_id_raises(self):
        issue = FakeIssue("TEST-1", links=[FakeLink("100", {})])
        client = YandexTrackerClient(tracker_client=FakeSdkClient(issue))

        with self.assertRaises(ValueError):
            client.unlink_issue("TEST-1", "999")

    def test_reference_dictionaries_use_sdk_collections(self):
        issue = FakeIssue("TEST-1")
        client = YandexTrackerClient(tracker_client=FakeSdkClient(issue))

        self.assertEqual(client.list_queues(), [{"key": "TEST"}])
        self.assertEqual(client.list_users(), [{"id": "user1"}])
        self.assertEqual(client.list_statuses(), [{"key": "open"}])
        self.assertEqual(client.list_issue_types(), [{"key": "bug"}])
        self.assertEqual(client.list_priorities(), [{"key": "normal"}])
        self.assertEqual(client.list_fields(), [{"id": "summary"}])
        self.assertEqual(client.list_link_types(), [{"id": "relates"}])

    def test_queue_versions_and_components(self):
        issue = FakeIssue("TEST-1")
        client = YandexTrackerClient(tracker_client=FakeSdkClient(issue))

        self.assertEqual(client.list_queue_versions("TEST"), [{"id": "v1"}])
        self.assertEqual(client.list_queue_components("TEST"), [{"id": "c1"}])

    def test_read_only_activity_collections(self):
        issue = FakeIssue("TEST-1")
        client = YandexTrackerClient(tracker_client=FakeSdkClient(issue))

        self.assertEqual(client.get_changelog("TEST-1"), [{"id": "cl1"}])
        self.assertEqual(client.list_worklog("TEST-1"), [{"id": "wl1"}])
        self.assertEqual(client.list_checklist("TEST-1"), [{"id": "ci1"}])
        self.assertEqual(
            client.list_attachments("TEST-1"),
            [{"id": "att1", "name": "a.txt", "size": 12}],
        )

    def test_add_worklog_creates_record(self):
        issue = FakeIssue("TEST-1")
        client = YandexTrackerClient(tracker_client=FakeSdkClient(issue))

        client.add_worklog("TEST-1", "PT1H", comment="did work")

        self.assertEqual(issue.worklog.created, [{"duration": "PT1H", "comment": "did work"}])

    def test_add_checklist_item_creates_entry(self):
        issue = FakeIssue("TEST-1")
        client = YandexTrackerClient(tracker_client=FakeSdkClient(issue))

        client.add_checklist_item("TEST-1", "step 1", checked=True)

        self.assertEqual(issue.checklist_items.created, [{"text": "step 1", "checked": True}])

    def test_download_attachment_writes_bytes_to_dir(self):
        import os
        import tempfile

        issue = FakeIssue("TEST-1")
        client = YandexTrackerClient(tracker_client=FakeSdkClient(issue))

        with tempfile.TemporaryDirectory() as directory:
            result = client.download_attachment("TEST-1", "att1", directory)

            expected_path = os.path.join(directory, "a.txt")
            self.assertEqual(result, {"path": expected_path, "name": "a.txt", "size": 12})
            with open(expected_path, "rb") as handle:
                self.assertEqual(handle.read(), b"chunk1chunk2")

    def test_download_attachment_sanitizes_filename(self):
        import os
        import tempfile

        issue = FakeIssue("TEST-1")
        issue.attachments = FakeAttachments([FakeAttachment("att9", "../evil.txt")])
        client = YandexTrackerClient(tracker_client=FakeSdkClient(issue))

        with tempfile.TemporaryDirectory() as directory:
            result = client.download_attachment("TEST-1", "att9", directory)

            self.assertEqual(os.path.dirname(result["path"]), directory)
            self.assertEqual(result["name"], "evil.txt")

    def test_upload_attachment_creates_via_sdk(self):
        import os
        import tempfile

        issue = FakeIssue("TEST-1")
        client = YandexTrackerClient(tracker_client=FakeSdkClient(issue))

        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "up.txt")
            with open(path, "wb") as handle:
                handle.write(b"data")

            client.upload_attachment("TEST-1", path, filename="renamed.txt")

            self.assertEqual(
                issue.attachments.created,
                [{"file": path, "params": {"filename": "renamed.txt"}}],
            )

    def test_upload_attachment_missing_file_raises(self):
        issue = FakeIssue("TEST-1")
        client = YandexTrackerClient(tracker_client=FakeSdkClient(issue))

        with self.assertRaises(ValueError):
            client.upload_attachment("TEST-1", "/no/such/file.xyz")

    def test_delete_comment_calls_sdk_delete(self):
        issue = FakeIssue("TEST-1")
        client = YandexTrackerClient(tracker_client=FakeSdkClient(issue))

        result = client.delete_comment("TEST-1", "1")

        self.assertEqual(result, {"deleted": "1", "issue": "TEST-1"})
        self.assertEqual(issue.comments.deleted, ["1"])

    def test_delete_attachment_calls_sdk_delete(self):
        issue = FakeIssue("TEST-1")
        client = YandexTrackerClient(tracker_client=FakeSdkClient(issue))

        result = client.delete_attachment("TEST-1", "att1")

        self.assertEqual(result, {"deleted": "att1", "issue": "TEST-1"})
        self.assertEqual(issue.attachments["att1"].deleted_calls, 1)

    def test_get_user_reads_from_users_collection(self):
        issue = FakeIssue("TEST-1")
        client = YandexTrackerClient(tracker_client=FakeSdkClient(issue))

        self.assertEqual(client.get_user("user1"), {"id": "user1"})

    def test_get_current_user_reads_myself(self):
        issue = FakeIssue("TEST-1")
        client = YandexTrackerClient(tracker_client=FakeSdkClient(issue))

        # `self` is stripped as transport noise by _to_plain.
        self.assertEqual(
            client.get_current_user(),
            {"login": "me", "uid": 42},
        )

    def test_list_users_passes_server_side_filters(self):
        issue = FakeIssue("TEST-1")
        sdk_client = FakeSdkClient(issue)
        client = YandexTrackerClient(tracker_client=sdk_client)

        result = client.list_users(email="a@b.c", group="42", limit=50)

        self.assertEqual(result, [{"id": "user1"}])
        self.assertEqual(
            sdk_client.users.get_all_calls,
            [{"perPage": 50, "email": "a@b.c", "group": "42"}],
        )

    def test_list_users_always_bounds_the_page_size(self):
        issue = FakeIssue("TEST-1")
        sdk_client = FakeSdkClient(issue)
        client = YandexTrackerClient(tracker_client=sdk_client)

        client.list_users()
        # perPage rides along even with no filters: without it the SDK falls back
        # to its own default page size and the iterator walks the whole directory.
        self.assertEqual(sdk_client.users.get_all_calls, [{"perPage": 50}])

    def test_list_users_clamps_page_size_to_the_api_maximum(self):
        issue = FakeIssue("TEST-1")
        sdk_client = FakeSdkClient(issue)
        client = YandexTrackerClient(tracker_client=sdk_client)

        client.list_users(limit=400)

        self.assertEqual(sdk_client.users.get_all_calls, [{"perPage": 100}])

    def test_list_queue_local_fields(self):
        issue = FakeIssue("TEST-1")
        queue = FakeQueue("TEST", local_fields=[{"id": "customField"}])
        client = YandexTrackerClient(
            tracker_client=FakeSdkClient(issue, queues=[queue])
        )

        self.assertEqual(
            client.list_queue_local_fields("TEST"), [{"id": "customField"}]
        )

    def test_list_queue_tags_uses_raw_connection(self):
        issue = FakeIssue("TEST-1")
        sdk_client = FakeSdkClient(issue)
        client = YandexTrackerClient(tracker_client=sdk_client)

        self.assertEqual(client.list_queue_tags("TEST"), ["backend", "urgent"])
        self.assertEqual(sdk_client._connection.gets, ["/v2/queues/TEST/tags"])

    def test_get_changelog_passes_filters(self):
        issue = FakeIssue("TEST-1")
        client = YandexTrackerClient(tracker_client=FakeSdkClient(issue))

        result = client.get_changelog(
            "TEST-1", field="status", change_type="IssueWorkflow", limit=10
        )

        self.assertEqual(result, [{"id": "cl1"}])
        self.assertEqual(
            issue.changelog.get_all_calls,
            [{"perPage": 10, "field": "status", "type": "IssueWorkflow"}],
        )

    # --- Compact write receipts and link projection (P0) -------------------
    def test_update_issue_returns_a_write_receipt(self):
        issue = FakeIssue("TEST-1")
        issue.update = lambda **kwargs: dict(FULL_ISSUE_PAYLOAD)
        client = YandexTrackerClient(tracker_client=FakeSdkClient(issue))

        result = client.update_issue(
            "TEST-1", {"summary": "Новое название", "boardStatus": "review"}
        )

        self.assertEqual(
            result,
            {
                "key": "TEST-1",
                "summary": "Новое название",
                "status": {"key": "inProgress", "id": "2", "display": "В работе"},
                "type": {"key": "task", "id": "2", "display": "Задача"},
                "priority": {"key": "normal", "id": "3", "display": "Средний"},
                "assignee": {"id": "42", "display": "J. Smith"},
                "queue": {"key": "TEST", "id": "1", "display": "Test"},
                "updatedAt": "2026-08-23T10:00:00.000+0000",
                "createdAt": "2026-07-01T10:00:00.000+0000",
                "version": 12,
                # Patched but outside the projection: echoed so the caller sees
                # the value the server actually stored.
                "boardStatus": "review",
            },
        )

    def test_update_issue_full_returns_the_complete_object(self):
        issue = FakeIssue("TEST-1")
        issue.update = lambda **kwargs: dict(FULL_ISSUE_PAYLOAD)
        client = YandexTrackerClient(tracker_client=FakeSdkClient(issue))

        result = client.update_issue("TEST-1", {"summary": "x"}, full=True)

        self.assertEqual(result["description"], FULL_ISSUE_PAYLOAD["description"])
        self.assertIn("followers", result)
        # full=True still strips transport noise.
        self.assertNotIn("self", result)
        self.assertNotIn("cloudUid", result["assignee"])

    def test_create_issue_receipt_keeps_the_key_and_the_extra_fields(self):
        issue = FakeIssue("TEST-1")
        sdk_client = FakeSdkClient(issue)
        sdk_client.issues.create = lambda **kwargs: dict(FULL_ISSUE_PAYLOAD)
        client = YandexTrackerClient(tracker_client=sdk_client)

        result = client.create_issue(
            "TEST", "Новое название", description="тело", fields={"boardStatus": "review"}
        )

        self.assertEqual(result["key"], "TEST-1")
        self.assertEqual(result["boardStatus"], "review")
        # The description the caller just sent is not echoed back.
        self.assertNotIn("description", result)

    def test_list_links_collapses_the_embedded_issue(self):
        issue = FakeIssue("TEST-1", links=[dict(LINK_PAYLOAD)])
        client = YandexTrackerClient(tracker_client=FakeSdkClient(issue))

        self.assertEqual(
            client.list_links("TEST-1"),
            [
                {
                    "id": 100,
                    "direction": "outward",
                    "status": {"key": "open", "id": "1", "display": "Открыт"},
                    # inward/outward survive: the type id alone does not say
                    # which way the relationship reads.
                    "type": {
                        "id": "depends",
                        "inward": "Зависит от",
                        "outward": "Блокирует",
                    },
                    "object": {
                        "key": "TEST-2",
                        "id": "issue-2",
                        "display": "Починить логин",
                    },
                }
            ],
        )

    def test_list_links_full_keeps_the_whole_payload(self):
        issue = FakeIssue("TEST-1", links=[dict(LINK_PAYLOAD)])
        client = YandexTrackerClient(tracker_client=FakeSdkClient(issue))

        result = client.list_links("TEST-1", full=True)

        self.assertEqual(
            result[0]["object"]["description"],
            LINK_PAYLOAD["object"]["description"],
        )
        self.assertIn("createdBy", result[0])

    def test_link_issue_returns_the_compact_link(self):
        issue = FakeIssue("TEST-1")
        issue.links.create = lambda **kwargs: dict(LINK_PAYLOAD)
        client = YandexTrackerClient(tracker_client=FakeSdkClient(issue))

        result = client.link_issue("TEST-1", "depends", "TEST-2")

        self.assertEqual(result["object"], {"key": "TEST-2", "id": "issue-2", "display": "Починить логин"})
        self.assertNotIn("createdBy", result)

    def test_add_worklog_receipt_drops_the_embedded_issue(self):
        issue = FakeIssue("TEST-1")
        issue.worklog = FakeCreatableList(
            create_result={
                "self": "https://api/…",
                "id": "wl-9",
                "version": 1,
                "issue": dict(FULL_ISSUE_PAYLOAD),
                "comment": "did work",
                "duration": "PT1H",
                "start": "2026-08-23T10:00:00.000+0000",
                "createdBy": {"self": "…", "id": "42", "display": "J. Smith"},
                "createdAt": "2026-08-23T10:05:00.000+0000",
                "updatedAt": "2026-08-23T10:05:00.000+0000",
            }
        )
        client = YandexTrackerClient(tracker_client=FakeSdkClient(issue))

        result = client.add_worklog("TEST-1", "PT1H", comment="did work")

        self.assertEqual(
            result,
            {
                "id": "wl-9",
                "duration": "PT1H",
                "start": "2026-08-23T10:00:00.000+0000",
                "createdBy": {"id": "42", "display": "J. Smith"},
                "createdAt": "2026-08-23T10:05:00.000+0000",
            },
        )

    def test_add_checklist_item_rereads_when_the_sdk_discards_the_response(self):
        issue = FakeIssue("TEST-1")
        issue.checklist_items = FakeSilentChecklist(
            [{"self": "https://api/…", "id": "ci1", "text": "шаг 1", "checked": False}]
        )
        client = YandexTrackerClient(tracker_client=FakeSdkClient(issue))

        result = client.add_checklist_item("TEST-1", "шаг 2", checked=True)

        self.assertEqual(issue.checklist_items.created, [{"text": "шаг 2", "checked": True}])
        # Without the re-read the caller would get a bare null and no item id.
        self.assertEqual(
            result,
            [
                {"id": "ci1", "text": "шаг 1", "checked": False},
                {"id": "ci2", "text": "шаг 2", "checked": True},
            ],
        )

    # --- Editing comments and checklist items -------------------------------
    def test_update_comment_returns_an_edit_receipt(self):
        issue = FakeIssue("TEST-1")
        client = YandexTrackerClient(tracker_client=FakeSdkClient(issue))

        result = client.update_comment("TEST-1", "5", "исправленный текст")

        self.assertEqual(issue.comments.updated, [("5", {"text": "исправленный текст"})])
        self.assertEqual(
            result,
            {
                "id": "5",
                "updatedBy": {"id": "42", "display": "J. Smith"},
                "updatedAt": "2026-08-23T11:00:00.000+0000",
            },
        )

    def test_update_checklist_item_ticks_an_item_off(self):
        item = FakeChecklistItem("ci2", "шаг 2")
        issue = FakeIssue("TEST-1")
        issue.checklist_items = FakeCreatableList(
            [FakeChecklistItem("ci1", "шаг 1", checked=True), item]
        )
        client = YandexTrackerClient(tracker_client=FakeSdkClient(issue))

        result = client.update_checklist_item("TEST-1", "ci2", checked=True)

        self.assertTrue(item.checked)
        self.assertEqual(result, {"id": "ci2", "text": "шаг 2", "checked": True})

    def test_update_checklist_item_needs_something_to_change(self):
        issue = FakeIssue("TEST-1")
        client = YandexTrackerClient(tracker_client=FakeSdkClient(issue))

        with self.assertRaises(ValueError):
            client.update_checklist_item("TEST-1", "ci1")

    def test_delete_checklist_item_removes_the_matching_item(self):
        item = FakeChecklistItem("ci1", "шаг 1")
        issue = FakeIssue("TEST-1")
        issue.checklist_items = FakeCreatableList([item])
        client = YandexTrackerClient(tracker_client=FakeSdkClient(issue))

        result = client.delete_checklist_item("TEST-1", "ci1")

        self.assertTrue(item.deleted)
        self.assertEqual(result, {"deleted": "ci1", "issue": "TEST-1"})

    def test_checklist_item_lookup_reports_an_unknown_id(self):
        issue = FakeIssue("TEST-1")
        issue.checklist_items = FakeCreatableList([FakeChecklistItem("ci1", "шаг 1")])
        client = YandexTrackerClient(tracker_client=FakeSdkClient(issue))

        with self.assertRaises(ValueError):
            client.delete_checklist_item("TEST-1", "nope")

    # --- Every list call is bounded (P1) -----------------------------------
    def test_list_calls_stop_at_the_limit_instead_of_draining_pages(self):
        cases = {
            "list_comments": lambda c: c.list_comments("TEST-1", limit=3),
            "list_worklog": lambda c: c.list_worklog("TEST-1", limit=3),
            "list_checklist": lambda c: c.list_checklist("TEST-1", limit=3),
            "list_attachments": lambda c: c.list_attachments("TEST-1", limit=3),
            "list_links": lambda c: c.list_links("TEST-1", limit=3),
            "get_changelog": lambda c: c.get_changelog("TEST-1", limit=3),
            "list_queues": lambda c: c.list_queues(limit=3),
            "list_users": lambda c: c.list_users(limit=3),
        }
        attach = {
            "list_comments": lambda issue, sdk, col: setattr(issue, "comments", col),
            "list_worklog": lambda issue, sdk, col: setattr(issue, "worklog", col),
            "list_checklist": lambda issue, sdk, col: setattr(issue, "checklist_items", col),
            "list_attachments": lambda issue, sdk, col: setattr(issue, "attachments", col),
            "list_links": lambda issue, sdk, col: setattr(issue, "links", col),
            "get_changelog": lambda issue, sdk, col: setattr(issue, "changelog", col),
            "list_queues": lambda issue, sdk, col: setattr(sdk, "queues", col),
            "list_users": lambda issue, sdk, col: setattr(sdk, "users", col),
        }
        for name, call in cases.items():
            with self.subTest(method=name):
                issue = FakeIssue("TEST-1")
                sdk_client = FakeSdkClient(issue)
                collection = FakeEndlessCollection()
                attach[name](issue, sdk_client, collection)
                client = YandexTrackerClient(tracker_client=sdk_client)

                result = call(client)

                self.assertEqual(len(result), 3)
                # The page after the cap is never fetched, let alone the rest.
                self.assertEqual(collection.yielded, 3)

    def test_reference_dictionaries_are_bounded_by_the_runaway_guard(self):
        issue = FakeIssue("TEST-1")
        sdk_client = FakeSdkClient(issue)
        sdk_client.fields = FakeEndlessCollection()
        client = YandexTrackerClient(tracker_client=sdk_client)

        result = client.list_fields()

        self.assertEqual(len(result), 500)
        self.assertEqual(sdk_client.fields.yielded, 500)

    def test_call_sdk_wraps_transport_errors_as_api_errors(self):
        issue = FakeIssue("TEST-1")
        client = YandexTrackerClient(tracker_client=FakeSdkClient(issue))

        def boom(_client):
            raise ConnectionError("dns failure")

        with self.assertRaises(TrackerApiError):
            client._call_sdk(boom)


if __name__ == "__main__":
    unittest.main()
