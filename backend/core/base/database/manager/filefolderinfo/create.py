from sqlmodel import Session

from . import base
from . import read
from core.base.database.models.filefolderinfo import (
    FileFolderInfo,
    FileFolderInfoCreate,
    FileFolderInfoRead,
)
from core.base.database.models.media import MediaRead
from core.base.database.utils.engine import manage_session


def _create_new_node(
    session: Session,
    media_id: int,
    incoming: FileFolderInfoCreate,
    parent_id: int,
) -> FileFolderInfo:
    """Handles the creation of a new database record and its children."""
    db_item = FileFolderInfo(**incoming.model_dump(exclude={"children"}))
    db_item.media_id = media_id
    db_item.parent_id = parent_id
    session.add(db_item)
    session.flush()  # Generate ID for child recursion
    return db_item


def _update_existing_node(
    session: Session,
    existing_id: int,
    incoming: FileFolderInfoCreate,
    parent_id: int,
) -> FileFolderInfo | None:
    """Updates an existing database record metadata."""
    db_item = session.get(FileFolderInfo, existing_id)

    if db_item is None:
        # Safety check: Item might have been deleted by another process
        return None

    _update_data = incoming.model_dump(exclude_unset=True)
    db_item.sqlmodel_update(_update_data)
    db_item.parent_id = parent_id

    session.add(db_item)
    session.flush()  # Generate ID for child recursion
    return db_item


def sync_file_tree(
    session: Session,
    media_id: int,
    existing_list: list[FileFolderInfoRead],
    incoming_list: list[FileFolderInfoCreate],
    parent_id: int,
) -> list[FileFolderInfoRead]:
    """
    Recursive coordinator that synchronizes a level of the tree.
    Args:
        session (Session): SQLModel Session
        media_id (int): ID of the media item
        existing_list (list[FileFolderInfoRead]): Existing items at this \
            tree level
        incoming_list (list[FileFolderInfoCreate]): Incoming items to sync
        parent_id (int): Parent ID for the current tree level.
    Returns:
        list[FileFolderInfoRead]: Updated list of FileFolderInfoRead items \
            at this tree level.
    """
    existing_map = {item.path: item for item in existing_list}
    incoming_map = {item.path: item for item in incoming_list}
    updated_tree: list[FileFolderInfoRead] = []

    # 1. Delete items no longer present
    for path, existing_read in existing_map.items():
        if path not in incoming_map:
            db_item = session.get(FileFolderInfo, existing_read.id)
            if db_item:
                session.delete(db_item)

    # 2. Process Incoming items (Update or Create)
    for path, incoming_item in incoming_map.items():
        db_item = None
        current_children: list[FileFolderInfoRead] = []
        if path in existing_map:
            # UPDATE if exists
            existing_read = existing_map[path]
            db_item = _update_existing_node(
                session, existing_read.id, incoming_item, parent_id
            )
            current_children = existing_read.children

        # CREATE if new, or if update failed
        if db_item is None:
            db_item = _create_new_node(
                session, media_id, incoming_item, parent_id
            )
            current_children = []
        read_item = base.convert_to_read_item(db_item)

        # Recurse for children
        child_reads = sync_file_tree(
            session,
            media_id,
            current_children,
            incoming_item.children,
            parent_id=read_item.id,
        )

        # Build the Read model for the return value
        read_item.children = child_reads
        updated_tree.append(read_item)

    updated_tree.sort()
    return updated_tree


@manage_session
def update(
    media: MediaRead,
    incoming_root: FileFolderInfoCreate,
    *,
    _session: Session = None,  # type: ignore
) -> FileFolderInfoRead:
    """Create or update a FileFolderInfo in the database for a given media.
    Takes care of the full tree structure of folders and files.
    Args:
        media (MediaRead): The media item to associate the FileFolderInfo with.
        incoming_root (FileFolderInfoCreate): The data for the FileFolderInfo.
        _session (Session, optional=None): A session to use for the database \
            connection. A new session is created if not provided.
    Returns:
        FileFolderInfoRead: The created or updated FileFolderInfo (read).
    """
    # Get existing children
    existing_root = read.read_by_media_id(media.id, _session=_session)
    existing_children = existing_root.children if existing_root else []

    # Handle the root node itself
    # If it exists in DB, update it; otherwise create it
    root_db = None
    if existing_root:
        root_db = _session.get(FileFolderInfo, existing_root.id)

    if root_db is None:
        # root_db = FileFolderInfo.model_validate(incoming_root)
        root_db = FileFolderInfo(
            **incoming_root.model_dump(exclude={"children"})
        )
    _update_data = incoming_root.model_dump(
        exclude_unset=True, exclude={"children"}
    )
    root_db.sqlmodel_update(_update_data)
    root_db.media_id = media.id
    root_db.parent_id = None

    _session.add(root_db)
    _session.flush()  # Generate ID for child recursion
    read_item = base.convert_to_read_item(root_db)

    # Perform the tree sync
    new_children = sync_file_tree(
        _session,
        media.id,
        existing_children,
        incoming_root.children,
        read_item.id,
    )
    # Commit all changes
    _session.commit()

    # Return the complete Read model
    read_item.children = new_children
    return read_item


create = update
