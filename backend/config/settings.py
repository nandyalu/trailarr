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


class _Config:
    """Class to hold configuration settings for the application. \n
    Reads environment variables to set properties. \n
    Default values are used if environment variables are not provided/invalid. \n
    \n
    **DO NOT USE THIS CLASS DIRECTLY. USE `app_settings` OBJECT INSTEAD!** \n
    \n
    **Environment variables set in the system will take precedence. \
        Changing class values doesn't have any effect if relevant env variable is set!** \n
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

    _VALID_LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    _VALID_AUDIO_FORMATS = ["aac", "ac3", "eac3", "flac", "opus"]
    _VALID_VIDEO_FORMATS = ["h264", "h265", "vp8", "vp9", "av1"]
    _VALID_SUBTITLES_FORMATS = ["srt", "vtt", "pgs"]
    _VALID_FILE_FORMATS = ["mp4", "mkv", "webm"]
    _VALID_RESOLUTIONS = [240, 360, 480, 720, 1080, 1440, 2160]

    def __init__(self):
        # Some generic attributes for server
        self.version = os.getenv("APP_VERSION", "0.0.1")
        _now = datetime.now(timezone.utc)
        self.server_start_time = os.getenv("SERVER_START_TIME", f"{_now}")
        self.timezone = os.getenv("TZ", "UTC")
        self.app_data_dir = APP_DATA_DIR

        # Read properties from ENV variables or set default values if not present
        self.api_key = os.getenv("API_KEY", "")
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.testing = os.getenv("TESTING", "False").lower() in ["true", "1"]
        self.database_url = os.getenv("DATABASE_URL", self._DEFAULT_DB_URL)
        self.monitor_enabled = os.getenv(
            "MONITOR_ENABLED",
            "True",
        ).lower() in ["true", "1"]
        self.monitor_interval = int(os.getenv("MONITOR_INTERVAL", 60))
        self.wait_for_media = os.getenv(
            "WAIT_FOR_MEDIA",
            "False",
        ).lower() in ["true", "1"]
        self.trailer_folder_movie = os.getenv(
            "TRAILER_FOLDER_MOVIE",
            "False",
        ).lower() in ["true", "1"]
        self.trailer_folder_series = os.getenv(
            "TRAILER_FOLDER_SERIES",
            "True",
        ).lower() in ["true", "1"]
        self.trailer_resolution = os.getenv(
            "TRAILER_RESOLUTION", self._DEFAULT_RESOLUTION
        )
        self.trailer_audio_format = os.getenv(
            "TRAILER_AUDIO_FORMAT", self._DEFAULT_AUDIO_FORMAT
        )
        self.trailer_video_format = os.getenv(
            "TRAILER_VIDEO_FORMAT", self._DEFAULT_VIDEO_FORMAT
        )
        self.trailer_subtitles_enabled = os.getenv(
            "TRAILER_SUBTITLES_ENABLED",
            "True",
        ).lower() in ["true", "1"]
        self.trailer_subtitles_format = os.getenv(
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
        self.trailer_file_name = os.getenv("TRAILER_FILE_NAME", self._DEFAULT_FILE_NAME)
        self.yt_cookies_path = os.getenv("YT_COOKIES_PATH", "")

    def as_dict(self):
        return {
            "api_key": self.api_key,
            "app_data_dir": APP_DATA_DIR,
            "log_level": self.log_level,
            "monitor_enabled": self.monitor_enabled,
            "monitor_interval": self.monitor_interval,
            "timezone": self.timezone,
            "trailer_audio_format": self.trailer_audio_format,
            "trailer_embed_metadata": self.trailer_embed_metadata,
            "trailer_file_format": self.trailer_file_format,
            "trailer_folder_movie": self.trailer_folder_movie,
            "trailer_folder_series": self.trailer_folder_series,
            "trailer_remove_sponsorblocks": self.trailer_remove_sponsorblocks,
            "trailer_resolution": self.trailer_resolution,
            "trailer_subtitles_enabled": self.trailer_subtitles_enabled,
            "trailer_subtitles_format": self.trailer_subtitles_format,
            "trailer_subtitles_language": self.trailer_subtitles_language,
            "trailer_video_format": self.trailer_video_format,
            "trailer_web_optimized": self.trailer_web_optimized,
            "server_start_time": self.server_start_time,
            "version": self.version,
            "wait_for_media": self.wait_for_media,
            "trailer_file_name": self.trailer_file_name,
            "yt_cookies_path": self.yt_cookies_path,
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
    def log_level(self):
        """Log level for the application. \n
        Default is INFO. \n
        Valid values are DEBUG, INFO, WARNING, ERROR, CRITICAL."""
        return self._debug

    @log_level.setter
    def log_level(self, value: str):
        if value.upper() not in self._VALID_LOG_LEVELS:
            value = "INFO"
        self._debug = value.upper()
        app_logger_opts.set_logger_level(self._debug)
        self._save_to_env("LOG_LEVEL", self._debug)

    @property
    def testing(self):
        """Testing mode for the application. \n
        Default is False. \n
        Valid values are True/False."""
        return self._testing

    @testing.setter
    def testing(self, value: bool):
        self._testing = value
        self._save_to_env("TESTING", self._testing)

    @property
    def database_url(self):
        """Database URL for the application. \n
        Default is 'sqlite:////data/trailarr.db'. \n
        Valid values are any database URL."""
        return self._database_url

    @database_url.setter
    def database_url(self, value: str):
        if not value:
            value = self._DEFAULT_DB_URL
        # If APP_DATA_DIR has updated, and database_url is default, update it to new path
        # If ENV DATABASE_URL is modified by user, don't update it
        _untouched_db_url = "sqlite:////data/trailarr.db"
        if value == _untouched_db_url:
            value = self._DEFAULT_DB_URL
        self._database_url = value
        self._save_to_env("DATABASE_URL", self._database_url)

    @property
    def monitor_enabled(self):
        """Monitor enabled for the application. \n
        Default is True. \n
        Valid values are True/False."""
        return self._monitor_enabled

    @monitor_enabled.setter
    def monitor_enabled(self, value: bool):
        self._monitor_enabled = value
        self._save_to_env("MONITOR_ENABLED", self._monitor_enabled)

    @property
    def monitor_interval(self):
        """Monitor interval for the application. \n
        Default is 60 minutes. Minimum is 10 \n
        Valid values are integers."""
        return self._monitor_interval

    @monitor_interval.setter
    def monitor_interval(self, value: int):
        value = max(10, value)  # Minimum interval is 10 minutes
        self._monitor_interval = value
        self._save_to_env("MONITOR_INTERVAL", self._monitor_interval)

    @property
    def wait_for_media(self):
        """Wait for media to be available. \n
        Default is False. \n
        Valid values are True/False."""
        return self._wait_for_media

    @wait_for_media.setter
    def wait_for_media(self, value: bool):
        self._wait_for_media = value
        self._save_to_env("WAIT_FOR_MEDIA", self._wait_for_media)

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

    @property
    def trailer_folder_movie(self):
        """Trailer folder for movies. \n
        Default is False. \n
        Valid values are True/False."""
        return self._trailer_folder_movie

    @trailer_folder_movie.setter
    def trailer_folder_movie(self, value: bool):
        self._trailer_folder_movie = value
        self._save_to_env("TRAILER_FOLDER_MOVIE", self._trailer_folder_movie)

    @property
    def trailer_folder_series(self):
        """Trailer folder for series. \n
        Default is True. \n
        Valid values are True/False."""
        return self._trailer_folder_series

    @trailer_folder_series.setter
    def trailer_folder_series(self, value: bool):
        self._trailer_folder_series = value
        self._save_to_env("TRAILER_FOLDER_SERIES", self._trailer_folder_series)

    @property
    def trailer_subtitles_enabled(self):
        """Subtitles enabled for trailers. \n
        Default is True. \n
        Valid values are True/False."""
        return self._trailer_subtitles_enabled

    @trailer_subtitles_enabled.setter
    def trailer_subtitles_enabled(self, value: bool):
        self._trailer_subtitles_enabled = value
        self._save_to_env("TRAILER_SUBTITLES_ENABLED", self._trailer_subtitles_enabled)

    @property
    def trailer_subtitles_language(self):
        """Language Code for trailers. \n
        Default is 'en' for English. \n
        Valid values are any language."""
        return self._trailer_language

    @trailer_subtitles_language.setter
    def trailer_subtitles_language(self, value: str):
        self._trailer_language = value
        self._save_to_env("TRAILER_SUBTITLES_LANGUAGE", self._trailer_language)

    @property
    def trailer_resolution(self) -> int:
        """Resolution for trailers. \n
        Default is 1080. \n
        Valid input values are '240', '360', '480', '720', '1080', '1440', '2160',
        'SD', 'FSD', 'HD', 'FHD', 'QHD', 'UHD'.
        Always stored as a number. Ex: '1080'.
        """
        return self._trailer_resolution

    @trailer_resolution.setter
    def trailer_resolution(self, value: str | int):
        # Try to resolve the closest resolution or assign default
        self._trailer_resolution = self.resolve_closest_resolution(value)
        self._save_to_env("TRAILER_RESOLUTION", self._trailer_resolution)

    @property
    def trailer_audio_format(self):
        """Audio format for trailers. \n
        Default is 'aac'. \n
        Valid values are 'aac', 'ac3', 'eac3', 'mp3', 'flac', 'vorbis', 'opus'."""
        return self._trailer_audio_format

    @trailer_audio_format.setter
    def trailer_audio_format(self, value: str):
        self._trailer_audio_format = value
        if self._trailer_audio_format.lower() not in self._VALID_AUDIO_FORMATS:
            self._trailer_audio_format = self._DEFAULT_AUDIO_FORMAT
        self._save_to_env("TRAILER_AUDIO_FORMAT", self._trailer_audio_format)

    @property
    def trailer_video_format(self):
        """Video format for trailers. \n
        Default is 'h264'. \n
        Valid values are 'h264', 'h265', 'vp8', 'vp9', 'av1'."""
        return self._trailer_video_format

    @trailer_video_format.setter
    def trailer_video_format(self, value: str):
        self._trailer_video_format = value
        if self._trailer_video_format.lower() not in self._VALID_VIDEO_FORMATS:
            self._trailer_video_format = self._DEFAULT_VIDEO_FORMAT
        self._save_to_env("TRAILER_VIDEO_FORMAT", self._trailer_video_format)

    @property
    def trailer_subtitles_format(self):
        """Subtitles format for trailers. \n
        Default is 'srt'. \n
        Valid values are 'srt', 'vtt', 'pgs'."""
        return self._trailer_subtitles_format

    @trailer_subtitles_format.setter
    def trailer_subtitles_format(self, value: str):
        self._trailer_subtitles_format = value
        if self._trailer_subtitles_format.lower() not in self._VALID_SUBTITLES_FORMATS:
            self._trailer_subtitles_format = self._DEFAULT_SUBTITLES_FORMAT
        self._save_to_env("TRAILER_VIDEO_FORMAT", self._trailer_subtitles_format)

    @property
    def trailer_file_format(self):
        """File format for trailers. \n
        Default is 'mkv'. \n
        Valid values are 'mp4', 'mkv', 'webm'."""
        return self._trailer_file_format

    @trailer_file_format.setter
    def trailer_file_format(self, value: str):
        self._trailer_file_format = value
        if self._trailer_file_format.lower() not in self._VALID_FILE_FORMATS:
            self._trailer_file_format = self._DEFAULT_FILE_FORMAT
        self._save_to_env("TRAILER_FILE_FORMAT", self._trailer_file_format)

    @property
    def trailer_embed_metadata(self):
        """Embed metadata for trailers. \n
        Default is True. \n
        Valid values are True/False."""
        return self._trailer_embed_metadata

    @trailer_embed_metadata.setter
    def trailer_embed_metadata(self, value: bool):
        self._trailer_embed_metadata = value
        self._save_to_env("TRAILER_EMBED_METADATA", self._trailer_embed_metadata)

    @property
    def trailer_remove_sponsorblocks(self):
        """Remove sponsorblocks from the trailers. \n
        Default is True. \n
        Valid values are True/False."""
        return self._trailer_remove_sponsorblocks

    @trailer_remove_sponsorblocks.setter
    def trailer_remove_sponsorblocks(self, value: bool):
        self._trailer_remove_sponsorblocks = value
        self._save_to_env(
            "TRAILER_REMOVE_SPONSORBLOCKS", self._trailer_remove_sponsorblocks
        )

    @property
    def trailer_web_optimized(self):
        """Web optimized for trailers. \n
        Default is True. \n
        Valid values are True/False."""
        return self._trailer_web_optimized

    @trailer_web_optimized.setter
    def trailer_web_optimized(self, value: bool):
        self._trailer_web_optimized = value
        self._save_to_env("TRAILER_WEB_OPTIMIZED", self._trailer_web_optimized)

    @property
    def yt_cookies_path(self):
        """Path to the YouTube cookies file. \n
        Default is empty string. \n
        Valid values are any file path."""
        return self._yt_cookies_path

    @yt_cookies_path.setter
    def yt_cookies_path(self, value: str):
        self._yt_cookies_path = value
        self._save_to_env("YT_COOKIES_PATH", self._yt_cookies_path)

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
                # raise TypeError(f"Expected str or int, got {type(value).__name__}")

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
