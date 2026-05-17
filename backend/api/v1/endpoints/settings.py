from fastapi import APIRouter

from api.v1.models import Settings, UpdateLogin, UpdateSetting
from api.v1 import deps
from config.settings import app_settings
from db.repos.stats import ServerStats, get_stats

settings_router = APIRouter(prefix="/settings", tags=["Settings"])


@settings_router.get("/")
async def get_settings() -> Settings:
    return Settings(**app_settings.as_dict())


@settings_router.get("/stats")
async def get_server_stats() -> ServerStats:
    return get_stats()


@settings_router.put("/update")
async def update_setting(update: UpdateSetting) -> str:
    if not update.key:
        return "Error updating setting: Key is required"
    if update.value is None or update.value == "":
        return "Error updating setting: Value is required"
    if not hasattr(app_settings, update.key):
        msg = f"Error updating setting: Invalid key '{update.key}'! Valid values are {app_settings.as_dict().keys()}"
        return msg
    setattr(app_settings, update.key, update.value)
    _new_value = getattr(app_settings, update.key, None)
    _name = update.key.replace("_", " ").title()
    return f"Setting {_name} updated to {_new_value}"


@settings_router.put("/updatelogin")
async def update_login(login: UpdateLogin) -> str:
    if not login.current_password:
        return "Error updating login: Current password is required!"
    if not deps.verify_password(login.current_password):
        return "Error updating login: Current password is incorrect!"
    if login.new_username:
        if not login.new_password:
            return deps.set_username(login.new_username)
        else:
            deps.set_username(login.new_username)
            deps.set_password(login.new_password)
            return "Username and password updated successfully"
    if login.new_password:
        return deps.set_password(login.new_password)
    return "Error updating credentials: None were provided!"
