from typing import Any
from backend.core.radarr.models import MovieCreate


def parse_movie(connection_id: int, movie_data: dict[str, Any]) -> MovieCreate:
    """Parse the movie data from Radarr to a MovieCreate object.

    Args:
        connection_id (int): The connection id.
        movie_data (dict[str, Any]): The movie data from Radarr.

    Returns:
        MovieCreate: The movie data as a MovieCreate object."""
    _radarr_id = movie_data.get("id", "")
    _title = movie_data.get("title", "")
    _tmdb_id = movie_data.get("tmdbId", "")
    new_movie = MovieCreate(
        connection_id=connection_id,
        radarr_id=_radarr_id,
        title=_title,
        tmdb_id=_tmdb_id,
    )

    _year = movie_data.get("year", "")
    if _year:
        new_movie.year = int(_year)
    _language = movie_data.get("originalLanguage", {}).get("name", "")
    if _language:
        new_movie.language = _language
    new_movie.overview = movie_data.get("overview", "")
    new_movie.runtime = int(movie_data.get("runtime", 0))
    new_movie.website = movie_data.get("website", "")
    new_movie.youtube_trailer_id = movie_data.get("youTubeTrailerId", "")
    new_movie.folder_path = movie_data.get("path", "")
    new_movie.imdb_id = movie_data.get("imdbId", "")
    for image in movie_data["images"]:
        if image["coverType"] == "poster":
            new_movie.poster_url = image["remoteUrl"]
        elif image["coverType"] == "fanart":
            new_movie.fanart_url = image["remoteUrl"]
    new_movie.radarr_monitored = movie_data.get("monitored", False)

    return new_movie
