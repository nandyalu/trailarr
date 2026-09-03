"""Tests for media update manager functions."""

import pytest
from sqlmodel import Session

from database.models.connection import ArrType, Connection
from database.models.media import MediaCreate
from database.engine import write_session
import database.manager.media as media_manager


@write_session
def _create_test_connection(
    *,
    _session: Session = None,  # type: ignore
) -> Connection:
    connection = Connection(
        name="Test Plex Connection",
        arr_type=ArrType.PLEX,
        url="http://localhost:32400",
        api_key="test-token",
        monitor_new_media=True,
    )
    _session.add(connection)
    _session.commit()
    _session.refresh(connection)
    return connection


class TestUpdatePlexTrailer:
    """Tests for media_manager.update_plex_trailer."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.connection = _create_test_connection()
        media_data = MediaCreate(
            connection_id=self.connection.id,  # type: ignore
            arr_id=1,
            is_movie=True,
            title="Test Movie",
            txdb_id="tt9999999",
        )
        result = media_manager.create_or_update_bulk([media_data])
        self.media, _, _, _ = result[0]

    def test_sets_plex_trailer_true(self):
        """Sets plex_trailer to True on a media row."""
        media_manager.update_plex_trailer(self.media.id, True)
        updated = media_manager.read(self.media.id)
        assert updated.plex_trailer is True

    def test_sets_plex_trailer_false(self):
        """Sets plex_trailer to False on a media row."""
        media_manager.update_plex_trailer(self.media.id, False)
        updated = media_manager.read(self.media.id)
        assert updated.plex_trailer is False

    def test_sets_plex_trailer_none(self):
        """Resets plex_trailer to None (unknown state)."""
        # First set it to True, then reset
        media_manager.update_plex_trailer(self.media.id, True)
        media_manager.update_plex_trailer(self.media.id, None)
        updated = media_manager.read(self.media.id)
        assert updated.plex_trailer is None

    def test_plex_trailer_defaults_to_none_on_create(self):
        """New media rows have plex_trailer=None by default."""
        assert self.media.plex_trailer is None

    def test_update_does_not_touch_other_fields(self):
        """update_plex_trailer only changes plex_trailer, not other fields."""
        original_title = self.media.title
        original_monitor = self.media.monitor
        media_manager.update_plex_trailer(self.media.id, True)
        updated = media_manager.read(self.media.id)
        assert updated.title == original_title
        assert updated.monitor == original_monitor


class TestUpdateMonitoringPlainWrite:
    """Phase 4: the monitor toggle is pure user intent — a plain flag write
    with no refusals and no download-path coupling."""

    def _make_media(self, txdb_id: str, **overrides) -> int:
        conn = _create_test_connection()
        create = MediaCreate(
            connection_id=conn.id,
            arr_id=1,
            is_movie=True,
            title=f"Monitor Test {txdb_id}",
            txdb_id=txdb_id,
            **overrides,
        )
        result = media_manager.create_or_update_bulk([create])
        return result[0][0].id

    def test_monitor_true_allowed_even_with_trailer(self):
        """The old guardrail refused monitoring media whose trailer exists;
        user intent now always wins (satisfaction prevents re-downloads)."""
        from datetime import datetime, timezone

        import database.manager.download as download_manager
        from database.models.download import DownloadCreate

        media_id = self._make_media("mon1")
        now = datetime.now(timezone.utc)
        download_manager.create(
            DownloadCreate(
                media_id=media_id,
                path=f"/tmp/{media_id}/trailer.mkv",
                file_name="trailer.mkv",
                file_hash=f"hash{media_id}",
                size=1000,
                resolution=1080,
                file_format="mkv",
                video_format="h264",
                audio_format="aac",
                file_exists=True,
                added_at=now,
                updated_at=now,
            )
        )
        msg, updated = media_manager.update_monitoring(media_id, True)
        assert updated is True
        assert media_manager.read(media_id).monitor is True

    def test_monitor_false_plain_write(self):
        media_id = self._make_media("mon2", monitor=True)
        msg, updated = media_manager.update_monitoring(media_id, False)
        assert updated is True
        assert media_manager.read(media_id).monitor is False

    def test_noop_when_already_set(self):
        media_id = self._make_media("mon3", monitor=True)
        msg, updated = media_manager.update_monitoring(media_id, True)
        assert updated is False
        assert "already" in msg


class TestDownloadsCannotWriteMonitor:
    """Phase 4 invariant #6: download-path status writes never touch the
    monitor flag (MediaUpdateDC deliberately has no monitor field)."""

    def test_update_download_facts_leaves_monitor_untouched(self):
        from datetime import datetime, timezone

        from database.models.helpers import MediaUpdateDC

        conn = _create_test_connection()
        create = MediaCreate(
            connection_id=conn.id,
            arr_id=2,
            is_movie=True,
            title="Monitor Untouched",
            txdb_id="mon4",
            monitor=True,
        )
        media_id = media_manager.create_or_update_bulk([create])[0][0].id

        downloaded_at = datetime.now(timezone.utc)
        media_manager.update_download_facts(
            MediaUpdateDC(
                id=media_id,
                yt_id="yt123",
                downloaded_at=downloaded_at,
            )
        )
        media = media_manager.read(media_id)
        assert media.monitor is True  # unchanged despite download facts write
        assert media.youtube_trailer_id == "yt123"
        assert media.downloaded_at is not None

    def test_media_update_dc_has_no_monitor_field(self):
        from database.models.helpers import MediaUpdateDC

        assert "monitor" not in MediaUpdateDC.__slots__
