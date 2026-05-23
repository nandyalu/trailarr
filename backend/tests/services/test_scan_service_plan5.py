"""Tests for Plan 5 — File Scanner: MediaTrailerStatus Attribution.

Covers:
- _build_filename_pattern: regex construction from templates
- _attribute_tier1: template reverse-match
- _attribute_tier2: metadata-based match
- _process_trailer_changes: attribution flow with status row updates
"""
import datetime
import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from db.models.media import MediaRead
from services.scan_service import (
    _attribute_tier1,
    _attribute_tier2,
    _build_filename_pattern,
)


# ─── helpers ──────────────────────────────────────────────────────────────────

def _make_media(**kwargs) -> MediaRead:
    defaults = dict(
        id=1, connection_id=1, arr_id=1, is_movie=True,
        title="The Batman", clean_title="the batman", year=2022,
        language="en", studio="DC", txdb_id="414906", title_slug="the-batman",
        monitor=True, arr_monitored=True, media_exists=False, media_filename="",
        season_count=0, runtime=176,
        added_at=datetime.datetime(2022, 3, 4, tzinfo=datetime.timezone.utc),
        updated_at=datetime.datetime(2022, 3, 4, tzinfo=datetime.timezone.utc),
        downloaded_at=None, folder_path="/media/The Batman (2022)",
    )
    defaults.update(kwargs)
    return MediaRead(**defaults)


def _make_profile(
    pid: int = 1,
    file_name: str = "{title} ({year})-trailer.{ext}",
    for_movies: bool = True,
    enabled: bool = True,
    video_resolution: int = 1080,
    min_duration: float = 60.0,
    max_duration: float = 600.0,
):
    p = MagicMock()
    p.id = pid
    p.file_name = file_name
    p.for_movies = for_movies
    p.enabled = enabled
    p.video_resolution = video_resolution
    p.min_duration = min_duration
    p.max_duration = max_duration
    return p


# ─── _build_filename_pattern ──────────────────────────────────────────────────

class TestBuildFilenamePattern:
    def test_default_template_matches_expected_filename(self):
        pattern = _build_filename_pattern("{title} ({year})-trailer.{ext}")
        assert pattern.match("The Batman (2022)-trailer.mkv")

    def test_default_template_captures_ext(self):
        pattern = _build_filename_pattern("{title} ({year})-trailer.{ext}")
        m = pattern.match("The Batman (2022)-trailer.mkv")
        assert m is not None
        assert m.group("ext") == "mkv"

    def test_season_captured_as_digits(self):
        pattern = _build_filename_pattern("{title}-S{season}E{sequence}.{ext}")
        m = pattern.match("The Show-S02E01.mp4")
        assert m is not None
        assert m.group("season") == "02"
        assert m.group("sequence") == "01"

    def test_no_match_returns_none(self):
        pattern = _build_filename_pattern("{title} ({year})-trailer.{ext}")
        assert pattern.match("random_file_name.mkv") is None

    def test_ii_placeholder_is_optional(self):
        pattern = _build_filename_pattern("{title}{ii}-trailer.{ext}")
        assert pattern.match("The Batman-trailer.mkv")
        assert pattern.match("The Batman2-trailer.mkv")

    def test_case_insensitive(self):
        pattern = _build_filename_pattern("{title} ({year})-trailer.{ext}")
        assert pattern.match("THE BATMAN (2022)-TRAILER.MKV")


# ─── _attribute_tier1 ─────────────────────────────────────────────────────────

