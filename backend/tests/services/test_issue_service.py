"""Comprehensive tests for services/issue_service.py."""

from unittest.mock import MagicMock, patch

import pytest

from db.models.issue import EntityType, IssueType
from services import issue_service


class TestUpsert:

    def test_delegates_to_repo(self):
        with patch("services.issue_service.issue_repo.upsert") as mock_upsert:
            issue_service.upsert(
                IssueType.FILE_DELETED,
                EntityType.DOWNLOAD,
                42,
                "Trailer file missing",
                "/path/to/file",
            )
        mock_upsert.assert_called_once_with(
            IssueType.FILE_DELETED, EntityType.DOWNLOAD, 42,
            "Trailer file missing", "/path/to/file",
        )

    def test_details_optional(self):
        with patch("services.issue_service.issue_repo.upsert") as mock_upsert:
            issue_service.upsert(IssueType.CONNECTION_FAILED, EntityType.CONNECTION, 1, "Desc")
        mock_upsert.assert_called_once_with(
            IssueType.CONNECTION_FAILED, EntityType.CONNECTION, 1, "Desc", None
        )


class TestResolve:

    def test_returns_true_when_resolved(self):
        with patch("services.issue_service.issue_repo.resolve", return_value=True) as mock_resolve:
            result = issue_service.resolve(IssueType.FILE_DELETED, EntityType.DOWNLOAD, 5)
        assert result is True
        mock_resolve.assert_called_once_with(IssueType.FILE_DELETED, EntityType.DOWNLOAD, 5)

    def test_returns_false_when_nothing_to_resolve(self):
        with patch("services.issue_service.issue_repo.resolve", return_value=False):
            result = issue_service.resolve(IssueType.TOKEN_INVALID, EntityType.CONNECTION, 9)
        assert result is False


class TestResolveAllForEntity:

    def test_returns_count_of_resolved_issues(self):
        with patch("services.issue_service.issue_repo.resolve_all_for_entity", return_value=3) as mock_resolve:
            result = issue_service.resolve_all_for_entity(EntityType.CONNECTION, 7)
        assert result == 3
        mock_resolve.assert_called_once_with(EntityType.CONNECTION, 7)

    def test_returns_zero_when_nothing_resolved(self):
        with patch("services.issue_service.issue_repo.resolve_all_for_entity", return_value=0):
            result = issue_service.resolve_all_for_entity(EntityType.DOWNLOAD, 99)
        assert result == 0


class TestGetAll:

    def test_returns_all_issues_no_filter(self):
        mock_issues = [MagicMock(), MagicMock()]
        with patch("services.issue_service.issue_repo.get_all", return_value=mock_issues) as mock_get:
            result = issue_service.get_all()
        assert result is mock_issues
        mock_get.assert_called_once_with(None)

    def test_filters_by_entity_type(self):
        mock_issues = [MagicMock()]
        with patch("services.issue_service.issue_repo.get_all", return_value=mock_issues) as mock_get:
            result = issue_service.get_all(EntityType.CONNECTION)
        assert result is mock_issues
        mock_get.assert_called_once_with(EntityType.CONNECTION)


class TestGetForEntity:

    def test_delegates_to_repo(self):
        mock_issues = [MagicMock()]
        with patch("services.issue_service.issue_repo.get_for_entity", return_value=mock_issues) as mock_get:
            result = issue_service.get_for_entity(EntityType.DOWNLOAD, 12)
        assert result is mock_issues
        mock_get.assert_called_once_with(EntityType.DOWNLOAD, 12)

    def test_returns_empty_list_when_none(self):
        with patch("services.issue_service.issue_repo.get_for_entity", return_value=[]):
            result = issue_service.get_for_entity(EntityType.CONNECTION, 999)
        assert result == []


class TestDelete:

    def test_returns_true_when_deleted(self):
        with patch("services.issue_service.issue_repo.delete", return_value=True) as mock_del:
            result = issue_service.delete(55)
        assert result is True
        mock_del.assert_called_once_with(55)

    def test_returns_false_when_not_found(self):
        with patch("services.issue_service.issue_repo.delete", return_value=False):
            result = issue_service.delete(9999)
        assert result is False
