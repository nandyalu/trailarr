from sqlmodel import Session

from app_logger import ModuleLogger
from core.base.database.manager.customfilter.update import __update_filters
from core.base.database.manager.trailerprofile.base import (
    convert_to_read_item,
)
from core.base.database.models.trailerprofile import (
    TrailerProfile,
    TrailerProfileCreate,
    TrailerProfileRead,
)
from core.base.database.utils.engine import manage_session
from exceptions import ItemNotFoundError

logger = ModuleLogger("TrailerProfileManager")


@manage_session
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
    _update_data = trailerprofile_create.model_dump(exclude_unset=True)
    trailerprofile_db.sqlmodel_update(_update_data)
    # Update the filters
    __update_filters(
        trailerprofile_db.customfilter,
        trailerprofile_create.customfilter,
        _session=_session,
    )

    # Validate the updated trailer profile
    TrailerProfile.model_validate(trailerprofile_db)

    # Commit the changes to the database
    # _session.add(trailerprofile_db)
    _session.commit()
    _session.refresh(trailerprofile_db)
    logger.info(
        "Updated trailer profile:"
        f" {trailerprofile_db.customfilter.filter_name}"
    )
    return convert_to_read_item(trailerprofile_db)


@manage_session
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
    if TrailerProfile.is_bool_field(setting):
        # Convert the value to a boolean if the setting is a boolean field
        value = trailerprofile_db.validate_bool(value)
    if TrailerProfile.is_int_field(setting):
        # Convert the value to an integer if the setting is an integer field
        value = int(value)
    setattr(trailerprofile_db, setting, value)

    # Validate the updated trailer profile
    TrailerProfile.model_validate(trailerprofile_db)

    # Commit the changes to the database
    # _session.add(new_profile)
    _session.commit()
    _session.refresh(trailerprofile_db)
    logger.info(
        "Updated trailer profile setting:"
        f" {trailerprofile_db.customfilter.filter_name} - {setting}: {value}"
    )
    return convert_to_read_item(trailerprofile_db)
