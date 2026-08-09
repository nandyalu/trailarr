"""Tests for core/tasks/download_attribution.py — the startup pass that
attributes unattributed downloads (profile_id=0) to matching profiles."""

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import call, patch

import pytest
from sqlmodel import Session

import core.base.database.manager.download as download_manager
import core.base.database.manager.media as media_manager
import core.base.database.manager.trailerprofile as trailerprofile_manager
from core.base.database.models.connection import (
    ArrType,
    Connection,
)
from core.base.database.models.download import DownloadCreate
from core.base.database.models.media import MediaCreate
from core.base.database.utils.engine import write_session
from core.tasks.download_attribution import (
    attribute_unattributed_downloads,
    count_tracked_media,
)


def make_profile(
    profile_id: int, priority: int = 100, filters: list | None = None
) -> SimpleNamespace:
    return SimpleNamespace(
        id=profile_id,
        priority=priority,
        customfilter=SimpleNamespace(
            filter_name=f"Profile {profile_id}",
            filters=filters if filters is not None else [],
        ),
    )


def make_download(
    download_id: int,
    media_id: int = 1,
    profile_id: int = 0,
    file_exists: bool = True,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=download_id,
        media_id=media_id,
        profile_id=profile_id,
        file_exists=file_exists,
        file_name=f"trailer-{download_id}.mkv",
    )


def make_media(
    media_id: int = 1,
    downloads: list | None = None,
    is_movie: bool = True,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=media_id,
        title=f"Media {media_id}",
        downloads=downloads if downloads is not None else [],
        is_movie=is_movie,
        monitor=False,
    )


PKG = "core.tasks.download_attribution"


class TestAttributeUnattributedDownloads:

    @pytest.mark.asyncio
    async def test_no_unattributed_downloads_returns_early(self):
        with (
            patch(f"{PKG}.download_manager.read_unattributed", return_value=[]),
            patch(
                f"{PKG}.trailerprofile_manager.get_trailerprofiles"
            ) as mock_profiles,
            patch(
                f"{PKG}.download_manager.update_profile_id"
            ) as mock_update,
        ):
            await attribute_unattributed_downloads()

        mock_profiles.assert_not_called()
        mock_update.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_profiles_leaves_downloads_unattributed(self):
        dl = make_download(1)
        with (
            patch(
                f"{PKG}.download_manager.read_unattributed", return_value=[dl]
            ),
            patch(
                f"{PKG}.trailerprofile_manager.get_trailerprofiles",
                return_value=[],
            ),
            patch(
                f"{PKG}.download_manager.update_profile_id"
            ) as mock_update,
        ):
            await attribute_unattributed_downloads()

        mock_update.assert_not_called()

    @pytest.mark.asyncio
    async def test_single_download_claimed_by_matching_profile(self):
        dl = make_download(1)
        media = make_media(downloads=[dl])
        profile = make_profile(7)
        with (
            patch(
                f"{PKG}.download_manager.read_unattributed", return_value=[dl]
            ),
            patch(
                f"{PKG}.trailerprofile_manager.get_trailerprofiles",
                return_value=[profile],
            ),
            patch(f"{PKG}.media_manager.read", return_value=media),
            patch(
                f"{PKG}.download_manager.update_profile_id"
            ) as mock_update,
        ):
            await attribute_unattributed_downloads()

        mock_update.assert_called_once_with(1, 7)

    @pytest.mark.asyncio
    async def test_oldest_download_gets_highest_priority_profile(self):
        """Unattributed downloads come oldest first; profiles are assigned in
        priority order (lower number = higher priority)."""
        older = make_download(1)
        newer = make_download(2)
        media = make_media(downloads=[older, newer])
        low = make_profile(11, priority=500)
        high = make_profile(22, priority=10)
        with (
            patch(
                f"{PKG}.download_manager.read_unattributed",
                return_value=[older, newer],
            ),
            patch(
                f"{PKG}.trailerprofile_manager.get_trailerprofiles",
                return_value=[low, high],
            ),
            patch(f"{PKG}.media_manager.read", return_value=media),
            patch(
                f"{PKG}.download_manager.update_profile_id"
            ) as mock_update,
        ):
            await attribute_unattributed_downloads()

        assert mock_update.call_args_list == [call(1, 22), call(2, 11)]

    @pytest.mark.asyncio
    async def test_profile_already_owning_download_is_skipped(self):
        """A profile that already owns an active download for the media
        cannot claim a second one."""
        owned = make_download(1, profile_id=7)
        unattributed = make_download(2)
        media = make_media(downloads=[owned, unattributed])
        owner = make_profile(7, priority=10)
        other = make_profile(8, priority=500)
        with (
            patch(
                f"{PKG}.download_manager.read_unattributed",
                return_value=[unattributed],
            ),
            patch(
                f"{PKG}.trailerprofile_manager.get_trailerprofiles",
                return_value=[owner, other],
            ),
            patch(f"{PKG}.media_manager.read", return_value=media),
            patch(
                f"{PKG}.download_manager.update_profile_id"
            ) as mock_update,
        ):
            await attribute_unattributed_downloads()

        mock_update.assert_called_once_with(2, 8)

    @pytest.mark.asyncio
    async def test_download_stays_unattributed_when_nothing_matches(self):
        from core.base.database.models.filter import (
            FilterCondition,
            FilterRead,
        )

        movie_filter = FilterRead(
            id=1,
            customfilter_id=1,
            filter_by="is_movie",
            filter_condition=FilterCondition.EQUALS,
            filter_value="true",
        )
        dl = make_download(1)
        media = make_media(downloads=[dl], is_movie=False)
        profile = make_profile(7, filters=[movie_filter])
        with (
            patch(
                f"{PKG}.download_manager.read_unattributed", return_value=[dl]
            ),
            patch(
                f"{PKG}.trailerprofile_manager.get_trailerprofiles",
                return_value=[profile],
            ),
            patch(f"{PKG}.media_manager.read", return_value=media),
            patch(
                f"{PKG}.download_manager.update_profile_id"
            ) as mock_update,
        ):
            await attribute_unattributed_downloads()

        mock_update.assert_not_called()

    @pytest.mark.asyncio
    async def test_media_read_failure_skips_that_media(self):
        dl1 = make_download(1, media_id=1)
        dl2 = make_download(2, media_id=2)
        media2 = make_media(media_id=2, downloads=[dl2])
        profile = make_profile(7)

        def read_side_effect(media_id):
            if media_id == 1:
                raise Exception("media gone")
            return media2

        with (
            patch(
                f"{PKG}.download_manager.read_unattributed",
                return_value=[dl1, dl2],
            ),
            patch(
                f"{PKG}.trailerprofile_manager.get_trailerprofiles",
                return_value=[profile],
            ),
            patch(f"{PKG}.media_manager.read", side_effect=read_side_effect),
            patch(
                f"{PKG}.download_manager.update_profile_id"
            ) as mock_update,
        ):
            await attribute_unattributed_downloads()

        mock_update.assert_called_once_with(2, 7)


