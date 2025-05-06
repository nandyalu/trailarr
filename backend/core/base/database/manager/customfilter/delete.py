from sqlmodel import Session

from core.base.database.models.customfilter import CustomFilter
from core.base.database.utils.engine import manage_session


@manage_session
def delete_customfilter(
    id: int, *, _session: Session = None  # type: ignore
) -> bool:
    """
    Delete a Custom filter by id.
    Args:
        id (int): The id of the view filter to delete.
        _session (Session, optional=None): A session to use for the \
            database connection. A new session is created if not provided.
    Returns:
        bool: True if the Custom filter was deleted successfully.
    """
    db_customfilter = _session.get(CustomFilter, id)
    if not db_customfilter:
        return False

    # Delete all filters associated with the custom filter
    for filter in db_customfilter.filters:
        _session.delete(filter)
    # Delete the custom filter
    _session.delete(db_customfilter)
    _session.commit()
    return True
