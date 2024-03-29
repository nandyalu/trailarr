from typing import Any

from backend.database.models.connection import ArrType
from backend.database.models.movie import MovieCreate
from backend.database.models.series import SeriesCreate


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


def parse_series(connection_id: int, series_data: dict[str, Any]) -> SeriesCreate:
    """Parse the series data from Sonarr to a SeriesCreate object.

    Args:
        connection_id (int): The connection id.
        series_data (dict[str, Any]): The series data from Sonarr.

    Returns:
        SeriesCreate: The series data as a SeriesCreate object."""
    _sonarr_id = series_data.get("id", "")
    _title = series_data.get("title", "")
    _tvdb_id = series_data.get("tvdbId", "")
    new_series = SeriesCreate(
        connection_id=connection_id,
        sonarr_id=_sonarr_id,
        title=_title,
        tvdb_id=_tvdb_id,
    )

    _year = series_data.get("year", "")
    if _year:
        new_series.year = int(_year)
    _language = series_data.get("originalLanguage", {}).get("name", "")
    if _language:
        new_series.language = _language
    new_series.overview = series_data.get("overview", "")
    new_series.runtime = int(series_data.get("runtime", 0))
    new_series.youtube_trailer_id = series_data.get("youTubeTrailerId", "")
    new_series.folder_path = series_data.get("path", "")
    new_series.imdb_id = series_data.get("imdbId", "")
    for image in series_data["images"]:
        if image["coverType"] == "poster":
            new_series.poster_url = image["remoteUrl"]
        elif image["coverType"] == "fanart":
            new_series.fanart_url = image["remoteUrl"]
    new_series.sonarr_monitored = series_data.get("monitored", False)

    return new_series


def parse_media(
    type: ArrType, connection_id: int, media_data: dict[str, Any]
) -> MovieCreate | SeriesCreate:
    """Parse the media data from the Arr application.

    Args:
        type (ArrType): The Arr type.
        connection_id (int): The connection id.
        media_data (dict[str, Any]): The media data from the Arr application.

    Returns:
        MovieCreate | SeriesCreate: The media data as a MovieCreate or SeriesCreate object.

    Raises:
        NotImplementedError: If the Arr type is not implemented."""
    if type == ArrType.RADARR:
        return parse_movie(connection_id, media_data)
    elif type == ArrType.SONARR:
        return parse_series(connection_id, media_data)
    else:
        raise NotImplementedError("Arr type not implemented")
