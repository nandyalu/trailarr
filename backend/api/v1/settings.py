from fastapi import APIRouter

from api.v1.models import Settings, UpdateLogin, UpdateSetting
from api.v1 import authentication
from config.settings import app_settings
from core.base.database.manager.general import ServerStats
from core.base.database.manager.general import get_stats as get_generic_stats

settings_router = APIRouter(prefix="/settings", tags=["Settings"])


@settings_router.get("/")
async def get_settings() -> Settings:
    return Settings(**app_settings.as_dict())


@settings_router.get("/stats")
async def get_stats() -> ServerStats:
    return get_generic_stats()


@settings_router.put("/update")
async def update_setting(update: UpdateSetting) -> str:
    if not update.key:
        return "Error updating setting: Key is required"
    if update.value is None or update.value == "":
        return "Error updating setting: Value is required"
    if not hasattr(app_settings, update.key):
        msg = "Error updating setting: Invalid key"
        msg += (
            f" '{update.key}'! Valid values are"
            f" {app_settings.as_dict().keys()}"
        )
        return msg
    setattr(app_settings, update.key, update.value)
    _new_value = getattr(app_settings, update.key, None)
    _name = update.key.replace("_", " ").title()
    return f"Setting {_name} updated to {_new_value}"


@settings_router.put("/updatelogin")
async def update_login(login: UpdateLogin) -> str:
    # Current username and password are required
    if not login.current_password:
        return "Error updating login: Current password is required!"

    # Verify the current password
    if not authentication.verify_password(login.current_password):
        return "Error updating login: Current password is incorrect!"

    # New username and password are optional, but at least one is required
    if login.new_username:
        # If only the new username is provided, set it
        if not login.new_password:
            return authentication.set_username(login.new_username)
        else:
            # If both are provided, set both
            authentication.set_username(login.new_username)
            authentication.set_password(login.new_password)
            return "Username and password updated successfully"
    # If only the new password is provided, set it
    if login.new_password:
        return authentication.set_password(login.new_password)
    # If neither is provided, return an error
    return "Error updating credentials: None were provided!"
