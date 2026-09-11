"""FastAPI dependencies that guard the API.

These turn the answers from `services/auth.py` into 401 responses. The
session store, hashing and credential checks live there; this module only
reads the request and decides whether to let it through.

The names below are re-exported so that `api.v1.authentication.verify_password`
and friends keep working for existing callers.
"""

from typing import Annotated

from fastapi import Cookie, Depends, HTTPException
from fastapi.security import (
    APIKeyHeader,
    APIKeyQuery,
)

from services.auth import (  # noqa: F401 — re-exported for existing callers
    create_session,
    delete_session,
    get_session,
    get_string_hash,
    set_password,
    set_username,
    verify_api_key,
    verify_password,
    verify_session,
    verify_username,
)


def verify_login(
    username: str, password: str, valid_api_key: str | None
) -> None:
    """Verifies the login credentials or API key \n
    Args:
        username (str): The username to verify \n
        password (str): The password to verify \n
        valid_api_key (str | None): The valid API key, if provided \n
    Raises:
        HTTPException: If the credentials are invalid"""
    if not valid_api_key:
        if not (verify_username(username) and verify_password(password)):
            raise HTTPException(status_code=401, detail="Invalid credentials")


# Dependency to validate the API key provided in the query or header
header_scheme = APIKeyHeader(name="X-API-KEY", auto_error=False)
query_schema = APIKeyQuery(name="api_key", auto_error=False)


# Dependency to validate the API key provided in the header.
# Used for endpoints that want to optionally accept an API key (e.g., reverse
# proxy auth), without raising if the header is missing/invalid.
def validate_api_key_header(
    header_api_key: str | None = Depends(header_scheme),
) -> str | None:
    """Validates the API key provided in the header \n
    Args:
        header_api_key (str | None): The API key provided in the header \n
    Returns:
        str | None: The valid API key if provided, otherwise None"""
    if header_api_key and verify_api_key(header_api_key):
        return header_api_key
    return None


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
    if verify_session(trailarr_session):
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
    if verify_session(trailarr_session):
        return True
    _api_key = query_api_key or header_api_key or trailarr_api_key or ""
    if _api_key and verify_api_key(_api_key):
        return True
    raise HTTPException(status_code=401, detail="Authentication required")
