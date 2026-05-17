import functools

from fastapi import APIRouter, HTTPException

from api.v1.models import UpdateSetting
from app_logger import ModuleLogger
import db.repos.trailer_profile as trailer_profile_repo
import db.repos.media as media_repo
import db.repos.trailer_status as trailer_status_repo
from db.models.trailerprofile import TrailerProfileCreate, TrailerProfileRead
from utils.filters import matches_filters

logger = ModuleLogger("TrailerProfileAPI")

trailerprofiles_router = APIRouter(prefix="/trailerprofiles", tags=["Trailer Profiles"])


def _sync_status_rows(profile: TrailerProfileRead) -> None:
    """Create/delete MediaTrailerStatus rows to match the profile's current filters."""
    all_media = media_repo.read_all(movies_only=profile.for_movies)
    filters = profile.customfilter.filters

    matching = [m for m in all_media if matches_filters(m, filters)]
    non_matching_ids = [m.id for m in all_media if not matches_filters(m, filters)]

    if matching:
        created = trailer_status_repo.create_rows_for_profile(
            profile_id=profile.id,
            for_movies=profile.for_movies,
            max_count=profile.max_count,
            download_season_videos=profile.download_season_videos,
            media_list=matching,
        )
        if created:
            logger.info(f"Profile '{profile.customfilter.filter_name}': created {created} new MediaTrailerStatus row(s).")

    if non_matching_ids:
        deleted = trailer_status_repo.delete_undownloaded_rows_for_profile(
            profile_id=profile.id,
            media_ids=non_matching_ids,
        )
        if deleted:
            logger.info(f"Profile '{profile.customfilter.filter_name}': deleted {deleted} undownloaded row(s) for non-matching media.")


def _handle_exceptions(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(e)
            try:
                _msg = str(e).split("Value error, ")[1].split(" [")[0].strip()
            except Exception:
                _msg = str(e)
            raise HTTPException(status_code=400, detail=_msg)
    return wrapper


@trailerprofiles_router.get("/", response_model=list[TrailerProfileRead])
async def get_trailer_profiles() -> list[TrailerProfileRead]:
    return trailer_profile_repo.read_all()


@trailerprofiles_router.post("/", response_model=TrailerProfileRead)
@_handle_exceptions
async def create_trailer_profile(trailerprofile_create: TrailerProfileCreate) -> TrailerProfileRead:
    created_profile = trailer_profile_repo.create(trailerprofile_create)
    _sync_status_rows(created_profile)
    return created_profile


@trailerprofiles_router.get("/{trailerprofile_id}", response_model=TrailerProfileRead)
@_handle_exceptions
async def get_trailer_profile(trailerprofile_id: int) -> TrailerProfileRead:
    return trailer_profile_repo.read(trailerprofile_id)


@trailerprofiles_router.put("/{trailerprofile_id}", response_model=TrailerProfileRead)
@_handle_exceptions
async def update_trailer_profile(trailerprofile_id: int, trailerprofile_update: TrailerProfileCreate) -> TrailerProfileRead:
    updated_profile = trailer_profile_repo.update(trailerprofile_id, trailerprofile_update)
    _sync_status_rows(updated_profile)
    return updated_profile


@trailerprofiles_router.post("/{trailerprofile_id}/setting", response_model=TrailerProfileRead)
@_handle_exceptions
async def update_trailer_profile_setting(trailerprofile_id: int, update: UpdateSetting) -> TrailerProfileRead:
    updated_profile = trailer_profile_repo.update_setting(trailerprofile_id, update.key, update.value)
    _sync_status_rows(updated_profile)
    return updated_profile


@trailerprofiles_router.delete("/{trailerprofile_id}", response_model=bool)
@_handle_exceptions
async def delete_trailer_profile(trailerprofile_id: int) -> bool:
    return trailer_profile_repo.delete(trailerprofile_id)
