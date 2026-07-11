"""Tests for the downgrade guard (core/base/database/utils/version_guard.py)."""

from unittest.mock import patch

import pytest

from core.base.database.utils import version_guard


class TestVersionGuard:

    def test_known_revisions_parsed_from_migration_files(self):
        revisions = version_guard._known_revisions()
        assert len(revisions) > 5
        assert "fe3fa57174bc" in revisions  # this phase's migration

    def test_fresh_db_passes(self):
        with patch.object(version_guard, "_db_revision", return_value=None):
            version_guard.ensure_db_not_from_newer_version()

    def test_known_revision_passes(self):
        with patch.object(
            version_guard, "_db_revision", return_value="fe3fa57174bc"
        ):
            version_guard.ensure_db_not_from_newer_version()

    def test_unknown_revision_refuses_to_start(self):
        """DB migrated by a newer app version → clear refusal, not a crash
        on missing columns three tasks later."""
        with patch.object(
            version_guard, "_db_revision", return_value="ffffuture999"
        ):
            with pytest.raises(SystemExit):
                version_guard.ensure_db_not_from_newer_version()
