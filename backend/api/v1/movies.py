import logging

from fastapi import APIRouter, HTTPException, status

from api.v1 import websockets
from api.v1.models import ErrorResponse
from core.base.database.manager.base import MediaDatabaseManager
from core.base.database.models.media import MediaRead, MediaUpdate
from core.files_handler import FilesHandler, FolderInfo
from core.tasks.download_trailers import download_trailer_by_id


movies_router = APIRouter(prefix="/movies", tags=["Movies"])


@movies_router.get("/")
async def get_recent_movies(limit: int = 30, offset: int = 0) -> list[MediaRead]:
    db_handler = MediaDatabaseManager()
    movies = db_handler.read_recent(limit, offset)
    return movies


@movies_router.get("/downloaded")
async def get_recently_download(limit: int = 30, offset: int = 0) -> list[MediaRead]:
    db_handler = MediaDatabaseManager()
    media_list = db_handler.read_recently_downloaded(limit, offset)
    return media_list


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
async def get_movie_by_id(movie_id: int) -> MediaRead:
    db_handler = MediaDatabaseManager()
    try:
        movie = db_handler.read(movie_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return movie


@movies_router.get(
    "/{movie_id}/files",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Movie Not Found",
        }
    },
)
async def get_movie_files(movie_id: int) -> FolderInfo | str:
    db_handler = MediaDatabaseManager()
    try:
        movie = db_handler.read(movie_id)
        if not movie.folder_path:
            return "Movie has no folder path!"
        files_handler = FilesHandler()
        files = await files_handler.get_folder_files(movie.folder_path)
        if not files:
            return "No files found in movie folder!"
        return files
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@movies_router.post(
    "/{movie_id}/download",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Movie Not Found",
        }
    },
)
async def download_movie_trailer(movie_id: int, yt_id: str = "") -> str:
    msg = f"Downloading trailer for movie with ID: {movie_id}"
    if yt_id:
        msg += f" from [{yt_id}]"
    logging.info(msg)
    return download_trailer_by_id(movie_id, is_movie=True, yt_id=yt_id)


@movies_router.post(
    "/{movie_id}/monitor",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Movie Not Found",
        }
    },
)
async def monitor_movie(movie_id: int, monitor: bool = True) -> str:
    logging.info(f"Monitoring movie with ID: {movie_id}")
    db_handler = MediaDatabaseManager()
    try:
        movie = db_handler.read(movie_id)
        if movie.trailer_exists and monitor:
            msg = f"Movie '{movie.title}' [{movie.id}] already has a trailer!"
            await websockets.ws_manager.broadcast(msg, "Error")
            return msg
        movie_update = MediaUpdate(monitor=monitor)
        db_handler.update(movie_id, movie_update)
        if monitor:
            msg = f"Movie '{movie.title}' [{movie.id}] is now monitored"
        else:
            msg = f"Movie '{movie.title}' [{movie.id}] is no longer monitored"
        logging.info(msg)
        await websockets.ws_manager.broadcast(msg, "Success")
        return msg
    except Exception as e:
        await websockets.ws_manager.broadcast("Error changing Monitor status!", "Error")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@movies_router.delete(
    "/{movie_id}/trailer",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Movie Not Found",
        }
    },
)
async def delete_movie_trailer(movie_id: int) -> str:
    logging.info(f"Deleting trailer for movie with ID: {movie_id}")
    db_handler = MediaDatabaseManager()
    try:
        movie = db_handler.read(movie_id)
        if not movie.trailer_exists:
            msg = f"Movie '{movie.title}' [{movie.id}] has no trailer to delete"
            await websockets.ws_manager.broadcast(msg, "Error")
            return msg
        if not movie.folder_path:
            msg = f"Movie '{movie.title}' [{movie.id}] has no folder path"
            await websockets.ws_manager.broadcast(msg, "Error")
            return msg
        files_handler = FilesHandler()
        res = await files_handler.delete_trailer(movie.folder_path)
        if not res:
            msg = f"Failed to delete trailer for movie '{movie.title}' [{movie.id}]"
            await websockets.ws_manager.broadcast(msg, "Error")
            return msg
        movie_update = MediaUpdate(trailer_exists=False)
        db_handler.update(movie_id, movie_update)
        msg = f"Trailer for movie '{movie.title}' [{movie.id}] has been deleted."
        logging.info(msg)
        await websockets.ws_manager.broadcast(msg, "Success")
        return msg
    except Exception as e:
        await websockets.ws_manager.broadcast("Error deleting trailer!", "Error")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@movies_router.get("/search/{query}")
async def search_movies(query: str) -> list[MediaRead]:
    db_handler = MediaDatabaseManager()
    movies = db_handler.search(query)
    return movies
