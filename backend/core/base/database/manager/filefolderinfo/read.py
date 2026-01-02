from . import base
from sqlmodel import select, Session, text
from core.base.database.models.filefolderinfo import (
    FileFolderInfo,
    FileFolderInfoRead,
)
from core.base.database.utils.engine import manage_session


@manage_session
def read_by_media_id(
    media_id: int,
    *,
    _session: Session = None,  # type: ignore
) -> FileFolderInfoRead | None:
    """
    Get FileFolderInfoRead tree for a specific media ID.
    Args:
        media_id (int): The media ID to filter downloads by.
        _session (Session, optional=None): A session to use for the \
            database connection. A new session is created if not provided.
    Returns:
        FileFolderInfoRead | None: The file/folder info tree (read-only) \
            or None.
    """
    statement = select(FileFolderInfo).where(
        FileFolderInfo.media_id == media_id
    )
    db_filefolderinfo = _session.exec(statement).all()
    return base.build_file_tree(db_filefolderinfo)


# NOTE: Read all function has been intentionally omitted to avoid \
# loading large data sets into memory.
# Use read_by_media_id or read_all_raw instead.


@manage_session
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
