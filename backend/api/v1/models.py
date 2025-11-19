from pydantic import BaseModel

# THESE MODELS ARE ONLY FOR API RESPONSES


class BatchUpdate(BaseModel):
    media_ids: list[int]
    action: str
    profile_id: int | None = None


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
    app_mode: str
    app_theme: str
    gpu_available_amd: bool
    gpu_available_intel: bool
    gpu_available_nvidia: bool
    gpu_enabled_amd: bool
    gpu_enabled_intel: bool
    gpu_enabled_nvidia: bool
    log_level: str
    monitor_enabled: bool
    monitor_interval: int
    server_start_time: str
    timezone: str
    update_available: bool
    update_available_ytdlp: bool
    update_ytdlp: bool
    url_base: str
    version: str
    wait_for_media: bool
    webui_username: str
    yt_cookies_path: str
    ytdlp_version: str


class UpdateSetting(BaseModel):
    key: str
    value: int | str | bool


class UpdateLogin(BaseModel):
    current_password: str
    new_username: str | None
    new_password: str | None
