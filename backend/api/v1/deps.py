import secrets
from typing import Annotated

import bcrypt
from fastapi import Cookie, Depends, HTTPException
from fastapi.security import APIKeyHeader, APIKeyQuery

from config.settings import app_settings

# In-memory session store — cleared on app restart
_sessions: set[str] = set()


def create_session() -> str:
    token = secrets.token_hex(32)
    _sessions.add(token)
    return token


def delete_session(token: str) -> None:
    _sessions.discard(token)


def _is_valid_session(token: str | None) -> bool:
    return bool(token and token in _sessions)


def get_string_hash(str_to_hash: str) -> bytes:
    pwd_bytes = str_to_hash.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password=pwd_bytes, salt=salt)


def set_username(new_username: str) -> str:
    app_settings.webui_username = new_username
    return "Username updated successfully"


def set_password(new_password: str) -> str:
    app_settings.webui_password = get_string_hash(new_password).decode("utf-8")
    return "Password updated successfully"


def verify_username(plain_username: str) -> bool:
    username_byte_enc = plain_username.encode("utf-8")
    curr_username_hashed = get_string_hash(app_settings.webui_username)
    return bcrypt.checkpw(password=username_byte_enc, hashed_password=curr_username_hashed)


def verify_password(plain_password: str) -> bool:
    password_byte_enc = plain_password.encode("utf-8")
    hashed_password = app_settings.webui_password.encode("utf-8")
    return bcrypt.checkpw(password=password_byte_enc, hashed_password=hashed_password)


header_scheme = APIKeyHeader(name="X-API-KEY", auto_error=False)
query_schema = APIKeyQuery(name="api_key", auto_error=False)


def verify_api_key(api_key: str) -> bool:
    return api_key == app_settings.api_key


def verify_login(username: str, password: str, valid_api_key: str | None) -> None:
    if not valid_api_key:
        if not (verify_username(username) and verify_password(password)):
            raise HTTPException(status_code=401, detail="Invalid credentials")


def validate_api_key_header(
    header_api_key: str | None = Depends(header_scheme),
) -> str | None:
    if header_api_key and verify_api_key(header_api_key):
        return header_api_key
    return None


def validate_api_key_cookie(
    trailarr_api_key: Annotated[str | None, Cookie()] = None,
    trailarr_session: Annotated[str | None, Cookie()] = None,
) -> bool:
    if _is_valid_session(trailarr_session):
        return True
    if trailarr_api_key and verify_api_key(trailarr_api_key):
        return True
    raise HTTPException(status_code=401, detail="Not authenticated")


def validate_api_key(
    query_api_key: str | None = Depends(query_schema),
    header_api_key: str | None = Depends(header_scheme),
    trailarr_api_key: Annotated[str | None, Cookie()] = None,
    trailarr_session: Annotated[str | None, Cookie()] = None,
) -> bool:
    if _is_valid_session(trailarr_session):
        return True
    _api_key = query_api_key or header_api_key or trailarr_api_key or ""
    if _api_key and verify_api_key(_api_key):
        return True
    raise HTTPException(status_code=401, detail="Authentication required")
