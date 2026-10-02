"""Tests for the download path of `Upgrade To TMDB Trailer` —
plans/track-tmdb-upgrade.md, decisions 7–9 and wargame W2, W3.

The delete and rename steps run on real files in a temporary folder. The
database, YouTube and the websocket are the only things replaced.
"""

from contextlib import ExitStack
import threading
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from database.models.mediavideo import VideoSource
from exceptions import DownloadFailedError
from services.trailers.video_analysis import VideoInfo

PKG = "services.trailers.trailer"


def _video(video_id: str, source=VideoSource.TMDB):
    return SimpleNamespace(video_id=video_id, source=source, language="en")


def _download(download_id: int, path: Path, youtube_id: str):
    return SimpleNamespace(
        id=download_id,
        path=str(path),
        youtube_id=youtube_id,
        profile_id=1,
        file_exists=True,
    )


@pytest.fixture
def media():
    media = MagicMock()
    media.id = 1
    media.title = "Test Movie"
    media.downloads = []
    media.plex_connection_id = None
    return media


@pytest.fixture
def profile():
    profile = MagicMock()
    profile.id = 1
    profile.customfilter.filter_name = "Movies"
    profile.upgrade_to_tmdb = True
    profile.delete_replaced_trailer = True
    profile.always_search = False
    profile.language = ""
    profile.notify_plex = False
    profile.skip_if_plex_trailer = True
    return profile


