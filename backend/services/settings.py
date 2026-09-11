"""Changing application settings and the web UI login.

Both functions give back a message for the user rather than raising. The
API returns that message with a 200, which is the contract the frontend
expects — do not change it to an HTTP error without changing the frontend
and the OpenAPI spec together.
"""

from app_logger import ModuleLogger
from config.settings import app_settings
from exceptions import InvalidResponseError
from services import auth
from services.tmdb.api_manager import TMDBAPI, TMDBAuthError
from utils.secrets import MASK

logger = ModuleLogger("Settings")

# Settings whose value the API only ever sends masked. The value of one of
# these never goes back to the client, not in the settings and not in the
# message that says it changed.
SECRET_SETTINGS = ("tmdb_api_key",)


async def update_setting(key: str | None, value) -> str:
    """Change one application setting.

    A secret is checked before it is stored, and it is never sent back:
    the message says that it changed, not what it is.

    Args:
        key (str | None): The name of the setting.
        value: The new value.

    Returns:
        str: A message that says what changed, or why nothing changed.
    """
    if not key:
        return "Error updating setting: Key is required"
    if value is None or value == "":
        return "Error updating setting: Value is required"
    if not hasattr(app_settings, key):
        msg = "Error updating setting: Invalid key"
        msg += f" '{key}'! Valid values are {app_settings.as_dict().keys()}"
        return msg
    if key in SECRET_SETTINGS:
        return await _update_secret(key, str(value))
    setattr(app_settings, key, value)
    _new_value = getattr(app_settings, key, None)
    _name = key.replace("_", " ").title()
    return f"Setting {_name} updated to {_new_value}"


async def _update_secret(key: str, value: str) -> str:
    """Store a secret, after a check that it works.

    The API sends a secret masked, so the page shows something like
    `****99eb`. If the user saves the page without touching the field,
    that masked text comes back. Writing it would replace a working key
    with four stars and some digits, so a value that is the masked form of
    the stored value changes nothing.
    """
    value = value.strip()
    if value.startswith(MASK):
        return "The TMDB API key did not change."
    if key == "tmdb_api_key":
        message = await _validate_tmdb_key(value)
        if message:
            return message
    setattr(app_settings, key, value)
    _name = key.replace("_", " ").title()
    return f"Setting {_name} updated."


async def _validate_tmdb_key(value: str) -> str:
    """Ask TMDB whether the key works.

    Returns:
        str: An error message for the user, or an empty string when the
            key is good. A key that Trailarr cannot check, because TMDB is
            unreachable, is stored: the network is the problem, not the key.
    """
    try:
        await TMDBAPI(value).validate_key()
    except TMDBAuthError:
        return (
            "Error updating setting: TMDB refused that key. Check that you"
            " copied the whole key from your TMDB account."
        )
    except InvalidResponseError as e:
        logger.warning(
            f"Trailarr could not check the TMDB key, and stored it: {e}"
        )
    except Exception as e:
        logger.warning(
            f"Trailarr could not check the TMDB key, and stored it: {e}"
        )
    return ""


def update_login(
    current_password: str | None,
    new_username: str | None,
    new_password: str | None,
) -> str:
    """Change the web UI username, password, or both.

    The current password is always required. Give a new username, a new
    password, or both.

    Args:
        current_password (str | None): The password in use now.
        new_username (str | None): The username to set, if it changes.
        new_password (str | None): The password to set, if it changes.

    Returns:
        str: A message that says what changed, or why nothing changed.
    """
    # Current username and password are required
    if not current_password:
        return "Error updating login: Current password is required!"

    # Verify the current password
    if not auth.verify_password(current_password):
        return "Error updating login: Current password is incorrect!"

    # New username and password are optional, but at least one is required
    if new_username:
        # If only the new username is provided, set it
        if not new_password:
            return auth.set_username(new_username)
        # If both are provided, set both
        auth.set_username(new_username)
        auth.set_password(new_password)
        return "Username and password updated successfully"
    # If only the new password is provided, set it
    if new_password:
        return auth.set_password(new_password)
    # If neither is provided, return an error
    return "Error updating credentials: None were provided!"
