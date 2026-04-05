from sqlmodel import Session, col, select

from core.base.database.models.media import Media
from core.base.database.utils.engine import write_session

# There are no explicit media delete methods bacause we shouldn't be deleting them,
# instead media is added/updated/deleted in bulk during connection updates.
# The delete_except method is used to delete all media items except the ones provided,
# which is the most common use case for deleting media items.


@write_session
def delete_except(
    connection_id: int,
    media_ids: list[int],
    *,
    _session: Session = None,  # type: ignore
) -> None:
    """Delete all media items from the database except the ones provided.\n
    Args:
        connection_id (int): The id of the connection to delete media items for.
        media_ids (list[int]): List of media id's to keep.
        _session (Session, Optional): A session to use for the database connection.\
            Default is None, in which case a new session will be created.\n
    Returns:
        None
    Raises:
        ItemNotFoundError: If any of the media items with provided id's don't exist.
    """
    statement = (
        select(Media)
        .where(Media.connection_id == connection_id)
        .where(~col(Media.id).in_(media_ids))
    )
    db_media_list = _session.exec(statement).all()
    for db_media in db_media_list:
        _session.delete(db_media)
    _session.commit()
    return
