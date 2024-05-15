from fastapi import APIRouter, HTTPException, status

from api.v1.models import ErrorResponse
from core.sonarr.database_manager import SeriesDatabaseManager
from core.sonarr.models import SeriesRead


series_router = APIRouter(prefix="/series", tags=["Series"])


@series_router.get("/")
async def get_recent_series(limit: int = 30, offset: int = 0) -> list[SeriesRead]:
    db_handler = SeriesDatabaseManager()
    all_series = db_handler.read_recent(limit, offset)
    return all_series


@series_router.get(
    "/{series_id}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Series Not Found",
        }
    },
)
async def get_series_by_id(series_id: int) -> SeriesRead:
    db_handler = SeriesDatabaseManager()
    try:
        series = db_handler.read(series_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return series


@series_router.get("/search/{query}")
async def search_series(query: str) -> list[SeriesRead]:
    db_handler = SeriesDatabaseManager()
    series = db_handler.search(query)
    return series
