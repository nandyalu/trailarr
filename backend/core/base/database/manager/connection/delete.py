from sqlmodel import Session

from . import base
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
    _session.delete(connection)
    # SQLite will take care of the cascade delete of path mappings and media items.
    # No need to manually delete them here. Just commit the transaction to persist the changes.
    _session.commit()
    return True
