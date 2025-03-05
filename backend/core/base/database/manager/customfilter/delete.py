from sqlmodel import Session

from core.base.database.models.customfilter import CustomFilter


def delete_customfilter(
    id: int, *, _session: Session = None  # type: ignore
) -> bool:
    """
    Delete a view filter by id.
    Args:
        id (int): The id of the view filter to delete.
        _session (Session, optional=None): A session to use for the \
            database connection. A new session is created if not provided.
    Returns:
        bool: True if the view filter was deleted successfully.
    """
    db_customfilter = _session.get(CustomFilter, id)
    if not db_customfilter:
        return False
    _session.delete(db_customfilter)
    _session.commit()
    return True
