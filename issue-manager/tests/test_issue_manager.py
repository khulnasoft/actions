"""Characterization tests for issue-manager."""

import datetime as dt
from unittest.mock import MagicMock

from app.main import (
    KeywordMeta,
    Settings,
    discard_schema,
    get_labeled_events,
    get_last_event_for_label,
    get_last_interaction_date,
)


class TestKeywordMeta:
    def test_defaults(self):
        km = KeywordMeta()
        assert km.delay == dt.timedelta(days=10)
        assert km.remove_label_on_comment is True
        assert km.remove_label_on_close is False
        assert "automatically closed" in km.message

    def test_iso8601_delay(self):
        km = KeywordMeta(delay="P3DT12H30M5S")
        assert km.delay == dt.timedelta(days=3, hours=12, minutes=30, seconds=5)

    def test_seconds_delay(self):
        km = KeywordMeta(delay=86400)
        assert km.delay == dt.timedelta(seconds=86400)


class TestDiscardSchema:
    def test_removes_schema_key(self):
        data = {"$schema": "https://example.com/schema.json", "answered": {"delay": 100}}
        result = discard_schema(data)
        assert "$schema" not in result
        assert "answered" in result

    def test_no_schema_key(self):
        data = {"answered": {"delay": 100}}
        result = discard_schema(data)
        assert result == data

    def test_not_dict(self):
        result = discard_schema("not a dict")
        assert result == "not a dict"


class TestGetLabeledEvents:
    def test_filters_labeled(self):
        e1 = MagicMock(event="labeled")
        e2 = MagicMock(event="closed")
        e3 = MagicMock(event="labeled")
        result = get_labeled_events([e1, e2, e3])
        assert len(result) == 2

    def test_empty(self):
        assert get_labeled_events([]) == []


class TestGetLastEventForLabel:
    def test_finds_matching(self):
        e1 = MagicMock(event="labeled", created_at=dt.datetime(2024, 1, 1, tzinfo=dt.UTC))
        e1.label = MagicMock()
        e1.label.name = "answered"
        e2 = MagicMock(event="labeled", created_at=dt.datetime(2024, 1, 2, tzinfo=dt.UTC))
        e2.label = MagicMock()
        e2.label.name = "waiting"
        result = get_last_event_for_label(labeled_events=[e1, e2], label="answered")
        assert result is e1

    def test_none_if_no_match(self):
        e1 = MagicMock(event="labeled", created_at=dt.datetime(2024, 1, 1, tzinfo=dt.UTC))
        e1.label = MagicMock()
        e1.label.name = "waiting"
        result = get_last_event_for_label(labeled_events=[e1], label="answered")
        assert result is None

    def test_returns_latest(self):
        e1 = MagicMock(event="labeled", created_at=dt.datetime(2024, 1, 1, tzinfo=dt.UTC))
        e1.label = MagicMock()
        e1.label.name = "answered"
        e2 = MagicMock(event="labeled", created_at=dt.datetime(2024, 1, 5, tzinfo=dt.UTC))
        e2.label = MagicMock()
        e2.label.name = "answered"
        result = get_last_event_for_label(labeled_events=[e1, e2], label="answered")
        assert result is e2


class TestGetLastInteractionDate:
    def test_issue_no_comments(self):
        issue = MagicMock()
        issue.pull_request = None
        issue.get_comments.return_value = []
        result = get_last_interaction_date(issue)
        assert result is None

    def test_issue_with_comments(self):
        issue = MagicMock()
        issue.pull_request = None
        c1 = MagicMock(created_at=dt.datetime(2024, 1, 1, tzinfo=dt.UTC))
        c2 = MagicMock(created_at=dt.datetime(2024, 1, 5, tzinfo=dt.UTC))
        issue.get_comments.return_value = [c1, c2]
        result = get_last_interaction_date(issue)
        assert result == dt.datetime(2024, 1, 5, tzinfo=dt.UTC)

    def test_pr_with_none_review_submitted_at(self):
        issue = MagicMock()
        issue.pull_request = True
        pr = MagicMock()
        issue.as_pull_request.return_value = pr
        issue.get_comments.return_value = []
        pr.get_comments.return_value = []
        pr.get_commits.return_value = []
        r1 = MagicMock(submitted_at=None)
        r2 = MagicMock(submitted_at=dt.datetime(2024, 1, 3, tzinfo=dt.UTC))
        pr.get_reviews.return_value = [r1, r2]
        result = get_last_interaction_date(issue)
        assert result == dt.datetime(2024, 1, 3, tzinfo=dt.UTC)

    def test_pr_with_none_commit_date(self):
        issue = MagicMock()
        issue.pull_request = True
        pr = MagicMock()
        issue.as_pull_request.return_value = pr
        issue.get_comments.return_value = []
        pr.get_comments.return_value = []
        c = MagicMock()
        c.commit.author = None
        pr.get_commits.return_value = [c]
        pr.get_reviews.return_value = []
        result = get_last_interaction_date(issue)
        assert result is None


class TestSettings:
    def test_env_ignore_empty(self, monkeypatch):
        monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
        monkeypatch.setenv("INPUT_TOKEN", "tok")
        monkeypatch.setenv("GITHUB_EVENT_PATH", "/tmp/ev.json")
        monkeypatch.setenv("INPUT_CONFIG", '{"answered": {"delay": 100}}')
        s = Settings()
        assert s.github_repository == "owner/repo"
        assert "answered" in s.input_config

    def test_discard_schema_in_settings(self, monkeypatch, tmp_path):
        ev = tmp_path / "ev.json"
        ev.write_text("{}")
        monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
        monkeypatch.setenv("INPUT_TOKEN", "tok")
        monkeypatch.setenv("GITHUB_EVENT_PATH", str(ev))
        monkeypatch.setenv(
            "INPUT_CONFIG",
            '{"$schema": "https://example.com/s.json", "answered": {"delay": 100}}',
        )
        s = Settings()
        assert "$schema" not in s.input_config
        assert "answered" in s.input_config
