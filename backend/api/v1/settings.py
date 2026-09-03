"""Application settings and the web UI login."""

from fastapi import APIRouter

from api.v1.models import Settings, UpdateLogin, UpdateSetting
from config.settings import app_settings
from database.manager.general import ServerStats
from database.manager.general import get_stats as get_generic_stats
from services import settings as settings_service

settings_router = APIRouter(prefix="/settings", tags=["Settings"])


@settings_router.get("/")
async def get_settings() -> Settings:
    return Settings(**app_settings.as_dict())


@settings_router.get("/stats")
async def get_stats() -> ServerStats:
    return get_generic_stats()


@settings_router.put("/update")
async def update_setting(update: UpdateSetting) -> str:
    return settings_service.update_setting(update.key, update.value)


@settings_router.put("/updatelogin")
async def update_login(login: UpdateLogin) -> str:
    return settings_service.update_login(
        current_password=login.current_password,
        new_username=login.new_username,
        new_password=login.new_password,
    )
