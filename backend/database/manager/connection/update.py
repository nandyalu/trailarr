"""Change a stored connection to a Radarr, Sonarr or Plex server."""

from sqlmodel import Session, select

from . import base
from database.models.connection import (
    ConnectionRead,
    ConnectionUpdate,
    PathMapping,
)
from database.engine import write_session
from utils.path_utils import normalize_trailing_slash


@write_session
def update_path_mapping_section_key(
    pm_id: int,
    section_key: str,
    *,
    _session: Session = None,  # type: ignore
) -> None:
    """Persist the detected Plex library section key on a path mapping row.

    Called by PlexConnectionManager the first time it discovers which section
    a path mapping belongs to.  Skips gracefully if the row is not found.
    """
    pm = _session.exec(select(PathMapping).where(PathMapping.id == pm_id)).first()
    if pm is None:
        return
    pm.plex_section_key = section_key
    _session.add(pm)
    _session.commit()


@write_session
def add_path_mapping(
    connection_id: int,
    path_from: str,
    path_to: str,
    *,
    _session: Session = None,  # type: ignore
) -> None:
    """Add one path mapping row to a connection.

    Used by the Connection Doctor's one-click "Apply" for a suggested
    mapping. It updates path_to when the same path_from is already on
    the connection (the user applied it twice).
    """
    path_from = normalize_trailing_slash(path_from)
    path_to = normalize_trailing_slash(path_to)
    existing = _session.exec(
        select(PathMapping)
        .where(PathMapping.connection_id == connection_id)
        .where(PathMapping.path_from == path_from)
    ).first()
    if existing is not None:
        existing.path_to = path_to
        _session.add(existing)
        _session.commit()
        return
    _session.add(
        PathMapping(
            connection_id=connection_id,
            path_from=path_from,
            path_to=path_to,
        )
    )
    _session.commit()


@write_session
def update(
    connection_id: int,
    connection_update: ConnectionUpdate,
    *,
    machine_identifier: str | None = None,
    _session: Session = None,  # type: ignore
) -> ConnectionRead:
    """Write the changed fields of a connection to the database.

    The caller validates the connection against the server first. This
    function only writes the row. See `services/connections/service.py`.

    Args:
        connection_id (int): The id of the connection to update.
        connection_update (ConnectionUpdate): The fields to change.
        machine_identifier (str | None): The Plex server identifier, when
            the caller read one. `None` leaves the stored value alone.
        _session (optional): A session to use for the database connection. \
            Defaults to None, in which case a new session is created. \n

    Returns:
        ConnectionRead: The updated read-only connection object. \n

    Raises:
        ItemNotFoundError: If a connection with provided id does not exist
    """
    # Get the connection from the database
    db_connection = base._get_db_item(connection_id, _session=_session)
    # Update the connection details from input
    connection_update_data = connection_update.model_dump(exclude_unset=True)
    db_connection.sqlmodel_update(connection_update_data)
    # Update the path mappings
    base._update_path_mappings(
        db_connection, connection_update, _session=_session
    )
    # Store the Plex machine identifier the caller read, if there is one
    if machine_identifier is not None:
        db_connection.machine_identifier = machine_identifier
    # Commit the changes to the database
    _session.add(db_connection)
    _session.commit()
    return ConnectionRead.model_validate(db_connection)
