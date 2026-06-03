import re
from datetime import datetime, timedelta, timezone
from typing import Generator

from sqlalchemy.orm import selectinload
from sqlmodel import Session, col, desc, or_, select, text
from sqlmodel.sql.expression import SelectOfScalar

from db.engine import read_session, write_session
from db.models.helpers import MediaImage, MediaUpdateDC
from db.models.media import Media, MediaCreate, MediaRead, MediaUpdate
from exceptions import ItemNotFoundError


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_or_404(media_id: int, session: Session) -> Media:
    db = session.get(Media, media_id)
    if not db:
        raise ItemNotFoundError("Media", media_id)
    return db


def _to_read(db: Media) -> MediaRead:
    return MediaRead.model_validate(db)


def _to_read_list(items) -> list[MediaRead]:
    return [MediaRead.model_validate(m, from_attributes=True) for m in items]


def has_updated(
    db_media: Media,
    update: MediaCreate | MediaRead | MediaUpdate,
    *,
    ignore_attrs: set[str] | None = None,
) -> bool:
    _fields = {"title", "year", "media_exists", "media_filename", "folder_path", "monitor", "arr_monitored"}
    if ignore_attrs:
        _fields = _fields.difference(ignore_attrs)
    db_data = db_media.model_dump()
    update_data = update.model_dump()
    for field in _fields:
        if update_data.get(field) is not None and db_data.get(field) != update_data.get(field):
            return True
    return False


def _apply_filter(statement: SelectOfScalar[Media], filter_by: str) -> SelectOfScalar[Media]:
    if filter_by == "downloaded":
        return statement.where(col(Media.downloaded_at).is_not(None))
    if filter_by == "monitored":
        return statement.where(col(Media.monitor).is_(True))
    if filter_by == "missing":
        return statement.where(col(Media.downloaded_at).is_(None))
    if filter_by == "unmonitored":
        return statement.where(col(Media.monitor).is_(False))
    return statement


# ---------------------------------------------------------------------------
# Single-item reads
# ---------------------------------------------------------------------------

@read_session
def read(media_id: int, *, _session: Session = None) -> MediaRead:  # type: ignore
    return _to_read(_get_or_404(media_id, _session))


@read_session
def read_by_folder_path(folder_path: str, *, _session: Session = None) -> MediaRead | None:  # type: ignore
    """Find a media item by folder path, with two-stage prefix fallback."""
    db = _session.exec(select(Media).where(Media.folder_path == folder_path)).first()
    if db:
        return _to_read(db)

    rows = _session.exec(
        select(Media.id, Media.folder_path).where(col(Media.folder_path).is_not(None))
    ).all()
    best_id: int | None = None
    best_len = 0
    for row_id, row_path in rows:
        if row_path and row_id and folder_path.startswith(row_path) and len(row_path) > best_len:
            best_id = row_id
            best_len = len(row_path)
    if best_id is None:
        return None
    return _to_read(_get_or_404(best_id, _session))


# ---------------------------------------------------------------------------
# Bulk reads
# ---------------------------------------------------------------------------

@read_session
def read_all(
    movies_only: bool | None = None,
    filter_by: str | None = "all",
    sort_by: str | None = None,
    sort_asc: bool = True,
    *,
    _session: Session = None,  # type: ignore
) -> list[MediaRead]:
    stmt = select(Media).options(selectinload(Media.downloads))  # type: ignore[arg-type]
    if movies_only is not None:
        stmt = stmt.where(col(Media.is_movie).is_(movies_only))
    if filter_by:
        stmt = _apply_filter(stmt, filter_by)
    if sort_by and hasattr(Media, sort_by):
        stmt = stmt.order_by(sort_by if sort_asc else desc(sort_by))
    return _to_read_list(_session.exec(stmt).all())


@read_session
def read_all_raw(*, _session: Session = None) -> list[dict]:  # type: ignore
    return [dict(r) for r in _session.execute(text("SELECT * FROM media")).mappings()]


@read_session
def read_all_by_connection(connection_id: int, *, _session: Session = None) -> list[MediaRead]:  # type: ignore
    items = _session.exec(
        select(Media).options(selectinload(Media.downloads)).where(Media.connection_id == connection_id)  # type: ignore[arg-type]
    ).all()
    return _to_read_list(items)


@read_session
def read_arr_linked_to_plex_connection(plex_connection_id: int, *, _session: Session = None) -> list[MediaRead]:  # type: ignore
    items = _session.exec(
        select(Media).where(
            (Media.plex_connection_id == plex_connection_id) & (Media.connection_id != plex_connection_id)
        )
    ).all()
    return _to_read_list(items)


