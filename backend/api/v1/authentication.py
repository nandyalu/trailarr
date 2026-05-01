import secrets
from typing import Annotated
import bcrypt
from fastapi import Cookie, Depends, HTTPException
from fastapi.security import (
    APIKeyHeader,
    APIKeyQuery,
)

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
        if _is_valid_session(token):
            return token
    return create_session()


def delete_session(token: str) -> None:
    _sessions.discard(token)


def _is_valid_session(token: str | None) -> bool:
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


# Dependency to validate the API key provided in the query or header
header_scheme = APIKeyHeader(name="X-API-KEY", auto_error=False)
query_schema = APIKeyQuery(name="api_key", auto_error=False)


def verify_api_key(api_key: str) -> bool:
    """Verifies the API key provided by the user \n
    Args:
        api_key (str): The API key to verify \n
    Returns:
        bool: True if the API key is valid, False otherwise"""
    return api_key == app_settings.api_key


# Dependency to validate the API key provided in the cookie, or a valid session token.
# Used for WebSocket connections (which can only send cookies, not headers).
def validate_api_key_cookie(
    trailarr_api_key: Annotated[str | None, Cookie()] = None,
    trailarr_session: Annotated[str | None, Cookie()] = None,
) -> bool:
    """Validates the session token or API key provided in cookies \n
    Args:
        trailarr_api_key (str | None): Legacy API key cookie \n
        trailarr_session (str | None): Session token cookie \n
    Raises:
        HTTPException: If neither a valid session nor API key is present"""
    if _is_valid_session(trailarr_session):
        return True
    if trailarr_api_key and verify_api_key(trailarr_api_key):
        return True
    raise HTTPException(status_code=401, detail="Not authenticated")


# Dependency to validate the API key provided in the query/header/cookie,
# or a valid session token (for frontend requests).
def validate_api_key(
    query_api_key: str | None = Depends(query_schema),
    header_api_key: str | None = Depends(header_scheme),
    trailarr_api_key: Annotated[str | None, Cookie()] = None,
    trailarr_session: Annotated[str | None, Cookie()] = None,
) -> bool:
    """Validates the API key or session token \n
    Accepts: session cookie (frontend), API key in header, query, or cookie \n
    Args:
        query_api_key (str | None): The API key provided in the query \n
        header_api_key (str | None): The API key provided in the header \n
        trailarr_api_key (str | None): Legacy API key cookie \n
        trailarr_session (str | None): Session token cookie \n
    Raises:
        HTTPException: If authentication fails"""
    if _is_valid_session(trailarr_session):
        return True
    _api_key = query_api_key or header_api_key or trailarr_api_key or ""
    if _api_key and verify_api_key(_api_key):
        return True
    raise HTTPException(status_code=401, detail="Authentication required")