class TestCountTrackedMedia:

    def test_counts_media_with_active_downloads(self):
        """Only downloads with file_exists=True make a media item tracked;
        deleted-only downloads do not count."""
        tracked = make_media(
            media_id=1, downloads=[make_download(1, profile_id=5)]
        )
        untracked = make_media(media_id=2, downloads=[])
        deleted_only = make_media(
            media_id=3, downloads=[make_download(2, file_exists=False)]
        )

        def gen():
            yield from [tracked, untracked, deleted_only]

        with patch(
            f"{PKG}.media_manager.read_all_generator", return_value=gen()
        ):
            assert count_tracked_media() == (1, 3)

    def test_all_tracked(self):
        tracked = make_media(
            media_id=1, downloads=[make_download(1, profile_id=5)]
        )

        def gen():
            yield tracked

        with patch(
            f"{PKG}.media_manager.read_all_generator", return_value=gen()
        ):
            assert count_tracked_media() == (1, 1)


@write_session
def _make_connection(*, _session: Session = None) -> Connection:  # type: ignore
    conn = Connection(
        name="Attribution Test Connection",
        arr_type=ArrType.RADARR,
        url="http://localhost:7878",
        api_key="test_key",
        monitor_new_media=True,
    )
    _session.add(conn)
    _session.commit()
    _session.refresh(conn)
    return conn


def _make_download_create(media_id: int, path: str) -> DownloadCreate:
    now = datetime.now(timezone.utc)
    return DownloadCreate(
        media_id=media_id,
        path=path,
        file_name=path.rsplit("/", 1)[-1],
        file_hash="attrhash123",
        size=100_000_000,
        resolution=1080,
        file_format="mkv",
        video_format="vp9",
        audio_format="opus",
        added_at=now,
        updated_at=now,
        profile_id=0,
    )


def _make_default_like_profile(filter_name: str, is_movie: bool):
    """Create a profile with an is_movie filter plus an explicit
    has_downloads=false state filter. Note: the v0.11.0 shipped defaults
    carry only the is_movie filter — the Phase 5 migration removes
    download-state filters from profiles. The extra filter here exercises
    attribution with a user-added state filter."""
    from core.base.database.models.customfilter import CustomFilterCreate
    from core.base.database.models.filter import (
        FilterCondition,
        FilterCreate,
    )
    from core.base.database.models.trailerprofile import TrailerProfileCreate

    return trailerprofile_manager.create_trailerprofile(
        TrailerProfileCreate(
            customfilter=CustomFilterCreate(
                filter_name=filter_name,
                filters=[
                    FilterCreate(
                        filter_by="is_movie",
                        filter_condition=FilterCondition.EQUALS,
                        filter_value="true" if is_movie else "false",
                    ),
                    FilterCreate(
                        filter_by="has_downloads",
                        filter_condition=FilterCondition.EQUALS,
                        filter_value="false",
                    ),
                ],
            )
        )
    )