@read_session
def read_recent(
    limit: int = 100,
    offset: int = 0,
    movies_only: bool | None = None,
    *,
    _session: Session = None,  # type: ignore
) -> list[MediaRead]:
    offset = max(0, offset)
    limit = max(1, min(limit, 100))
    stmt = select(Media)
    if movies_only is not None:
        stmt = stmt.where(col(Media.is_movie).is_(movies_only))
    stmt = stmt.order_by(desc(Media.added_at)).offset(offset).limit(limit)
    return _to_read_list(_session.exec(stmt).all())


@read_session
def read_recently_downloaded(limit: int = 100, offset: int = 0, *, _session: Session = None) -> list[MediaRead]:  # type: ignore
    offset = max(0, offset)
    limit = max(1, min(limit, 100))
    stmt = (
        select(Media)
        .where(col(Media.downloaded_at).is_not(None))
        .order_by(desc(Media.downloaded_at))
        .offset(offset)
        .limit(limit)
    )
    return _to_read_list(_session.exec(stmt).all())


@read_session
def read_updated_after(seconds: int, *, _session: Session = None) -> list[MediaRead]:  # type: ignore
    seconds = max(1, min(seconds + 1, 86400))
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=seconds)
    stmt = select(Media).where(
        or_(Media.updated_at > cutoff, Media.added_at > cutoff, Media.downloaded_at > cutoff)  # type: ignore
    )
    return _to_read_list(_session.exec(stmt).all())


@read_session
def read_all_generator(
    movies_only: bool | None = None,
    monitored_only: bool = False,
    downloaded_only: bool = False,
    plex_linked_only: bool = False,
    *,
    _session: Session = None,  # type: ignore
) -> Generator[MediaRead, None, None]:
    stmt = select(Media).execution_options(stream_results=True)
    if movies_only is not None:
        stmt = stmt.where(col(Media.is_movie).is_(movies_only))
    if monitored_only:
        stmt = _apply_filter(stmt, "monitored")
    if downloaded_only:
        stmt = _apply_filter(stmt, "downloaded")
    if plex_linked_only:
        stmt = stmt.where(
            col(Media.plex_connection_id).is_not(None),
            col(Media.plex_rating_key).is_not(None),
        )
    for db in _session.exec(stmt):
        yield _to_read(db)


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

@read_session
def search(query: str, *, offset: int = 0, _session: Session = None) -> list[MediaRead]:  # type: ignore
    offset = max(0, offset)
    stmt = _get_search_statement(query, limit=50, offset=offset)
    if stmt is None:
        return []
    return _to_read_list(_session.exec(stmt).all())


def _get_search_statement(query: str, limit: int = 50, offset: int = 0) -> SelectOfScalar[Media] | None:
    if not query:
        return None
    imdb_id = _extract_imdb_id(query)
    if imdb_id:
        return select(Media).where(Media.imdb_id == imdb_id)
    media_id = _extract_media_id(query)
    if media_id:
        return select(Media).where(
            or_(Media.tmdb_id == media_id, Media.tvdb_id == media_id)
        )
    stmt = select(Media)
    year = _extract_four_digit_number(query)
    if year and 1900 < int(year) < 2100:
        query = query.replace(year, "").strip().replace("  ", " ")
        stmt = stmt.where(Media.year == year)
    return (
        stmt.where(col(Media.title).ilike(f"%{query}%"))
        .offset(offset)
        .limit(limit)
        .order_by(desc(Media.added_at))
    )


def _extract_four_digit_number(query: str) -> str | None:
    matches = re.findall(r"\b\d{4}\b", query)
    return matches[-1] if matches else None


def _extract_imdb_id(query: str) -> str | None:
    matches = re.findall(r"tt\d{7,}", query)
    return matches[-1] if matches else None


def _extract_media_id(query: str) -> str | None:
    matches = re.findall(r"\b\d{5,9}\b", query)
    return matches[-1] if matches else None


# ---------------------------------------------------------------------------
# Create / bulk upsert
# ---------------------------------------------------------------------------

@write_session
def create(media_create: MediaCreate, *, _session: Session = None) -> MediaRead:  # type: ignore
    from db.repos import connection as connection_repo
    if not connection_repo.exists(media_create.connection_id, _session=_session):
        raise ItemNotFoundError("Connection", media_create.connection_id)
    db = Media.model_validate(media_create)
    _session.add(db)
    _session.commit()
    _session.refresh(db)
    return _to_read(db)


@write_session
def create_or_update_bulk(
    media_create_list: list[MediaCreate],
    *,
    _session: Session = None,  # type: ignore
) -> list[tuple[MediaRead, bool, bool, bool, int]]:
    """Create or update multiple media items. Returns list of (MediaRead, created, updated, arr_linked, old_season_count)."""
    from db.repos import connection as connection_repo
    connection_ids = {m.connection_id for m in media_create_list}
    for cid in connection_ids:
        if not connection_repo.exists(cid, _session=_session):
            raise ItemNotFoundError("Connection", cid)

    results: list[tuple[Media, bool, bool, bool, int]] = []
    for media_create in media_create_list:
        db, created, updated, arr_linked, old_season_count = _create_or_update(media_create, _session)
        results.append((db, created, updated, arr_linked, old_season_count))
    _session.commit()
    return [(_to_read(db), created, updated, arr_linked, old_season_count) for db, created, updated, arr_linked, old_season_count in results]


