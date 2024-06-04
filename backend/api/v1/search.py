from fastapi import APIRouter

from api.v1.models import SearchMedia
from api.v1.movies import search_movies
from api.v1.series import search_series


search_router = APIRouter(prefix="/search", tags=["Search"])


@search_router.get("/{query}")
async def search_media(query: str) -> list[SearchMedia]:
    movies_list = await search_movies(query)
    series_list = await search_series(query)
    media_list: list[SearchMedia] = []
    for movie in movies_list:
        movie_data = movie.model_dump()
        movie_data["is_movie"] = True
        media_read = SearchMedia.model_validate(movie_data)
        media_read.is_movie = True
        media_list.append(media_read)
    for series in series_list:
        series_data = series.model_dump()
        series_data["is_movie"] = False
        media_read = SearchMedia.model_validate(series_data)
        media_read.is_movie = False
        media_list.append(media_read)
    return media_list
