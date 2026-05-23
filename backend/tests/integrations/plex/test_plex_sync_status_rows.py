"""Tests for PlexConnectionManager._process_item — MediaTrailerStatus row creation.

Verifies that create_rows_for_new_media is called for newly created Plex-only media,
matching the behaviour already present in arr_connection_manager.py.
"""
import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch, call

from db.models.connection import MonitorType


def _make_connection(monitor: MonitorType = MonitorType.MONITOR_MISSING) -> MagicMock:
    conn = MagicMock()
    conn.id = 1
    conn.name = "MyPlex"
    conn.url = "http://plex.local"
    conn.api_key = "token123"
    conn.monitor = monitor
    conn.path_mappings = [
        MagicMock(id=1, path_from="/movies", path_to="/movies", plex_section_key=None)
    ]
    return conn


def _make_section(key: str = "1") -> MagicMock:
    s = MagicMock()
    s.key = key
    s.title = "Movies"
    s.folders = ["/movies"]
    return s


def _make_item(title: str = "The Batman", media_folder: str = "/movies/The Batman (2022)") -> MagicMock:
    item = MagicMock()
    item.title = title
    item.ratingKey = "abc123"
    item.media_filename = "The Batman (2022).mkv"
    item.media_folder = media_folder
    return item


def _make_manager(monitor: MonitorType = MonitorType.MONITOR_MISSING):
    """Create a PlexConnectionManager with all external deps mocked."""
    conn = _make_connection(monitor)
    with patch("integrations.plex.sync.PlexAPI") as mock_api_cls:
        mock_api = MagicMock()
        mock_api.server_url = "http://plex.local"
        mock_api_cls.return_value = mock_api
        from integrations.plex.sync import PlexConnectionManager
        mgr = PlexConnectionManager(conn)
    mgr.api = MagicMock()
    return mgr


class TestProcessItemCreatesStatusRows:
    """create_rows_for_new_media is called when a new Plex-only media item is created."""

    @pytest.mark.asyncio
    async def test_new_media_calls_create_rows_for_new_media(self):
        mgr = _make_manager()
        item = _make_item()
        section = _make_section()
        mock_media_read = MagicMock()
        mock_media_read.id = 42
        mock_media_read.monitor = False

        with (
            patch("integrations.plex.sync.media_repo.read_by_folder_path", return_value=None),
            patch("integrations.plex.sync.parse_plex_item", return_value=MagicMock()),
            patch("integrations.plex.sync.media_repo.create", return_value=mock_media_read),
            patch("integrations.plex.sync.event_service.track_media_added"),
            patch("integrations.plex.sync.media_repo.update_monitor_only"),
            patch("integrations.plex.sync.event_service.track_monitor_changed"),
            patch("services.trailer_profile_service.create_rows_for_new_media") as mock_create,
        ):
            await mgr._process_item(item, section, is_movie=True, plex_folder="/movies/The Batman (2022)")

        mock_create.assert_called_once_with(mock_media_read)

    @pytest.mark.asyncio
    async def test_existing_media_does_not_call_create_rows(self):
        """Plex link-update of an existing Arr item must not create duplicate rows."""
        mgr = _make_manager()
        item = _make_item()
        section = _make_section()
        existing = MagicMock()
        existing.id = 7
        existing.arr_id = 99
        existing.plex_connection_id = mgr.connection_id
        existing.monitor = True

        with (
            patch("integrations.plex.sync.media_repo.read_by_folder_path", return_value=existing),
            patch("integrations.plex.sync.media_repo.update_plex_fields", return_value=False),
            patch("services.trailer_profile_service.create_rows_for_new_media") as mock_create,
        ):
            await mgr._process_item(item, section, is_movie=True, plex_folder="/movies/The Batman (2022)")

        mock_create.assert_not_called()

    @pytest.mark.asyncio
    async def test_monitor_none_still_creates_rows(self):
        """Even with MonitorType.MONITOR_NONE, status rows should be created
        (monitor=False means they won't be picked up by the download loop, but
        the rows should exist for when monitoring is re-enabled)."""
        mgr = _make_manager(monitor=MonitorType.MONITOR_NONE)
        item = _make_item()
        section = _make_section()
        mock_media_read = MagicMock()
        mock_media_read.id = 55
        mock_media_read.monitor = False

        with (
            patch("integrations.plex.sync.media_repo.read_by_folder_path", return_value=None),
            patch("integrations.plex.sync.parse_plex_item", return_value=MagicMock()),
            patch("integrations.plex.sync.media_repo.create", return_value=mock_media_read),
            patch("integrations.plex.sync.event_service.track_media_added"),
            patch("integrations.plex.sync.media_repo.update_monitor_only"),
            patch("integrations.plex.sync.event_service.track_monitor_changed"),
            patch("services.trailer_profile_service.create_rows_for_new_media") as mock_create,
        ):
            await mgr._process_item(item, section, is_movie=True, plex_folder="/movies/The Batman (2022)")

        mock_create.assert_called_once_with(mock_media_read)

    @pytest.mark.asyncio
    async def test_item_outside_configured_library_skipped(self):
        """Items not under a configured path mapping are skipped before any DB call."""
        mgr = _make_manager()
        item = _make_item(media_folder="/other_drive/The Batman (2022)")
        section = _make_section()

        with patch("services.trailer_profile_service.create_rows_for_new_media") as mock_create:
            await mgr._process_item(item, section, is_movie=True, plex_folder="/other_drive/The Batman (2022)")

        mock_create.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_path_mappings_skipped(self):
        """Manager with no path mappings skips all items."""
        mgr = _make_manager()
        mgr.all_path_mappings = []
        item = _make_item()
        section = _make_section()

        with patch("services.trailer_profile_service.create_rows_for_new_media") as mock_create:
            await mgr._process_item(item, section, is_movie=True, plex_folder="/movies/The Batman (2022)")

        mock_create.assert_not_called()