def _create_or_update(
    media_create: MediaCreate, session: Session
) -> tuple[Media, bool, bool, bool, int]:
    """Internal: create or update a single media row without committing."""
    from db.models.event import EventSource
    db = _read_if_exists(media_create.connection_id, media_create, session)
    arr_linked = False
    if db is None:
        plex_row = _read_plex_only_by_folder_path(media_create.folder_path, session)
        if plex_row is not None:
            db = plex_row
            arr_linked = True
    if db:
        old_season_count = db.season_count or 0
        update_data = media_create.model_dump(
            exclude_unset=True,
            exclude_none=True,
            exclude={"youtube_trailer_id", "downloaded_at", "created_at", "updated_at"},
        )
        db.sqlmodel_update(update_data)
        updated = False
        if not db.youtube_trailer_id and media_create.youtube_trailer_id:
            # Event tracking for yt_id change is deferred to the calling service
            db.youtube_trailer_id = media_create.youtube_trailer_id
            updated = True
        elif has_updated(
            db, media_create,
            ignore_attrs={"monitor", "updated_at", "downloaded_at", "youtube_trailer_id", "created_at"},
        ):
            db.updated_at = datetime.now(timezone.utc)
            updated = True
        session.add(db)
        return db, False, updated, arr_linked, old_season_count
    else:
        db = Media.model_validate(media_create)
        session.add(db)
        return db, True, False, False, 0


def _read_if_exists(connection_id: int, media_create: MediaCreate, session: Session) -> Media | None:
    if media_create.tmdb_id:
        return session.exec(
            select(Media).where(
                Media.connection_id == connection_id,
                Media.tmdb_id == media_create.tmdb_id,
            )
        ).first()
    if media_create.tvdb_id:
        return session.exec(
            select(Media).where(
                Media.connection_id == connection_id,
                Media.tvdb_id == media_create.tvdb_id,
            )
        ).first()
    if media_create.folder_path:
        return session.exec(
            select(Media).where(
                Media.connection_id == connection_id,
                Media.folder_path == media_create.folder_path,
            )
        ).first()
    return None


def _read_plex_only_by_folder_path(folder_path: str | None, session: Session) -> Media | None:
    if not folder_path:
        return None
    db = session.exec(
        select(Media).where(Media.folder_path == folder_path, Media.arr_id == 0)
    ).first()
    if db:
        return db
    rows = session.exec(
        select(Media.id, Media.folder_path)
        .where(col(Media.folder_path).is_not(None))
        .where(Media.arr_id == 0)
    ).all()
    best_id: int | None = None
    best_len = 0
    for row_id, row_path in rows:
        if row_path and row_id and folder_path.startswith(row_path) and len(row_path) > best_len:
            best_id = row_id
            best_len = len(row_path)
    if best_id is None:
        return None
    return _get_or_404(best_id, session)


# ---------------------------------------------------------------------------
# Updates
# ---------------------------------------------------------------------------

@write_session
def update_media_image(media_image: MediaImage, *, _session: Session = None) -> None:  # type: ignore
    db = _get_or_404(media_image.id, _session)
    if media_image.is_poster:
        if db.poster_path != media_image.image_path:
            db.poster_path = media_image.image_path
            _session.add(db)
            _session.commit()
    else:
        if db.fanart_path != media_image.image_path:
            db.fanart_path = media_image.image_path
            _session.add(db)
            _session.commit()


@write_session
def update_monitor_only(media_id: int, monitor: bool, *, _commit: bool = True, _session: Session = None) -> None:  # type: ignore
    db = _get_or_404(media_id, _session)
    if db.monitor != monitor:
        db.monitor = monitor
        db.updated_at = datetime.now(timezone.utc)
        _session.add(db)
        if _commit:
            _session.commit()


@write_session
def update_monitoring(media_id: int, monitor: bool, *, _commit: bool = True, _session: Session = None) -> tuple[str, bool]:  # type: ignore
    db = _get_or_404(media_id, _session)
    if db.monitor == monitor:
        msg = f"Media '{db.title}' [{db.id}] is already"
        msg += " monitored!" if monitor else " not monitored!"
        return msg, False
    db.monitor = monitor
    db.updated_at = datetime.now(timezone.utc)
    _session.add(db)
    if _commit:
        _session.commit()
    return f"Media '{db.title}' [{db.id}] is now {'monitored' if monitor else 'no longer monitored'}", True


