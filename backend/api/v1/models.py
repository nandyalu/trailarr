from pydantic import BaseModel

# THESE MODELS ARE ONLY FOR API RESPONSES


class ErrorResponse(BaseModel):
    message: str


class Log(BaseModel):
    datetime: str
    level: str
    filename: str
    lineno: int
    module: str
    message: str
    raw_log: str


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
    app_data_dir: str
    exclude_words: str
    version: str
    server_start_time: str
    timezone: str
    log_level: str
    monitor_enabled: bool
    monitor_interval: int
    trailer_folder_movie: bool
    trailer_folder_series: bool
    trailer_resolution: int
    trailer_file_name: str
    trailer_file_format: str
    trailer_always_search: bool
    trailer_search_query: str
    trailer_audio_format: str
    trailer_audio_volume_level: int
    trailer_video_format: str
    trailer_subtitles_enabled: bool
    trailer_subtitles_format: str
    trailer_subtitles_language: str
    trailer_embed_metadata: bool
    trailer_min_duration: int
    trailer_max_duration: int
    trailer_remove_sponsorblocks: bool
    trailer_web_optimized: bool
    update_available: bool
    wait_for_media: bool
    yt_cookies_path: str


class UpdateSetting(BaseModel):
    key: str
    value: int | str | bool


class UpdatePassword(BaseModel):
    current_password: str
    new_password: str
