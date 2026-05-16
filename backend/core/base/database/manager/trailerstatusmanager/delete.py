from sqlmodel import Session, col, select

from core.base.database.models.mediatrailerstatus import MediaTrailerStatus
from core.base.database.utils.engine import write_session


@write_session
def delete_undownloaded_rows_for_profile(
    profile_id: int,
    media_ids: list[int],
    *,
    _session: Session = None,  # type: ignore
) -> int:
    """Delete rows for *profile_id* / *media_ids* where no file was ever downloaded.

    Rows with a linked_download_id (file exists) are left untouched.
    Returns the number of rows deleted.
    """
    rows = _session.exec(
        select(MediaTrailerStatus).where(
            MediaTrailerStatus.profile_id == profile_id,
            col(MediaTrailerStatus.media_id).in_(media_ids),
            MediaTrailerStatus.linked_download_id == None,  # noqa: E711
        )
    ).all()
    count = len(rows)
    for row in rows:
        _session.delete(row)
    _session.commit()
    return count
