from sqlmodel import select
from backend.core.base.database.manager.base import DatabaseHandler
from backend.core.sonarr.models import (
    Series,
    SeriesCreate,
    SeriesRead,
    SeriesUpdate,
)


class SeriesDatabaseHandler(
    DatabaseHandler[Series, SeriesCreate, SeriesRead, SeriesUpdate]
):
    """CRUD operations for series database table."""

    def __init__(self):
        super().__init__(db_model=Series, read_model=SeriesRead)

    def _get_txdb_statement(self, txdb_id: str):
        return select(Series).where(Series.tmdb_id == txdb_id)

    def _get_read_by_id_statement(self, connection_id: int, media_id: int):
        return (
            select(Series)
            .where(Series.connection_id == connection_id)
            .where(Series.sonarr_id == media_id)
        )
