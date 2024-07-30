from typing import Annotated
from fastapi import Cookie, Depends, HTTPException
from fastapi.security import APIKeyHeader, APIKeyQuery

from config.settings import app_settings


# Dependency to validate the API key provided in the query or header
header_scheme = APIKeyHeader(name="X-API-KEY", auto_error=False)
query_schema = APIKeyQuery(name="api_key", auto_error=False)


def verify_api_key(api_key: str) -> bool:
    return api_key == app_settings.api_key


# Websockets does not support query parameters, so we need to validate the API key from the cookie
# Since websockets are only used for the frontend, we can use the cookie to validate the API key
# Dependency to validate the API key provided in the cookie
def validate_api_key_cookie(
    trailarr_api_key: Annotated[str | None, Cookie()] = None,
) -> bool:
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
