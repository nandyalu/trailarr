from sqlmodel import Session, select
from core.base.database.manager.trailerprofile.base import (
    convert_to_read_item,
    convert_to_read_list,
)
from core.base.database.models.trailerprofile import (
    TrailerProfile,
    TrailerProfileRead,
)
from core.base.database.utils.engine import manage_session
from exceptions import ItemNotFoundError


@manage_session
def get_trailerprofile(
    trailerprofile_id: int,
    *,
    _session: Session = None,  # type: ignore
) -> TrailerProfileRead:
    """
    Get a trailer profile by ID.
    Args:
        trailerprofile_id (int): The ID of the trailer profile to retrieve.
        _session (Session, optional=None): A session to use for the \
            database connection. A new session is created if not provided.
    Returns:
        TrailerProfileRead: The trailer profile (read-only).
    Raises:
        ItemNotFoundError: If the trailer profile with the given ID is not found.
    """
    db_trailerprofile = _session.get(TrailerProfile, trailerprofile_id)
    if db_trailerprofile is None:
        raise ItemNotFoundError(
            model_name="TrailerProfile", id=trailerprofile_id
        )
    return convert_to_read_item(db_trailerprofile)


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


@manage_session
def get_trailer_folders(
    *,
    _session: Session = None,  # type: ignore
) -> set[str]:
    """
    Get all Trailer folder names from the database.
    Args:
        _session (Session, optional=None): A session to use for the \
            database connection. A new session is created if not provided.
    Returns:
        set[str]: Set of folder names.
    """
    statement = select(TrailerProfile.folder_name).distinct()
    db_trailerprofiles = _session.exec(statement).all()
    return {folder.strip() for folder in db_trailerprofiles}
