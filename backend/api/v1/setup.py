"""The first-run setup guide."""

from fastapi import APIRouter, status

from api.v1 import errors
from app_logger import ModuleLogger
from database.models.setup import SetupStatus
from services import setup as setup_service

logger = ModuleLogger("SetupAPI")

setup_router = APIRouter(prefix="/setup", tags=["Setup"])


@setup_router.get("/status")
async def get_setup_status() -> SetupStatus:
    """Whether this installation still needs the setup guide. \n
    Returns:
        SetupStatus: Whether the guide is needed, and the few numbers it
            shows: how many connections and media items exist, whether
            downloads are on, and whether a TMDB key is set.
    """
    return setup_service.status()


@setup_router.post("/complete", status_code=status.HTTP_200_OK)
async def complete_setup() -> SetupStatus:
    """Record that the setup guide is behind this installation. \n
    Sent when the user finishes the guide, and when they skip it. Both mean
    the same thing: do not show it again. \n
    Returns:
        SetupStatus: The state after the change.
    """
    try:
        return setup_service.complete()
    except Exception as e:
        raise errors.as_http_error(
            e, logger=logger, action="Complete the setup"
        )
