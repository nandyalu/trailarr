from datetime import datetime
from . import base
from sqlmodel import select, Session, text
from core.base.database.models.filefolderinfo import (
    FileFolderInfo,
    FileFolderInfoRead,
    FileFolderType,
)
from core.base.database.utils.engine import read_session


@read_session
def read_by_media_id_flat(
    media_id: int,
    *,
    _session: Session = None,  # type: ignore
) -> list[FileFolderInfoRead]:
    """
    Get FileFolderInfoRead tree for a specific media ID.
    Args:
        media_id (int): The media ID to filter downloads by.
        _session (Session, optional=None): A session to use for the \
            database connection. A new session is created if not provided.
    Returns:
        list[FileFolderInfoRead]: Flat list of file/folder info (read-only).
    """
    statement = select(FileFolderInfo).where(
        FileFolderInfo.media_id == media_id
    )
    db_filefolderinfo = _session.exec(statement).all()
    return base.convert_to_read_list(db_filefolderinfo)


@read_session
def read_by_media_id(
    media_id: int,
    *,
    _session: Session = None,  # type: ignore
) -> FileFolderInfoRead | None:
    """Get FileFolderInfo tree for a specific media ID.
    Args:
        media_id (int): The media ID to filter downloads by.
        _session (Session, optional=None): A session to use for the \
            database connection. A new session is created if not provided.
    Returns:
        FileFolderInfoRead | None: The file/folder info tree (read-only), or \
            None if not found.
    """
    flat_items = read_by_media_id_flat(
        media_id,
        _session=_session,
    )
    if not flat_items or len(flat_items) == 0:
        return None
    return base.build_file_tree(flat_items)


@read_session
def get_folder_modified_times(
    media_id: int,
    *,
    _session: Session = None,  # type: ignore
) -> dict[str, datetime]:
    """Return {path: modified} for all FOLDER entries for a media item.
    Args:
        media_id (int): The media ID to look up.
        _session (Session, optional=None): A session to use for the \
            database connection. A new session is created if not provided.
    Returns:
        dict[str, datetime]: Mapping of folder path to its stored modified time.
    """
    statement = select(FileFolderInfo.path, FileFolderInfo.modified).where(
        FileFolderInfo.media_id == media_id,
        FileFolderInfo.type == FileFolderType.FOLDER,
    )
    results = _session.exec(statement).all()
    return {path: modified for path, modified in results}


# NOTE: Read all function has been intentionally omitted to avoid \
# loading large data sets into memory.
# Use read_by_media_id or read_all_raw instead.


@read_session
def read_all_raw(
    *,
    _session: Session = None,  # type: ignore
) -> list[dict]:
    """Get all FileFolderInfo items from the database.
    Args:
        _session (Session, optional=None): A session to use for the \
            database connection. A new session is created if not provided.
    Returns:
        list[FileFolderInfo]: List of all FileFolderInfo items.
    """
    query = text("SELECT * FROM filefolderinfo")
    result = _session.execute(query)
    rows = []
    for row in result.mappings():
        item = dict(row)
        rows.append(item)
    return rows
