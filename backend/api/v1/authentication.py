import hashlib
from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader, APIKeyQuery

from config.settings import app_settings

# DEFAULT APP USER CREDENTIALS
APP_USERNAME = "admin"
APP_PASSWORD = "trailarr"
# TODO: Figure out a way to make this changeable from the environment variables
# and make frontend use it for login


def hash_password(password: str) -> str:
    """Returns the MD5 hash of the provided string."""
    return hashlib.md5(password.encode()).hexdigest()


def verify_password(provided_password: str) -> bool:
    """Verify the provided password with the app's password."""
    hashed_password = hash_password(provided_password)
    _saved_password = hash_password(APP_PASSWORD)
    return hashed_password == _saved_password


def authenticate_user(username: str, password: str):
    """Authenticate the user with the provided credentials."""
    if not username or username != APP_USERNAME:
        return ""
    if not password:
        return ""
    if not verify_password(password):
        return ""
    return app_settings.api_key


# Dependency to validate the API key provided in the query or header
header_scheme = APIKeyHeader(name="X-API-KEY", auto_error=False)
query_schema = APIKeyQuery(name="api_key", auto_error=False)


def validate_api_key(
    api_key: str | None = Depends(query_schema),
    x_api_key: str | None = Depends(header_scheme),
) -> bool:
    # Check if the API key is provided in query and matches the app's API key
    if api_key and api_key == app_settings.api_key:
        return True
    # Check if the API key is provided in header and matches the app's API key
    if x_api_key and x_api_key == app_settings.api_key:
        return True
    # Raise an exception if the API key is missing
    raise HTTPException(status_code=401, detail="API key is missing")
