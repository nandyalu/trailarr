from sqlmodel import Session

from . import base
from core.base.database.models.connection import ArrType
from core.base.database.utils.engine import write_session


@write_session
def delete(
    connection_id: int,
    *,
    _session: Session = None,  # type: ignore
) -> bool:
    """Delete a connection from the database \n
    Args:
        connection_id (int): The id of the connection to delete
        _session (optional): A session to use for the database connection. \
            Defaults to None, in which case a new session is created. \n
    Returns:
        bool: True if the connection was deleted successfully. \n
    Raises:
        ItemNotFoundError: If a connection with provided id does not exist
    """
    connection = base._get_db_item(connection_id, _session=_session)

    # For Plex connections: fire PLEX_UNLINKED for any Arr-sourced rows that
    # are linked to this connection.  Must happen *before* the DELETE so the
    # media rows still exist (plex_connection_id is SET NULL by the cascade).
    if connection.arr_type == ArrType.PLEX:
        # Import here to avoid circular imports at module level
        import core.base.database.manager.media as media_manager
        import core.base.database.manager.event as event_manager
        from core.base.database.models.event import EventSource

        linked_media = media_manager.read_arr_linked_to_plex_connection(
            connection_id, _session=_session
        )
        for media in linked_media:
            event_manager.track_plex_unlinked(
                media_id=media.id,
                connection_name=connection.name,
                source=EventSource.SYSTEM,
                source_detail="ConnectionDeleted",
                _session=_session,
            )

    _session.delete(connection)
    # SQLite will take care of the cascade delete of path mappings and media items.
    # No need to manually delete them here. Just commit the transaction to persist the changes.
    _session.commit()
    return True
