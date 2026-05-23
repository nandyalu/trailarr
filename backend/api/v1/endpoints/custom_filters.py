from fastapi import APIRouter

import db.repos.custom_filter as custom_filter_repo
from db.models.customfilter import CustomFilterCreate, CustomFilterRead, FilterType

customfilters_router = APIRouter(prefix="/customfilters", tags=["Custom Filters"])


@customfilters_router.get("/")
async def get_all_customfilters() -> list[CustomFilterRead]:
    return custom_filter_repo.read_all()


@customfilters_router.post("/")
async def create_or_update_customfilter(view_filter: CustomFilterCreate) -> CustomFilterRead:
    return custom_filter_repo.create(view_filter)


@customfilters_router.put("/{id}")
async def update_customfilter(id: int, view_filter: CustomFilterCreate) -> CustomFilterRead:
    return custom_filter_repo.update(id, view_filter)


@customfilters_router.delete("/{id}")
async def delete_customfilter(id: int) -> bool:
    return custom_filter_repo.delete(id)


@customfilters_router.get("/home")
async def get_home_customfilters() -> list[CustomFilterRead]:
    return custom_filter_repo.read_by_type(FilterType.HOME)


@customfilters_router.get("/movie")
async def get_movie_customfilters() -> list[CustomFilterRead]:
    return custom_filter_repo.read_by_type(FilterType.MOVIE)


@customfilters_router.get("/series")
async def get_series_customfilters() -> list[CustomFilterRead]:
    return custom_filter_repo.read_by_type(FilterType.SERIES)
