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
