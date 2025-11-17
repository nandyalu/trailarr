import re
from sqlmodel import Session, col, desc, select
from sqlmodel.sql.expression import SelectOfScalar

from . import base
from core.base.database.models.media import (
    Media,
    MediaRead,
)
from core.base.database.utils.engine import manage_session


@manage_session
def search(
    query: str,
    *,
    offset: int = 0,
    _session: Session = None,  # type: ignore
) -> list[MediaRead]:
    """Search for media objects in the database by `title`, `overview`, \
        `imdb id`, or `txdb id` [tmdb for `Movie`, tvdb for `Series`].\n
    If an exact match is found for `imdb id` or `txdb id`, it will return only that item.\n
    If a 4 digit number is found in the query, \
        it will only return list of media from that year [1900-2100].\n
    Otherwise, it will return a list of [max 50 recently added] Media matching the query.\n
    Args:
        query (str): The search query to search for in the media items.
        offset (int, Optional): The offset to start from. Default is 0.
        _session (Session, Optional): A session to use for the database connection.\n
            Default is None, in which case a new session will be created.\n
    Returns:
        list[MediaRead]: List of MediaRead objects.
    """
    offset = max(0, offset)
    limit = 50
    statement = _get_search_statement(query, limit, offset)
    if statement is None:
        return []
    db_media_list = _session.exec(statement).all()
    # logger.info(f"Found {len(db_media_list)} media items.")
    return base._convert_to_read_list(db_media_list)


def _get_search_statement(
    query: str, limit: int = 50, offset: int = 0
) -> SelectOfScalar[Media] | None:
    """🚨This is a private method🚨 \n
    Get a search statement for the database query.\n"""
    # logger.info(f"Searching for: {query}")
    if not query:
        # logger.info("Empty query. Returning empty list.")
        return None
    imdb_id = _extract_imdb_id(query)
    if imdb_id:
        # logger.info(f"Found imdb id: {imdb_id}")
        return _get_imdb_statement(imdb_id)
    txdb_id = _extract_txdb_id(query)
    if txdb_id:
        # logger.info(f"Found txdb id: {txdb_id}")
        return _get_txdb_statement(txdb_id)
    # logger.info("No imdb or txdb id found. Building statement...")
    statement = select(Media)
    year = _extract_four_digit_number(query)
    if year and int(year) > 1900 and int(year) < 2100:
        query = query.replace(year, "").strip().replace("  ", " ")
        statement = _get_year_statement(year)
        # logger.info(f"Found year: {year}")

    statement = (
        statement.where(
            col(Media.title).ilike(f"%{query}%"),
            # or_(
            #     col(Media.title).ilike(f"%{query}%"),
            #     col(Media.overview).ilike(f"%{query}%"),
            # )
        )
        .offset(offset)
        .limit(limit)
        .order_by(desc(Media.added_at))
    )
    # logger.info(f"Final statement: {statement}")
    return statement


def _extract_four_digit_number(query: str) -> str | None:
    """🚨This is a private method🚨 \n
    Extract a 4 digit number from a string."""
    matches = re.findall(r"\b\d{4}\b", query)
    last_match = matches[-1] if matches else None
    return last_match


def _extract_imdb_id(query: str) -> str | None:
    """🚨This is a private method🚨 \n
    Extract an imdb id from a string."""
    matches = re.findall(r"tt\d{7,}", query)
    last_match = matches[-1] if matches else None
    return last_match


def _extract_txdb_id(query: str) -> str | None:
    """🚨This is a private method🚨 \n
    Extract a txdb id from a string.\n
    Series 5 digits -> tvdb id, Movie 6 digits -> tmdb id."""
    matches = re.findall(r"\b\d{5,6}\b", query)
    last_match = matches[-1] if matches else None
    return last_match


def _get_txdb_statement(txdb_id: str) -> SelectOfScalar[Media]:
    """🚨This is a private method🚨 \n
    Get a statement for the database query with txdb id.\n"""
    statement = select(Media).where(Media.txdb_id == txdb_id)
    return statement


def _get_imdb_statement(imdb_id: str) -> SelectOfScalar[Media]:
    """🚨This is a private method🚨 \n
    Get a statement for the database query with imdb id.\n"""
    statement = select(Media).where(Media.imdb_id == imdb_id)
    return statement


def _get_year_statement(year: str) -> SelectOfScalar[Media]:
    """🚨This is a private method🚨 \n
    Get a statement for the database query with year.\n"""
    statement = select(Media).where(Media.year == year)
    return statement
