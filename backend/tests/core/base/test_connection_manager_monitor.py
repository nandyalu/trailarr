"""Phase 4: monitor is user intent — Arr syncs apply monitor_new_media once
at creation and never rewrite the flag afterwards
(plans/phase-04-monitor-intent.md, decisions 2/3; exit criteria)."""

from types import SimpleNamespace

import pytest
from sqlmodel import Session

import database.manager.event as event_manager
import database.manager.media as media_manager
from core.base.connection_manager import BaseConnectionManager
from database.models.connection import ArrType, Connection
from database.models.event import EventType
from database.models.media import MediaCreate
from database.engine import write_session


@write_session
def _make_connection(
    name: str,
    *,
    _session: Session = None,  # type: ignore
) -> int:
    conn = Connection(
        name=name,
        arr_type=ArrType.RADARR,
        url="http://localhost:7878",
        api_key="key",
        monitor_new_media=True,
    )
    _session.add(conn)
    _session.commit()
    _session.refresh(conn)
    return conn.id


def _build_manager(
    conn_id: int, name: str, monitor_new_media: bool
) -> BaseConnectionManager:
    connection = SimpleNamespace(
        id=conn_id,
        name=name,
        monitor_new_media=monitor_new_media,
        path_mappings=[],
    )
    return BaseConnectionManager(
        connection,  # type: ignore[arg-type]
        arr_manager=SimpleNamespace(),  # type: ignore[arg-type]
        parse_media=lambda cid, data: None,  # type: ignore[arg-type]
    )


def _make_media_create(conn_id: int, txdb_id: str) -> MediaCreate:
    return MediaCreate(
        connection_id=conn_id,
        arr_id=int(txdb_id[-4:], 36),
        is_movie=True,
        title=f"Sync Media {txdb_id}",
        txdb_id=txdb_id,
        arr_monitored=True,
    )


def _monitor_changed_count(media_ids: list[int]) -> int:
    count = 0
    for media_id in media_ids:
        events = event_manager.read_by_media_id(media_id)
        count += sum(
            1 for e in events if e.event_type == EventType.MONITOR_CHANGED
        )
    return count


async def _sync(manager: BaseConnectionManager, parsed: list[MediaCreate]):
    await manager._process_media_list(parsed)


class TestArrSyncMonitorIntent:

    @pytest.mark.asyncio
    async def test_creation_default_applied(self):
        import uuid

        p = uuid.uuid4().hex[:8]
        conn_id = _make_connection(f"ArrDef-{p}")
        manager = _build_manager(conn_id, f"ArrDef-{p}", True)
        await _sync(manager, [_make_media_create(conn_id, f"cd{p}")])

        media = media_manager.read_all_by_connection(conn_id)
        assert [m.monitor for m in media] == [True]

    @pytest.mark.asyncio
    async def test_creation_default_false(self):
        import uuid

        p = uuid.uuid4().hex[:8]
        conn_id = _make_connection(f"ArrDefF-{p}")
        manager = _build_manager(conn_id, f"ArrDefF-{p}", False)
        await _sync(manager, [_make_media_create(conn_id, f"cf{p}")])

        media = media_manager.read_all_by_connection(conn_id)
        assert [m.monitor for m in media] == [False]

    @pytest.mark.asyncio
    async def test_resync_never_rewrites_monitor_and_fires_zero_events(self):
        """THE exit-criteria regression: sync twice — the second sync
        changes no monitor value and produces zero new MONITOR_CHANGED
        events, even after the user flipped the flag and even if the
        connection default changed in between."""
        import uuid

        p = uuid.uuid4().hex[:8]
        conn_id = _make_connection(f"ArrResync-{p}")
        manager = _build_manager(conn_id, f"ArrResync-{p}", True)
        parsed = [
            _make_media_create(conn_id, f"rs{p}a"),
            _make_media_create(conn_id, f"rs{p}b"),
        ]
        await _sync(manager, parsed)
        media = media_manager.read_all_by_connection(conn_id)
        media_ids = [m.id for m in media]
        assert [m.monitor for m in media] == [True, True]

        # User unmonitors one item
        media_manager.update_monitoring(media_ids[0], False)
        events_after_first = _monitor_changed_count(media_ids)

        # Second sync — with a DIFFERENT default, proving existing rows are
        # untouched even when the connection setting changes
        manager2 = _build_manager(conn_id, f"ArrResync-{p}", False)
        await _sync(manager2, [
            _make_media_create(conn_id, f"rs{p}a"),
            _make_media_create(conn_id, f"rs{p}b"),
        ])

        refreshed = media_manager.read_all_by_connection(conn_id)
        assert {m.id: m.monitor for m in refreshed} == {
            media_ids[0]: False,  # user intent survives
            media_ids[1]: True,  # untouched by the new default
        }
        assert _monitor_changed_count(media_ids) == events_after_first

    @pytest.mark.asyncio
    async def test_arr_monitored_fact_still_synced(self):
        """arr_monitored is a synced FACT (not intent) — it keeps updating
        while monitor stays user-owned."""
        import uuid

        p = uuid.uuid4().hex[:8]
        conn_id = _make_connection(f"ArrFact-{p}")
        manager = _build_manager(conn_id, f"ArrFact-{p}", True)
        create = _make_media_create(conn_id, f"af{p}")
        create.arr_monitored = True
        await _sync(manager, [create])
        media_id = media_manager.read_all_by_connection(conn_id)[0].id

        update = _make_media_create(conn_id, f"af{p}")
        update.arr_monitored = False
        await _sync(manager, [update])

        refreshed = media_manager.read(media_id)
        assert refreshed.arr_monitored is False
        assert refreshed.monitor is True  # untouched
