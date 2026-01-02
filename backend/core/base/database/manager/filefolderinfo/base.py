from typing import Sequence

from sqlmodel import Session
from exceptions import ItemNotFoundError
from core.base.database.models.filefolderinfo import (
    FileFolderInfo,
    FileFolderInfoRead,
)


def convert_to_read_item(
    db_item: FileFolderInfo,
) -> FileFolderInfoRead:
    """Convert a FileFolderInfo database object to a FileFolderInfoRead object.
    Args:
        db_item (FileFolderInfo): The database object.
    Returns:
        FileFolderInfoRead: The read object.
    """
    read_item = FileFolderInfoRead.model_validate(db_item)
    return read_item


def convert_to_read_list(
    db_item_list: Sequence[FileFolderInfo],
) -> list[FileFolderInfoRead]:
    """Convert a list of FileFolderInfo database objects to a list of \
        FileFolderInfoRead objects.
    Args:
        db_item_list (Sequence[FileFolderInfo]): List of database objects.
    Returns:
        list[FileFolderInfoRead]: List of read objects.
    """
    if not db_item_list or len(db_item_list) == 0:
        return []
    read_list: list[FileFolderInfoRead] = []
    for db_item in db_item_list:
        read_item = FileFolderInfoRead.model_validate(db_item)
        read_list.append(read_item)
    return read_list


def get_db_item(id: int, session: Session) -> FileFolderInfo:
    """Get a FileFolderInfo database object by ID.
    Args:
        id (int): ID of the FileFolderInfo to get.
        session (Session): SQLModel Session.
    Returns:
        FileFolderInfo: The database object.
    Raises:
        ItemNotFoundError: If the FileFolderInfo with the given ID is not found.
    """
    db_item = session.get(FileFolderInfo, id)
    if db_item is None:
        raise ItemNotFoundError(model_name="FileFolderInfo", id=id)
    return db_item


def build_file_tree(
    flat_items: Sequence[FileFolderInfo],
) -> FileFolderInfoRead | None:
    """
    Converts a flat list of FileFolderInfo items into a single nested tree.
    Args:
        flat_items (Sequence[FileFolderInfo]): Flat sequence of file/folder \
            info items
    Returns:
        FileFolderInfoRead | None: the root node, or None if the list is empty.
    """
    if not flat_items:
        return None
    # Convert to Read items
    _flat_items = convert_to_read_list(flat_items)
    # 1. Create a mapping of ID -> Item and initialize empty children lists
    # We create copies to avoid mutating the original objects in the list
    item_map: dict[int, FileFolderInfoRead] = {}
    for item in _flat_items:
        # Ensure children is an empty list so we can append to it
        item.children = []
        item_map[item.id] = item

    root_node: FileFolderInfoRead | None = None

    # 2. Distribute items to their parents
    for item in _flat_items:
        if item.parent_id is None:
            # This is our root node (the Media folder)
            root_node = item
        else:
            # Find the parent in the map and attach this item as a child
            parent = item_map.get(item.parent_id)
            if parent:
                parent.children.append(item)
                # Keep the children sorted (folders first, then name)
                parent.children.sort()

    return root_node
