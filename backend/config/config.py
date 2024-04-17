import os

from dotenv import load_dotenv, set_key

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
    **DO NOT USE THIS CLASS DIRECTLY. USE `config` OBJECT INSTEAD!** \n
    \n
    **Environment variables set in the system will take precedence. \
        Changing class values doesn't any effect if relevant env variable is set!** \n
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
    _DEFAULT_DB_URL = "sqlite:///trailarr.db"

    _VALID_AUDIO_FORMATS = ["aac", "ac3", "eac3", "mp3", "flac", "vorbis", "opus"]
    _VALID_VIDEO_FORMATS = ["h264", "h265", "vp8", "vp9", "av1"]
    _VALID_SUBTITLES_FORMATS = ["srt", "vtt", "pgs"]
    _VALID_FILE_FORMATS = ["mp4", "mkv", "webm"]
    _VALID_RESOLUTIONS = [240, 360, 480, 720, 1080, 1440, 2160]

    def __init__(self):
        # Setting default values for properties
        self.debug = os.getenv("DEBUG", "False").lower() in ["true", "1"]
        self.database_url = os.getenv("DATABASE_URL", self._DEFAULT_DB_URL)
        self.dark_mode_enabled = os.getenv(
            "DARK_MODE_ENABLED",
            "True",
        ).lower() in ["true", "1"]
        self.monitor_enabled = os.getenv(
            "MONITOR_ENABLED",
            "True",
        ).lower() in ["true", "1"]
        self.monitor_interval = int(os.getenv("MONITOR_INTERVAL", 60))
        self.trailer_folder_movie = os.getenv(
            "TRAILER_FOLDER_MOVIE",
            "False",
        ).lower() in ["true", "1"]
        self.trailer_folder_series = os.getenv(
            "TRAILER_FOLDER_SERIES",
            "False",
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
        self.trailer_web_optimized = os.getenv(
            "TRAILER_WEB_OPTIMIZED",
            "False",
        ).lower() in ["true", "1"]

    @property
    def debug(self):
        """Debug mode for the application. \n
        Default is False. \n
        Valid values are True/False."""
        return self._debug

    @debug.setter
    def debug(self, value: bool):
        self._debug = value
        self._save_to_env("DEBUG", self._debug)

    @property
    def dark_mode_enabled(self):
        """Dark mode for the application. \n
        Default is True. \n
        Valid values are True/False."""
        return self._dark_mode_enabled

    @dark_mode_enabled.setter
    def dark_mode_enabled(self, value: bool):
        self._dark_mode_enabled = value
        self._save_to_env("DARK_MODE_ENABLED", self._dark_mode_enabled)

    @property
    def database_url(self):
        """Database URL for the application. \n
        Default is 'sqlite:///trailarr.db'. \n
        Valid values are any database URL."""
        return self._database_url

    @database_url.setter
    def database_url(self, value: str):
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
        Default is 60 seconds. \n
        Valid values are integers."""
        return self._monitor_interval

    @monitor_interval.setter
    def monitor_interval(self, value: int):
        value = max(10, value)  # Minimum interval is 10 minutes
        self._monitor_interval = value
        self._save_to_env("MONITOR_INTERVAL", self._monitor_interval)

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
        Default is False. \n
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
    def trailer_resolution(self):
        """Resolution for trailers. \n
        Default is '1080p'. \n
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
    def trailer_web_optimized(self):
        """Web optimized for trailers. \n
        Default is False. \n
        Valid values are True/False."""
        return self._trailer_web_optimized

    @trailer_web_optimized.setter
    def trailer_web_optimized(self, value: bool):
        self._trailer_web_optimized = value
        self._save_to_env("TRAILER_WEB_OPTIMIZED", self._trailer_web_optimized)

    def _save_to_env(self, key: str, value: str | int | bool):
        """Save the given key-value pair to the environment variables."""
        os.environ[key.upper()] = str(value)
        set_key(".env", key.upper(), str(value))

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
load_dotenv(override=False)
# Create Config object to be used in the application
config = _Config()
