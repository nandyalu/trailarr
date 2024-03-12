import os

from dotenv import load_dotenv


class _Config:
    """Class to hold configuration settings for the application. \n
    Reads environment variables to set properties. \n
    Default values are used if environment variables are not provided/invalid. \n
    \n
    **DO NOT USE THIS CLASS DIRECTLY. USE `config` OBJECT INSTEAD!** \n
    \n
    **DO NOT CHANGE VALUES DIRECTLY. Change Environment Variables instead!** \n
    """

    _DEFAULT_AUDIO_FORMAT = "aac"
    _DEFAULT_VIDEO_FORMAT = "x264"
    _DEFAULT_FILE_FORMAT = "mkv"
    _DEFAULT_QUALITY = "high"
    _DEFAULT_RESOLUTION = "1080p"
    _DEFAULT_DB_URL = "sqlite:///trailarr.db"

    _VALID_AUDIO_FORMATS = ["aac", "ac3", "eac3", "mp3", "flac", "vorbis", "opus"]
    _VALID_VIDEO_FORMATS = ["x264", "x265", "vp8", "vp9", "av1"]
    _VALID_FILE_FORMATS = ["mp4", "mkv", "webm", "avi", "mov"]
    _VALID_QUALITIES = ["low", "medium", "high"]
    _VALID_RESOLUTIONS = ["240p", "360p", "480p", "720p", "1080p", "1440p", "2160p"]

    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ["true", "1"]
    DARK_MODE_ENABLED: bool = os.getenv(
        "DARK_MODE_ENABLED",
        "True",
    ).lower() in ["true", "1"]
    MONITOR_ENABLED: bool = os.getenv(
        "MONITOR_ENABLED",
        "True",
    ).lower() in ["true", "1"]
    MONITOR_INTERVAL: int = int(os.getenv("MONITOR_INTERVAL", 60))
    TRAILER_FOLDER_MOVIE: bool = os.getenv(
        "TRAILER_FOLDER_MOVIE",
        "False",
    ).lower() in ["true", "1"]
    TRAILER_FOLDER_SERIES: bool = os.getenv(
        "TRAILER_FOLDER_SERIES", "False"
    ).lower() in ["true", "1"]
    TRAILER_LANGUAGE = os.getenv("TRAILER_LANGUAGE", "English")

    DATABASE_URL: str = os.getenv("DATABASE_URL", _DEFAULT_DB_URL)

    def __init__(self):
        # Setting default values for properties
        self.trailer_resolution = os.getenv(
            "TRAILER_RESOLUTION", self._DEFAULT_RESOLUTION
        )

        self.trailer_quality = os.getenv("TRAILER_QUALITY", self._DEFAULT_RESOLUTION)

        self.trailer_audio_format = os.getenv(
            "TRAILER_AUDIO_FORMAT", self._DEFAULT_AUDIO_FORMAT
        )
        self.trailer_video_format = os.getenv(
            "TRAILER_VIDEO_FORMAT", self._DEFAULT_VIDEO_FORMAT
        )
        self.trailer_file_format = os.getenv(
            "TRAILER_FILE_FORMAT", self._DEFAULT_FILE_FORMAT
        )

    @property
    def trailer_resolution(self):
        """Resolution for trailers. \n
        Default is '1080p'. \n
        Valid input values are '240p', '360p', '480p', '720p', '1080p', '1440p', '2160p',
        'SD', 'FSD', 'HD', 'FHD', 'QHD', 'UHD'.
        Always stored as 'numberp' format. Ex: '1080p'.
        """
        return self._trailer_resolution

    @trailer_resolution.setter
    def trailer_resolution(self, value: str):
        value = value.lower()
        self._trailer_resolution = value
        if value not in self._VALID_RESOLUTIONS:
            # Resolve the closest resolution
            _resolution = self.resolve_closest_resolution(value)
            if _resolution:
                self._trailer_resolution = _resolution
            else:
                self._trailer_resolution = self._DEFAULT_RESOLUTION

    @property
    def trailer_quality(self):
        """Quality for trailers. \n
        Default is 'high'. \n
        Valid values are 'low', 'medium', 'high'."""
        return self._trailer_quality

    @trailer_quality.setter
    def trailer_quality(self, value: str):
        self._trailer_quality = value
        if self._trailer_quality.lower() not in self._VALID_QUALITIES:
            self._trailer_quality = self._DEFAULT_QUALITY

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

    @property
    def trailer_video_format(self):
        """Video format for trailers. \n
        Default is 'x264'. \n
        Valid values are 'x264', 'x265', 'vp8', 'vp9', 'av1'."""
        return self._trailer_video_format

    @trailer_video_format.setter
    def trailer_video_format(self, value: str):
        self._trailer_video_format = value
        if self._trailer_video_format.lower() not in self._VALID_VIDEO_FORMATS:
            self._trailer_video_format = self._DEFAULT_VIDEO_FORMAT

    @property
    def trailer_file_format(self):
        """File format for trailers. \n
        Default is 'mkv'. \n
        Valid values are 'mp4', 'mkv', 'webm', 'avi', 'mov'."""
        return self._trailer_file_format

    @trailer_file_format.setter
    def trailer_file_format(self, value: str):
        self._trailer_file_format = value
        if self._trailer_file_format.lower() not in self._VALID_FILE_FORMATS:
            self._trailer_file_format = self._DEFAULT_FILE_FORMAT

    # For future reference
    # To make this editable in the future, we can use the following code
    # set_key(".env", "MONITORING_ENABLED", str(config.MONITORING_ENABLED))

    def resolve_closest_resolution(self, value: str) -> str | None:
        """Resolve the closest resolution for the given value.
        Returns the closest resolution as a string.

        Args:
            - value: Resolution as a string (ex: 1080p or UHD) or number

        Returns:
            - str | None: Closest resolution as a string or None if invalid value
        """
        resolution = value.lower()
        if resolution[-1] != "p":
            if resolution.isdigit():
                resolution = int(resolution)
            else:
                res_str = {
                    "SD": 360,
                    "FSD": 480,
                    "HD": 720,
                    "FHD": 1080,
                    "QHD": 1440,
                    "UHD": 2160,
                }
                if resolution.upper() in res_str:
                    resolution = res_str[resolution.upper()]
                    return f"{resolution}p"
                return None
        else:
            resolution = int(resolution[:-1])
        valid_resolutions = [int(res[:-1]) for res in self._VALID_RESOLUTIONS]
        closest_resolution = min(
            valid_resolutions, key=lambda res: abs(res - resolution)
        )
        return f"{closest_resolution}p"


# Load environment variables, do not override system environment variables
load_dotenv(override=False)
# Create Config object to be used in the application
config = _Config()
