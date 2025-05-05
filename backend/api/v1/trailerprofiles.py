from fastapi import APIRouter, HTTPException

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


@trailerprofiles_router.post(
    "/",
    response_model=TrailerProfileRead,
    summary="Create a new trailer profile",
    description="Create a new trailer profile",
)
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
    try:
        return trailerprofile.create_trailerprofile(trailerprofile_create)
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=400, detail=str(e))


@trailerprofiles_router.get(
    "/{trailerprofile_id}",
    response_model=TrailerProfileRead,
    summary="Get a trailer profile by ID",
    description="Get a trailer profile by ID",
)
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
    try:
        return trailerprofile.get_trailerprofile(trailerprofile_id)
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=404, detail=e)


@trailerprofiles_router.put(
    "/{trailerprofile_id}",
    response_model=TrailerProfileRead,
    summary="Update a trailer profile",
    description="Update a trailer profile",
)
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
    try:
        return trailerprofile.update_trailerprofile(
            trailerprofile_id, trailerprofile_update
        )
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=400, detail=e)


@trailerprofiles_router.post(
    "/{trailerprofile_id}/setting",
    response_model=TrailerProfileRead,
    summary="Update a trailer profile setting",
    description="Update a trailer profile setting",
)
async def update_trailer_profile_setting(
    trailerprofile_id: int,
    setting: str,
    value: str | int | bool,
) -> TrailerProfileRead:
    """
    Update a trailer profile setting by ID.
    Args:
        trailerprofile_id (int): ID of the trailer profile.
        setting (str): Setting name to update.
        value (str | int | bool): New value for the setting.
    Returns:
        TrailerProfileRead: Updated trailer profile.
    """
    try:
        return trailerprofile.update_trailerprofile_setting(
            trailerprofile_id, setting, value
        )
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=400, detail=e)


@trailerprofiles_router.delete(
    "/{trailerprofile_id}",
    response_model=bool,
    summary="Delete a trailer profile",
    description="Delete a trailer profile",
)
async def delete_trailer_profile(
    trailerprofile_id: int,
) -> bool:
    """
    Delete a trailer profile by ID.
    Args:
        trailerprofile_id (int): ID of the trailer profile.
    Returns:
        bool: True if the trailer profile was deleted successfully, False otherwise.
    """
    try:
        return trailerprofile.delete_trailerprofile(trailerprofile_id)
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=404, detail=e)
