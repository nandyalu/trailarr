"""The TMDB upgrade and unmonitored items (#707).

Before v0.10.0, Trailarr turned monitoring off when it downloaded a
trailer, and Phase 4 kept those values. The download task skips an
unmonitored item, so `Upgrade To TMDB Trailer` never reached most of an old
library. `compute_unmonitored_upgrades` finds these items for a banner on
the library page. The user decides whether to monitor them.

The same issue asked for a TMDB badge, which `tmdb_video` in
`/media/downloads_raw` feeds.
"""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import patch

from sqlmodel import Session

import database.manager.download as download_manager
import database.manager.media as media_manager
import database.manager.mediavideo as video_manager
from database.engine import write_session
from database.models.connection import ArrType, Connection
from database.models.download import DownloadCreate
from database.models.media import MediaCreate
from database.models.mediavideo import MediaVideoCreate, VideoSource
from services.trailers.trailers.pending import compute_unmonitored_upgrades

NOW = datetime.now(timezone.utc)
PKG = "services.trailers.trailers.pending"


def _profile(profile_id: int = 1, upgrade: bool = True) -> SimpleNamespace:
    return SimpleNamespace(
        id=profile_id,
        priority=profile_id,
        enabled=True,
        upgrade_to_tmdb=upgrade,
        replace_unknown_videos=False,
        always_search=False,
        search_youtube=True,
        language="",
        video_type="trailer",
        customfilter=SimpleNamespace(
            filter_name=f"Profile {profile_id}", filters=[]
        ),
    )


def _download(youtube_id: str, profile_id: int = 1) -> SimpleNamespace:
    return SimpleNamespace(
        id=1,
        profile_id=profile_id,
        file_exists=True,
        added_at=NOW - timedelta(hours=1),
        video_type="trailer",
        youtube_id=youtube_id,
    )


def _media(
    media_id: int,
    youtube_id: str = "search1",
    monitor: bool = False,
    tmdb_asked: bool = False,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=media_id,
        title=f"Media {media_id}",
        is_movie=True,
        monitor=monitor,
        downloads=[_download(youtube_id)],
        tmdb_id=media_id,
        last_videos_refresh=NOW if tmdb_asked else None,
    )


def _tmdb(video_id: str) -> SimpleNamespace:
    return SimpleNamespace(
        video_id=video_id,
        source=VideoSource.TMDB,
        language="en",
        video_type="trailer",
    )


def _run(profiles, media_list, videos_by_media, tmdb_key: str = "k"):
    with (
        patch(
            f"{PKG}.trailerprofile.get_trailerprofiles",
            return_value=profiles,
        ),
        patch(
            f"{PKG}.media_manager.read_all_generator",
            return_value=iter(media_list),
        ) as read_all,
        patch(
            f"{PKG}.video_manager.read_candidates_by_media",
            return_value=videos_by_media,
        ),
        patch(
            "services.trailers.resolver.app_settings",
            SimpleNamespace(tmdb_api_key=tmdb_key),
        ),
    ):
        return compute_unmonitored_upgrades(), read_all


class TestWhichItemsCount:

    def test_a_trailer_to_replace_counts(self):
        result, _ = _run(
            [_profile()], [_media(1, "search1")], {1: [_tmdb("tmdb1")]}
        )
        assert result.media_ids == [1]
        assert result.other_downloads == 0

    def test_an_item_never_asked_about_counts(self):
        """TMDB was never asked, so it may list a better trailer."""
        result, _ = _run([_profile()], [_media(1, tmdb_asked=False)], {})
        assert result.media_ids == [1]

    def test_an_item_tmdb_lists_nothing_for_does_not_count(self):
        """Monitoring it changes nothing: there is no TMDB trailer."""
        result, _ = _run([_profile()], [_media(1, tmdb_asked=True)], {})
        assert result.media_ids == []

    def test_a_tmdb_trailer_does_not_count(self):
        result, _ = _run(
            [_profile()],
            [_media(1, "tmdb1", tmdb_asked=True)],
            {1: [_tmdb("tmdb1")]},
        )
        assert result.media_ids == []

    def test_a_monitored_item_does_not_count(self):
        """The download task reaches it already."""
        result, _ = _run(
            [_profile()],
            [_media(1, "search1", monitor=True)],
            {1: [_tmdb("tmdb1")]},
        )
        assert result.media_ids == []

    def test_only_items_with_a_trailer_are_read(self):
        _, read_all = _run([_profile()], [], {})
        read_all.assert_called_once_with(downloaded_only=True)


