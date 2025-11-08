from sqlmodel import Session

from . import base
from core.base.database.utils.engine import manage_session


@manage_session
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
    # # Delete all path mappings associated with the connection
    # for path_mapping in connection.path_mappings:
    #     _session.delete(path_mapping)
    # # Delete all media associated with the connection
    # _statement = select(Media).where(Media.connection_id == connection_id)
    # media_list = _session.exec(_statement).all()
    # for media in media_list:
    #     _session.delete(media)
    _session.commit()
    return True
