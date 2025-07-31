from datetime import datetime, timezone
import os
import secrets

from dotenv import load_dotenv, set_key

from config import app_logger_opts

APP_DATA_DIR = os.path.abspath(os.getenv("APP_DATA_DIR", "/config"))
ENV_PATH = f"{APP_DATA_DIR}/.env"
RESOLUTION_DICT = {
    "SD": 360,
    "FSD": 480,
    "HD": 720,
    "FHD": 1080,
    "QHD": 1440,
    "UHD": 2160,
}

if os.getcwd().startswith("/app/backend"):
    APP_MODE = "Docker"
else:
    APP_MODE = "Standalone"


def _save_to_env(key: str, value: str | int | bool) -> None:
    """Save the given key-value pair to the environment variables. \n
    Args:
        key (str): Key to save.
        value (str, int, bool): Value to save. \n
    Returns:
        None"""
    os.environ[key.upper()] = str(value)
    set_key(ENV_PATH, key.upper(), str(value))
    return None


def getenv_bool(key: str, default: bool) -> bool:
    """Get the boolean value from the environment variables. \n
    Args:
        key (str): Key to get the value from.
        default (bool): Default value if the key is not found. \n
    Returns:
        bool: Value of the key from environment variables or default value."""
    return os.getenv(key.upper(), str(default)).lower() in ["true", "1"]


def getenv_int(key: str, default: int) -> int:
    """Get the integer value from the environment variables. \n
    Args:
        key (str): Key to get the value from.
        default (int): Default value if the key is not found. \n
    Returns:
        int: Value of the key from environment variables or default value."""
    return int(os.getenv(key.upper(), str(default)))


def getenv_str(key: str, default: str) -> str:
    """Get the string value from the environment variables. \n
    Args:
        key (str): Key to get the value from.
        default (str): Default value if the key is not found. \n
    Returns:
        str: Value of the key from environment variables or default value."""
    return os.getenv(key.upper(), default)


def bool_property(name: str, *, default: bool) -> property:
    """Create a boolean property with getter and setter methods. \n
    Args:
        name (str): Name of the property.
        default (bool): Default value for the property. \n
    Returns:
        property: Getter and Setter methods for the property."""

    def getter(self) -> bool:
        return getenv_bool(name, default)

    def setter(self, value: bool) -> None:
        _save_to_env(name, value)

    return property(getter, setter)


def int_property(
    name: str,
    *,
    default: int,
    min_: int | None = None,
    max_: int | None = None,
) -> property:
    """Creates an integer property with getter and setter methods. \n
    Args:
        name (str): Name of the property.
        default (int): Default value for the property.
        min (int, Optional=None): Minimum value for the property.
        max (int, Optional=None): Maximum value for the property. \n
    Returns:
        property: Getter and Setter methods for the property."""

    def getter(self) -> int:
        return getenv_int(name, default)

    def setter(self, value: int) -> None:
        # Convert to int if value is a string to handle API input
        if isinstance(value, str):
            try:
                value = int(value)
            except ValueError:
                value = default  # Use default if conversion fails
        if min_ is not None:
            value = max(min_, value)
        if max_ is not None:
            value = min(max_, value)
        # setattr(self, f"_{name.lower()}", value)
        _save_to_env(name, value)

    return property(getter, setter)


def str_property(
    name: str, *, default: str, valid_values: list[str] = []
) -> property:
    """Creates a string property with getter and setter methods. \n
    Args:
        name (str): Name of the property.
        default (str): Default value for the property.
        valid_values (list[str], Optional): list of valid values if applicable.
    Returns:
        property: Getter and Setter methods for the property."""

    def getter(self) -> str:
        return getenv_str(name, default)

    def setter(self, value: str) -> None:
        value = value.strip()
        if valid_values and value.lower() not in valid_values:
            value = default
        # setattr(self, f"_{name.lower()}", value)
        _save_to_env(name, value)

    return property(getter, setter)


def get_ytdlp_version() -> str:
    """Get the version of yt-dlp. \n
    Returns:
        str: Version of yt-dlp."""
    _ver = getenv_str("YTDLP_VERSION", "")
    if _ver:
        return _ver
    # If version is not set, try to get it from yt-dlp --version command
    try:
        from subprocess import check_output

        _ytdlp = "/usr/local/bin/yt-dlp"
        _ver = check_output([_ytdlp, "--version"]).decode("utf-8").strip()
    except Exception:
        _ver = "0.0.0"
    _save_to_env("YTDLP_VERSION", _ver)
    return _ver


