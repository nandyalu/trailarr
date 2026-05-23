from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from pydantic import BaseModel

from api.v1.deps import (
    _is_valid_session,
    create_session,
    delete_session,
    validate_api_key_header,
    verify_login,
)
from config.settings import app_settings

auth_router = APIRouter(prefix="/auth", tags=["Auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


def _set_session_cookie(token: str, response: Response) -> None:
    response.set_cookie(
        key="trailarr_session",
        value=token,
        path=app_settings.url_base or "/",
        samesite="lax",
        httponly=True,
    )


@auth_router.post("/login")
async def login(
    request: LoginRequest,
    response: Response,
    header_api_key: str | None = Depends(validate_api_key_header),
) -> dict:
    verify_login(request.username, request.password, header_api_key)
    token = create_session()
    _set_session_cookie(token, response)
    return {"status": "ok"}


@auth_router.post("/logout")
async def logout(
    response: Response,
    trailarr_session: Annotated[str | None, Cookie()] = None,
) -> dict:
    if trailarr_session:
        delete_session(trailarr_session)
    response.delete_cookie(key="trailarr_session", path=app_settings.url_base or "/")
    return {"status": "ok"}


@auth_router.get("/status")
async def auth_status(
    response: Response,
    header_api_key: str | None = Depends(validate_api_key_header),
    trailarr_session: Annotated[str | None, Cookie()] = None,
) -> dict:
    if _is_valid_session(trailarr_session):
        return {"authenticated": True}
    if header_api_key:
        token = create_session()
        _set_session_cookie(token, response)
        return {"authenticated": True}
    raise HTTPException(status_code=401, detail="Not authenticated")
