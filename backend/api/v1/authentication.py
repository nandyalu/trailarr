import secrets
from typing import Annotated
import bcrypt
from fastapi import Cookie, Depends, HTTPException, status
from fastapi.security import APIKeyHeader, APIKeyQuery, HTTPBasic, HTTPBasicCredentials

from config.settings import app_settings

# Dependency to validate HHTP Basic Authentication in frontend
browser_security = HTTPBasic()


# Hash a password using bcrypt
def get_password_hash(password: str) -> bytes:
    """Converts the password to bytes and hashes it using bcrypt \n
    Args:
        password (str): The password to hash \n
    Returns:
        bytes: The hashed password as bytes"""
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password=pwd_bytes, salt=salt)
    return hashed_password


def set_password(new_password: str) -> str:
    """Sets the new password for the webui \n
    Args:
        new_password (str): The new password to set \n
    Returns:
        str: The result message"""
    app_settings.webui_password = get_password_hash(new_password).decode("utf-8")
    return "Password updated successfully"


# Check if the provided password matches the stored password (hashed)
def verify_password(plain_password: str) -> bool:
    """Checks if the provided password matches the stored password (hashed) \n
    Args:
        plain_password (str): The password to check \n
    Returns:
        bool: True if the password matches, False otherwise"""
    password_byte_enc = plain_password.encode("utf-8")
    hashed_password = app_settings.webui_password.encode("utf-8")
    return bcrypt.checkpw(password=password_byte_enc, hashed_password=hashed_password)


def validate_login(
    credentials: Annotated[HTTPBasicCredentials, Depends(browser_security)],
):
    """Validates the login credentials provided by the user \n
    Args:
        credentials (HTTPBasicCredentials): The login credentials \n
    Raises:
        HTTPException: If the username or password is incorrect"""
    current_username_bytes = credentials.username.encode("utf8")
    correct_username_bytes = b"admin"
    is_correct_username = secrets.compare_digest(
        current_username_bytes, correct_username_bytes
    )
    is_correct_password = verify_password(credentials.password)
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return True


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
