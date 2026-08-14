import functools

from fastapi import APIRouter, HTTPException

from app_logger import ModuleLogger
from core.base.database.manager import customfilter
from core.base.database.models.customfilter import (
    CustomFilterCreate,
    CustomFilterRead,
)

logger = ModuleLogger("CustomFiltersAPI")

customfilters_router = APIRouter(
    prefix="/customfilters", tags=["Custom Filters"]
)


def handle_exceptions(func):
    """
    Decorator to handle exceptions for custom filter endpoints.
    Logs the exception and raises HTTPException with a cleaned-up message,
    so validation errors (e.g. a download filter on a Trailer Profile)
    reach the UI instead of a bare 500.
    """

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(e)
            # Try to extract a user-friendly message, fallback to str(e)
            try:
                _msg = str(e).split("Value error, ")[1].split(" [")[0].strip()
            except Exception:
                _msg = str(e)
            raise HTTPException(status_code=400, detail=_msg)

    return wrapper


@customfilters_router.get("/")
async def get_all_customfilters() -> list[CustomFilterRead]:
    return customfilter.get_all_customfilters()


@customfilters_router.post("/")
@handle_exceptions
async def create_or_update_customfilter(
    view_filter: CustomFilterCreate,
) -> CustomFilterRead:
    return customfilter.create_customfilter(view_filter)


@customfilters_router.put("/{id}")
@handle_exceptions
async def update_customfilter(
    id: int,
    view_filter: CustomFilterCreate,
) -> CustomFilterRead:
    return customfilter.update_customfilter(id, view_filter)


@customfilters_router.delete("/{id}")
async def delete_customfilter(id: int) -> bool:
    return customfilter.delete_customfilter(id)


@customfilters_router.get("/home")
async def get_home_customfilters() -> list[CustomFilterRead]:
    return customfilter.get_home_customfilters()


@customfilters_router.get("/movie")
async def get_movie_customfilters() -> list[CustomFilterRead]:
    return customfilter.get_movie_customfilters()


@customfilters_router.get("/series")
async def get_series_customfilters() -> list[CustomFilterRead]:
    return customfilter.get_series_customfilters()
