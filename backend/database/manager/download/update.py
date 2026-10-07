"""Change a trailer download that is already stored."""

from sqlmodel import Session, col, select

from . import base
from database.models.download import (
    Download,
    DownloadCreate,
    DownloadRead,
)
from database.engine import write_session


@write_session
def update(
    download_id: int,
    download_create: DownloadCreate,
    *,
    _session: Session = None,  # type: ignore
) -> DownloadRead:
    """
    Update a download in the database.
    Args:
        download_id (int): The ID of the download to update.
        download_create (DownloadCreate): The new data for the download.
        _session (Session, optional): A session to use for the database connection. Defaults to None.
    Returns:
        DownloadRead: The updated download.
    Raises:
        ItemNotFoundError: If the download with the given ID is not found.
        ValueError: If the download is invalid.
    """
    # Get the existing download from the database
    download_db = base._get_db_item(download_id, _session)

    # Update the fields of the existing download
    _update_data = download_create.model_dump(exclude_unset=True)
    download_db.sqlmodel_update(_update_data)

    # Validate the updated download
    Download.model_validate(download_db)

    # Commit the changes to the database
    # _session.add(download_db)
    _session.commit()
    _session.refresh(download_db)
    return base.convert_to_read_item(download_db)


@write_session
def mark_as_deleted(
    download_id: int,
    *,
    _session: Session = None,  # type: ignore
) -> None:
    """
    Mark a download as deleted in the database.
    Args:
        download_id (int): The ID of the download to mark as deleted.
        _session (Session, optional): A session to use for the database connection. Defaults to None.
    Raises:
        ItemNotFoundError: If the download with the given ID is not found.
    """
    # Get the existing download from the database
    download_db = base._get_db_item(download_id, _session)

    # Mark the download as deleted
    download_db.file_exists = False

    # Commit the changes to the database
    _session.add(download_db)
    _session.commit()


@write_session
def update_profile_id(
    download_id: int,
    profile_id: int,
    *,
    video_type: str | None = None,
    _session: Session = None,  # type: ignore
) -> None:
    """
    Set the owning trailer profile for a download.
    Used to attribute downloads recorded without a profile (profile_id=0)
    to the profile that should own them.
    Args:
        download_id (int): The ID of the download to update.
        profile_id (int): The ID of the TrailerProfile to attribute it to.
        video_type (str | None): The type the download takes with the
            profile. A person who assigns a file to a profile says what
            the file is, so the row records the type of the profile.
            None keeps the type of the row.
        _session (Session, optional): A session to use for the database connection. Defaults to None.
    Raises:
        ItemNotFoundError: If the download with the given ID is not found.
    """
    download_db = base._get_db_item(download_id, _session)
    download_db.profile_id = profile_id
    if video_type is not None:
        download_db.video_type = video_type
    _session.add(download_db)
    _session.commit()


@write_session
def relabel_video_type_for_profile(
    profile_id: int,
    video_type: str,
    *,
    _session: Session = None,  # type: ignore
) -> int:
    """
    Give every download of one profile a new video type.
    The downloads of a profile are what the profile asked for, so when
    the profile changes its type, its downloads change with it. This is
    what keeps a profile satisfied after the change: the satisfaction
    rule matches a download to its profile by type.
    Args:
        profile_id (int): The profile whose downloads change.
        video_type (str): The new type, in its stored form.
        _session (Session, optional): A session to use for the database connection. Defaults to None.
    Returns:
        int: How many downloads changed.
    """
    statement = (
        select(Download)
        .where(Download.profile_id == profile_id)
        .where(col(Download.video_type) != video_type)
    )
    rows = _session.exec(statement).all()
    for row in rows:
        row.video_type = video_type
        _session.add(row)
    _session.commit()
    return len(rows)
