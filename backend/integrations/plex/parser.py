from db.models.media import MediaCreate
from integrations.plex.models import PlexMediaItem


def parse_plex_item(
    item: PlexMediaItem,
    connection_id: int,
    section_key: str,
    is_movie: bool,
    server_url: str = "",
) -> MediaCreate:
    """Convert a PlexMediaItem to a MediaCreate.

    arr_id=0 indicates a Plex-only row (no Arr backing).
    Both connection_id and plex_connection_id point to the Plex connection.
    """
    txdb_id = ""
    if is_movie and item.tmdb_id:
        txdb_id = str(item.tmdb_id)
    elif not is_movie and item.tvdb_id:
        txdb_id = str(item.tvdb_id)
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
