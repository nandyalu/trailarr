from sqlmodel import Session

from core.base.database.models.customfilter import CustomFilter
from core.base.database.models.mediatrailerstatus import (
    MediaTrailerStatus,
    MediaTrailerStatusRead,
)
from core.base.database.models.trailerprofile import TrailerProfile
from exceptions import ItemNotFoundError


def _get_db_item(row_id: int, session: Session) -> MediaTrailerStatus:
    """Get a MediaTrailerStatus row by id, raising ItemNotFoundError if missing."""
    row = session.get(MediaTrailerStatus, row_id)
    if row is None:
        raise ItemNotFoundError(model_name="MediaTrailerStatus", id=row_id)
    return row


def _to_read(row: MediaTrailerStatus, session: Session) -> MediaTrailerStatusRead:
    """Convert a MediaTrailerStatus row to a Read model with joined profile fields."""
    read = MediaTrailerStatusRead.model_validate(row)
    if row.profile_id is not None:
        profile = session.get(TrailerProfile, row.profile_id)
        if profile is not None:
            read.video_type = profile.video_type
            cf = session.get(CustomFilter, profile.customfilter_id)
            if cf is not None:
                read.profile_name = cf.filter_name
    return read
