from typing import Annotated
import bcrypt
from fastapi import Cookie, Depends, HTTPException, status
from fastapi.security import (
    APIKeyHeader,
    APIKeyQuery,
    HTTPBasic,
    HTTPBasicCredentials,
)

from config.settings import app_settings

# Dependency to validate HTTP Basic Authentication in frontend
# auto_error=False allows bypassing auth when webui_disable_auth is True
browser_security = HTTPBasic(auto_error=False)


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


def validate_login(
    credentials: Annotated[
        HTTPBasicCredentials | None, Depends(browser_security)
    ] = None,
):
    """Validates the login credentials provided by the user \n
    Or bypasses auth if `webui_disable_auth` is True \n
    Args:
        credentials (HTTPBasicCredentials): The login credentials \n
    Raises:
        HTTPException: If the username or password is incorrect"""
    # For disabled auth, always return True
    if app_settings.webui_disable_auth:
        return True
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    is_correct_username = verify_username(credentials.username)
    is_correct_password = verify_password(credentials.password)
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return True


def logout_user() -> dict:
    """Force logout by returning a 401 response with WWW-Authenticate header.
    This clears browser's cached Basic Auth credentials.
    Returns:
        dict: Logout success message
    Raises:
        HTTPException: Always raises 401 to clear browser credentials
    """
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Logged out successfully. Please log in again.",
        headers={"WWW-Authenticate": 'Basic realm="Trailarr"'},
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


# Websockets does not support query parameters, so we need to validate the API key from the cookie
# Since websockets are only used for the frontend, we can use the cookie to validate the API key
# Dependency to validate the API key provided in the cookie
def validate_api_key_cookie(
    trailarr_api_key: Annotated[str | None, Cookie()] = None,
) -> bool:
    """Validates the API key provided in the cookie \n
    Args:
        trailarr_api_key (Annotated[str | None, Cookie]): The API key provided in the cookie \n
    Raises:
        HTTPException: If the API key is missing or invalid"""
    # Check if the API key is provide and valid
    if trailarr_api_key and verify_api_key(trailarr_api_key):
        return True
    # Raise an exception if the API key is missing
    raise HTTPException(status_code=401, detail="API key is missing")


# Dependency to validate the API key provided in the query/header/cookie
def validate_api_key(
    query_api_key: str | None = Depends(query_schema),
    header_api_key: str | None = Depends(header_scheme),
    trailarr_api_key: Annotated[str | None, Cookie()] = None,
) -> bool:
    """Validates the API key provided in the query, header or cookie \n
    Args:
        query_api_key (str | None): The API key provided in the query \n
        header_api_key (str | None): The API key provided in the header \n
        trailarr_api_key (Annotated[str | None, Cookie]): The API key provided in the cookie \n
    Raises:
        HTTPException: If the API key is missing or invalid"""
    _api_key = ""
    # Check if the API key is provided in query
    if query_api_key:
        _api_key = query_api_key
    # Check if the API key is provided in header
    if header_api_key:
        _api_key = header_api_key
    # Check if the API key is provided in cookie
    if trailarr_api_key:
        _api_key = trailarr_api_key
    # Check if the API key is valid
    if _api_key and verify_api_key(_api_key):
        return True
    # Raise an exception if the API key is missing
    raise HTTPException(status_code=401, detail="API key is missing")
