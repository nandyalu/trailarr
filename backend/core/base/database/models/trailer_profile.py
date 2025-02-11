from sqlmodel import Field, SQLModel


class _TrailerProfileBase(SQLModel):
    """
    Base model for TrailerProfile.\n
    Note: \n
        🚨DO NOT USE THIS CLASS DIRECTLY.🚨 \n
    👉Use :class:`TrailerProfile` for working with database.👈 \n
    👉Use :class:`TrailerProfileCreate` to create/update trailer profiles.👈 \n
    👉Use :class:`TrailerProfileRead` to read the data.👈
    """

    # File settings
    file_format: str = "mkv"
    file_name: str = "{title} ({year})-trailer.{ext}"
    folder_enabled: bool = False
    folder_name: str = "Trailers"
    # Audio settings
    audio_format: str = "aac"
    audio_volume_level: int = 100
    # Video settings
    video_resolution: int = 1080
    video_format: str = "h264"
    # Subtitle settings
    subtitles_enabled: bool = True
    subtitles_format: str = "srt"
    subtitles_language: str = "en"
    # General settings
    embed_metadata: bool = True
    exclude_words: str = ""
    include_words: str = ""
    min_duration: int = 60
    max_duration: int = 600
    remove_silence: bool = False
    search_query: str = "{title} {year} {is_movie} trailer"
    # Filter id to apply to select this profile
    viewfilter_id: int


class TrailerProfile(_TrailerProfileBase, table=True):
    """
    Database model for TrailerProfile.\n
    Note: \n
        🚨DO NOT USE THIS CLASS OUTSIDE OF DATABASE MANAGER.🚨 \n
    👉Use :class:`TrailerProfileCreate` to create/update trailer profiles.👈 \n
    👉Use :class:`TrailerProfileRead` to read the data.👈
    """

    id: int | None = Field(default=None, primary_key=True)


class TrailerProfileCreate(_TrailerProfileBase):
    """
    Model for creating/updating TrailerProfile.
    """

    id: int | None = None


class TrailerProfileRead(_TrailerProfileBase):
    """
    Model for reading TrailerProfile.
    """

    id: int
