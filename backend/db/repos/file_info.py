from datetime import datetime
from typing import Sequence

from sqlmodel import Session, select, text

from db.engine import read_session, write_session
from db.models.filefolderinfo import FileFolderInfo, FileFolderInfoCreate, FileFolderInfoRead, FileFolderType
from db.models.media import MediaRead


def _to_read(db: FileFolderInfo) -> FileFolderInfoRead:
    return FileFolderInfoRead.model_validate(db)


def _to_read_list(items: Sequence[FileFolderInfo]) -> list[FileFolderInfoRead]:
    return [_to_read(item) for item in items]


def build_file_tree(flat_items: Sequence[FileFolderInfoRead]) -> FileFolderInfoRead | None:
    """Convert a flat list of FileFolderInfoRead items into a nested tree."""
    if not flat_items:
        return None
    item_map: dict[int, FileFolderInfoRead] = {}
    for item in flat_items:
        item.children = []
        item_map[item.id] = item

    root_node: FileFolderInfoRead | None = None
    for item in flat_items:
        if item.parent_id is None:
            root_node = item
        else:
            parent = item_map.get(item.parent_id)
            if parent:
                parent.children.append(item)
                parent.children.sort()
    return root_node


def _create_new_node(
    session: Session,
    media_id: int,
    incoming: FileFolderInfoCreate,
    parent_id: int,
) -> FileFolderInfo:
    db_item = FileFolderInfo(**incoming.model_dump(exclude={"children"}))
    db_item.media_id = media_id
    db_item.parent_id = parent_id
    session.add(db_item)
    session.flush()
    return db_item


def _update_existing_node(
    session: Session,
    existing_id: int,
    incoming: FileFolderInfoCreate,
    parent_id: int,
) -> FileFolderInfo | None:
    db_item = session.get(FileFolderInfo, existing_id)
    if db_item is None:
        return None
    db_item.sqlmodel_update(incoming.model_dump(exclude_unset=True, exclude_defaults=True))
    db_item.parent_id = parent_id
    session.add(db_item)
    session.flush()
    return db_item


def sync_file_tree(
    session: Session,
    media_id: int,
    existing_list: list[FileFolderInfoRead],
    incoming_list: list[FileFolderInfoCreate],
    parent_id: int,
) -> list[FileFolderInfoRead]:
    """Recursively synchronize one level of the tree. Returns updated children."""
    existing_map = {item.path: item for item in existing_list}
    incoming_map = {item.path: item for item in incoming_list}
    updated_tree: list[FileFolderInfoRead] = []

    for path, existing_read in existing_map.items():
        if path not in incoming_map:
            db_item = session.get(FileFolderInfo, existing_read.id)
            if db_item:
                session.delete(db_item)

    for path, incoming_item in incoming_map.items():
        db_item = None
        current_children: list[FileFolderInfoRead] = []
        if path in existing_map:
            existing_read = existing_map[path]
            db_item = _update_existing_node(session, existing_read.id, incoming_item, parent_id)
            current_children = existing_read.children
        if db_item is None:
            db_item = _create_new_node(session, media_id, incoming_item, parent_id)
            current_children = []
        read_item = _to_read(db_item)
        child_reads = sync_file_tree(
            session, media_id, current_children, incoming_item.children, parent_id=read_item.id
        )
        read_item.children = child_reads
        updated_tree.append(read_item)

    updated_tree.sort()
    return updated_tree


@read_session
def read_flat(media_id: int, *, _session: Session = None) -> list[FileFolderInfoRead]:  # type: ignore
    items = _session.exec(
        select(FileFolderInfo).where(FileFolderInfo.media_id == media_id)
    ).all()
    return _to_read_list(items)


@read_session
def read_by_media_id(media_id: int, *, _session: Session = None) -> FileFolderInfoRead | None:  # type: ignore
    flat = read_flat(media_id, _session=_session)
    if not flat:
        return None
    return build_file_tree(flat)


@read_session
def get_folder_modified_times(media_id: int, *, _session: Session = None) -> dict[str, datetime]:  # type: ignore
    results = _session.exec(
        select(FileFolderInfo.path, FileFolderInfo.modified).where(
            FileFolderInfo.media_id == media_id,
            FileFolderInfo.type == FileFolderType.FOLDER,
        )
    ).all()
    return {path: modified for path, modified in results}


@read_session
def read_all_raw(*, _session: Session = None) -> list[dict]:  # type: ignore
    return [dict(r) for r in _session.execute(text("SELECT * FROM filefolderinfo")).mappings()]


@write_session
def upsert(media: MediaRead, incoming_root: FileFolderInfoCreate, *, _session: Session = None) -> FileFolderInfoRead:  # type: ignore
    """Create or update the full file tree for a media item."""
    existing_root = read_by_media_id(media.id, _session=_session)
    existing_children = existing_root.children if existing_root else []

    root_db = None
    if existing_root:
        root_db = _session.get(FileFolderInfo, existing_root.id)

    if root_db is None:
        root_db = FileFolderInfo(**incoming_root.model_dump(exclude={"children"}))
    root_db.sqlmodel_update(incoming_root.model_dump(exclude_unset=True, exclude={"children"}))
    root_db.media_id = media.id
    root_db.parent_id = None

    _session.add(root_db)
    _session.flush()
    read_item = _to_read(root_db)

    new_children = sync_file_tree(
        _session, media.id, existing_children, incoming_root.children, read_item.id
    )
    _session.commit()
    read_item.children = new_children
    return read_item
