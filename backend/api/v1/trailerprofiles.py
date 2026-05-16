import functools
from fastapi import APIRouter, HTTPException

from api.v1.models import UpdateSetting
from app_logger import ModuleLogger
from core.base.database.manager import trailerprofile
import core.base.database.manager.media as media_manager
import core.base.database.manager.trailerstatusmanager as trailer_status_manager
from core.base.database.models.trailerprofile import (
    TrailerProfileCreate,
    TrailerProfileRead,
)
from core.base.utils.filters import matches_filters

logger = ModuleLogger("TrailerProfileAPI")


def _sync_status_rows(profile: TrailerProfileRead) -> None:
    """Create/delete MediaTrailerStatus rows so they match the profile's current filters.

    - Matching media (passes filter + correct for_movies type): create PENDING rows if
      they don't already exist (idempotent; never overwrites UNMONITORED).
    - Non-matching media: delete rows that have no linked download.

    Called after every profile create, update, or setting change.
    """
    all_media = media_manager.read_all(movies_only=profile.for_movies)
    filters = profile.customfilter.filters

    matching = [m for m in all_media if matches_filters(m, filters)]
    non_matching_ids = [m.id for m in all_media if not matches_filters(m, filters)]

    if matching:
        created = trailer_status_manager.create_rows_for_profile(
            profile_id=profile.id,
            for_movies=profile.for_movies,
            max_count=profile.max_count,
            download_season_videos=profile.download_season_videos,
            media_list=matching,
        )
        if created:
            logger.info(
                f"Profile '{profile.customfilter.filter_name}': created"
                f" {created} new MediaTrailerStatus row(s)."
            )

    if non_matching_ids:
        deleted = trailer_status_manager.delete_undownloaded_rows_for_profile(
            profile_id=profile.id,
            media_ids=non_matching_ids,
        )
        if deleted:
            logger.info(
                f"Profile '{profile.customfilter.filter_name}': deleted"
                f" {deleted} undownloaded row(s) for non-matching media."
            )

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
    created_profile = trailerprofile.create_trailerprofile(trailerprofile_create)
    _sync_status_rows(created_profile)
    return created_profile


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
    updated_profile = trailerprofile.update_trailerprofile(
        trailerprofile_id, trailerprofile_update
    )
    _sync_status_rows(updated_profile)
    return updated_profile


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
    updated_profile = trailerprofile.update_trailerprofile_setting(
        trailerprofile_id, update.key, update.value
    )
    _sync_status_rows(updated_profile)
    return updated_profile


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
