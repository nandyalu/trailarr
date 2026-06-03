"""Tests for migration d4e5f6a7b8c9 — cleanup of stale NULL-profile PENDING rows.

With the dynamic work-queue approach (get_work_items), PENDING rows are never
pre-created. This migration only cleans up any stale NULL-profile PENDING rows
that may have been created by older code, then adds schema columns.
"""

import datetime
from unittest.mock import patch

import sqlalchemy as sa
import pytest
from sqlmodel import Session

from db.engine import engine, write_session
from db.models.connection import ArrType, Connection, MonitorType
from db.models.mediatrailerstatus import MediaTrailerStatus, TrailerStatusEnum
from db.models.trailerprofile import TrailerProfile


@write_session
def _make_connection(*, _session: Session = None) -> int:  # type: ignore
    conn = Connection(
        name="Mig Test Connection",
        arr_type=ArrType.RADARR,
        url="http://localhost:7878",
        api_key="testkey",
        monitor=MonitorType.MONITOR_MISSING,
    )
    _session.add(conn)
    _session.commit()
    _session.refresh(conn)
    return conn.id  # type: ignore


@write_session
def _make_media(
    connection_id: int,
    is_movie: bool = True,
    season_count: int = 0,
    downloaded_at: datetime.datetime | None = None,
    *,
    _session: Session = None,  # type: ignore
) -> int:
    from db.models.media import Media
    import random
    uid = random.randint(10000, 99999)
    media = Media(
        connection_id=connection_id,
        arr_id=uid,
        is_movie=is_movie,
        title=f"Mig Movie {uid}",
        clean_title=f"mig movie {uid}",
        year=2024,
        language="en",
        studio="Studio",
        tmdb_id=str(uid),
        title_slug=f"mig-movie-{uid}",
        monitor=True,
        arr_monitored=True,
        media_exists=False,
        media_filename="",
        season_count=season_count,
        runtime=100,
        added_at=datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc),
        updated_at=datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc),
        downloaded_at=downloaded_at,
    )
    _session.add(media)
    _session.commit()
    _session.refresh(media)
    return media.id  # type: ignore


@write_session
def _insert_null_profile_pending(media_id: int, *, _session: Session = None) -> int:  # type: ignore
    """Simulates a stale NULL-profile PENDING row from older migration code."""
    row = MediaTrailerStatus(
        media_id=media_id,
        profile_id=None,
        season=0,
        sequence=1,
        status=TrailerStatusEnum.PENDING,
        source="app",
    )
    _session.add(row)
    _session.commit()
    _session.refresh(row)
    return row.id  # type: ignore


@write_session
def _insert_null_profile_downloaded(media_id: int, *, _session: Session = None) -> int:  # type: ignore
    """Simulates a manual/unattributed DOWNLOADED row (must be preserved)."""
    row = MediaTrailerStatus(
        media_id=media_id,
        profile_id=None,
        season=0,
        sequence=1,
        status=TrailerStatusEnum.DOWNLOADED,
        source="manual",
    )
    _session.add(row)
    _session.commit()
    _session.refresh(row)
    return row.id  # type: ignore


@write_session
def _count_rows(media_id: int, status: TrailerStatusEnum, *, _session: Session = None) -> int:  # type: ignore
    from sqlmodel import select
    stmt = select(MediaTrailerStatus).where(
        MediaTrailerStatus.media_id == media_id,
        MediaTrailerStatus.status == status,
    )
    return len(_session.exec(stmt).all())


def _run_upgrade():
    """Run the migration SQL. Mocks batch_alter_table since columns already exist in test DB."""
    import importlib.util, os
    spec = importlib.util.spec_from_file_location(
        "migration_d4e5f6a7b8c9",
        os.path.join(
            os.path.dirname(__file__),
            "../../alembic/versions/20260523_0000-d4e5f6a7b8c9_add_tmdb_language_and_youtube_id.py",
        ),
    )
    mod = importlib.util.module_from_spec(spec)  # type: ignore[attr-defined]
    spec.loader.exec_module(mod)  # type: ignore[union-attr]

    with engine.connect() as conn:
        with patch("alembic.op.get_bind", return_value=conn), \
             patch("alembic.op.batch_alter_table"):
            mod.upgrade()
        conn.commit()


class TestOrphanedRowMigration:
    """Migration must clean up stale NULL-profile PENDING rows without creating new ones."""

    def test_non_downloaded_rows_deleted(self):
        conn_id = _make_connection()
        media_id = _make_media(conn_id)
        _insert_null_profile_pending(media_id)

        _run_upgrade()

        assert _count_rows(media_id, TrailerStatusEnum.PENDING) == 0, \
            "All non-DOWNLOADED rows must be deleted"

    def test_manual_downloaded_row_preserved(self):
        conn_id = _make_connection()
        media_id = _make_media(
            conn_id, downloaded_at=datetime.datetime(2024, 6, 1, tzinfo=datetime.timezone.utc)
        )
        _insert_null_profile_downloaded(media_id)

        _run_upgrade()

        assert _count_rows(media_id, TrailerStatusEnum.DOWNLOADED) == 1, \
            "NULL-profile DOWNLOADED rows must be preserved"

    def test_no_pending_rows_created_for_undownloaded_media(self):
        """Migration no longer pre-creates PENDING rows — get_work_items() handles that."""
        conn_id = _make_connection()
        media_id = _make_media(conn_id, is_movie=True)

        _run_upgrade()

        assert _count_rows(media_id, TrailerStatusEnum.PENDING) == 0, \
            "Migration must not create PENDING rows — dynamic queue handles this"

    def test_migration_is_idempotent(self):
        conn_id = _make_connection()
        media_id = _make_media(conn_id)
        _insert_null_profile_pending(media_id)

        _run_upgrade()
        _run_upgrade()  # second run should be a no-op

        assert _count_rows(media_id, TrailerStatusEnum.PENDING) == 0, \
            "Migration must be idempotent"
