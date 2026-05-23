"""Tests for db/init_db.py — verifies that init_db() runs without error."""

from unittest.mock import patch

from db.init_db import init_db


class TestInitDB:
    def test_init_db_runs(self):
        """init_db() should complete without raising."""
        # Simply call init_db(); it is idempotent via Alembic migrations.
        # We just verify it doesn't crash in the test environment.
        init_db()  # should not raise
