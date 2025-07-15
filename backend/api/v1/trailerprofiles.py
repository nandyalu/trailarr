import functools
from fastapi import APIRouter, HTTPException

from api.v1.models import UpdateSetting
from app_logger import ModuleLogger
from core.base.database.manager import trailerprofile
from core.base.database.models.trailerprofile import (
    TrailerProfileCreate,
    TrailerProfileRead,
)

logger = ModuleLogger("TrailerProfileAPI")

trailerprofiles_router = APIRouter(
    prefix="/trailerprofiles", tags=["Trailer Profiles"]
)


@trailerprofiles_router.get(
    "/",
    response_model=list[TrailerProfileRead],
    summary="Get all trailer profiles",
    description="Get all trailer profiles",
)
async def get_trailer_profiles() -> list[TrailerProfileRead]:
    """
    Get all trailer profiles.

    Returns:
        list[TrailerProfileRead]: List of trailer profiles.
    """
    return trailerprofile.get_trailerprofiles()


def handle_exceptions(func):
    """
    Decorator to handle exceptions for trailer profile endpoints.
    Logs the exception and raises HTTPException with a cleaned-up message.
    """

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(e)
            # Try to extract a user-friendly message, fallback to str(e)
            try:
                _msg = str(e).split("Value error, ")[1].split(" [")[0].strip()
            except Exception:
                _msg = str(e)
            raise HTTPException(status_code=400, detail=_msg)

    return wrapper


@trailerprofiles_router.post(
    "/",
    response_model=TrailerProfileRead,
    summary="Create a new trailer profile",
    description="Create a new trailer profile",
)
@handle_exceptions
async def create_trailer_profile(
    trailerprofile_create: TrailerProfileCreate,
) -> TrailerProfileRead:
    """
    Create a new trailer profile.
    Args:
        trailerprofile_create (TrailerProfileCreate): Trailer profile data to create.
    Returns:
        TrailerProfileRead: Created trailer profile.
    """
    return trailerprofile.create_trailerprofile(trailerprofile_create)


@trailerprofiles_router.get(
    "/{trailerprofile_id}",
    response_model=TrailerProfileRead,
    summary="Get a trailer profile by ID",
    description="Get a trailer profile by ID",
)
@handle_exceptions
async def get_trailer_profile(
    trailerprofile_id: int,
) -> TrailerProfileRead:
    """
    Get a trailer profile by ID.

    Args:
        trailerprofile_id (int): ID of the trailer profile.

    Returns:
        TrailerProfileRead: Trailer profile.
    """
    return trailerprofile.get_trailerprofile(trailerprofile_id)


@trailerprofiles_router.put(
    "/{trailerprofile_id}",
    response_model=TrailerProfileRead,
    summary="Update a trailer profile",
    description="Update a trailer profile",
)
@handle_exceptions
async def update_trailer_profile(
    trailerprofile_id: int,
    trailerprofile_update: TrailerProfileCreate,
) -> TrailerProfileRead:
    """
    Update a trailer profile by ID.
    Args:
        trailerprofile_id (int): ID of the trailer profile.
        trailerprofile_create (TrailerProfileCreate): Trailer profile data to update.
    Returns:
        TrailerProfileRead: Updated trailer profile.
    """
    return trailerprofile.update_trailerprofile(
        trailerprofile_id, trailerprofile_update
    )


@trailerprofiles_router.post(
    "/{trailerprofile_id}/setting",
    response_model=TrailerProfileRead,
    summary="Update a trailer profile setting",
    description="Update a trailer profile setting",
)
@handle_exceptions
async def update_trailer_profile_setting(
    trailerprofile_id: int, update: UpdateSetting
) -> TrailerProfileRead:
    """
    Update a trailer profile setting by ID.
    Args:
        trailerprofile_id (int): ID of the trailer profile.
        update (UpdateSetting): UpdateSetting model containing the key and value to update.
    Returns:
        TrailerProfileRead: Updated trailer profile.
    """
    return trailerprofile.update_trailerprofile_setting(
        trailerprofile_id, update.key, update.value
    )


@trailerprofiles_router.delete(
    "/{trailerprofile_id}",
    response_model=bool,
    summary="Delete a trailer profile",
    description="Delete a trailer profile",
)
@handle_exceptions
async def delete_trailer_profile(
    trailerprofile_id: int,
) -> bool:
    """
    Delete a trailer profile by ID.
    Args:
        trailerprofile_id (int): ID of the trailer profile.
    Returns:
        bool: True if the trailer profile was deleted successfully. \
            Raises HTTPException otherwise.
    """
    return trailerprofile.delete_trailerprofile(trailerprofile_id)