class TestNothingToDo:

    def test_no_upgrade_profile_reads_nothing(self):
        result, read_all = _run(
            [_profile(upgrade=False)], [_media(1)], {1: [_tmdb("tmdb1")]}
        )
        assert result.media_ids == []
        read_all.assert_not_called()

    def test_an_inert_upgrade_reads_nothing(self):
        """Without a TMDB key the upgrade cannot act."""
        result, read_all = _run(
            [_profile()], [_media(1)], {1: [_tmdb("tmdb1")]}, tmdb_key=""
        )
        assert result.media_ids == []
        read_all.assert_not_called()

    def test_a_disabled_upgrade_profile_reads_nothing(self):
        profile = _profile()
        profile.enabled = False
        result, read_all = _run([profile], [_media(1)], {})
        assert result.media_ids == []
        read_all.assert_not_called()


class TestOtherDownloads:
    """Monitoring an item also lets every other matching profile act. The
    banner says how many items get a new download that way."""

    def test_a_second_profile_with_no_download_is_counted(self):
        result, _ = _run(
            [_profile(1), _profile(2, upgrade=False)],
            [_media(1, "search1")],
            {1: [_tmdb("tmdb1")]},
        )
        assert result.media_ids == [1]
        assert result.other_downloads == 1

    def test_a_profile_that_waits_for_tmdb_is_not_a_download(self):
        waiting = _profile(2, upgrade=False)
        waiting.search_youtube = False
        result, _ = _run(
            [_profile(1), waiting],
            [_media(1, "search1")],
            {1: [_tmdb("tmdb1")]},
        )
        # Profile 2 could take tmdb1 too, so it is a plain download here.
        assert result.other_downloads == 1
        result, _ = _run([_profile(1), waiting], [_media(1)], {})
        # With no known video, profile 2 waits for TMDB: no download.
        assert result.media_ids == [1]
        assert result.other_downloads == 0


@write_session
def _make_connection(*, _session: Session = None) -> Connection:  # type: ignore
    conn = Connection(
        name="Unmonitored Upgrades Test Connection",
        arr_type=ArrType.RADARR,
        url="http://localhost:7878",
        api_key="test_key",
        monitor_new_media=False,
    )
    _session.add(conn)
    _session.commit()
    _session.refresh(conn)
    return conn


def _seed(conn_id: int, arr_id: int, youtube_id: str, monitor: bool) -> int:
    """One real media item with one trailer on disk."""
    media = media_manager.create(
        MediaCreate(
            connection_id=conn_id,
            arr_id=arr_id,
            is_movie=True,
            title=f"Upgrade Item {arr_id}",
            txdb_id=f"upgrade-{arr_id}",
            monitor=monitor,
        )
    )
    path = f"/media/upgrade-{arr_id}/trailer.mkv"
    download_manager.create(
        DownloadCreate(
            media_id=media.id,
            path=path,
            file_name="trailer.mkv",
            file_hash="hash",
            size=1000,
            resolution=1080,
            file_format="mkv",
            video_format="vp9",
            audio_format="opus",
            youtube_id=youtube_id,
            added_at=NOW,
            updated_at=NOW,
            profile_id=0,
        )
    )
    return media.id


def _list_on_tmdb(media_id: int, video_id: str) -> None:
    video_manager.replace_source_rows(
        media_id,
        VideoSource.TMDB,
        [
            MediaVideoCreate(
                media_id=media_id,
                video_id=video_id,
                source=VideoSource.TMDB,
                language="en",
            )
        ],
    )


class TestAgainstTheRealDatabase:
    """The SQL of the badge and the reads of the banner, on real rows."""

    def test_the_badge_flag_and_the_banner_list(self):
        conn = _make_connection()
        replace = _seed(conn.id, 97001, "search97001", monitor=False)
        _list_on_tmdb(replace, "tmdb97001")
        already = _seed(conn.id, 97002, "tmdb97002", monitor=False)
        _list_on_tmdb(already, "tmdb97002")
        # The same video id, but TMDB does not list it for this item.
        other_item = _seed(conn.id, 97003, "tmdb97002", monitor=False)
        monitored = _seed(conn.id, 97004, "search97004", monitor=True)
        _list_on_tmdb(monitored, "tmdb97004")

        flags = {
            row["media_id"]: row["tmdb_video"]
            for row in download_manager.read_all_raw()
        }
        assert flags[replace] == 0
        assert flags[already] == 1
        assert flags[other_item] == 0
        assert flags[monitored] == 0

        with (
            patch(
                f"{PKG}.trailerprofile.get_trailerprofiles",
                return_value=[_profile(upgrade=True)],
            ),
            patch(
                "services.trailers.resolver.app_settings",
                SimpleNamespace(tmdb_api_key="k"),
            ),
        ):
            ids = set(compute_unmonitored_upgrades().media_ids)
        # Replaces a search trailer. Was never asked about. Not: a TMDB
        # trailer already, or monitored.
        assert replace in ids
        assert other_item in ids
        assert already not in ids
        assert monitored not in ids
