from sqlmodel import Session, select
from core.base.database.manager.trailerprofile.base import convert_to_read_list
from core.base.database.models.trailerprofile import (
    TrailerProfile,
    TrailerProfileRead,
)
from core.base.database.utils.engine import manage_session


@manage_session
def get_trailerprofiles(
    *,
    _session: Session = None,  # type: ignore
) -> list[TrailerProfileRead]:
    """
    Get all trailer profiles.
    Args:
        _session (Session, optional=None): A session to use for the \
            database connection. A new session is created if not provided.
    Returns:
        list[TrailerProfileRead]: List of trailer profiles (read-only).
    """
    statement = select(TrailerProfile)
    db_trailerprofiles = _session.exec(statement).all()
    return convert_to_read_list(db_trailerprofiles)
