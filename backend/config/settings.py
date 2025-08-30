from datetime import datetime, timezone
import os
import secrets

from dotenv import load_dotenv, set_key

from config import app_logger_opts

APP_DATA_DIR = os.path.abspath(os.getenv("APP_DATA_DIR", "/config"))
ENV_PATH = f"{APP_DATA_DIR}/.env"


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
    # Try to get version from yt-dlp --version command
    try:
        from subprocess import check_output

        # Check for different yt-dlp installation paths
        _ytdlp_paths = [
            getenv_str(
                "YTDLP_PATH", "/usr/local/bin/yt-dlp"
            ),  # Configurable path
            "/opt/trailarr/bin/yt-dlp",  # Bare metal local install
            "/opt/trailarr/venv/bin/yt-dlp",  # Bare metal venv
            "/usr/local/bin/yt-dlp",  # Docker
            "yt-dlp",  # System PATH
        ]

        for _ytdlp_path in _ytdlp_paths:
            try:
                _ver = (
                    check_output([_ytdlp_path, "--version"])
                    .decode("utf-8")
                    .strip()
                )
                break
            except (FileNotFoundError, OSError):
                continue
        else:
            _ver = "0.0.0"  # If none of the paths work
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

    _DEFAULT_DB_URL = f"sqlite:///{APP_DATA_DIR}/trailarr.db"
    _DEFAULT_FILE_NAME = "{title} - Trailer-trailer.{ext}"
    # Default WebUI user 'admin'
    _DEFAULT_WEBUI_USERNAME = "admin"
    # Default WebUI password 'trailarr' hashed
    _DEFAULT_WEBUI_PASSWORD = (
        "$2b$12$CU7h.sOkBp5RFRJIYEwXU.1LCUTD2pWE4p5nsW3k1iC9oZEGVWeum"
    )

    _VALID_LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

    def __init__(self):
        # Some generic attributes for server
        self.version = getenv_str("APP_VERSION", "0.0.0")
        self.ytdlp_version = get_ytdlp_version()
        self.update_available = False
        self.update_available_ytdlp = False
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

        # If the webui_password is empty, set it to the default
        # Handle whitespace and empty strings (even improperly escaped quotes)
        _webui_password = self.webui_password.replace('"', '').replace("'", "")
        _webui_password = _webui_password.replace("\t", "").strip()
        if not _webui_password:
            self.webui_password = self._DEFAULT_WEBUI_PASSWORD
        self.yt_cookies_path = os.getenv("YT_COOKIES_PATH", "")
        self.trailer_max_duration = ""

    def as_dict(self):
        return {
            "api_key": self.api_key,
            "app_data_dir": APP_DATA_DIR,
            "app_mode": self.app_mode,
            "gpu_available_nvidia": self.gpu_available_nvidia,
            "gpu_available_intel": self.gpu_available_intel,
            "gpu_available_amd": self.gpu_available_amd,
            "gpu_enabled_nvidia": self.gpu_enabled_nvidia,
            "gpu_enabled_intel": self.gpu_enabled_intel,
            "gpu_enabled_amd": self.gpu_enabled_amd,
            "log_level": self.log_level,
            "monitor_enabled": self.monitor_enabled,
            "monitor_interval": self.monitor_interval,
            "server_start_time": self.server_start_time,
            "timezone": self.timezone,
            "update_available": self.update_available,
            "update_available_ytdlp": self.update_available_ytdlp,
            "update_ytdlp": self.update_ytdlp,
            "url_base": self.url_base,
            "version": self.version,
            "wait_for_media": self.wait_for_media,
            "webui_username": self.webui_username,
            "yt_cookies_path": self.yt_cookies_path,
            "ytdlp_version": self.ytdlp_version,
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
        _save_to_env("API_KEY", self._api_key)

    @property
    def app_data_dir(self):
        """Application data directory. \n
        Default is '/config'. \n
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
        - Direct Linux
        """
        return os.getenv("APP_MODE", "Direct")

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
        _save_to_env("LOG_LEVEL", self._log_level)

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

    gpu_available_amd = bool_property("GPU_AVAILABLE_AMD", default=False)
    """AMD GPU available for hardware acceleration (AMF).
        - Value is set during container startup based on availability.
        - Default is False.
        - Valid values are True/False."""

    gpu_available_intel = bool_property("GPU_AVAILABLE_INTEL", default=False)
    """Intel GPU available for hardware acceleration (VAAPI).
        - Value is set during container startup based on availability.
        - Default is False.
        - Valid values are True/False."""

    gpu_available_nvidia = bool_property("GPU_AVAILABLE_NVIDIA", default=False)
    """NVIDIA GPU available for hardware acceleration.
        - Value is set during container startup based on availability.
        - Default is False.
        - Valid values are True/False."""

    gpu_enabled_amd = bool_property("GPU_ENABLED_AMD", default=True)
    """Enable AMD GPU hardware acceleration (AMF).
        - Default is True (enabled if available).
        - Valid values are True/False."""

    gpu_enabled_intel = bool_property("GPU_ENABLED_INTEL", default=True)
    """Enable Intel GPU hardware acceleration (VAAPI).
        - Default is True (enabled if available).
        - Valid values are True/False."""

    gpu_enabled_nvidia = bool_property("GPU_ENABLED_NVIDIA", default=True)
    """Enable NVIDIA GPU hardware acceleration.
        - Default is True (enabled if available).
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

    ffmpeg_path = str_property("FFMPEG_PATH", default="/usr/local/bin/ffmpeg")
    """Path to ffmpeg binary.
        - Default is /usr/local/bin/ffmpeg (Docker).
        - For bare metal installations, this should point to local ffmpeg installation.
        - Valid values are any valid file path to ffmpeg binary."""

    ffprobe_path = str_property(
        "FFPROBE_PATH", default="/usr/local/bin/ffprobe"
    )
    """Path to ffprobe binary.
        - Default is /usr/local/bin/ffprobe (Docker).
        - For bare metal installations, this should point to local ffprobe installation.
        - Valid values are any valid file path to ffprobe binary."""

    ytdlp_path = str_property("YTDLP_PATH", default="/usr/local/bin/yt-dlp")
    """Path to yt-dlp binary.
        - Default is /usr/local/bin/yt-dlp (Docker).
        - For bare metal installations, this should point to local yt-dlp installation.
        - Valid values are any valid file path to yt-dlp binary."""

    # def resolve_closest_resolution(self, value: str | int) -> int:
    #     """Resolve the closest resolution for the given value. \n
    #     Returns the closest resolution as an integer. \n
    #     Args:
    #         - value: Resolution as a string or integer (ex: 1080 or UHD) \n
    #     Returns:
    #         - int: Closest resolution as an int, returns default resolution \
    #             if input value is invalid.
    #     """
    #     if not isinstance(value, (str, int)):
    #         try:
    #             value = str(value)
    #         except ValueError:
    #             return self._DEFAULT_RESOLUTION

    #     resolution = 1080
    #     if isinstance(value, int):
    #         resolution = value

    #     if isinstance(value, str):
    #         # Check if value is like HD/UHD etc.
    #         if value.upper() in RESOLUTION_DICT:
    #             resolution = RESOLUTION_DICT[value.upper()]
    #             return resolution
    #         # Else, Convert to lowercase and remove 'p' from the end if present
    #         resolution = value.lower()
    #         resolution = resolution.rstrip("p")
    #         if not resolution.isdigit():
    #             return self._DEFAULT_RESOLUTION
    #         resolution = int(resolution)

    #     # If resolution is valid, return it
    #     if resolution in self._VALID_RESOLUTIONS:
    #         return resolution
    #     # Find the closest resolution. Ex: 1079 -> 1080
    #     closest_resolution = min(
    #         self._VALID_RESOLUTIONS, key=lambda res: abs(res - resolution)
    #     )
    #     return closest_resolution


# Load environment variables, do not override system environment variables
load_dotenv(dotenv_path=ENV_PATH, override=False)
# Create Config object to be used in the application
app_settings = _Config()