@pytest.fixture
def video_info():
    now = datetime.now(timezone.utc)
    return VideoInfo(
        name="new.mkv",
        file_path="/tmp/new.mkv",
        format_name="matroska",
        duration_seconds=120,
        duration="0:02:00",
        size=1,
        bitrate="1 Mbps",
        streams=[],
        youtube_id="tmdb1",
        youtube_channel="Studio",
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def folder(tmp_path):
    """A Trailers folder with the old trailer and the new one in it."""
    old = tmp_path / "Test Movie-trailer.mkv"
    new = tmp_path / "Test Movie 2-trailer.mkv"
    old.write_bytes(b"old")
    new.write_bytes(b"new")
    return SimpleNamespace(old=old, new=new)


@pytest.fixture
def pipeline(folder, video_info):
    """Everything around the upgrade steps, replaced."""

    async def delete(path, media_id):
        Path(path).unlink()
        return True

    with ExitStack() as stack:
        mocks = SimpleNamespace(
            candidates=stack.enter_context(
                patch(f"{PKG}.video_manager.read_candidates")
            ),
            get_video_id=stack.enter_context(
                patch(
                    f"{PKG}.trailer_search.get_video_id", return_value="tmdb1"
                )
            ),
            plex=stack.enter_context(
                patch(
                    f"{PKG}._check_plex_trailer",
                    new_callable=AsyncMock,
                    return_value=True,
                )
            ),
            download=stack.enter_context(
                patch(f"{PKG}.download_video", return_value="/tmp/x.mkv")
            ),
            verify=stack.enter_context(
                patch(
                    f"{PKG}.trailer_file.verify_download",
                    return_value=(True, video_info),
                )
            ),
            move=stack.enter_context(
                patch(
                    f"{PKG}.trailer_file.move_trailer_to_folder",
                    return_value=str(folder.new),
                )
            ),
            preferred=stack.enter_context(
                patch(
                    f"{PKG}.trailer_file.get_trailer_path",
                    return_value=str(folder.old),
                )
            ),
            record=stack.enter_context(
                patch(
                    f"{PKG}.record_new_trailer_download",
                    new_callable=AsyncMock,
                    return_value=True,
                )
            ),
            delete=stack.enter_context(
                patch(
                    f"{PKG}.files_service.delete_file_or_folder",
                    side_effect=delete,
                )
            ),
            downloads=stack.enter_context(
                patch(f"{PKG}.download_manager.read_by_media_id")
            ),
            rename=stack.enter_context(
                patch(
                    f"{PKG}.rename_trailer_download",
                    new_callable=AsyncMock,
                    return_value=True,
                )
            ),
            deleted_event=stack.enter_context(
                patch(f"{PKG}.event_manager.track_trailer_deleted")
            ),
        )
        stack.enter_context(
            patch(f"{PKG}.event_manager.track_trailer_downloaded")
        )
        stack.enter_context(
            patch(f"{PKG}.media_manager.update_download_facts")
        )
        stack.enter_context(
            patch(f"{PKG}.attempt_manager.clear")
        )
        stack.enter_context(
            patch(
                f"{PKG}.websockets.ws_manager.broadcast",
                new_callable=AsyncMock,
            )
        )
        stack.enter_context(
            patch(
                "services.trailers.resolver.app_settings",
                MagicMock(tmdb_api_key="k"),
            )
        )
        mocks.candidates.return_value = [_video("tmdb1"), _video("tmdb2")]
        mocks.downloads.return_value = [_download(9, folder.new, "tmdb1")]
        yield mocks


@pytest.mark.asyncio
class TestUpgradeDownload:

    async def test_replaces_and_takes_the_old_name(
        self, media, profile, folder, pipeline
    ):
        from services.trailers.trailer import download_trailer

        old = _download(1, folder.old, "search1")
        result = await download_trailer(media, profile, 0, replace=[old])

        assert result is True
        # Decision 7: only a TMDB trailer, never a search.
        assert pipeline.get_video_id.call_args.kwargs["upgrade_only"] is True
        # Decision 8: Plex is not asked.
        pipeline.plex.assert_not_called()
        # Decision 9: the old file goes after the new one is recorded.
        pipeline.record.assert_awaited_once()
        pipeline.delete.assert_called_once_with(str(folder.old), media.id)
        pipeline.deleted_event.assert_called_once()
        # The new trailer took the name that the old one freed.
        assert folder.old.read_bytes() == b"new"
        assert not folder.new.exists()
        renamed, new_path = pipeline.rename.call_args.args
        assert renamed.id == 9 and new_path == str(folder.old)

    async def test_keeps_the_old_trailer_when_told_to(
        self, media, profile, folder, pipeline
    ):
        """Decision 1: the user decides whether the old file stays."""
        from services.trailers.trailer import download_trailer

        profile.delete_replaced_trailer = False
        old = _download(1, folder.old, "search1")
        assert await download_trailer(media, profile, 0, replace=[old])

        pipeline.delete.assert_not_called()
        pipeline.rename.assert_not_called()
        assert folder.old.read_bytes() == b"old"
        assert folder.new.read_bytes() == b"new"

    async def test_no_rename_when_the_freed_name_is_not_the_profile_name(
        self, media, profile, folder, pipeline, tmp_path
    ):
        from services.trailers.trailer import download_trailer

        pipeline.preferred.return_value = str(tmp_path / "other.mkv")
        old = _download(1, folder.old, "search1")
        assert await download_trailer(media, profile, 0, replace=[old])

        assert not folder.old.exists()
        assert folder.new.exists()
        pipeline.rename.assert_not_called()

    async def test_already_a_tmdb_trailer_after_the_refresh(
        self, media, profile, folder, pipeline
    ):
        """W2: the refreshed list names the trailer on disk."""
        from services.trailers.trailer import download_trailer

        old = _download(1, folder.old, "tmdb2")
        assert await download_trailer(media, profile, 0, replace=[old]) is False

        pipeline.get_video_id.assert_not_called()
        pipeline.delete.assert_not_called()

    async def test_a_video_the_user_chose_is_kept_after_the_refresh(
        self, media, profile, folder, pipeline
    ):
        """Decision 3, in any language (Copilot review on #696)."""
        from services.trailers.trailer import download_trailer

        profile.language = "it"
        pipeline.candidates.return_value = [
            SimpleNamespace(
                video_id="mine", source=VideoSource.USER, language=None
            ),
            SimpleNamespace(
                video_id="tmdb_it", source=VideoSource.TMDB, language="it"
            ),
        ]
        old = _download(1, folder.old, "mine")
        assert await download_trailer(media, profile, 0, replace=[old]) is False
        pipeline.get_video_id.assert_not_called()

    async def test_an_unrecorded_download_keeps_the_old_trailer(
        self, media, profile, folder, pipeline
    ):
        """Decision 9: the old file goes only after the new one is in the
        database. A failed record keeps it (Copilot review on #696)."""
        from services.trailers.trailer import download_trailer

        pipeline.record.return_value = False
        old = _download(1, folder.old, "search1")
        assert await download_trailer(media, profile, 0, replace=[old])

        pipeline.delete.assert_not_called()
        pipeline.rename.assert_not_called()
        assert folder.old.read_bytes() == b"old"

    async def test_tmdb_lists_nothing_after_the_refresh(
        self, media, profile, folder, pipeline
    ):
        """W2: the refreshed list is empty."""
        from services.trailers.trailer import download_trailer

        pipeline.candidates.return_value = [_video("arr1", VideoSource.ARR)]
        old = _download(1, folder.old, "search1")
        assert await download_trailer(media, profile, 0, replace=[old]) is False

        pipeline.get_video_id.assert_not_called()

    async def test_a_video_another_profile_owns_is_still_a_target(
        self, media, profile, folder, pipeline, tmp_path
    ):
        """Another profile has the only TMDB trailer on disk. This profile
        still downloads its own copy of it. Leaving it out gave the upgrade
        no target, and an upgrade never searches, so the profile failed
        and backed off on every run (Copilot review on #696)."""
        from services.trailers.trailer import download_trailer

        pipeline.candidates.return_value = [_video("tmdb1")]
        theirs = _download(2, tmp_path / "Theirs-trailer.mkv", "tmdb1")
        theirs.profile_id = 2
        old = _download(1, folder.old, "search1")
        media.downloads = [old, theirs]
        assert await download_trailer(media, profile, 0, replace=[old])

        exclude = pipeline.get_video_id.call_args.args[2]
        assert "tmdb1" not in exclude
        assert "search1" in exclude

    async def test_no_target_left_says_the_trailer_stays(
        self, media, profile, folder, pipeline
    ):
        """The pending view shows this error. The item has a trailer, so
        the text must not read as if it had none."""
        from services.trailers.trailer import download_trailer

        pipeline.get_video_id.return_value = None
        old = _download(1, folder.old, "search1")
        with pytest.raises(DownloadFailedError, match="current trailer stays"):
            await download_trailer(media, profile, 0, replace=[old])
        assert folder.old.read_bytes() == b"old"

    async def test_a_stop_between_retries_stops_the_retry(
        self, media, profile, folder, pipeline
    ):
        """The retry carries the stop event (Copilot review on #696)."""
        from services.trailers.trailer import download_trailer

        stop = threading.Event()
        calls = {"n": 0}

        def choose(*args, **kwargs):
            # The stop arrives while the retry picks its video.
            calls["n"] += 1
            if calls["n"] == 2:
                stop.set()
            return "tmdb1"

        pipeline.get_video_id.side_effect = choose
        pipeline.download.side_effect = RuntimeError("video unavailable")
        old = _download(1, folder.old, "search1")
        result = await download_trailer(
            media, profile, 2, replace=[old], stop_event=stop
        )

        assert result is False
        pipeline.download.assert_called_once()
        assert pipeline.get_video_id.call_count == 2
        assert folder.old.read_bytes() == b"old"

    async def test_a_failed_upgrade_keeps_the_old_trailer(
        self, media, profile, folder, pipeline
    ):
        """W3: every retry fails; the old file is untouched."""
        from services.trailers.trailer import download_trailer

        pipeline.download.side_effect = RuntimeError("video unavailable")
        old = _download(1, folder.old, "search1")
        with pytest.raises(DownloadFailedError):
            await download_trailer(media, profile, 1, replace=[old])

        # The retry stays an upgrade: TMDB only.
        assert pipeline.get_video_id.call_count == 2
        for call in pipeline.get_video_id.call_args_list:
            assert call.kwargs["upgrade_only"] is True
        pipeline.delete.assert_not_called()
        assert folder.old.read_bytes() == b"old"

    async def test_a_plain_download_still_asks_plex(
        self, media, profile, pipeline
    ):
        """Decision 10: without `replace`, nothing changes."""
        from services.trailers.trailer import download_trailer

        assert await download_trailer(media, profile, 0) is False
        pipeline.plex.assert_awaited_once()
        pipeline.get_video_id.assert_not_called()


class TestDownloadsToReplace:

    def test_an_unknown_video_is_left_alone_unless_the_profile_replaces_it(
        self,
    ):
        """Decision 4, amended. The replacement list of a profile leaves
        out a trailer whose video is unknown while `Replace Unknown
        Videos` is off, and never touches another profile's trailer."""
        from services.trailers.trailers.missing import _downloads_to_replace

        media = MagicMock(id=1)
        profile = SimpleNamespace(
            id=1, upgrade_to_tmdb=True, replace_unknown_videos=False
        )
        downloads = [
            SimpleNamespace(
                id=1, profile_id=1, file_exists=True, youtube_id="unknown0000"
            ),
            SimpleNamespace(
                id=2, profile_id=1, file_exists=True, youtube_id="search1"
            ),
            SimpleNamespace(
                id=3, profile_id=2, file_exists=True, youtube_id="search2"
            ),
        ]
        with patch(
            "services.trailers.trailers.missing.download_manager"
            ".read_by_media_id",
            return_value=downloads,
        ):
            assert [d.id for d in _downloads_to_replace(media, profile)] == [2]
            profile.replace_unknown_videos = True
            assert [d.id for d in _downloads_to_replace(media, profile)] == [
                1,
                2,
            ]


class TestUpgradeNeverSearches:

    def test_no_target_left_returns_none_without_a_search(self):
        """Decision 7."""
        from services.trailers import trailer_search

        media = MagicMock(id=1, title="Test Movie")
        profile = MagicMock(
            id=1, upgrade_to_tmdb=True, always_search=False, language=""
        )
        with (
            patch.object(
                trailer_search.video_manager,
                "read_candidates",
                return_value=[_video("arr1", VideoSource.ARR)],
            ),
            patch.object(
                trailer_search, "_last_tried_video_id", return_value=None
            ),
            patch.object(trailer_search, "search_yt_for_trailer") as search,
            patch(
                "services.trailers.resolver.app_settings",
                MagicMock(tmdb_api_key="k"),
            ),
        ):
            video_id = trailer_search.get_video_id(
                media, profile, [], upgrade_only=True
            )

        assert video_id is None
        search.assert_not_called()

    def test_upgrade_takes_the_next_tmdb_trailer(self):
        from services.trailers import trailer_search

        media = MagicMock(id=1, title="Test Movie")
        profile = MagicMock(
            id=1, upgrade_to_tmdb=True, always_search=False, language=""
        )
        with (
            patch.object(
                trailer_search.video_manager,
                "read_candidates",
                return_value=[
                    _video("arr1", VideoSource.ARR),
                    _video("tmdb1"),
                    _video("tmdb2"),
                ],
            ),
            patch.object(
                trailer_search, "_last_tried_video_id", return_value=None
            ),
            patch.object(trailer_search, "search_yt_for_trailer") as search,
            patch(
                "services.trailers.resolver.app_settings",
                MagicMock(tmdb_api_key="k"),
            ),
        ):
            video_id = trailer_search.get_video_id(
                media, profile, ["tmdb1"], upgrade_only=True
            )

        assert video_id == "tmdb2"
        search.assert_not_called()


@pytest.mark.asyncio
async def test_a_failing_cleanup_does_not_download_again(
    media, profile, folder, pipeline
):
    """The new trailer is in place; a cleanup error must not retry."""
    from services.trailers.trailer import download_trailer

    pipeline.delete.side_effect = OSError("read-only file system")
    old = _download(1, folder.old, "search1")
    assert await download_trailer(media, profile, 2, replace=[old]) is True
    pipeline.download.assert_called_once()
    pipeline.record.assert_awaited_once()
