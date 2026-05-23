import functools

from fastapi import APIRouter, HTTPException

from api.v1.models import UpdateSetting
from app_logger import ModuleLogger
import db.repos.trailer_profile as trailer_profile_repo
import services.trailer_profile_service as trailer_profile_service
from db.models.trailerprofile import TrailerProfileCreate, TrailerProfileRead

logger = ModuleLogger("TrailerProfileAPI")

trailerprofiles_router = APIRouter(prefix="/trailerprofiles", tags=["Trailer Profiles"])


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
    return trailer_profile_service.create(trailerprofile_create)


@trailerprofiles_router.get("/{trailerprofile_id}", response_model=TrailerProfileRead)
@_handle_exceptions
async def get_trailer_profile(trailerprofile_id: int) -> TrailerProfileRead:
    return trailer_profile_repo.read(trailerprofile_id)


@trailerprofiles_router.put("/{trailerprofile_id}", response_model=TrailerProfileRead)
@_handle_exceptions
async def update_trailer_profile(trailerprofile_id: int, trailerprofile_update: TrailerProfileCreate) -> TrailerProfileRead:
    return trailer_profile_service.update(trailerprofile_id, trailerprofile_update)


@trailerprofiles_router.post("/{trailerprofile_id}/setting", response_model=TrailerProfileRead)
@_handle_exceptions
async def update_trailer_profile_setting(trailerprofile_id: int, update: UpdateSetting) -> TrailerProfileRead:
    return trailer_profile_service.update_setting(trailerprofile_id, update.key, update.value)


@trailerprofiles_router.delete("/{trailerprofile_id}", response_model=bool)
@_handle_exceptions
async def delete_trailer_profile(trailerprofile_id: int) -> bool:
    return trailer_profile_repo.delete(trailerprofile_id)