class TestAttributionAgainstRealDatabase:
    """End-to-end check against the real test DB using two profiles named
    like the shipped defaults ('Movie Trailers' / 'Series Trailers'). Each
    filters on is_movie plus an explicit has_downloads=false state filter —
    a stricter shape than the v0.11.0 defaults, which carry only is_movie
    (Phase 5 removes download-state filters from profiles)."""

    @pytest.mark.asyncio
    async def test_default_profiles_claim_movie_and_series_downloads(self):
        existing = {
            p.customfilter.filter_name
            for p in trailerprofile_manager.get_trailerprofiles()
        }
        if "Movie Trailers" not in existing:
            _make_default_like_profile("Movie Trailers", is_movie=True)
        if "Series Trailers" not in existing:
            _make_default_like_profile("Series Trailers", is_movie=False)
        by_name = {
            p.customfilter.filter_name: p
            for p in trailerprofile_manager.get_trailerprofiles()
        }

        conn = _make_connection()
        movie = media_manager.create(
            MediaCreate(
                connection_id=conn.id,  # type: ignore[arg-type]
                arr_id=90001,
                is_movie=True,
                title="Attribution Movie",
                txdb_id="attr-movie-1",
            )
        )
        series = media_manager.create(
            MediaCreate(
                connection_id=conn.id,  # type: ignore[arg-type]
                arr_id=90002,
                is_movie=False,
                title="Attribution Series",
                txdb_id="attr-series-1",
            )
        )
        movie_dl = download_manager.create(
            _make_download_create(movie.id, "/media/attr-movie/m-trailer.mkv")
        )
        series_dl = download_manager.create(
            _make_download_create(series.id, "/media/attr-series/s-trailer.mkv")
        )
        # The exact upgrade scenario: the trailer download rows already exist
        # (file_exists=True), which the default profiles' has_downloads=false
        # state filter must not block during attribution.

        await attribute_unattributed_downloads()

        assert (
            download_manager.read(movie_dl.id).profile_id
            == by_name["Movie Trailers"].id
        )
        assert (
            download_manager.read(series_dl.id).profile_id
            == by_name["Series Trailers"].id
        )

    @pytest.mark.asyncio
    async def test_rerun_is_idempotent(self):
        """A second pass finds nothing to claim and changes nothing."""
        before = {
            d["id"]: d["profile_id"]
            for d in download_manager.read_all_raw()
        }
        await attribute_unattributed_downloads()
        after = {
            d["id"]: d["profile_id"]
            for d in download_manager.read_all_raw()
        }
        assert before == after


class TestUnclaimedReasons:

    @pytest.mark.asyncio
    async def test_logs_extra_file_reason_when_profiles_taken(self, caplog):
        owned = make_download(1, profile_id=7)
        unattributed = make_download(2)
        media = make_media(downloads=[owned, unattributed])
        profile = make_profile(7)
        with (
            patch(
                f"{PKG}.download_manager.read_unattributed",
                return_value=[unattributed],
            ),
            patch(
                f"{PKG}.trailerprofile_manager.get_trailerprofiles",
                return_value=[profile],
            ),
            patch(f"{PKG}.media_manager.read", return_value=media),
            patch(f"{PKG}.download_manager.update_profile_id"),
        ):
            with caplog.at_level("INFO"):
                await attribute_unattributed_downloads()

        assert "extra trailer file" in caplog.text

    @pytest.mark.asyncio
    async def test_logs_no_match_reason_when_nothing_matches(self, caplog):
        from core.base.database.models.filter import (
            FilterCondition,
            FilterRead,
        )

        movie_filter = FilterRead(
            id=1,
            customfilter_id=1,
            filter_by="is_movie",
            filter_condition=FilterCondition.EQUALS,
            filter_value="true",
        )
        dl = make_download(1)
        media = make_media(downloads=[dl], is_movie=False)
        profile = make_profile(7, filters=[movie_filter])
        with (
            patch(
                f"{PKG}.download_manager.read_unattributed", return_value=[dl]
            ),
            patch(
                f"{PKG}.trailerprofile_manager.get_trailerprofiles",
                return_value=[profile],
            ),
            patch(f"{PKG}.media_manager.read", return_value=media),
            patch(f"{PKG}.download_manager.update_profile_id"),
        ):
            with caplog.at_level("INFO"):
                await attribute_unattributed_downloads()

        assert "no profile filters match this media" in caplog.text
