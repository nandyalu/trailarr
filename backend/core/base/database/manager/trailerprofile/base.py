from typing import Sequence

from core.base.database.models.trailerprofile import (
    TrailerProfile,
    TrailerProfileRead,
)


def convert_to_read_item(
    db_profile: TrailerProfile,
) -> TrailerProfileRead:
    """
    Convert a TrailerProfile database object to a TrailerProfileRead object.
    Args:
        db_profile (TrailerProfile): TrailerProfile database object
    Returns:
        TrailerProfileRead: TrailerProfileRead object
    """
    trailerprofile_read = TrailerProfileRead.model_validate(db_profile)
    return trailerprofile_read


def convert_to_read_list(
    db_profile_list: Sequence[TrailerProfile],
) -> list[TrailerProfileRead]:
    """
    Convert a list of TrailerProfile database objects to a list of \
        TrailerProfileRead objects.
    Args:
        db_profile_list (list[TrailerProfile]): List of TrailerProfile\
            database objects
    Returns:
        list[TrailerProfileRead]: List of TrailerProfileRead objects
    """
    if not db_profile_list or len(db_profile_list) == 0:
        return []
    trailerprofile_read_list: list[TrailerProfileRead] = []
    for db_profile in db_profile_list:
        trailerprofile_read = TrailerProfileRead.model_validate(db_profile)
        trailerprofile_read_list.append(trailerprofile_read)
    return trailerprofile_read_list
