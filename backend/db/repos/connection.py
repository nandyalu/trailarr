"""Connection repository — pure DB access only.

validate_connection() and get_rootfolders() live in services/connection_service.py
because they call external APIs. Event tracking (plex_unlinked on delete) is also
in connection_service.py.
"""
from sqlmodel import Session, select

from db.engine import read_session, write_session
from db.models.connection import (
    ArrType,
    Connection,
    ConnectionCreate,
    ConnectionRead,
    ConnectionUpdate,
    PathMapping,
)
from exceptions import ItemNotFoundError
from utils.path_utils import normalize_trailing_slash


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_or_404(connection_id: int, session: Session) -> Connection:
    connection = session.get(Connection, connection_id)
    if not connection:
        raise ItemNotFoundError("Connection", connection_id)
    return connection


def _convert_path_mappings(
    connection: ConnectionCreate | ConnectionUpdate,
) -> list[PathMapping]:
    db_path_mappings: list[PathMapping] = []
    for pm in connection.path_mappings:
        db_pm = PathMapping.model_validate(pm)
        db_pm.path_from = normalize_trailing_slash(db_pm.path_from)
        db_pm.path_to = normalize_trailing_slash(db_pm.path_to)
        db_path_mappings.append(db_pm)
    return db_path_mappings


def _sync_path_mappings(
    db_connection: Connection,
    connection_update: ConnectionUpdate,
    *,
    session: Session,
) -> None:
    new_mappings = _convert_path_mappings(connection_update)
    new_ids = [m.id for m in new_mappings if m.id]
    existing = db_connection.path_mappings
    existing_dict = {m.id: m for m in existing}

    for db_pm in existing[:]:
        if db_pm.id not in new_ids:
            db_connection.path_mappings.remove(db_pm)
            session.delete(db_pm)

    for new_pm in new_mappings:
        if new_pm.id:
            if new_pm.id in existing_dict:
                ex = existing_dict[new_pm.id]
                ex.path_from = new_pm.path_from
                ex.path_to = new_pm.path_to
                session.add(ex)
            else:
                new_pm.id = None
                new_pm.connection_id = db_connection.id
                db_connection.path_mappings.append(new_pm)
        else:
            db_connection.path_mappings.append(new_pm)


# ---------------------------------------------------------------------------
# Public CRUD
# ---------------------------------------------------------------------------

@read_session
def exists(connection_id: int, *, _session: Session = None) -> bool:  # type: ignore
    return bool(_session.get(Connection, connection_id))


@read_session
def read(connection_id: int, *, _session: Session = None) -> ConnectionRead:  # type: ignore
    return ConnectionRead.model_validate(_get_or_404(connection_id, _session))


@read_session
def read_all(*, _session: Session = None) -> list[ConnectionRead]:  # type: ignore
    return [ConnectionRead.model_validate(c) for c in _session.exec(select(Connection)).all()]


@write_session
def save(db_connection: Connection, *, _session: Session = None) -> int:  # type: ignore
    """Persist a pre-validated Connection object. Returns the new id."""
    _session.add(db_connection)
    _session.commit()
    assert db_connection.id is not None
    return db_connection.id


@write_session
def create(connection_create: ConnectionCreate, *, _session: Session = None) -> tuple[ConnectionRead, int]:  # type: ignore
    """Create a new connection row from a ConnectionCreate.

    Does NOT validate connectivity — call connection_service.validate() first.
    Returns (ConnectionRead, new_id).
    """
    path_mappings = _convert_path_mappings(connection_create)
    connection_create.path_mappings = []
    db_conn = Connection.model_validate(connection_create)
    db_conn.path_mappings = path_mappings
    _session.add(db_conn)
    _session.commit()
    _session.refresh(db_conn)
    return ConnectionRead.model_validate(db_conn), db_conn.id  # type: ignore


@write_session
def update(
    connection_id: int,
    connection_update: ConnectionUpdate,
    machine_identifier: str | None = None,
    *,
    _session: Session = None,  # type: ignore
) -> ConnectionRead:
    """Update an existing connection.

    Accepts a pre-fetched machine_identifier for Plex (pass None for Arr).
    Does NOT re-validate connectivity — call connection_service.validate() first.
    """
    db_conn = _get_or_404(connection_id, _session)
    update_data = connection_update.model_dump(exclude_unset=True)
    db_conn.sqlmodel_update(update_data)
    _sync_path_mappings(db_conn, connection_update, session=_session)
    if machine_identifier is not None:
        db_conn.machine_identifier = machine_identifier
    _session.add(db_conn)
    _session.commit()
    _session.refresh(db_conn)
    return ConnectionRead.model_validate(db_conn)


@write_session
def update_path_mapping_section_key(
    pm_id: int,
    section_key: str,
    *,
    _session: Session = None,  # type: ignore
) -> None:
    pm = _session.exec(select(PathMapping).where(PathMapping.id == pm_id)).first()
    if pm is None:
        return
    pm.plex_section_key = section_key
    _session.add(pm)
    _session.commit()


@write_session
def delete(connection_id: int, *, _session: Session = None) -> bool:  # type: ignore
    """Delete a connection row.

    Does NOT fire PLEX_UNLINKED events — call connection_service.delete() which
    fires events before delegating here.
    """
    db_conn = _get_or_404(connection_id, _session)
    _session.delete(db_conn)
    _session.commit()
    return True


@read_session
def read_arr_linked_to_plex(plex_connection_id: int, *, _session: Session = None) -> list:  # type: ignore
    """Return Arr-sourced media rows (as plain Media objects) linked to this Plex connection.

    Used by connection_service before deleting a Plex connection to fire events.
    Returns raw Media ORM objects — caller must convert if needed.
    """
    from db.models.media import Media, MediaRead
    stmt = select(Media).where(
        (Media.plex_connection_id == plex_connection_id)
        & (Media.connection_id != plex_connection_id)
    )
    return [MediaRead.model_validate(m) for m in _session.exec(stmt).all()]
