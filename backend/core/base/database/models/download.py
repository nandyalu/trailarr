from datetime import datetime
from sqlmodel import Field, Relationship
from core.base.database.models.base import AppSQLModel
from core.base.database.models.media import Media


class Download(AppSQLModel, table=True):
    """Download model for the database."""

    id: int | None = Field(default=None, primary_key=True)
    path: str
    file_name: str
    size: int
    updated_at: datetime
    resolution: str
    video_format: str
    audio_format: str
    audio_channels: str
    file_format: str
    duration: int = Field(default=0)
    subtitles: str = Field(default="unk")
    added_at: datetime = Field(default_factory=datetime.utcnow)
    profile_id: int
    media_id: int = Field(foreign_key="media.id", ondelete="CASCADE")
    youtube_id: str
    file_exists: bool = Field(default=True)

    media: "Media" = Relationship(back_populates="downloads")
