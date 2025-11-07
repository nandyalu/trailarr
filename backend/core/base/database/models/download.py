from __future__ import annotations
from datetime import datetime, timezone
from typing import Any

from sqlmodel import Field

from core.base.database.models.base import AppSQLModel


def get_current_time():
    return datetime.now(timezone.utc)


class DownloadBase(AppSQLModel):
    """
    Base model for Download.\n
    Note: \n
        🚨DO NOT USE THIS CLASS DIRECTLY.🚨 \n
    👉Use :class:`Download` for working with database.👈 \n
    👉Use :class:`DownloadCreate` to create/update downloads.👈 \n
    👉Use :class:`DownloadRead` to read the data.👈
    """

    path: str
    file_name: str
    size: int
    updated_at: datetime
    resolution: str
    video_format: str
    audio_format: str
    audio_channels: str
    file_format: str
    duration: int = 0
    subtitles: str = "unk"
    added_at: datetime = Field(default_factory=get_current_time)
    profile_id: int
    youtube_id: str
    file_exists: bool = True


class Download(DownloadBase, table=True):
    """
    Database model for Download.\n
    Note: \n
        🚨DO NOT USE THIS CLASS OUTSIDE OF DATABASE MANAGER.🚨 \n
    👉Use :class:`DownloadCreate` to create/update downloads.👈 \n
    👉Use :class:`DownloadRead` to read the data.👈
    """

    id: int | None = Field(default=None, primary_key=True)

    media_id: int | None = Field(
        default=None, foreign_key="media.id", ondelete="CASCADE"
    )

    @classmethod
    def model_validate(
        cls,
        obj: "Download | DownloadCreate | DownloadRead | dict[str, Any]",
        *,
        strict: bool | None = None,
        from_attributes: bool | None = None,
        context: dict[str, Any] | None = None,
        update: dict[str, Any] | None = None,
    ) -> "Download":
        """
        Validate the Download model. \n
        This method ensures that the nested models are validated
        correctly before validating the Download itself.
        """
        if isinstance(obj, cls):
            # If obj is already a Download instance, return it
            return obj
        return super().model_validate(
            obj,
            strict=strict,
            from_attributes=from_attributes,
            context=context,
            update=update,
        )


class DownloadCreate(DownloadBase):
    """
    Model for creating/updating Download.
    """

    id: int | None = None
    media_id: int | None = None


class DownloadRead(DownloadBase):
    """
    Model for reading Download.
    """

    id: int
    media_id: int