class TestAttributeTier1:
    def test_matches_default_template(self):
        media = _make_media()
        profile = _make_profile(pid=1, file_name="{title} ({year})-trailer.{ext}")
        result = _attribute_tier1("The Batman (2022)-trailer.mkv", [profile], media)
        assert result == [(1, 0, 1)]

    def test_no_match_returns_empty(self):
        media = _make_media()
        profile = _make_profile(pid=1, file_name="{title} ({year})-trailer.{ext}")
        result = _attribute_tier1("random_file.mkv", [profile], media)
        assert result == []

    def test_skips_disabled_profiles(self):
        media = _make_media()
        profile = _make_profile(pid=1, file_name="{title} ({year})-trailer.{ext}", enabled=False)
        result = _attribute_tier1("The Batman (2022)-trailer.mkv", [profile], media)
        assert result == []

    def test_skips_wrong_media_type(self):
        media = _make_media(is_movie=False)
        profile = _make_profile(pid=1, for_movies=True)
        result = _attribute_tier1("The Batman (2022)-trailer.mkv", [profile], media)
        assert result == []

    def test_extracts_season_from_filename(self):
        media = _make_media(is_movie=False)
        profile = _make_profile(
            pid=2,
            file_name="{title}-S{season}.{ext}",
            for_movies=False,
        )
        result = _attribute_tier1("The Show-S03.mkv", [profile], media)
        assert len(result) == 1
        _, season, _ = result[0]
        assert season == 3

    def test_extracts_sequence_from_filename(self):
        media = _make_media(is_movie=False)
        profile = _make_profile(
            pid=2,
            file_name="{title}-S{season}-{sequence}.{ext}",
            for_movies=False,
        )
        result = _attribute_tier1("The Show-S02-3.mkv", [profile], media)
        assert len(result) == 1
        _, season, sequence = result[0]
        assert season == 2
        assert sequence == 3

    def test_first_match_wins_on_multiple_profiles(self):
        media = _make_media()
        p1 = _make_profile(pid=1, file_name="{title} ({year})-trailer.{ext}")
        p2 = _make_profile(pid=2, file_name="{title} ({year})-trailer.{ext}")
        result = _attribute_tier1("The Batman (2022)-trailer.mkv", [p1, p2], media)
        assert len(result) == 2
        assert result[0][0] == 1

    def test_invalid_regex_profile_skipped_gracefully(self):
        media = _make_media()
        bad_profile = _make_profile(pid=99, file_name="{title} [unclosed")
        good_profile = _make_profile(pid=1, file_name="{title} ({year})-trailer.{ext}")
        result = _attribute_tier1("The Batman (2022)-trailer.mkv", [bad_profile, good_profile], media)
        assert any(r[0] == 1 for r in result)
        assert not any(r[0] == 99 for r in result)


# ─── _attribute_tier2 ─────────────────────────────────────────────────────────

class TestAttributeTier2:
    def _make_video_stream(self, height: int):
        s = MagicMock()
        s.codec_type = "video"
        s.coded_height = height
        return s

    def _make_info(self, height: int, duration: float):
        info = MagicMock()
        info.streams = [self._make_video_stream(height)]
        info.duration_seconds = duration
        return info

    def test_matches_resolution_and_duration(self):
        media = _make_media()
        profile = _make_profile(pid=1, video_resolution=1080, min_duration=60.0, max_duration=600.0)
        info = self._make_info(height=1080, duration=120.0)
        with (
            patch("download.analysis.get_media_info", return_value=info),
            patch("download.pipeline.get_resolution_label", return_value=1080),
        ):
            result = _attribute_tier2("/media/trailer.mkv", [profile], media)
        assert result == [1]

    def test_rejects_low_resolution(self):
        media = _make_media()
        profile = _make_profile(pid=1, video_resolution=1080, min_duration=60.0, max_duration=600.0)
        info = self._make_info(height=720, duration=120.0)
        with (
            patch("download.analysis.get_media_info", return_value=info),
            patch("download.pipeline.get_resolution_label", return_value=720),
        ):
            result = _attribute_tier2("/media/trailer.mkv", [profile], media)
        assert result == []

    def test_rejects_duration_too_short(self):
        media = _make_media()
        profile = _make_profile(pid=1, video_resolution=1080, min_duration=60.0, max_duration=600.0)
        info = self._make_info(height=1080, duration=30.0)
        with (
            patch("download.analysis.get_media_info", return_value=info),
            patch("download.pipeline.get_resolution_label", return_value=1080),
        ):
            result = _attribute_tier2("/media/trailer.mkv", [profile], media)
        assert result == []

    def test_rejects_duration_too_long(self):
        media = _make_media()
        profile = _make_profile(pid=1, video_resolution=1080, min_duration=60.0, max_duration=600.0)
        info = self._make_info(height=1080, duration=700.0)
        with (
            patch("download.analysis.get_media_info", return_value=info),
            patch("download.pipeline.get_resolution_label", return_value=1080),
        ):
            result = _attribute_tier2("/media/trailer.mkv", [profile], media)
        assert result == []

    def test_returns_empty_when_no_media_info(self):
        media = _make_media()
        profile = _make_profile(pid=1)
        with patch("download.analysis.get_media_info", return_value=None):
            result = _attribute_tier2("/media/trailer.mkv", [profile], media)
        assert result == []

    def test_skips_disabled_profile(self):
        media = _make_media()
        profile = _make_profile(pid=1, enabled=False, video_resolution=1080, min_duration=60.0, max_duration=600.0)
        info = self._make_info(height=1080, duration=120.0)
        with (
            patch("download.analysis.get_media_info", return_value=info),
            patch("download.pipeline.get_resolution_label", return_value=1080),
        ):
            result = _attribute_tier2("/media/trailer.mkv", [profile], media)
        assert result == []

    def test_skips_wrong_media_type(self):
        media = _make_media(is_movie=False)
        profile = _make_profile(pid=1, for_movies=True, video_resolution=1080, min_duration=60.0, max_duration=600.0)
        info = self._make_info(height=1080, duration=120.0)
        with (
            patch("download.analysis.get_media_info", return_value=info),
            patch("download.pipeline.get_resolution_label", return_value=1080),
        ):
            result = _attribute_tier2("/media/trailer.mkv", [profile], media)
        assert result == []

    def test_handles_no_video_stream(self):
        media = _make_media()
        profile = _make_profile(pid=1, video_resolution=1080, min_duration=60.0, max_duration=600.0)
        info = MagicMock()
        info.streams = []
        info.duration_seconds = 120.0
        with (
            patch("download.analysis.get_media_info", return_value=info),
            patch("download.pipeline.get_resolution_label", return_value=0),
        ):
            result = _attribute_tier2("/media/trailer.mkv", [profile], media)
        assert result == []


