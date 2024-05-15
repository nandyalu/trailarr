from fastapi import APIRouter, HTTPException, status

from api.v1.models import ErrorResponse
from core.radarr.database_manager import MovieDatabaseManager
from core.radarr.models import MovieRead


movies_router = APIRouter(prefix="/movies", tags=["Movies"])


@movies_router.get("/")
async def get_recent_movies(limit: int = 30, offset: int = 0) -> list[MovieRead]:
    db_handler = MovieDatabaseManager()
    movies = db_handler.read_recent(limit, offset)
    return movies


@movies_router.get(
    "/{movie_id}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Movie Not Found",
        }
    },
)
async def get_movie_by_id(movie_id: int) -> MovieRead:
    db_handler = MovieDatabaseManager()
    try:
        movie = db_handler.read(movie_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return movie


@movies_router.get("/search/{query}")
async def search_movies(query: str) -> list[MovieRead]:
    db_handler = MovieDatabaseManager()
    movies = db_handler.search(query)
    return movies
