from backend.database.crud.base import DatabaseHandler
from backend.database.models.series import (
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
