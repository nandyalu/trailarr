from typing import Annotated
from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from pydantic import BaseModel

from api.v1.authentication import (
    create_session,
    delete_session,
    validate_api_key_header,
    verify_login,
    verify_session,
)
from config.settings import app_settings

auth_router = APIRouter(prefix="/auth", tags=["Auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


def _set_session_cookie(token: str, response: Response) -> None:
    """Helper function to set the session cookie in the response. \n
    > **_Modifies the response in-place_**
    Args:
        token (str): The session token to set in the cookie
        response (Response): The FastAPI Response object to set the cookie on
    Returns:
        None
    """
    response.set_cookie(
        key="trailarr_session",
        value=token,
        path=app_settings.url_base or "/",
        samesite="lax",
        httponly=True,
    )


@auth_router.post(
    "/login",
    responses={
        200: {
            "description": "Login successful",
            "content": {"application/json": {"example": {"status": "ok"}}},
        },
        401: {
            "description": "Invalid credentials",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid credentials"}
                }
            },
        },
    },
)
async def login(
    request: LoginRequest,
    response: Response,
    header_api_key: str | None = Depends(validate_api_key_header),
) -> dict:
    """Authenticate with username/password and/or API key and    create a session. \n
    Sets a `trailarr_session` cookie on success. \n
    Args:
        request (LoginRequest): The username and password \n
    Returns:
        dict: Status message"""
    verify_login(request.username, request.password, header_api_key)
    token = create_session()
    _set_session_cookie(token, response)
    return {"status": "ok"}


@auth_router.post(
    "/logout",
    responses={
        200: {
            "description": "Logout successful",
            "content": {"application/json": {"example": {"status": "ok"}}},
        },
        401: {
            "description": "Not authenticated",
            "content": {
                "application/json": {
                    "example": {"detail": "Not authenticated"}
                }
            },
        },
    },
)
async def logout(
    response: Response,
    trailarr_session: Annotated[str | None, Cookie()] = None,
) -> dict:
    """Delete the current session and clear the session cookie. \n
    Args:
        trailarr_session (str | None): Session token from cookie \n
    Returns:
        dict: Status message"""
    if trailarr_session:
        delete_session(trailarr_session)
    response.delete_cookie(
        key="trailarr_session", path=app_settings.url_base or "/"
    )
    return {"status": "ok"}


@auth_router.get(
    "/status",
    responses={
        200: {
            "description": "Authentication status",
            "content": {
                "application/json": {"example": {"authenticated": True}}
            },
        },
        401: {
            "description": "Not authenticated",
            "content": {
                "application/json": {
                    "example": {"detail": "Not authenticated"}
                }
            },
        },
    },
)
async def auth_status(
    response: Response,
    header_api_key: str | None = Depends(validate_api_key_header),
    trailarr_session: Annotated[str | None, Cookie()] = None,
) -> dict:
    """Check whether the current session is valid. \n
    Args:
        response (Response): The FastAPI Response object to set the cookie on \n
        header_api_key (str | None): API key from header \n
        trailarr_session (str | None): Session token from cookie \n
    Returns:
        dict: Authentication status \n
    Raises:
        HTTPException: 401 if not authenticated"""
    if verify_session(trailarr_session):
        return {"authenticated": True}
    if header_api_key:
        token = create_session()
        _set_session_cookie(token, response)
        return {"authenticated": True}
    if app_settings.webui_disable_auth:
        token = create_session()
        _set_session_cookie(token, response)
        return {"authenticated": True}
    raise HTTPException(status_code=401, detail="Not authenticated")
