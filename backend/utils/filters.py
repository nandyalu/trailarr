from datetime import datetime

from db.models.filefolderinfo import FileFolderInfoRead, FileFolderType
from db.models.filter import FilterCondition, FilterRead
from db.models.media import MediaRead


def _matches_boolean(media_value: bool, f: FilterRead) -> bool:
    if f.filter_condition == FilterCondition.EQUALS:
        return media_value == (f.filter_value.lower() == "true")
    elif f.filter_condition == FilterCondition.NOT_EQUALS:
        return media_value != (f.filter_value.lower() == "true")
    return False


def _matches_number(media_value: float, f: FilterRead) -> bool:
    fv = float(f.filter_value)
    if f.filter_condition == FilterCondition.EQUALS:
        return media_value == fv
    elif f.filter_condition == FilterCondition.NOT_EQUALS:
        return media_value != fv
    elif f.filter_condition == FilterCondition.GREATER_THAN:
        return media_value > fv
    elif f.filter_condition == FilterCondition.GREATER_THAN_EQUAL:
        return media_value >= fv
    elif f.filter_condition == FilterCondition.LESS_THAN:
        return media_value < fv
    elif f.filter_condition == FilterCondition.LESS_THAN_EQUAL:
        return media_value <= fv
    return False


def _matches_datetime(media_value: datetime, f: FilterRead) -> bool:
    if f.filter_condition in {FilterCondition.IN_THE_LAST, FilterCondition.NOT_IN_THE_LAST}:
        delta = media_value.date() - datetime.now().date()
        if f.filter_condition == FilterCondition.IN_THE_LAST:
            return delta.days <= int(f.filter_value)
        return delta.days > int(f.filter_value)
    try:
        fd = datetime.strptime(f.filter_value, "%Y-%m-%d")
    except ValueError:
        return False
    if f.filter_condition == FilterCondition.EQUALS:
        return media_value.date() == fd.date()
    elif f.filter_condition == FilterCondition.NOT_EQUALS:
        return media_value.date() != fd.date()
    elif f.filter_condition == FilterCondition.IS_AFTER:
        return media_value.date() > fd.date()
    elif f.filter_condition == FilterCondition.IS_BEFORE:
        return media_value.date() < fd.date()
    return False


def _matches_string(media_value: str, f: FilterRead) -> bool:
    fv = f.filter_value
    if f.filter_condition == FilterCondition.EQUALS:
        return media_value == fv
    elif f.filter_condition == FilterCondition.NOT_EQUALS:
        return media_value != fv
    elif f.filter_condition == FilterCondition.CONTAINS:
        return fv in media_value
    elif f.filter_condition == FilterCondition.NOT_CONTAINS:
        return fv not in media_value
    elif f.filter_condition == FilterCondition.STARTS_WITH:
        return media_value.startswith(fv)
    elif f.filter_condition == FilterCondition.NOT_STARTS_WITH:
        return not media_value.startswith(fv)
    elif f.filter_condition == FilterCondition.ENDS_WITH:
        return media_value.endswith(fv)
    elif f.filter_condition == FilterCondition.NOT_ENDS_WITH:
        return not media_value.endswith(fv)
    elif f.filter_condition == FilterCondition.IS_EMPTY:
        return not media_value.strip()
    elif f.filter_condition == FilterCondition.IS_NOT_EMPTY:
        return bool(media_value.strip())
    return False


def _matches_generic(media_value, f: FilterRead) -> bool:
    if f.filter_condition == FilterCondition.IS_EMPTY:
        return media_value is None
    elif f.filter_condition == FilterCondition.IS_NOT_EMPTY:
        return media_value is not None
    return False


def _matches_filter(media_value, f: FilterRead) -> bool:
    if isinstance(media_value, bool):
        return _matches_boolean(media_value, f)
    elif isinstance(media_value, (int, float)):
        return _matches_number(media_value, f)
    elif isinstance(media_value, datetime):
        return _matches_datetime(media_value, f)
    elif isinstance(media_value, str):
        return _matches_string(media_value, f)
    return _matches_generic(media_value, f)


def _matches_file_filter(files: list[FileFolderInfoRead], f: FilterRead) -> bool:
    required_type = FileFolderType.FOLDER if f.filter_by.lower() == "has_folder" else FileFolderType.FILE
    for file in files:
        if file.type != required_type:
            continue
        if _matches_string(file.name, f):
            return True
    return False


def matches_filters(media: MediaRead, filters: list[FilterRead]) -> bool:
    """Return True if media passes all filters."""
    _files: list[FileFolderInfoRead] | None = None
    for f in filters:
        if f.filter_by in ("has_file", "has_folder"):
            if _files is None:
                from db.repos.file_info import read_flat
                _files = read_flat(media.id)
            if not _matches_file_filter(_files, f):
                return False
            continue
        media_value = getattr(media, f.filter_by, None)
        if not _matches_filter(media_value, f):
            return False
    return True
