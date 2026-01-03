from datetime import datetime
from core.base.database.manager import filefolderinfo as files_manager
from core.base.database.models.filefolderinfo import (
    FileFolderInfoRead,
    FileFolderType,
)
from core.base.database.models.filter import FilterCondition, FilterRead
from core.base.database.models.media import MediaRead


def _matches_boolean(media_value: bool, filter: FilterRead) -> bool:
    """Handle boolean comparisons."""
    if filter.filter_condition == FilterCondition.EQUALS:
        return media_value == (filter.filter_value.lower() == "true")
    elif filter.filter_condition == FilterCondition.NOT_EQUALS:
        return media_value != (filter.filter_value.lower() == "true")
    return False  # Unsupported condition for booleans


def _matches_number(media_value: float, filter: FilterRead) -> bool:
    """Handle numeric comparisons."""
    filter_value = float(filter.filter_value)
    if filter.filter_condition == FilterCondition.EQUALS:
        return media_value == filter_value
    elif filter.filter_condition == FilterCondition.NOT_EQUALS:
        return media_value != filter_value
    elif filter.filter_condition == FilterCondition.GREATER_THAN:
        return media_value > filter_value
    elif filter.filter_condition == FilterCondition.GREATER_THAN_EQUAL:
        return media_value >= filter_value
    elif filter.filter_condition == FilterCondition.LESS_THAN:
        return media_value < filter_value
    elif filter.filter_condition == FilterCondition.LESS_THAN_EQUAL:
        return media_value <= filter_value
    return False  # Unsupported condition for numbers


def _matches_datetime(media_value: datetime, filter: FilterRead) -> bool:
    """Handle datetime comparisons."""
    if filter.filter_condition in {
        FilterCondition.IN_THE_LAST,
        FilterCondition.NOT_IN_THE_LAST,
    }:
        _delta = media_value.date() - datetime.now().date()
        if filter.filter_condition == FilterCondition.IN_THE_LAST:
            return _delta.days <= int(filter.filter_value)
        elif filter.filter_condition == FilterCondition.NOT_IN_THE_LAST:
            return _delta.days > int(filter.filter_value)
    else:
        try:
            filter_date = datetime.strptime(filter.filter_value, "%Y-%m-%d")
        except ValueError:
            return False  # Invalid date format in filter_value

        if filter.filter_condition == FilterCondition.EQUALS:
            return media_value.date() == filter_date.date()
        elif filter.filter_condition == FilterCondition.NOT_EQUALS:
            return media_value.date() != filter_date.date()
        elif filter.filter_condition == FilterCondition.IS_AFTER:
            return media_value.date() > filter_date.date()
        elif filter.filter_condition == FilterCondition.IS_BEFORE:
            return media_value.date() < filter_date.date()
    return False  # Unsupported condition for dates


def _matches_string(media_value: str, filter: FilterRead) -> bool:
    """Handle string comparisons."""
    filter_value = filter.filter_value
    if filter.filter_condition == FilterCondition.EQUALS:
        return media_value == filter_value
    elif filter.filter_condition == FilterCondition.NOT_EQUALS:
        return media_value != filter_value
    elif filter.filter_condition == FilterCondition.CONTAINS:
        return filter_value in media_value
    elif filter.filter_condition == FilterCondition.NOT_CONTAINS:
        return filter_value not in media_value
    elif filter.filter_condition == FilterCondition.STARTS_WITH:
        return media_value.startswith(filter_value)
    elif filter.filter_condition == FilterCondition.NOT_STARTS_WITH:
        return not media_value.startswith(filter_value)
    elif filter.filter_condition == FilterCondition.ENDS_WITH:
        return media_value.endswith(filter_value)
    elif filter.filter_condition == FilterCondition.NOT_ENDS_WITH:
        return not media_value.endswith(filter_value)
    elif filter.filter_condition == FilterCondition.IS_EMPTY:
        return not media_value.strip()
    elif filter.filter_condition == FilterCondition.IS_NOT_EMPTY:
        return bool(media_value.strip())
    return False  # Unsupported condition for strings


def _matches_generic(media_value, filter: FilterRead) -> bool:
    """Handle generic comparisons for unsupported types."""
    if filter.filter_condition == FilterCondition.IS_EMPTY:
        return media_value is None
    elif filter.filter_condition == FilterCondition.IS_NOT_EMPTY:
        return media_value is not None
    return False


def _matches_filter(media_value, filter: FilterRead) -> bool:
    """Check if a single media value matches a filter."""

    if isinstance(media_value, bool):
        return _matches_boolean(media_value, filter)
    elif isinstance(media_value, (int, float)):
        return _matches_number(media_value, filter)
    elif isinstance(media_value, datetime):
        return _matches_datetime(media_value, filter)
    elif isinstance(media_value, str):
        return _matches_string(media_value, filter)
    else:
        return _matches_generic(media_value, filter)


def _matches_file_filter(
    files: list[FileFolderInfoRead], filter: FilterRead
) -> bool:
    """Check if the media item has an associated file."""
    # Determine required type based on filter
    required_type = FileFolderType.FILE
    if filter.filter_by.lower() == "has_folder":
        required_type = FileFolderType.FOLDER
    # Check for matches in files
    for file in files:
        # Skip if type does not match
        if file.type != required_type:
            continue
        if _matches_string(file.name, filter):
            return True
    return False


def matches_filters(media: MediaRead, filters: list[FilterRead]) -> bool:
    """Check if a media item matches the given filters.
    Args:
        media (MediaRead): The media item to check.
        filters (list[FilterRead]): The list of filters to apply.
    Returns:
        bool: True if the media item matches all filters, False otherwise.
    """
    # Cache media files if fetched
    _files: list[FileFolderInfoRead] | None = None

    for filter in filters:
        # Handle special cases for 'has_file' and 'has_folder'
        if filter.filter_by in ("has_file", "has_folder"):
            if _files is None:
                _files = files_manager.read_by_media_id_flat(media.id)
            if not _matches_file_filter(_files, filter):
                return False
            continue
        # Generic attribute matching
        media_value = getattr(media, filter.filter_by, None)
        if not _matches_filter(media_value, filter):
            return False
    return True
