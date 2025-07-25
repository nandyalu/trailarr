from sqlmodel import Session

from app_logger import ModuleLogger
from core.base.database.manager.trailerprofile.base import convert_to_read_item

# from core.base.database.models.customfilter import CustomFilter
# from core.base.database.models.filter import Filter
from core.base.database.models.trailerprofile import (
    TrailerProfile,
    TrailerProfileCreate,
    TrailerProfileRead,
)
from core.base.database.utils.engine import manage_session

logger = ModuleLogger("TrailerProfileManager")


@manage_session
def create_trailerprofile(
    trailerprofile_create: TrailerProfileCreate,
    *,
    _session: Session = None,  # type: ignore
) -> TrailerProfileRead:
    """
    Create a new trailer profile.
    Args:
        trailerprofile_create (TrailerProfileCreate): TrailerProfileCreate model
        _session (Session, optional=None): A session to use for the \
            database connection. A new session is created if not provided.
    Returns:
        TrailerProfileRead: TrailerProfileRead object
    Raises:
        ValidationError: If the input data is not valid.
    """
    # Create a db TrailerProfile object
    db_trailerprofile = TrailerProfile.model_validate(trailerprofile_create)
    # Save to database
    _session.add(db_trailerprofile)
    _session.commit()
    _session.refresh(db_trailerprofile)
    logger.info(
        "Created trailer profile:"
        f" {db_trailerprofile.customfilter.filter_name}"
    )
    return convert_to_read_item(db_trailerprofile)
