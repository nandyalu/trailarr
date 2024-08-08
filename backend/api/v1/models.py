from pydantic import BaseModel

# THESE MODELS ARE ONLY FOR API RESPONSES


class ErrorResponse(BaseModel):
    message: str


class SearchMedia(BaseModel):
    id: int
    title: str
    year: int
    youtube_trailer_id: str
    imdb_id: str
    txdb_id: str
    is_movie: bool
    poster_path: str | None


class Settings(BaseModel):
    api_key: str
    version: str
    server_start_time: str
    timezone: str
    debug: bool
    monitor_enabled: bool
    monitor_interval: int
    trailer_folder_movie: bool
    trailer_folder_series: bool
    trailer_resolution: int
    trailer_file_format: str
    trailer_audio_format: str
    trailer_video_format: str
    trailer_subtitles_enabled: bool
    trailer_subtitles_format: str
    trailer_subtitles_language: str
    trailer_embed_metadata: bool
    trailer_remove_sponsorblocks: bool
    trailer_web_optimized: bool
    wait_for_media: bool


class UpdateSetting(BaseModel):
    key: str
    value: int | str | bool
