"""Change a trailer profile that is already stored."""

from sqlmodel import Session, col, select

from app_logger import ModuleLogger
from database.manager.customfilter.update import __update_filters
from database.manager.trailerprofile.base import (
    convert_to_read_item,
)
from database.models.trailerprofile import (
    TrailerProfile,
    TrailerProfileCreate,
    TrailerProfileRead,
)
from database.engine import write_session
from database.models.download import Download
from database.models.video_type import is_trailer_type, normalize_video_type
from exceptions import ItemNotFoundError

logger = ModuleLogger("TrailerProfileManager")


@write_session
def update_trailerprofile(
    trailerprofile_id: int,
    trailerprofile_create: TrailerProfileCreate,
    *,
    _session: Session = None,  # type: ignore
) -> TrailerProfileRead:
    """
    Update a trailer profile in the database.
    Args:
        trailerprofile_id (int): The ID of the trailer profile to update.
        trailerprofile_create (TrailerProfileCreate): The new data for the trailer profile.
        _session (Session, optional): A session to use for the database connection. Defaults to None.
    Returns:
        TrailerProfileRead: The updated trailer profile.
    Raises:
        ItemNotFoundError: If the trailer profile with the given ID is not found.
        ValueError: If the trailer profile is invalid.
    """
    # Get the existing trailer profile from the database
    trailerprofile_db = _session.get(TrailerProfile, trailerprofile_id)
    if trailerprofile_db is None:
        raise ItemNotFoundError(
            model_name="TrailerProfile", id=trailerprofile_id
        )

    # Update the fields of the existing trailer profile
    old_video_type = trailerprofile_db.video_type
    _update_data = trailerprofile_create.model_dump(exclude_unset=True)
    trailerprofile_db.sqlmodel_update(_update_data)
    if "search_youtube" not in _update_data:
        _search_off_for_extras(trailerprofile_db, old_video_type)
    elif not trailerprofile_db.search_youtube:
        _always_search_off_with_the_search(trailerprofile_db)
    # Update the filters
    __update_filters(
        trailerprofile_db.customfilter,
        trailerprofile_create.customfilter,
        _session=_session,
    )

    # Validate the updated trailer profile
    TrailerProfile.model_validate(trailerprofile_db)

    # The downloads change type in the same transaction as the profile,
    # so the two can never disagree (wargame W1).
    _relabel_downloads(trailerprofile_db, old_video_type, _session=_session)
    # Commit the changes to the database
    # _session.add(trailerprofile_db)
    _session.commit()
    _session.refresh(trailerprofile_db)
    logger.info(
        "Trailarr updated the trailer profile"
        f" '{trailerprofile_db.customfilter.filter_name}'."
    )
    return convert_to_read_item(trailerprofile_db)


def _search_off_for_extras(
    trailerprofile_db: TrailerProfile, old_video_type: str
) -> None:
    """Turn the search off when a profile leaves the Trailer type.

    A search finds trailers, and nothing in a result says that a video
    is a featurette, so a profile of another type starts without the
    search. A person who wants it turns it on again. Always Search goes
    off with it, because it needs the search.
    """
    if not is_trailer_type(old_video_type):
        return
    if is_trailer_type(trailerprofile_db.video_type):
        return
    if not trailerprofile_db.search_youtube:
        return
    trailerprofile_db.search_youtube = False
    trailerprofile_db.always_search = False
    logger.info(
        "Trailarr turned Search YouTube off for the profile"
        f" '{trailerprofile_db.customfilter.filter_name}', because its"
        " Video Type is no longer Trailer. Turn it on again to search."
    )


def _always_search_off_with_the_search(
    trailerprofile_db: TrailerProfile,
) -> None:
    """Turn Always Search off when the search goes off.

    Always Search is a mode of the search. A person who turns Search
    YouTube off means "do not search", so Always Search goes off with
    it, instead of the update failing because the two disagree.
    """
    if not trailerprofile_db.always_search:
        return
    trailerprofile_db.always_search = False
    logger.info(
        "Trailarr turned Always Search off for the profile"
        f" '{trailerprofile_db.customfilter.filter_name}', because Search"
        " YouTube is off for it."
    )


def _relabel_downloads(
    trailerprofile_db: TrailerProfile,
    old_video_type: str,
    *,
    _session: Session,
) -> None:
    """Give the downloads of a profile its new video type.

    A profile that changes its type keeps its downloads: they are what
    it asked for. Without this, the satisfaction rule would see no
    download of the new type and download every item again (wargame W1).

    Runs in the session of the profile update, before its commit: the
    profile and its downloads change in one transaction, so a failure
    leaves both as they were. The caller commits.
    """
    new_video_type = trailerprofile_db.video_type
    if new_video_type == old_video_type:
        return
    statement = (
        select(Download)
        .where(Download.profile_id == trailerprofile_db.id)
        .where(col(Download.video_type) != new_video_type)
    )
    rows = _session.exec(statement).all()
    for row in rows:
        row.video_type = new_video_type
        _session.add(row)
    if rows:
        logger.info(
            f"Trailarr changed the video type of {len(rows)} downloads of"
            f" the profile '{trailerprofile_db.customfilter.filter_name}'"
            f" from '{old_video_type}' to '{new_video_type}'."
        )


@write_session
def update_trailerprofile_setting(
    id: int,
    setting: str,
    value: str | int | bool,
    *,
    _session: Session = None,  # type: ignore
) -> TrailerProfileRead:
    """
    Update a setting of a trailer profile in the database.
    Args:
        id (int): The ID of the trailer profile to update.
        setting (str): The name of the setting to update.
        value (str | int | bool): The new value for the setting.
        _session (Session, optional): A session to use for the database connection. Defaults to None.
    Returns:
        TrailerProfileRead: The updated trailer profile.
    Raises:
        ItemNotFoundError: If the trailer profile with the given ID is not found.
        ValueError: If the trailer profile is invalid.
    """
    # Get the existing trailer profile from the database
    trailerprofile_db = _session.get(TrailerProfile, id)
    if trailerprofile_db is None:
        raise ItemNotFoundError(model_name="TrailerProfile", id=id)

    # Update the specified setting
    if not hasattr(trailerprofile_db, setting):
        raise ValueError(f"Invalid setting '{setting}' for trailer profile.")
    old_video_type = trailerprofile_db.video_type
    if TrailerProfile.is_bool_field(setting):
        # Convert the value to a boolean if the setting is a boolean field
        value = trailerprofile_db.validate_bool(value)
    if TrailerProfile.is_int_field(setting):
        # Convert the value to an integer if the setting is an integer field
        value = int(value)
    if setting == "video_type":
        # The row and its downloads take the stored form, 'featurette',
        # never 'Featurette': the resolver reads rows by this exact value.
        value = normalize_video_type(value)
    setattr(trailerprofile_db, setting, value)
    if setting == "video_type":
        _search_off_for_extras(trailerprofile_db, old_video_type)
    if setting == "search_youtube" and not value:
        _always_search_off_with_the_search(trailerprofile_db)

    # Validate the updated trailer profile
    TrailerProfile.model_validate(trailerprofile_db)

    # The downloads change type in the same transaction as the profile
    # (wargame W1).
    _relabel_downloads(trailerprofile_db, old_video_type, _session=_session)
    # Commit the changes to the database
    # _session.add(new_profile)
    _session.commit()
    _session.refresh(trailerprofile_db)
    logger.info(
        "Trailarr updated the trailer profile"
        f" '{trailerprofile_db.customfilter.filter_name}'. It set"
        f" {setting} to {value}."
    )
    return convert_to_read_item(trailerprofile_db)