# ─── _process_trailer_changes attribution flow ───────────────────────────────

class TestProcessTrailerChangesAttribution:
    """Test that _process_trailer_changes calls attribution and updates status rows."""

    def _make_download(self, path: str, file_exists: bool = True):
        d = MagicMock()
        d.path = path
        d.file_exists = file_exists
        d.id = 10
        return d

    @pytest.mark.asyncio
    async def test_tier1_match_links_status_row(self):
        from services.scan_service import _process_trailer_changes
        from db.models.event import EventSource

        media = _make_media()
        trailer_path = "/media/The Batman (2022)/The Batman (2022)-trailer.mkv"
        profile = _make_profile(pid=5, file_name="{title} ({year})-trailer.{ext}")
        mock_row = MagicMock()
        mock_row.id = 77

        with (
            patch("services.scan_service.trailer_profile_repo.read_all", return_value=[profile]),
            patch("services.scan_service._attribute_tier1", return_value=[(5, 0, 1)]),
            patch("services.scan_service._attribute_tier2", return_value=[]),
            patch("services.scan_service.trailer_status_repo.get_first_pending_row_for_profile", return_value=mock_row),
            patch("services.scan_service.record_new_trailer_download", new_callable=AsyncMock) as mock_record,
            patch("services.scan_service.event_service.track_trailer_detected"),
            patch("services.scan_service.issue_repo.resolve", return_value=False),
        ):
            new_count, _ = await _process_trailer_changes(
                media,
                {trailer_path},
                existing_downloads=[],
                deleted_downloads=[],
                source=EventSource.SYSTEM,
            )

        assert new_count == 1
        mock_record.assert_called_once()
        call_kwargs = mock_record.call_args
        assert call_kwargs.kwargs.get("status_row_id") == 77
        assert call_kwargs.args[1] == 5

    @pytest.mark.asyncio
    async def test_tier2_match_links_status_row(self):
        from services.scan_service import _process_trailer_changes
        from db.models.event import EventSource

        media = _make_media()
        trailer_path = "/media/The Batman (2022)/trailer.mkv"
        mock_row = MagicMock()
        mock_row.id = 88

        with (
            patch("services.scan_service.trailer_profile_repo.read_all", return_value=[]),
            patch("services.scan_service._attribute_tier1", return_value=[]),
            patch("services.scan_service._attribute_tier2", return_value=[3]),
            patch("services.scan_service.trailer_status_repo.get_first_pending_row_for_profile", return_value=mock_row),
            patch("services.scan_service.record_new_trailer_download", new_callable=AsyncMock) as mock_record,
            patch("services.scan_service.event_service.track_trailer_detected"),
            patch("services.scan_service.issue_repo.resolve", return_value=False),
        ):
            new_count, _ = await _process_trailer_changes(
                media,
                {trailer_path},
                existing_downloads=[],
                deleted_downloads=[],
                source=EventSource.SYSTEM,
            )

        assert new_count == 1
        mock_record.assert_called_once()
        call_kwargs = mock_record.call_args
        assert call_kwargs.kwargs.get("status_row_id") == 88
        assert call_kwargs.args[1] == 3

    @pytest.mark.asyncio
    async def test_unattributed_file_uses_profile_zero(self):
        from services.scan_service import _process_trailer_changes
        from db.models.event import EventSource

        media = _make_media()
        trailer_path = "/media/The Batman (2022)/unknown.mkv"

        with (
            patch("services.scan_service.trailer_profile_repo.read_all", return_value=[]),
            patch("services.scan_service._attribute_tier1", return_value=[]),
            patch("services.scan_service._attribute_tier2", return_value=[]),
            patch("services.scan_service.record_new_trailer_download", new_callable=AsyncMock) as mock_record,
            patch("services.scan_service.event_service.track_trailer_detected"),
            patch("services.scan_service.issue_repo.resolve", return_value=False),
        ):
            new_count, _ = await _process_trailer_changes(
                media,
                {trailer_path},
                existing_downloads=[],
                deleted_downloads=[],
                source=EventSource.SYSTEM,
            )

        assert new_count == 1
        mock_record.assert_called_once()
        assert mock_record.call_args.args[1] == 0

    @pytest.mark.asyncio
    async def test_tier1_no_pending_row_still_records(self):
        from services.scan_service import _process_trailer_changes
        from db.models.event import EventSource

        media = _make_media()
        trailer_path = "/media/The Batman (2022)/The Batman (2022)-trailer.mkv"

        with (
            patch("services.scan_service.trailer_profile_repo.read_all", return_value=[]),
            patch("services.scan_service._attribute_tier1", return_value=[(5, 0, 1)]),
            patch("services.scan_service.trailer_status_repo.get_first_pending_row_for_profile", return_value=None),
            patch("services.scan_service.record_new_trailer_download", new_callable=AsyncMock) as mock_record,
            patch("services.scan_service.event_service.track_trailer_detected"),
            patch("services.scan_service.issue_repo.resolve", return_value=False),
        ):
            new_count, _ = await _process_trailer_changes(
                media,
                {trailer_path},
                existing_downloads=[],
                deleted_downloads=[],
                source=EventSource.SYSTEM,
            )

        assert new_count == 1
        mock_record.assert_called_once()
        assert mock_record.call_args.kwargs.get("status_row_id") is None

    @pytest.mark.asyncio
    async def test_existing_paths_not_re_recorded(self):
        from services.scan_service import _process_trailer_changes
        from db.models.event import EventSource

        media = _make_media()
        trailer_path = "/media/The Batman (2022)/trailer.mkv"
        existing = self._make_download(trailer_path)

        with (
            patch("services.scan_service.trailer_profile_repo.read_all", return_value=[]),
            patch("services.scan_service.record_new_trailer_download", new_callable=AsyncMock) as mock_record,
            patch("services.scan_service.event_service.track_trailer_detected"),
            patch("services.scan_service.issue_repo.resolve", return_value=False),
        ):
            new_count, _ = await _process_trailer_changes(
                media,
                {trailer_path},
                existing_downloads=[existing],
                deleted_downloads=[],
                source=EventSource.SYSTEM,
            )

        assert new_count == 0
        mock_record.assert_not_called()

    @pytest.mark.asyncio
    async def test_deleted_file_creates_issue(self):
        from services.scan_service import _process_trailer_changes
        from db.models.event import EventSource
        import os

        media = _make_media()
        gone_path = "/media/The Batman (2022)/gone.mkv"
        dl = self._make_download(gone_path)

        with (
            patch("services.scan_service.trailer_profile_repo.read_all", return_value=[]),
            patch("services.scan_service.issue_repo.resolve", return_value=False),
            patch("services.scan_service.download_repo.mark_as_deleted"),
            patch("services.scan_service.issue_repo.upsert") as mock_upsert,
            patch("services.scan_service.event_service.track_trailer_deleted"),
            patch("services.scan_service.ws_broadcast"),
            patch("os.path.exists", return_value=False),
        ):
            _, missing_count = await _process_trailer_changes(
                media,
                set(),
                existing_downloads=[dl],
                deleted_downloads=[],
                source=EventSource.SYSTEM,
            )

        assert missing_count == 1
        mock_upsert.assert_called_once()

    @pytest.mark.asyncio
    async def test_restored_file_resolves_issue(self):
        from services.scan_service import _process_trailer_changes
        from db.models.event import EventSource

        media = _make_media()
        restored_path = "/media/The Batman (2022)/trailer.mkv"
        deleted_dl = self._make_download(restored_path)

        with (
            patch("services.scan_service.trailer_profile_repo.read_all", return_value=[]),
            patch("services.scan_service._attribute_tier1", return_value=[]),
            patch("services.scan_service._attribute_tier2", return_value=[]),
            patch("services.scan_service.record_new_trailer_download", new_callable=AsyncMock),
            patch("services.scan_service.event_service.track_trailer_detected"),
            patch("services.scan_service.issue_repo.resolve", return_value=True) as mock_resolve,
            patch("services.scan_service.ws_broadcast"),
        ):
            await _process_trailer_changes(
                media,
                {restored_path},
                existing_downloads=[],
                deleted_downloads=[deleted_dl],
                source=EventSource.SYSTEM,
            )

        mock_resolve.assert_called_once()
