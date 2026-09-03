"""Changing application settings and the web UI login.

Both functions give back a message for the user rather than raising. The
API returns that message with a 200, which is the contract the frontend
expects — do not change it to an HTTP error without changing the frontend
and the OpenAPI spec together.
"""

from config.settings import app_settings
from services import auth


def update_setting(key: str | None, value) -> str:
    """Change one application setting.

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
    setattr(app_settings, key, value)
    _new_value = getattr(app_settings, key, None)
    _name = key.replace("_", " ").title()
    return f"Setting {_name} updated to {_new_value}"


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
