"""
Plex API endpoints.

Provides REST API endpoints for Plex integration functionality.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any, Optional

from core.plex.auth import start_auth_flow, poll_for_token
from core.plex.scan import trigger_media_scan
from core.plex.extras import check_for_extras
from api.v1.models import ErrorResponse
import logging

logging = logging.getLogger("PlexAPI")

plex_router = APIRouter(prefix="/plex", tags=["Plex Integration"])


# Request/Response models
class AuthStartRequest(BaseModel):
    client_identifier: str
    product_name: str


class AuthStartResponse(BaseModel):
    pin: str
    auth_url: str
    expires_in: str


class AuthPollResponse(BaseModel):
    status: str  # "pending", "success", or "expired"
    token: Optional[str] = None
    plex_server_address: Optional[str] = None


class ScanRequest(BaseModel):
    token: str
    server_address: str
    media_folder_path: str


class ScanResponse(BaseModel):
    success: bool
    message: str


class ExtrasRequest(BaseModel):
    token: str
    server_address: str
    media_type: str  # "movie" or "show"
    tmdb_id: Optional[str] = None
    tvdb_id: Optional[str] = None


class ExtraDetail(BaseModel):
    title: str
    type: str
    duration: int


class ExtrasResponse(BaseModel):
    has_extras: bool
    extras: list[ExtraDetail]
    message: str


@plex_router.post(
    "/auth/start",
    status_code=status.HTTP_200_OK,
    response_model=AuthStartResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": "Failed to start authentication flow",
        },
    },
)
async def start_plex_auth(request: AuthStartRequest) -> AuthStartResponse:
    """
    Start the Plex authentication flow.
    
    Generates a PIN and auth URL for the user to authenticate with Plex.
    """
    try:
        logging.info(f"Starting Plex auth for client: {request.client_identifier}")
        result = await start_auth_flow(request.client_identifier, request.product_name)
        return AuthStartResponse(**result)
    except Exception as e:
        logging.error(f"Failed to start Plex auth: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@plex_router.get(
    "/auth/poll/{pin}",
    status_code=status.HTTP_200_OK,
    response_model=AuthPollResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": "Failed to poll for token",
        },
    },
)
async def poll_plex_token(pin: str) -> AuthPollResponse:
    """
    Poll for Plex authentication token.
    
    Checks if the user has completed authentication for the given PIN.
    """
    try:
        logging.debug(f"Polling Plex token for PIN: {pin}")
        result = await poll_for_token(pin)
        return AuthPollResponse(**result)
    except Exception as e:
        logging.error(f"Failed to poll Plex token: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@plex_router.post(
    "/scan",
    status_code=status.HTTP_200_OK,
    response_model=ScanResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": "Failed to trigger media scan",
        },
    },
)
async def trigger_plex_scan(request: ScanRequest) -> ScanResponse:
    """
    Trigger a media library scan on Plex server.
    
    Initiates a scan of the specified media folder path.
    """
    try:
        logging.info(f"Triggering Plex scan for: {request.media_folder_path}")
        result = await trigger_media_scan(
            request.token,
            request.server_address,
            request.media_folder_path
        )
        return ScanResponse(**result)
    except Exception as e:
        logging.error(f"Failed to trigger Plex scan: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@plex_router.post(
    "/extras",
    status_code=status.HTTP_200_OK,
    response_model=ExtrasResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": "Failed to check for extras",
        },
    },
)
async def check_plex_extras(request: ExtrasRequest) -> ExtrasResponse:
    """
    Check for media extras in Plex library.
    
    Searches for extras (trailers, behind-the-scenes, etc.) for the specified media item.
    """
    try:
        logging.info(f"Checking Plex extras for {request.media_type} - TMDB: {request.tmdb_id}, TVDB: {request.tvdb_id}")
        result = await check_for_extras(
            request.token,
            request.server_address,
            request.media_type,
            request.tmdb_id,
            request.tvdb_id
        )
        
        # Convert extras to the response model
        extras = [
            ExtraDetail(
                title=extra["title"],
                type=extra["type"],
                duration=extra["duration"]
            )
            for extra in result["extras"]
        ]
        
        return ExtrasResponse(
            has_extras=result["has_extras"],
            extras=extras,
            message=result["message"]
        )
    except Exception as e:
        logging.error(f"Failed to check Plex extras: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )