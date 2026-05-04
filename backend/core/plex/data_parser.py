from core.base.database.models.media import MediaCreate
from core.plex.models import PlexMediaItem


def parse_plex_item(
    item: PlexMediaItem,
    connection_id: int,
    section_key: str,
    is_movie: bool,
    server_url: str = "",
) -> MediaCreate:
    """Convert a PlexMediaItem into a MediaCreate object.

    For Plex-sourced items:
    - arr_id is set to 0 (no Arr application backing this item)
    - plex_rating_key / plex_section_key carry the Plex identifiers
    - plex_connection_id and connection_id both point to the Plex connection

    Args:
        item: Parsed Plex metadata item.
        connection_id: The DB id of the Plex Connection row.
        section_key: The Plex library section key this item belongs to.
        is_movie: True for movie libraries, False for TV show libraries.
        server_url: Plex server base URL (no trailing slash). When provided,
            poster_url and fanart_url are set to ``{server_url}{relative_path}``
            so that the image refresh task can download them (with token injection).
    """
    txdb_id = ""
    if is_movie and item.tmdb_id:
        txdb_id = str(item.tmdb_id)
    elif not is_movie and item.tvdb_id:
        txdb_id = str(item.tvdb_id)
    # Fallback: use the ratingKey prefixed so it stays unique in the DB
    if not txdb_id:
        txdb_id = f"plex-{item.ratingKey}"

    poster_url = f"{server_url}{item.thumb}" if server_url and item.thumb else None
    fanart_url = f"{server_url}{item.art}" if server_url and item.art else None

    return MediaCreate(
        connection_id=connection_id,
        arr_id=0,
        is_movie=is_movie,
        title=item.title,
        year=item.year,
        overview=item.summary if item.summary else None,
        runtime=item.duration,
        studio=item.studio,
        imdb_id=item.imdb_id,
        txdb_id=txdb_id,
        folder_path=item.media_folder if item.media_folder else None,
        media_filename=item.media_filename,
        media_exists=bool(item.media_filename),
        plex_rating_key=item.ratingKey if item.ratingKey else None,
        plex_section_key=section_key,
        plex_connection_id=connection_id,
        poster_url=poster_url,
        fanart_url=fanart_url,
    )
