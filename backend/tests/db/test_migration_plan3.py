"""Tests for Plan 3 migration — fix_orphaned_pending_rows.

Tests call upgrade() directly with the in-memory test engine, bypassing Alembic
so the logic can be verified without running a full migration stack.
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
        txdb_id=str(uid),
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
def _make_profile(
    for_movies: bool = True,
    enabled: bool = True,
    download_season_videos: bool = False,
    *,
    _session: Session = None,  # type: ignore
) -> int:
    from db.models.customfilter import CustomFilter, FilterType
    cf = CustomFilter(
        filter_name=f"Mig Profile {'Movie' if for_movies else 'Series'}",
        filter_type=FilterType.TRAILER,
    )
    _session.add(cf)
    _session.commit()
    _session.refresh(cf)
    tp = TrailerProfile(
        customfilter_id=cf.id,
        enabled=enabled,
        for_movies=for_movies,
        download_season_videos=download_season_videos,
        max_count=1,
    )
    _session.add(tp)
    _session.commit()
    _session.refresh(tp)
    return tp.id  # type: ignore


@write_session
def _insert_null_profile_pending(media_id: int, *, _session: Session = None) -> int:  # type: ignore
    """Simulates the orphaned row the previous migration created."""
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
def _count_rows(media_id: int, profile_id: int | None, status: TrailerStatusEnum, *, _session: Session = None) -> int:  # type: ignore
    from sqlmodel import select
    stmt = select(MediaTrailerStatus).where(
        MediaTrailerStatus.media_id == media_id,
        MediaTrailerStatus.status == status,
    )
    if profile_id is None:
        stmt = stmt.where(MediaTrailerStatus.profile_id.is_(None))  # type: ignore[union-attr]
    else:
        stmt = stmt.where(MediaTrailerStatus.profile_id == profile_id)
    return len(_session.exec(stmt).all())


def _run_upgrade():
    """Run the orphaned-row-fix SQL from the merged migration.

    The merged migration also adds columns (video_type, tmdb_language, youtube_id) that
    already exist in the test DB schema. We mock batch_alter_table so only the raw SQL
    DELETE/INSERT statements execute.
    """
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
    """Plan 3 — migration must fix NULL-profile PENDING rows."""

    def test_null_profile_pending_rows_deleted(self):
        conn_id = _make_connection()
        media_id = _make_media(conn_id)
        row_id = _insert_null_profile_pending(media_id)

        _run_upgrade()

        assert _count_rows(media_id, None, TrailerStatusEnum.PENDING) == 0, \
            "NULL-profile PENDING rows must be deleted"

    def test_manual_downloaded_row_preserved(self):
        conn_id = _make_connection()
        media_id = _make_media(conn_id, downloaded_at=datetime.datetime(2024, 6, 1, tzinfo=datetime.timezone.utc))
        row_id = _insert_null_profile_downloaded(media_id)

        _run_upgrade()

        assert _count_rows(media_id, None, TrailerStatusEnum.DOWNLOADED) == 1, \
            "NULL-profile DOWNLOADED rows must be preserved"

    def test_profile_linked_rows_created_for_undownloaded_media(self):
        conn_id = _make_connection()
        media_id = _make_media(conn_id, is_movie=True)
        profile_id = _make_profile(for_movies=True, enabled=True)
        _insert_null_profile_pending(media_id)

        _run_upgrade()

        assert _count_rows(media_id, profile_id, TrailerStatusEnum.PENDING) == 1, \
            "Profile-linked PENDING row must be created for undownloaded media"

    def test_already_downloaded_media_gets_no_pending_row(self):
        conn_id = _make_connection()
        media_id = _make_media(
            conn_id, downloaded_at=datetime.datetime(2024, 6, 1, tzinfo=datetime.timezone.utc)
        )
        profile_id = _make_profile(for_movies=True, enabled=True)

        _run_upgrade()

        assert _count_rows(media_id, profile_id, TrailerStatusEnum.PENDING) == 0, \
            "Downloaded media must not get PENDING rows"

    def test_disabled_profile_gets_no_rows(self):
        conn_id = _make_connection()
        media_id = _make_media(conn_id, is_movie=True)
        profile_id = _make_profile(for_movies=True, enabled=False)

        _run_upgrade()

        assert _count_rows(media_id, profile_id, TrailerStatusEnum.PENDING) == 0, \
            "Disabled profile must not get rows created"

    def test_season_rows_created_for_series(self):
        conn_id = _make_connection()
        media_id = _make_media(conn_id, is_movie=False, season_count=3)
        profile_id = _make_profile(for_movies=False, enabled=True, download_season_videos=True)
        _insert_null_profile_pending(media_id)

        _run_upgrade()

        with engine.connect() as conn:
            rows = conn.execute(sa.text("""
                SELECT season FROM mediatrailerstatus
                WHERE media_id = :mid AND profile_id = :pid AND status = 'pending'
                ORDER BY season
            """), {"mid": media_id, "pid": profile_id}).fetchall()
        seasons = [r[0] for r in rows]
        # season 0 (series-level) + seasons 1, 2, 3
        assert 1 in seasons and 2 in seasons and 3 in seasons, \
            "Per-season rows must be created for seasons 1..N"

    def test_season_rows_not_created_without_flag(self):
        conn_id = _make_connection()
        media_id = _make_media(conn_id, is_movie=False, season_count=2)
        profile_id = _make_profile(for_movies=False, enabled=True, download_season_videos=False)

        _run_upgrade()

        with engine.connect() as conn:
            rows = conn.execute(sa.text("""
                SELECT season FROM mediatrailerstatus
                WHERE media_id = :mid AND profile_id = :pid AND season > 0
            """), {"mid": media_id, "pid": profile_id}).fetchall()
        assert len(rows) == 0, "No per-season rows when download_season_videos=False"

    def test_media_with_downloaded_row_gets_no_pending_row(self):
        """Belt-and-suspenders: even with downloaded_at=None, if a DOWNLOADED row
        already exists (e.g. from Step 2.5 in a1b2c3d4e5f6), no PENDING row is created."""
        conn_id = _make_connection()
        media_id = _make_media(conn_id, is_movie=True)
        profile_id = _make_profile(for_movies=True, enabled=True)
        # Simulate a DOWNLOADED row already existing (e.g. from trailer_exists backfill)
        _insert_null_profile_downloaded(media_id)

        _run_upgrade()

        assert _count_rows(media_id, profile_id, TrailerStatusEnum.PENDING) == 0, \
            "Media with an existing DOWNLOADED row must not get PENDING rows"

    def test_existing_profile_rows_not_duplicated(self):
        conn_id = _make_connection()
        media_id = _make_media(conn_id, is_movie=True)
        profile_id = _make_profile(for_movies=True, enabled=True)
        # Pre-existing row — migration must not duplicate it
        _insert_null_profile_pending(media_id)

        _run_upgrade()
        _run_upgrade()  # run twice — idempotent

        assert _count_rows(media_id, profile_id, TrailerStatusEnum.PENDING) == 1, \
            "Migration must be idempotent — no duplicate rows"
