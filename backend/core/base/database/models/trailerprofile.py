from pydantic import field_validator, model_validator
from sqlmodel import Field, Relationship, SQLModel

# if TYPE_CHECKING:
from core.base.database.models.customfilter import (
    CustomFilter,
    CustomFilterCreate,
    CustomFilterRead,
)

VALID_AUDIO_FORMATS = ["aac", "ac3", "eac3", "flac", "opus", "copy"]
VALID_FILE_FORMATS = ["mkv", "mp4", "webm"]
VALID_VIDEO_FORMATS = ["h264", "hevc", "vp8", "vp9", "av1", "copy"]
VALID_VIDEO_RESOLUTIONS = [240, 360, 480, 720, 1080, 1440, 2160]
VALID_SUBTITLES_FORMATS = ["srt", "vtt"]

VALID_YT_DICT = {
    "clean_title": "clean_title",
    "imdb_id": "imdb_id",
    "is_movie": "is_movie",
    "language": "language",
    "media_filename": "media_filename",
    "studio": "studio",
    "title": "title",
    "title_slug": "title_slug",
    "txdb_id": "txdb_id",
    "year": "year",
}

VALID_FILE_DICT = {
    "clean_title": "clean_title",
    "imdb_id": "imdb_id",
    "is_movie": "is_movie",
    "language": "language",
    "media_filename": "media_filename",
    "studio": "studio",
    "title": "title",
    "title_slug": "title_slug",
    "txdb_id": "txdb_id",
    "year": "year",
    "acodec": "audio_format",
    "resolution": "video_resolution",
    "vcodec": "video_format",
    "youtube_id": "youtube_id",
}


class _TrailerProfileBase(SQLModel):
    """
    Base model for TrailerProfile.\n
    Note: \n
        🚨DO NOT USE THIS CLASS DIRECTLY.🚨 \n
    👉Use :class:`TrailerProfile` for working with database.👈 \n
    👉Use :class:`TrailerProfileCreate` to create/update trailer profiles.👈 \n
    👉Use :class:`TrailerProfileRead` to read the data.👈
    """

    enabled: bool = True
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
    always_search: bool = False
    embed_metadata: bool = True
    exclude_words: str = ""
    include_words: str = ""
    min_duration: int = 60
    max_duration: int = 600
    remove_silence: bool = False
    search_query: str = "{title} {year} {is_movie} trailer"
    # Filter id to apply to select this profile


class TrailerProfile(_TrailerProfileBase, table=True):
    """
    Database model for TrailerProfile.\n
    Note: \n
        🚨DO NOT USE THIS CLASS OUTSIDE OF DATABASE MANAGER.🚨 \n
    👉Use :class:`TrailerProfileCreate` to create/update trailer profiles.👈 \n
    👉Use :class:`TrailerProfileRead` to read the data.👈
    """

    id: int | None = Field(default=None, primary_key=True)
    customfilter_id: int | None = Field(
        default=None, foreign_key="customfilter.id"
    )
    customfilter: CustomFilter = Relationship(
        # back_populates="trailerprofile"
    )

    @field_validator("file_format", mode="after")
    @classmethod
    def validate_file_format(cls, v: str) -> str:
        if v in VALID_FILE_FORMATS:
            return v
        raise ValueError(
            f"Invalid file format: {v}. Valid formats are:"
            f" {VALID_FILE_FORMATS}"
        )

    @field_validator("file_name", mode="after")
    @classmethod
    def validate_file_name(cls, v: str) -> str:
        try:
            v.format(**VALID_FILE_DICT)
        except Exception as e:
            raise ValueError(f"Invalid file name template: '{v}'. {e}")
        return v

    @field_validator("folder_name", mode="after")
    @classmethod
    def validate_folder_name(cls, v: str) -> str:
        if bool(v.strip()):
            return v
        raise ValueError("Folder Name cannot be empty!")

    @field_validator("audio_format", mode="after")
    @classmethod
    def validate_audio_format(cls, v: str) -> str:
        if v in VALID_AUDIO_FORMATS:
            return v
        raise ValueError(
            f"Invalid audio format: {v}. Valid formats are:"
            f" {VALID_AUDIO_FORMATS}"
        )

    @field_validator("audio_volume_level", mode="after")
    @classmethod
    def validate_audio_volume_level(cls, v: int) -> int:
        if 1 <= v <= 200:
            return v
        raise ValueError(
            f"Invalid audio volume level: {v}. Valid range is: 1-200"
        )

    @field_validator("video_resolution", mode="after")
    @classmethod
    def validate_video_resolution(cls, v: int) -> int:
        if v in VALID_VIDEO_RESOLUTIONS:
            return v
        raise ValueError(
            f"Invalid video resolution: {v}. Valid resolutions are:"
            f" {VALID_VIDEO_RESOLUTIONS}"
        )

    @field_validator("video_format", mode="after")
    @classmethod
    def validate_video_format(cls, v: str) -> str:
        if v in VALID_VIDEO_FORMATS:
            return v
        raise ValueError(
            f"Invalid video format: {v}. Valid formats are:"
            f" {VALID_VIDEO_FORMATS}"
        )

    @field_validator("subtitles_format", mode="after")
    @classmethod
    def validate_subtitles_format(cls, v: str) -> str:
        if v in VALID_SUBTITLES_FORMATS:
            return v
        raise ValueError(
            f"Invalid subtitles format: {v}. Valid formats are:"
            f" {VALID_SUBTITLES_FORMATS}"
        )

    @field_validator("search_query", mode="after")
    @classmethod
    def validate_search_query(cls, v: str) -> str:
        try:
            v.format(**VALID_YT_DICT)
        except Exception as e:
            raise ValueError(f"Invalid search query template: '{v}'. {e}")
        return v

    @model_validator(mode="after")
    def validate_trailer_profile(self) -> "TrailerProfile":
        match (self.file_format):
            case "mp4":
                if self.video_format in ["vp8", "vp9"]:
                    raise ValueError(
                        "MP4 container does not support VP8/VP9 video codecs."
                    )
            case "webm":
                if self.video_format in ["h264", "h265", "hevc"]:
                    raise ValueError(
                        "WebM container does not support H264/H265 video"
                        " codecs."
                    )
                if self.audio_format == "opus":
                    raise ValueError(
                        "WebM container ONLY supports 'OPUS' audio codec."
                    )
        if self.min_duration < 30:
            raise ValueError(
                f"Invalid min_duration: {self.min_duration}. "
                "Valid range is 30 to 600 seconds."
            )
        if 90 > self.max_duration > 600:
            raise ValueError(
                f"Invalid max_duration: {self.max_duration}. "
                "Valid range is 90 to 600 seconds."
            )
        if self.max_duration - self.min_duration < 60:
            raise ValueError(
                "Duration difference should be at least 60 seconds. Provided:"
                f" {self.min_duration} seconds (min),"
                f" {self.max_duration} seconds (max)."
            )
        return self


class TrailerProfileCreate(_TrailerProfileBase):
    """
    Model for creating/updating TrailerProfile.
    """

    id: int | None = None
    customfilter_id: int | None = None
    customfilter: CustomFilterCreate


class TrailerProfileRead(_TrailerProfileBase):
    """
    Model for reading TrailerProfile.
    """

    id: int
    customfilter_id: int
    customfilter: CustomFilterRead
