from fastapi import APIRouter

from core.base.database.manager import customfilter
from core.base.database.models.customfilter import (
    CustomFilterCreate,
    CustomFilterRead,
)

customfilters_router = APIRouter(
    prefix="/customfilters", tags=["Custom Filters"]
)


@customfilters_router.post("/")
async def create_or_update_customfilter(
    view_filter: CustomFilterCreate,
) -> CustomFilterRead:
    return customfilter.create_customfilter(view_filter)


@customfilters_router.put("/{id}")
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
