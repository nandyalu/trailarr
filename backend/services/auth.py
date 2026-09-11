"""Sessions and credentials for the web UI.

This is the logic behind the login: the session store, password and username
hashing, and the API key check. It knows nothing about HTTP.

The FastAPI dependencies that turn these answers into 401 responses stay in
`api/v1/authentication.py`. Phase 7 Stage B made that split — this module
held both, so a service could not check a password without importing the api
layer.
"""

import secrets

import bcrypt

from config.settings import app_settings

# In-memory session store — cleared on app restart
_sessions: set[str] = set()


def create_session() -> str:
    token = secrets.token_hex(32)
    _sessions.add(token)
    return token


def get_session() -> str:
    """Returns the current session token if valid,
    otherwise creates a new one.
    > **Only used in status check endpoint when webui auth is disabled!** \n
    Returns:
        str: A valid session token
    """
    for token in _sessions:
        if verify_session(token):
            return token
    return create_session()


def delete_session(token: str) -> None:
    _sessions.discard(token)


def verify_session(token: str | None) -> bool:
    """Checks if the provided session token is valid \n
    Args:
        token (str | None): The session token to verify \n
    Returns:
        bool: True if the session token is valid, False otherwise"""
    return bool(token and token in _sessions)


# Hash a string using bcrypt
def get_string_hash(str_to_hash: str) -> bytes:
    """Converts the given string to bytes and hashes it using bcrypt \n
    Args:
        str_to_hash (str): The string to hash \n
    Returns:
        bytes: The hashed string as bytes"""
    pwd_bytes = str_to_hash.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password=pwd_bytes, salt=salt)
    return hashed_password


def set_username(new_username: str) -> str:
    """Sets the new username for the webui \n
    Args:
        new_username (str): The new username to set \n
    Returns:
        str: The result message"""
    app_settings.webui_username = new_username
    return "Username updated successfully"


def set_password(new_password: str) -> str:
    """Sets the new password for the webui \n
    Args:
        new_password (str): The new password to set \n
    Returns:
        str: The result message"""
    app_settings.webui_password = get_string_hash(new_password).decode("utf-8")
    return "Password updated successfully"


# Check if the provided username matches the stored username (hashed)
def verify_username(plain_username: str) -> bool:
    """Checks if the provided username matches the stored username \n
    Args:
        plain_username (str): The username to check \n
    Returns:
        bool: True if the username matches, False otherwise"""
    username_byte_enc = plain_username.encode("utf-8")
    curr_username_hashed = get_string_hash(app_settings.webui_username)
    return bcrypt.checkpw(
        password=username_byte_enc, hashed_password=curr_username_hashed
    )


# Check if the provided password matches the stored password (hashed)
def verify_password(plain_password: str) -> bool:
    """Checks if the provided password matches the stored password (hashed) \n
    Args:
        plain_password (str): The password to check \n
    Returns:
        bool: True if the password matches, False otherwise"""
    password_byte_enc = plain_password.encode("utf-8")
    hashed_password = app_settings.webui_password.encode("utf-8")
    return bcrypt.checkpw(
        password=password_byte_enc, hashed_password=hashed_password
    )


def verify_api_key(api_key: str) -> bool:
    """Verifies the API key provided by the user \n
    Args:
        api_key (str): The API key to verify \n
    Returns:
        bool: True if the API key is valid, False otherwise"""
    return api_key == app_settings.api_key

