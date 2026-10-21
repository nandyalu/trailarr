"""Add a trailer profile to the database."""

from sqlmodel import Session

from app_logger import ModuleLogger
from database.manager.trailerprofile.base import convert_to_read_item

# from database.models.customfilter import CustomFilter
# from database.models.filter import Filter
from database.models.trailerprofile import (
    TrailerProfile,
    TrailerProfileCreate,
    TrailerProfileRead,
)
from database.models.video_type import is_trailer_type
from database.engine import write_session

logger = ModuleLogger("TrailerProfileManager")


@write_session
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
    # Search YouTube starts off for a profile of another type than Trailer
    # (Phase 9, decision 5 as amended): a search finds trailers, and
    # nothing in a result says that a video is a featurette. A create
    # that sets the flag itself keeps its value. Always Search goes off
    # with the search, because it needs it.
    if (
        not is_trailer_type(db_trailerprofile.video_type)
        and "search_youtube" not in trailerprofile_create.model_fields_set
        and db_trailerprofile.search_youtube
    ):
        db_trailerprofile.search_youtube = False
        db_trailerprofile.always_search = False
        logger.info(
            "Trailarr turned Search YouTube off for the new profile"
            f" '{trailerprofile_create.customfilter.filter_name}', because"
            " its Video Type is not Trailer. Turn it on to search."
        )
    # Save to database
    _session.add(db_trailerprofile)
    _session.commit()
    _session.refresh(db_trailerprofile)
    logger.info(
        "Trailarr created the trailer profile"
        f" '{db_trailerprofile.customfilter.filter_name}'."
    )
    return convert_to_read_item(db_trailerprofile)
