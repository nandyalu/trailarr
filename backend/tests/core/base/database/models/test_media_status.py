"""Phase 3 (plans/phase-03-dynamic-status.md): list-level media status is
computed from downloads + monitor, never read from the stored column."""

from datetime import datetime, timezone

from core.base.database.models.download import DownloadRead
from core.base.database.models.media import (
    MediaRead,
    MonitorStatus,
    compute_media_status,
)

NOW = datetime.now(timezone.utc)


def make_download(
    download_id: int = 1,
    profile_id: int = 0,
    file_exists: bool = True,
) -> DownloadRead:
    return DownloadRead(
        id=download_id,
        media_id=1,
        path="/tmp/trailer.mkv",
        file_name="trailer.mkv",
        file_hash="abc123",
        size=1000,
        resolution=1080,
        file_format="mkv",
        video_format="h264",
        audio_format="aac",
        file_exists=file_exists,
        profile_id=profile_id,
        added_at=NOW,
        updated_at=NOW,
    )


def make_media_read(
    monitor: bool = False,
    status: MonitorStatus = MonitorStatus.MISSING,
    downloads: list[DownloadRead] | None = None,
) -> MediaRead:
    return MediaRead(
        id=1,
        connection_id=1,
        arr_id=10,
        title="Test Movie",
        txdb_id="123",
        monitor=monitor,
        status=status,
        downloads=downloads or [],
        added_at=NOW,
        updated_at=NOW,
        downloaded_at=None,
    )


class TestComputeMediaStatus:

    def test_active_download_wins(self):
        downloads = [make_download(file_exists=True)]
        assert (
            compute_media_status(False, downloads) == MonitorStatus.DOWNLOADED
        )

    def test_active_download_wins_even_when_monitored(self):
        downloads = [make_download(file_exists=True)]
        assert (
            compute_media_status(True, downloads) == MonitorStatus.DOWNLOADED
        )

    def test_deleted_download_does_not_count(self):
        downloads = [make_download(file_exists=False)]
        assert (
            compute_media_status(True, downloads) == MonitorStatus.MONITORED
        )
        assert compute_media_status(False, downloads) == MonitorStatus.MISSING

    def test_monitored_when_no_downloads(self):
        assert compute_media_status(True, []) == MonitorStatus.MONITORED

    def test_missing_when_nothing(self):
        assert compute_media_status(False, []) == MonitorStatus.MISSING

    def test_unattributed_download_still_counts(self):
        """Status is per media, not per profile — an unattributed active
        download (profile_id=0) still means a trailer exists on disk."""
        downloads = [make_download(profile_id=0)]
        assert (
            compute_media_status(False, downloads) == MonitorStatus.DOWNLOADED
        )


class TestMediaReadDerivesStatus:
    """MediaRead.status is always the computed value — the stored column is
    ignored at read time (W6: API consumers keep seeing truthy data)."""

    def test_stored_status_is_overridden_by_computed(self):
        media = make_media_read(
            monitor=True,
            status=MonitorStatus.DOWNLOADED,  # stale stored value
            downloads=[],
        )
        assert media.status == MonitorStatus.MONITORED

    def test_stuck_downloading_is_impossible_at_read_time(self):
        """The stuck-DOWNLOADING bug class: whatever the column holds, a
        MediaRead never reports DOWNLOADING (it is runtime-only state)."""
        media = make_media_read(
            monitor=True,
            status=MonitorStatus.DOWNLOADING,
            downloads=[],
        )
        assert media.status == MonitorStatus.MONITORED

    def test_active_download_reports_downloaded(self):
        media = make_media_read(
            monitor=False,
            status=MonitorStatus.MISSING,  # stale stored value
            downloads=[make_download()],
        )
        assert media.status == MonitorStatus.DOWNLOADED

    def test_unmonitored_no_downloads_reports_missing(self):
        media = make_media_read(
            monitor=False,
            status=MonitorStatus.MONITORED,
            downloads=[],
        )
        assert media.status == MonitorStatus.MISSING
