"""Phase 3: built-in media filters, recently-downloaded and home stats are
decided by download rows (EXISTS), never by the trailer_exists/status
mirror columns (plans/phase-03-dynamic-status.md, design decision 4)."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlmodel import Session

import core.base.database.manager.download as download_manager
import core.base.database.manager.general as general_manager
import core.base.database.manager.media as media_manager
from core.base.database.models.connection import (
    ArrType,
    Connection,
    MonitorType,
)
from core.base.database.models.download import DownloadCreate
from core.base.database.models.media import MediaCreate, MonitorStatus
from core.base.database.utils.engine import write_session

NOW = datetime.now(timezone.utc)


@write_session
def _make_connection(
    *,
    _session: Session = None,  # type: ignore
) -> Connection:
    conn = Connection(
        name="Filters Test Connection",
        arr_type=ArrType.RADARR,
        url="http://localhost:7878",
        api_key="test_key",
        monitor=MonitorType.MONITOR_MISSING,
    )
    _session.add(conn)
    _session.commit()
    _session.refresh(conn)
    return conn


def _make_media(
    connection_id: int,
    txdb_id: str,
    monitor: bool = False,
    trailer_exists: bool = False,
) -> MediaCreate:
    return MediaCreate(
        connection_id=connection_id,
        arr_id=1,
        is_movie=True,
        title=f"Filters Media {txdb_id}",
        txdb_id=txdb_id,
        monitor=monitor,
        trailer_exists=trailer_exists,
    )


def _make_download(
    media_id: int, file_exists: bool = True, age_hours: int = 0
) -> DownloadCreate:
    added = NOW - timedelta(hours=age_hours)
    return DownloadCreate(
        media_id=media_id,
        path=f"/tmp/{media_id}/trailer.mkv",
        file_name="trailer.mkv",
        file_hash=f"hash{media_id}",
        size=1000,
        resolution=1080,
        file_format="mkv",
        video_format="h264",
        audio_format="aac",
        file_exists=file_exists,
        added_at=added,
        updated_at=added,
    )


class TestDownloadsDrivenFilters:
    """The seeded rows deliberately contradict their mirror columns, so any
    filter still reading trailer_exists fails these tests."""

    @pytest.fixture(autouse=True)
    def seed(self):
        conn = _make_connection()
        cid = conn.id
        result = media_manager.create_or_update_bulk(
            [
                # active download; stale trailer_exists=False on purpose
                _make_media(cid, f"flt{cid}a", monitor=False),
                # monitored, nothing downloaded; stale trailer_exists=True
                _make_media(cid, f"flt{cid}b", monitor=True,
                            trailer_exists=True),
                # deleted download (file_exists=False), unmonitored
                _make_media(cid, f"flt{cid}c", monitor=False),
            ]
        )
        self.with_download = result[0][0]
        self.monitored = result[1][0]
        self.deleted_download = result[2][0]
        download_manager.create(_make_download(self.with_download.id))
        download_manager.create(
            _make_download(self.deleted_download.id, file_exists=False)
        )

    def _ids(self, filter_by: str) -> set[int]:
        return {m.id for m in media_manager.read_all(filter_by=filter_by)}

    def test_downloaded_filter_uses_download_rows(self):
        downloaded = self._ids("downloaded")
        assert self.with_download.id in downloaded
        assert self.monitored.id not in downloaded  # despite trailer_exists
        assert self.deleted_download.id not in downloaded

    def test_missing_filter_uses_download_rows(self):
        missing = self._ids("missing")
        assert self.with_download.id not in missing
        assert self.monitored.id in missing  # despite trailer_exists=True
        assert self.deleted_download.id in missing

    def test_unmonitored_filter(self):
        unmonitored = self._ids("unmonitored")
        assert self.deleted_download.id in unmonitored
        assert self.with_download.id not in unmonitored  # has active download
        assert self.monitored.id not in unmonitored  # monitored

    def test_monitored_filter_stays_flag_based(self):
        monitored = self._ids("monitored")
        assert self.monitored.id in monitored
        assert self.with_download.id not in monitored

    def test_computed_status_matches_filters(self):
        """The list filter and the computed status agree by construction."""
        media = media_manager.read(self.with_download.id)
        assert media.status == MonitorStatus.DOWNLOADED
        media = media_manager.read(self.monitored.id)
        assert media.status == MonitorStatus.MONITORED
        media = media_manager.read(self.deleted_download.id)
        assert media.status == MonitorStatus.MISSING


class TestRecentlyDownloaded:

    def test_ordered_by_download_added_at(self):
        conn = _make_connection()
        cid = conn.id
        result = media_manager.create_or_update_bulk(
            [
                _make_media(cid, f"rec{cid}old"),
                _make_media(cid, f"rec{cid}new"),
                _make_media(cid, f"rec{cid}none", monitor=True),
            ]
        )
        older, newer, no_download = (r[0] for r in result)
        download_manager.create(_make_download(older.id, age_hours=48))
        download_manager.create(_make_download(newer.id, age_hours=1))

        recent = media_manager.read_recently_downloaded(limit=100)
        ids = [m.id for m in recent]
        assert newer.id in ids and older.id in ids
        assert ids.index(newer.id) < ids.index(older.id)
        assert no_download.id not in ids

    def test_deleted_downloads_do_not_qualify(self):
        conn = _make_connection()
        result = media_manager.create_or_update_bulk(
            [_make_media(conn.id, f"rec{conn.id}del")]
        )
        media = result[0][0]
        download_manager.create(
            _make_download(media.id, file_exists=False)
        )
        ids = [m.id for m in media_manager.read_recently_downloaded()]
        assert media.id not in ids


class TestStats:

    def test_trailers_detected_counts_media_with_active_downloads(self):
        before = general_manager.get_stats()
        conn = _make_connection()
        result = media_manager.create_or_update_bulk(
            [
                _make_media(conn.id, f"st{conn.id}a"),
                # stale mirror flag must NOT count
                _make_media(conn.id, f"st{conn.id}b", trailer_exists=True),
            ]
        )
        with_download = result[0][0]
        # two active downloads for ONE media -> still counts once (distinct)
        download_manager.create(_make_download(with_download.id))
        download_manager.create(
            _make_download(with_download.id, age_hours=5)
        )
        after = general_manager.get_stats()
        assert after.trailers_detected == before.trailers_detected + 1
