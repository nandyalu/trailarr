from typing import Sequence
from core.base.database.models.customfilter import (
    CustomFilter,
    CustomFilterRead,
)


def convert_to_read_item(db_customfilter: CustomFilter) -> CustomFilterRead:
    """
    Convert a CustomFilter database object to a CustomFilterRead object.
    Args:
        db_customfilter (CustomFilter): CustomFilter database object
    Returns:
        CustomFilterRead: CustomFilterRead object
    """
    customfilter_read = CustomFilterRead.model_validate(db_customfilter)
    return customfilter_read


def convert_to_read_list(
    db_customfilter_list: Sequence[CustomFilter],
) -> list[CustomFilterRead]:
    """
    Convert a list of CustomFilter database objects to a list of \
        CustomFilterRead objects.
    Args:
        db_customfilter_list (list[CustomFilter]): List of CustomFilter\
            database objects
    Returns:
        list[CustomFilterRead]: List of CustomFilterRead objects
    """
    if not db_customfilter_list or len(db_customfilter_list) == 0:
        return []
    customfilter_read_list: list[CustomFilterRead] = []
    for db_customfilter in db_customfilter_list:
        customfilter_read = CustomFilterRead.model_validate(db_customfilter)
        customfilter_read_list.append(customfilter_read)
    return customfilter_read_list
