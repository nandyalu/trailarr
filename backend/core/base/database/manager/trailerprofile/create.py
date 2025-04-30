from sqlmodel import Session

from core.base.database.manager.trailerprofile.base import convert_to_read_item
from core.base.database.models.filter import Filter
from core.base.database.models.trailerprofile import (
    TrailerProfile,
    TrailerProfileCreate,
    TrailerProfileRead,
)
from core.base.database.utils.engine import manage_session


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
    """
    # Extract filters from the trailer profile create object
    # and create db Filter objects from them
    filter_create = trailerprofile_create.customfilter
    db_filters: list[Filter] = []
    for filter in filter_create.filters:
        db_filters.append(Filter.model_validate(filter))
    # Clear the filters from the trailer profile create object
    trailerprofile_create.customfilter.filters = []
    # Create a db TrailerProfile object
    db_trailerprofile = TrailerProfile.model_validate(trailerprofile_create)
    # Assign the filters to the db TrailerProfile object
    db_trailerprofile.customfilter.filters = db_filters
    _session.add(db_trailerprofile)
    _session.commit()
    _session.refresh(db_trailerprofile)
    return convert_to_read_item(db_trailerprofile)
