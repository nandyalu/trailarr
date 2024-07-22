from fastapi import APIRouter

from api.v1.models import Settings, UpdateSetting
from config.settings import app_settings
from core.base.database.manager.general import GeneralDatabaseManager, ServerStats


settings_router = APIRouter(prefix="/settings", tags=["Settings"])


@settings_router.get("/")
async def get_settings() -> Settings:
    return Settings(**app_settings.as_dict())


@settings_router.get("/stats")
async def get_stats() -> ServerStats:
    return GeneralDatabaseManager().get_stats()


@settings_router.put("/update")
async def update_setting(update: UpdateSetting) -> str:
    if not update.key:
        return "Error updating setting: Key is required"
    if update.value is None or update.value == "":
        return "Error updating setting: Value is required"
    if not hasattr(app_settings, update.key):
        msg = "Error updating setting: Invalid key"
        msg += f" '{update.key}'! Valid values are {app_settings.as_dict().keys()}"
        return msg
    setattr(app_settings, update.key, update.value)
    _new_value = getattr(app_settings, update.key, None)
    _name = update.key.replace("_", " ").title()
    return f"Setting {_name} updated to {_new_value}"
