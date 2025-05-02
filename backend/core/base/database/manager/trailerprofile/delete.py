from sqlmodel import Session

from app_logger import ModuleLogger
from core.base.database.models.trailerprofile import TrailerProfile
from core.base.database.utils.engine import manage_session

logger = ModuleLogger("TrailerProfileManager")


@manage_session
def delete_trailerprofile(
    id: int, *, _session: Session = None  # type: ignore
) -> bool:
    """
    Delete a trailer profile by id.
    Args:
        id (int): The id of the trailer profile to delete.
        _session (Session, optional=None): A session to use for the \
            database connection. A new session is created if not provided.
    Returns:
        bool: True if the trailer profile was deleted successfully.
    """
    db_trailerprofile = _session.get(TrailerProfile, id)
    if not db_trailerprofile:
        return False

    # Delete all filters associated with the custom filter
    for filter in db_trailerprofile.customfilter.filters:
        _session.delete(filter)
    # Delete the custom filter associated with the trailer profile
    _session.delete(db_trailerprofile.customfilter)
    # Delete the trailer profile
    _session.delete(db_trailerprofile)
    _session.commit()
    logger.info(
        "Deleted trailer profile:"
        f" {db_trailerprofile.customfilter.filter_name}"
    )
    return True
