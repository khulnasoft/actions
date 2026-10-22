"""Characterization tests for label-approved."""

from datetime import UTC, datetime
from unittest.mock import MagicMock

from label_approved.__main__ import (
    LabelSettings,
    apply_config,
    approved_count,
    latest_reviews_by_user,
)


class TestLabelSettings:
    def test_defaults(self):
        ls = LabelSettings(number=2)
        assert ls.await_label is None
        assert ls.number == 2

    def test_with_await_label(self):
        ls = LabelSettings(await_label="awaiting-review", number=3)
        assert ls.await_label == "awaiting-review"
        assert ls.number == 3


class TestLatestReviewsByUser:
    def test_single_review(self):
        r = MagicMock()
        r.user = MagicMock(login="alice")
        r.submitted_at = datetime(2024, 1, 1, tzinfo=UTC)
        r.state = "APPROVED"
        result = latest_reviews_by_user([r])
        assert "alice" in result
        assert result["alice"] is r

    def test_latest_wins(self):
        r1 = MagicMock()
        r1.user = MagicMock(login="alice")
        r1.submitted_at = datetime(2024, 1, 1, tzinfo=UTC)
        r1.state = "APPROVED"
        r2 = MagicMock()
        r2.user = MagicMock(login="alice")
        r2.submitted_at = datetime(2024, 1, 5, tzinfo=UTC)
        r2.state = "CHANGES_REQUESTED"
        result = latest_reviews_by_user([r1, r2])
        assert result["alice"].state == "CHANGES_REQUESTED"

    def test_approve_then_request_changes_not_approved(self):
        r1 = MagicMock()
        r1.user = MagicMock(login="alice")
        r1.submitted_at = datetime(2024, 1, 1, tzinfo=UTC)
        r1.state = "APPROVED"
        r2 = MagicMock()
        r2.user = MagicMock(login="alice")
        r2.submitted_at = datetime(2024, 1, 5, tzinfo=UTC)
        r2.state = "CHANGES_REQUESTED"
        count = approved_count([r1, r2])
        assert count == 0

    def test_deleted_user_skipped(self):
        r = MagicMock()
        r.user = None
        r.submitted_at = datetime(2024, 1, 1, tzinfo=UTC)
        result = latest_reviews_by_user([r])
        assert result == {}

    def test_pending_review_skipped(self):
        r = MagicMock()
        r.user = MagicMock(login="alice")
        r.submitted_at = None
        r.state = "PENDING"
        result = latest_reviews_by_user([r])
        assert result == {}

    def test_multiple_users(self):
        r1 = MagicMock()
        r1.user = MagicMock(login="alice")
        r1.submitted_at = datetime(2024, 1, 1, tzinfo=UTC)
        r1.state = "APPROVED"
        r2 = MagicMock()
        r2.user = MagicMock(login="bob")
        r2.submitted_at = datetime(2024, 1, 2, tzinfo=UTC)
        r2.state = "APPROVED"
        count = approved_count([r1, r2])
        assert count == 2


class TestApplyConfig:
    def test_adds_label_when_threshold_met(self):
        pr = MagicMock()
        pr.get_labels.return_value = []
        pr.get_labels.return_value = []
        # Simulate pr_label_by_name being empty
        conf = LabelSettings(await_label=None, number=1)
        config = {"approved-1": conf}
        applied = apply_config(pr, config, 2)
        assert "approved-1" in applied
        pr.add_to_labels.assert_called_with("approved-1")

    def test_does_not_add_when_below_threshold(self):
        pr = MagicMock()
        pr.get_labels.return_value = []
        conf = LabelSettings(await_label=None, number=3)
        config = {"approved-3": conf}
        applied = apply_config(pr, config, 1)
        assert applied == []
        pr.add_to_labels.assert_not_called()

    def test_await_label_gate_blocks_when_missing(self):
        pr = MagicMock()
        pr.get_labels.return_value = []
        conf = LabelSettings(await_label="awaiting-review", number=1)
        config = {"approved-1": conf}
        applied = apply_config(pr, config, 2)
        assert applied == []

    def test_removes_await_label_after_apply(self):
        pr = MagicMock()
        conf = LabelSettings(await_label="awaiting-review", number=1)
        config = {"approved-1": conf}
        # Monkey: apply_config reads pr.get_labels() internally
        m = MagicMock()
        m.name = "awaiting-review"
        pr.get_labels.return_value = [m]
        applied = apply_config(pr, config, 2)
        assert "approved-1" in applied
        pr.remove_from_labels.assert_called_with("awaiting-review")