class _Config:
    """Class to hold configuration settings for the application. \n
    Reads environment variables to set properties. \n
    Default values are used if environment variables are not provided/invalid.
    \n
    **DO NOT USE THIS CLASS DIRECTLY. USE `app_settings` OBJECT INSTEAD!** \n
    \n
    **Environment variables set in the system will take precedence. \
        Changing class values doesn't have any effect if relevant \
        env variable is set!** \n
    """

    _instance = None

    def __new__(cls) -> "_Config":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    _DEFAULT_AUDIO_FORMAT = "aac"
    _DEFAULT_VIDEO_FORMAT = "h264"
    _DEFAULT_SUBTITLES_FORMAT = "srt"
    _DEFAULT_FILE_FORMAT = "mkv"
    _DEFAULT_RESOLUTION = 1080
    _DEFAULT_LANGUAGE = "en"
    _DEFAULT_DB_URL = f"sqlite:///{APP_DATA_DIR}/trailarr.db"
    _DEFAULT_FILE_NAME = "{title} - Trailer-trailer.{ext}"
    _DEFAULT_SEARCH_QUERY = "{title} {year} {is_movie} trailer"
    # Default WebUI user 'admin'
    _DEFAULT_WEBUI_USERNAME = "admin"
    # Default WebUI password 'trailarr' hashed
    _DEFAULT_WEBUI_PASSWORD = (
        "$2b$12$CU7h.sOkBp5RFRJIYEwXU.1LCUTD2pWE4p5nsW3k1iC9oZEGVWeum"
    )

    _VALID_LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    _VALID_AUDIO_FORMATS = ["aac", "ac3", "eac3", "flac", "opus"]
    _VALID_VIDEO_FORMATS = ["h264", "h265", "vp8", "vp9", "av1"]
    _VALID_SUBTITLES_FORMATS = ["srt", "vtt"]
    _VALID_FILE_FORMATS = ["mp4", "mkv", "webm"]
    _VALID_RESOLUTIONS = [240, 360, 480, 720, 1080, 1440, 2160]

    def __init__(self):
        # Some generic attributes for server
        self.version = getenv_str("APP_VERSION", "0.0.0")
        self.ytdlp_version = get_ytdlp_version()
        self.update_available = False
        _now = datetime.now(timezone.utc)
        self.server_start_time = getenv_str("SERVER_START_TIME", f"{_now}")
        self.timezone = getenv_str("TZ", "UTC")
        self.app_data_dir = APP_DATA_DIR

        # Read properties from ENV variables or set default values \
        # if not present
        self.api_key = getenv_str("API_KEY", "")
        self.log_level = getenv_str("LOG_LEVEL", "INFO")
        # self.monitor_enabled = getenv_bool("MONITOR_ENABLED", True)
        self.monitor_interval = getenv_int("MONITOR_INTERVAL", 60)
        self.wait_for_media = getenv_bool("WAIT_FOR_MEDIA", False)
        self.trailer_folder_movie = getenv_bool("TRAILER_FOLDER_MOVIE", False)
        self.trailer_folder_series = getenv_bool("TRAILER_FOLDER_SERIES", True)
        self.trailer_resolution = getenv_str("TRAILER_RESOLUTION", "1080")
        self.trailer_audio_format = getenv_str(
            "TRAILER_AUDIO_FORMAT", self._DEFAULT_AUDIO_FORMAT
        )
        self.trailer_audio_volume_level = getenv_int(
            "TRAILER_AUDIO_VOLUME_LEVEL", 100
        )
        self.trailer_video_format = getenv_str(
            "TRAILER_VIDEO_FORMAT", self._DEFAULT_VIDEO_FORMAT
        )
        self.trailer_subtitles_enabled = getenv_bool(
            "TRAILER_SUBTITLES_ENABLED", True
        )
        self.trailer_subtitles_format = getenv_str(
            "TRAILER_SUBTITLES_FORMAT", self._DEFAULT_SUBTITLES_FORMAT
        )
        self.trailer_subtitles_language = os.getenv(
            "TRAILER_SUBTITLES_LANGUAGE", self._DEFAULT_LANGUAGE
        )
        self.trailer_file_format = os.getenv(
            "TRAILER_FILE_FORMAT", self._DEFAULT_FILE_FORMAT
        )
        self.trailer_embed_metadata = os.getenv(
            "TRAILER_EMBED_METADATA",
            "True",
        ).lower() in ["true", "1"]
        self.trailer_remove_sponsorblocks = os.getenv(
            "TRAILER_REMOVE_SPONSORBLOCKS",
            "True",
        ).lower() in ["true", "1"]
        self.trailer_web_optimized = os.getenv(
            "TRAILER_WEB_OPTIMIZED",
            "True",
        ).lower() in ["true", "1"]
        self.trailer_file_name = os.getenv(
            "TRAILER_FILE_NAME", self._DEFAULT_FILE_NAME
        )
        self.webui_password = os.getenv(
            "WEBUI_PASSWORD", self._DEFAULT_WEBUI_PASSWORD
        )
        self.yt_cookies_path = os.getenv("YT_COOKIES_PATH", "")
        self.exclude_words = os.getenv("EXCLUDE_WORDS", "")
        self.trailer_min_duration = int(os.getenv("TRAILER_MIN_DURATION", 30))
        self.trailer_max_duration = int(os.getenv("TRAILER_MAX_DURATION", 600))
        self.trailer_always_search = os.getenv(
            "TRAILER_ALWAYS_SEARCH",
            "False",
        ).lower() in ["true", "1"]
        self.trailer_search_query = getenv_str(
            "TRAILER_SEARCH_QUERY", self._DEFAULT_SEARCH_QUERY
        )
        # Advanced settings
        self.nvidia_gpu_available = getenv_bool("NVIDIA_GPU_AVAILABLE", False)
        self.trailer_hardware_acceleration = getenv_bool(
            "TRAILER_HARDWARE_ACCELERATION", True
        )
        # Experimental settings
        self.trailer_remove_silence = getenv_bool(
            "TRAILER_REMOVE_SILENCE", False
        )
        self.new_download_method = getenv_bool("NEW_DOWNLOAD_METHOD", False)

    def as_dict(self):
        return {
            "api_key": self.api_key,
            "app_data_dir": APP_DATA_DIR,
            "app_mode": APP_MODE,
            "exclude_words": self.exclude_words,
            "log_level": self.log_level,
            "monitor_enabled": self.monitor_enabled,
            "monitor_interval": self.monitor_interval,
            "timezone": self.timezone,
            "trailer_audio_format": self.trailer_audio_format,
            "trailer_audio_volume_level": self.trailer_audio_volume_level,
            "trailer_embed_metadata": self.trailer_embed_metadata,
            "trailer_file_format": self.trailer_file_format,
            "trailer_folder_movie": self.trailer_folder_movie,
            "trailer_folder_series": self.trailer_folder_series,
            "trailer_always_search": self.trailer_always_search,
            "trailer_search_query": self.trailer_search_query,
            "trailer_max_duration": self.trailer_max_duration,
            "trailer_min_duration": self.trailer_min_duration,
            "trailer_remove_sponsorblocks": self.trailer_remove_sponsorblocks,
            "trailer_resolution": self.trailer_resolution,
            "trailer_subtitles_enabled": self.trailer_subtitles_enabled,
            "trailer_subtitles_format": self.trailer_subtitles_format,
            "trailer_subtitles_language": self.trailer_subtitles_language,
            "trailer_video_format": self.trailer_video_format,
            "trailer_web_optimized": self.trailer_web_optimized,
            "server_start_time": self.server_start_time,
            "update_available": self.update_available,
            "version": self.version,
            "wait_for_media": self.wait_for_media,
            "trailer_file_name": self.trailer_file_name,
            "yt_cookies_path": self.yt_cookies_path,
            "ytdlp_version": self.ytdlp_version,
            "trailer_remove_silence": self.trailer_remove_silence,
            "nvidia_gpu_available": self.nvidia_gpu_available,
            "trailer_hardware_acceleration": (
                self.trailer_hardware_acceleration
            ),
            "new_download_method": self.new_download_method,
            "update_ytdlp": self.update_ytdlp,
            "url_base": self.url_base,
            "webui_username": self.webui_username,
        }

    @property
    def api_key(self):
        """API Key for the application. \n
        Reads the value from environment variable 'API_KEY' if present. \n
        If not present, generates a new API Key and returns it. \n
        Setting it to empty string will also generate a new API Key. \n
        Valid values would be any string of length 32."""
        return self._api_key

    def __generate_api_key(self) -> str:
        """Generate a new API Key of 32 characters and return it."""
        _key = secrets.token_hex(16)
        if len(_key) != 32:  # Ensure the key is 32 characters long
            return self.__generate_api_key()
        return _key

    @api_key.setter
    def api_key(self, value: str):
        if not value or len(value) < 32:
            value = self.__generate_api_key()  # Generate a new key
        self._api_key = value
        self._save_to_env("API_KEY", self._api_key)

    @property
    def app_data_dir(self):
        """Application data directory. \n
        Default is '/data'. \n
        Can be changed to any directory path with docker ENV variable. \n
        **Cannot be changed here!**"""
        return APP_DATA_DIR

    @app_data_dir.setter
    def app_data_dir(self, value: str):
        pass

    @property
    def app_mode(self) -> str:
        """App Running Mode:
        - Docker
        - Standalone
        """
        return APP_MODE

    @property
    def log_level(self):
        """Log level for the application. \n
        Default is INFO. \n
        Valid values are DEBUG, INFO, WARNING, ERROR, CRITICAL."""
        return self._log_level

    @log_level.setter
    def log_level(self, value: str):
        if value.upper() not in self._VALID_LOG_LEVELS:
            value = "INFO"
        self._log_level = value.upper()
        app_logger_opts.set_logger_level(self._log_level)
        self._save_to_env("LOG_LEVEL", self._log_level)

    testing = bool_property("TESTING", default=False)
    """Testing mode for the application. \n
        - Default is False. \n
        - Valid values are True/False."""

    @property
    def database_url(self):
        """Database URL for the application. \n
        Default is 'sqlite:////config/trailarr.db'. \n
        Valid values are any database URL."""
        # return self._database_url
        return self._DEFAULT_DB_URL

    # @database_url.setter
    # def database_url(self, value: str):
    #     if not value:
    #         value = self._DEFAULT_DB_URL
    #     # If APP_DATA_DIR has updated, and database_url is default,
    #     #    update it to new path
    #     # If ENV DATABASE_URL is modified by user, don't update it
    #     _untouched_db_url = "sqlite:////data/trailarr.db"
    #     # TODO: Change this to /data/trailarr.db in next update!
    #     if value == _untouched_db_url:
    #         value = self._DEFAULT_DB_URL
    #     self._database_url = value
    #     self._save_to_env("DATABASE_URL", self._database_url)

    monitor_enabled = bool_property("MONITOR_ENABLED", default=True)
    """Monitor enabled for the application.
        - Default is True.
        - Valid values are True/False."""

    monitor_interval = int_property("MONITOR_INTERVAL", default=60, min_=10)
    """Monitor interval for the application.
        - Default is 60 minutes. Minimum is 10
        - Valid values are integers."""

    wait_for_media = bool_property("WAIT_FOR_MEDIA", default=False)
    """Wait for media to be available.
        - Default is False.
        - Valid values are True/False."""

    trailer_always_search = bool_property(
        "TRAILER_ALWAYS_SEARCH", default=False
    )
    """Always search for trailers.
        - Default is False.
        - Valid values are True/False."""

    @property
    def trailer_search_query(self):
        """Search query for trailers. \n
        Default is '{title} {year} {is_movie} trailer'. \n
        Valid values are any string with placeholders."""
        return self._trailer_search_query

    @trailer_search_query.setter
    def trailer_search_query(self, value: str):
        value = value.strip()
        if value.count("{") != value.count("}"):
            value = self._DEFAULT_SEARCH_QUERY
        self._trailer_search_query = value
        self._save_to_env("TRAILER_SEARCH_QUERY", self._trailer_search_query)

    # trailer_search_query = str_property(
    #     "TRAILER_SEARCH_QUERY", default=_DEFAULT_SEARCH_QUERY
    # )

    @property
    def trailer_file_name(self):
        """File name format for trailers. \n
        Default is '{title} - Trailer{i}-trailer.{ext}'. \n
        Valid values are any string with placeholders."""
        return self._trailer_file_name

    @trailer_file_name.setter
    def trailer_file_name(self, value: str):
        value = value.strip()
        if value.count("{") != value.count("}"):
            value = self._DEFAULT_FILE_NAME
        if not value.endswith(".{ext}"):
            value = value.replace("{ext}", ".{ext}")
        if not value.endswith(".{ext}"):
            value += ".{ext}"
        self._trailer_file_name = value
        self._save_to_env("TRAILER_FILE_NAME", self._trailer_file_name)

    trailer_folder_movie = bool_property("TRAILER_FOLDER_MOVIE", default=False)
    """Trailer folder for movies.
        - Default is False.
        - Valid values are True/False."""

    trailer_folder_series = bool_property(
        "TRAILER_FOLDER_SERIES", default=True
    )
    """Trailer folder for series.
        - Default is True.
        - Valid values are True/False."""

    trailer_min_duration = int_property(
        "TRAILER_MIN_DURATION", default=30, min_=30
    )
    """Minimum duration for trailers.
        - Minimum is 30 seconds.
        - Default is 30 seconds.
        - Valid values are integers."""

    @property
    def trailer_max_duration(self):
        """Maximum duration for trailers. \n
        Minimum is greater than minimum duration by atleast a minute. \n
        Maximum is 600 seconds. \n
        Default is 600 seconds. \n
        Valid values are integers."""
        return self._trailer_max_duration

    @trailer_max_duration.setter
    def trailer_max_duration(self, value: int):
        # At least minimum + 60 seconds
        value = max(self.trailer_min_duration + 60, value)
        value = min(600, value)  # Maximum duration is 600 seconds
        self._trailer_max_duration = value
        self._save_to_env("TRAILER_MAX_DURATION", self._trailer_max_duration)

    trailer_subtitles_enabled = bool_property(
        "TRAILER_SUBTITLES_ENABLED", default=True
    )
    """Subtitles enabled for trailers.
        - Default is True.
        - Valid values are True/False."""

    trailer_subtitles_language = str_property(
        "TRAILER_SUBTITLES_LANGUAGE", default=_DEFAULT_LANGUAGE
    )
    """Language Code for trailers.
        - Default is 'en' for English.
        - Valid values are any language."""

    @property
    def trailer_resolution(self) -> int:
        """Resolution for trailers. \n
        Default is 1080. \n
        Valid input values are '240', '360', '480', '720', '1080', '1440',
        '2160', 'SD', 'FSD', 'HD', 'FHD', 'QHD', 'UHD'.
        Always stored as a number. Ex: '1080'.
        """
        return self._trailer_resolution

    @trailer_resolution.setter
    def trailer_resolution(self, value: str | int):
        # Try to resolve the closest resolution or assign default
        self._trailer_resolution = self.resolve_closest_resolution(value)
        self._save_to_env("TRAILER_RESOLUTION", self._trailer_resolution)

    trailer_audio_format = str_property(
        "TRAILER_AUDIO_FORMAT",
        default=_DEFAULT_AUDIO_FORMAT,
        valid_values=_VALID_AUDIO_FORMATS,
    )
    """Audio format for trailers.
        - Default is 'aac'.
        - Valid values are 'aac', 'ac3', 'eac3', 'mp3', 'vorbis', 'opus'."""

    trailer_audio_volume_level = int_property(
        "TRAILER_AUDIO_VOLUME_LEVEL", default=100, min_=1, max_=200
    )
    """Audio volume level for trailers, between 1 and 200.
        - Default is 100 -> No change in audio level.
        - Valid values are integers beteen 1 and 200."""

    trailer_video_format = str_property(
        "TRAILER_VIDEO_FORMAT",
        default=_DEFAULT_VIDEO_FORMAT,
        valid_values=_VALID_VIDEO_FORMATS,
    )
    """Video format for trailers.
        - Default is 'h264'.
        - Valid values are 'h264', 'h265', 'vp8', 'vp9', 'av1'."""

    trailer_subtitles_format = str_property(
        "TRAILER_SUBTITLES_FORMAT",
        default=_DEFAULT_SUBTITLES_FORMAT,
        valid_values=_VALID_SUBTITLES_FORMATS,
    )
    """Subtitles format for trailers.
        - Default is 'srt'.
        - Valid values are 'srt', 'vtt', 'pgs'."""

    trailer_file_format = str_property(
        "TRAILER_FILE_FORMAT",
        default=_DEFAULT_FILE_FORMAT,
        valid_values=_VALID_FILE_FORMATS,
    )
    """File format for trailers.
        - Default is 'mkv'.
        - Valid values are 'mp4', 'mkv', 'webm'."""

    trailer_embed_metadata = bool_property(
        "TRAILER_EMBED_METADATA", default=True
    )
    """Embed metadata for trailers.
        - Default is True.
        - Valid values are True/False."""

    trailer_remove_sponsorblocks = bool_property(
        "TRAILER_REMOVE_SPONSORBLOCKS", default=True
    )
    """Remove sponsorblocks from the trailers.
        - Default is True.
        - Valid values are True/False."""

    trailer_web_optimized = bool_property(
        "TRAILER_WEB_OPTIMIZED", default=True
    )
    """Web optimized for trailers.
        - Default is True.
        - Valid values are True/False."""

    webui_username = str_property(
        "WEBUI_USERNAME", default=_DEFAULT_WEBUI_USERNAME
    )
    """Username for the WebUI.
    - Default is 'admin'.
    - Valid values are any strings."""

    webui_password = str_property(
        "WEBUI_PASSWORD", default=_DEFAULT_WEBUI_PASSWORD
    )
    """Password for the WebUI (hashed and stored).
        - Default is 'trailarr'.
        - Valid values are any hashed string of password."""

    yt_cookies_path = str_property("YT_COOKIES_PATH", default="")
    """Path to the YouTube cookies file.
        - Default is empty string.
        - Valid values are any file path."""

    exclude_words = str_property("EXCLUDE_WORDS", default="")
    """Exclude words for trailers.
        - Default is empty string.
        - Valid values are any string."""

    nvidia_gpu_available = bool_property("NVIDIA_GPU_AVAILABLE", default=False)
    """NVIDIA GPU available for hardware acceleration.
        - Value is set during container startup based on availability.
        - Default is False.
        - Valid values are True/False."""

    trailer_hardware_acceleration = bool_property(
        "TRAILER_HARDWARE_ACCELERATION", default=True
    )
    """Hardware acceleration status for trailers.
        - Default is True.
        - Valid values are True/False."""

    new_download_method = bool_property("NEW_DOWNLOAD_METHOD", default=False)
    """Flag to enable new download method for yt-dlp and conversion.
        - Default is False.
        - Valid values are True/False"""

    trailer_remove_silence = bool_property(
        "TRAILER_REMOVE_SILENCE", default=False
    )
    """Remove silence from the trailers.
        - Default is False.
        - Valid values are True/False."""

    update_ytdlp = bool_property("UPDATE_YTDLP", default=False)
    """Update yt-dlp binary on startup.
        - Default is False.
        - Valid values are True/False."""

    url_base = str_property("URL_BASE", default="")
    """URL Base for the application for use with reverse proxy.
        - Default is empty string.
        - If a value is provided, app will start with that url_base as \
            root path."""

    def _save_to_env(self, key: str, value: str | int | bool):
        """Save the given key-value pair to the environment variables."""
        os.environ[key.upper()] = str(value)
        set_key(ENV_PATH, key.upper(), str(value))

    def resolve_closest_resolution(self, value: str | int) -> int:
        """Resolve the closest resolution for the given value. \n
        Returns the closest resolution as an integer. \n
        Args:
            - value: Resolution as a string or integer (ex: 1080 or UHD) \n
        Returns:
            - int: Closest resolution as an int, returns default resolution \
                if input value is invalid.
        """
        if not isinstance(value, (str, int)):
            try:
                value = str(value)
            except ValueError:
                return self._DEFAULT_RESOLUTION

        resolution = 1080
        if isinstance(value, int):
            resolution = value

        if isinstance(value, str):
            # Check if value is like HD/UHD etc.
            if value.upper() in RESOLUTION_DICT:
                resolution = RESOLUTION_DICT[value.upper()]
                return resolution
            # Else, Convert to lowercase and remove 'p' from the end if present
            resolution = value.lower()
            resolution = resolution.rstrip("p")
            if not resolution.isdigit():
                return self._DEFAULT_RESOLUTION
            resolution = int(resolution)

        # If resolution is valid, return it
        if resolution in self._VALID_RESOLUTIONS:
            return resolution
        # Find the closest resolution. Ex: 1079 -> 1080
        closest_resolution = min(
            self._VALID_RESOLUTIONS, key=lambda res: abs(res - resolution)
        )
        return closest_resolution


# Load environment variables, do not override system environment variables
load_dotenv(dotenv_path=ENV_PATH, override=False)
# Create Config object to be used in the application
app_settings = _Config()