@write_session
def update_monitoring_bulk(media_ids: list, monitor: bool, *, _session: Session = None) -> None:  # type: ignore
    for media_id in media_ids:
        update_monitoring(media_id, monitor, _session=_session, _commit=False)
    _session.commit()


@write_session
def update_monitor_and_trailer_exists_bulk(
    media_update_list,
    *,
    _session: Session = None,  # type: ignore
) -> None:
    for media_id, monitor, _trailer_exists in media_update_list:
        update_monitor_only(media_id, monitor, _session=_session, _commit=False)
    _session.commit()


@write_session
def update_media_status(media_update: MediaUpdateDC, *, _commit: bool = True, _session: Session = None) -> None:  # type: ignore
    db = _get_or_404(media_update.id, _session)
    _upd = MediaUpdate(**media_update.model_dump())
    if has_updated(db, _upd):
        db.updated_at = datetime.now(timezone.utc)
    db.monitor = media_update.monitor
    if media_update.downloaded_at:
        db.downloaded_at = media_update.downloaded_at
    if media_update.yt_id:
        db.youtube_trailer_id = media_update.yt_id
    _session.add(db)
    if _commit:
        _session.commit()


@write_session
def update_media_exists(media_id: int, media_exists: bool, *, _session: Session = None) -> None:  # type: ignore
    db = _get_or_404(media_id, _session)
    if db.media_exists != media_exists:
        db.media_exists = media_exists
        db.updated_at = datetime.now(timezone.utc)
        _session.add(db)
        _session.commit()


@write_session
def update_ytid(media_id: int, yt_id: str, *, _commit: bool = True, _session: Session = None) -> None:  # type: ignore
    db = _get_or_404(media_id, _session)
    db.youtube_trailer_id = yt_id
    _session.add(db)
    if _commit:
        _session.commit()


@write_session
def update_plex_fields(
    media_id: int,
    plex_rating_key: str | None,
    plex_section_key: str | None,
    plex_connection_id: int | None,
    media_filename: str | None = None,
    *,
    _session: Session = None,  # type: ignore
) -> bool:
    db = _get_or_404(media_id, _session)
    changed = (
        db.plex_rating_key != plex_rating_key
        or db.plex_section_key != plex_section_key
        or db.plex_connection_id != plex_connection_id
        or (media_filename is not None and db.media_filename != media_filename)
    )
    if not changed:
        return False
    db.plex_rating_key = plex_rating_key
    db.plex_section_key = plex_section_key
    db.plex_connection_id = plex_connection_id
    if media_filename is not None:
        db.media_filename = media_filename
    db.updated_at = datetime.now(timezone.utc)
    _session.add(db)
    _session.commit()
    return True


@write_session
def update_plex_trailer(media_id: int, plex_trailer: bool | None, *, _session: Session = None) -> None:  # type: ignore
    db = _get_or_404(media_id, _session)
    db.plex_trailer = plex_trailer
    db.updated_at = datetime.now(timezone.utc)
    _session.add(db)
    _session.commit()


@write_session
def update_plex_trailer_bulk(updates: list[tuple[int, bool | None]], *, _session: Session = None) -> None:  # type: ignore
    now = datetime.now(timezone.utc)
    for media_id, plex_trailer in updates:
        db = _session.get(Media, media_id)
        if db is None:
            continue
        db.plex_trailer = plex_trailer
        db.updated_at = now
        _session.add(db)
    _session.commit()


# ---------------------------------------------------------------------------
# Demotion / delete
# ---------------------------------------------------------------------------

@write_session
def demote_arr_items_with_plex_to_plex_only(
    connection_id: int,
    keep_ids: list[int],
    *,
    _session: Session = None,  # type: ignore
) -> list[int]:
    """Demote Arr rows being removed that still have a Plex link to Plex-only rows."""
    rows = _session.exec(
        select(Media)
        .where(Media.connection_id == connection_id)
        .where(~col(Media.id).in_(keep_ids))
        .where(col(Media.plex_connection_id).is_not(None))
    ).all()
    demoted_ids: list[int] = []
    for db in rows:
        db.connection_id = db.plex_connection_id  # type: ignore
        db.arr_id = 0
        db.updated_at = datetime.now(timezone.utc)
        _session.add(db)
        demoted_ids.append(db.id)  # type: ignore
    _session.commit()
    return demoted_ids


@write_session
def delete_except(connection_id: int, media_ids: list[int], *, _session: Session = None) -> None:  # type: ignore
    """Delete all media for a connection except the given ids."""
    rows = _session.exec(
        select(Media)
        .where(Media.connection_id == connection_id)
        .where(~col(Media.id).in_(media_ids))
    ).all()
    for db in rows:
        _session.delete(db)
    _session.commit()
