"""Tests for removal of media that disappeared from the Plex library.

The Plex refresh mirrors the Arr-side flow:
  - Plex-only rows that are gone from the library are deleted.
  - Arr-sourced rows only lose their plex_* fields (PLEX_UNLINKED).
  - A failed section or an empty seen-list skips removal entirely.
"""

import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from sqlmodel import Session

import database.manager.event as event_manager
import database.manager.media as media_manager
from database.models.connection import ArrType, Connection
from database.models.event import EventType
from database.models.media import Media
from database.engine import write_session
from services.connections.plex.connection_manager import PlexConnectionManager
from services.connections.plex.models import PlexLibrarySection, PlexMediaItem


@write_session
def _make_conn(
    name: str, arr_type: ArrType, *, _session: Session = None  # type: ignore
) -> int:
    conn = Connection(
        name=name,
        arr_type=arr_type,
        url="http://server:1234",
        api_key="tok",
        monitor_new_media=True,
    )
    _session.add(conn)
    _session.commit()
    _session.refresh(conn)
    return conn.id  # type: ignore


@write_session
def _make_arr_media_with_plex_link(
    arr_conn_id: int,
    plex_conn_id: int,
    title: str,
    *,
    _session: Session = None,  # type: ignore
) -> int:
    media = Media(
        connection_id=arr_conn_id,
        arr_id=9911,
        title=title,
        year=2020,
        is_movie=True,
        txdb_id=str(uuid.uuid4().int % 10_000_000),
        folder_path=f"/media/{title}",
        plex_connection_id=plex_conn_id,
        plex_rating_key="rk-1",
        plex_section_key="1",
    )
    _session.add(media)
    _session.commit()
    _session.refresh(media)
    return media.id  # type: ignore


def _pm(path_from: str) -> SimpleNamespace:
    return SimpleNamespace(
        id=9999,
        path_from=path_from,
        path_to=path_from,
        plex_section_key="1",
    )


def _section(prefix: str) -> PlexLibrarySection:
    return PlexLibrarySection.model_validate(
        {
            "key": "1",
            "type": "movie",
            "title": "Movies",
            "Location": [{"path": f"/plex/{prefix}/movies"}],
        }
    )


def _movie_item(prefix: str, i: int) -> PlexMediaItem:
    f = f"/plex/{prefix}/movies/Film{i}"
    return PlexMediaItem.model_validate(
        {
            "ratingKey": str(8100 + i),
            "title": f"Removal Film {prefix} {i}",
            "year": 2015,
            "Media": [{"Part": [{"file": f"{f}/movie.mkv"}]}],
            "Guid": [{"id": f"tmdb://{810000 + i}"}],
        }
    )


def _build_manager(conn_id: int, prefix: str) -> PlexConnectionManager:
    connection = SimpleNamespace(
        id=conn_id,
        name=f"PlexRm-{prefix}",
        url="http://plex:32400",
        api_key="tok",
        monitor_new_media=True,
        path_mappings=[_pm(f"/plex/{prefix}/movies")],
    )
    with patch("services.connections.plex.connection_manager.PlexAPI") as MockAPI:
        MockAPI.return_value = MagicMock(server_url="")
        return PlexConnectionManager(connection)  # type: ignore


async def _sync_items(
    mgr: PlexConnectionManager, prefix: str, indexes: list[int]
) -> None:
    section = _section(prefix)
    chunk = [
        (_movie_item(prefix, i), section, True, f"/plex/{prefix}/movies/Film{i}")
        for i in indexes
    ]
    await mgr._process_item_chunk(chunk)


def _media_for_conn(conn_id: int) -> dict[str, object]:
    return {
        m.title: m
        for m in media_manager.read_all()
        if m.connection_id == conn_id or m.plex_connection_id == conn_id
    }


class TestPlexOnlyRemoval:
    @pytest.mark.asyncio
    async def test_missing_plex_only_item_is_deleted(self):
        prefix = uuid.uuid4().hex[:10]
        conn_id = _make_conn(f"PlexRm-{prefix}", ArrType.PLEX)
        mgr = _build_manager(conn_id, prefix)
        await _sync_items(mgr, prefix, [0, 1])
        assert len(_media_for_conn(conn_id)) == 2

        # Next refresh only sees Film0 — Film1 must be deleted
        seen_both = list(mgr.media_ids)
        mgr.media_ids = [seen_both[0]]
        await mgr._remove_media_deleted_in_plex()

        remaining = _media_for_conn(conn_id)
        assert len(remaining) == 1
        assert f"Removal Film {prefix} 0" in remaining

    @pytest.mark.asyncio
    async def test_seen_items_are_kept(self):
        prefix = uuid.uuid4().hex[:10]
        conn_id = _make_conn(f"PlexRm-{prefix}", ArrType.PLEX)
        mgr = _build_manager(conn_id, prefix)
        await _sync_items(mgr, prefix, [0, 1])

        await mgr._remove_media_deleted_in_plex()

        assert len(_media_for_conn(conn_id)) == 2


class TestArrLinkedUnlink:
    @pytest.mark.asyncio
    async def test_arr_linked_item_is_unlinked_not_deleted(self):
        prefix = uuid.uuid4().hex[:10]
        plex_conn_id = _make_conn(f"PlexRm-{prefix}", ArrType.PLEX)
        arr_conn_id = _make_conn(f"ArrRm-{prefix}", ArrType.RADARR)
        title = f"ArrLinked {prefix}"
        media_id = _make_arr_media_with_plex_link(
            arr_conn_id, plex_conn_id, title
        )

        mgr = _build_manager(plex_conn_id, prefix)
        # Refresh saw one plex-only item, but not the Arr-linked one
        await _sync_items(mgr, prefix, [0])
        await mgr._remove_media_deleted_in_plex()

        media = media_manager.read(media_id)
        assert media is not None, "Arr-sourced row must not be deleted"
        assert media.plex_connection_id is None
        assert media.plex_rating_key is None
        assert media.plex_section_key is None

        events = event_manager.read_by_media_id(media_id)
        assert any(
            e.event_type == EventType.PLEX_UNLINKED
            and e.source_detail == "PlexRefresh"
            for e in events
        )


class TestRemovalGuards:
    @pytest.mark.asyncio
    async def test_failed_section_skips_removal(self):
        prefix = uuid.uuid4().hex[:10]
        conn_id = _make_conn(f"PlexRm-{prefix}", ArrType.PLEX)
        mgr = _build_manager(conn_id, prefix)
        await _sync_items(mgr, prefix, [0, 1])

        mgr.media_ids = [list(mgr.media_ids)[0]]
        mgr._sections_failed = 1
        await mgr._remove_media_deleted_in_plex()

        assert len(_media_for_conn(conn_id)) == 2

    @pytest.mark.asyncio
    async def test_empty_seen_list_skips_removal(self):
        prefix = uuid.uuid4().hex[:10]
        conn_id = _make_conn(f"PlexRm-{prefix}", ArrType.PLEX)
        mgr = _build_manager(conn_id, prefix)
        await _sync_items(mgr, prefix, [0, 1])

        mgr.media_ids = []
        await mgr._remove_media_deleted_in_plex()

        assert len(_media_for_conn(conn_id)) == 2
