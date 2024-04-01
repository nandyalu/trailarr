from typing import Any

from backend.core.sonarr.models import SeriesCreate


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
