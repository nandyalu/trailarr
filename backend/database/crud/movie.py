from backend.database.crud.base import DatabaseHandler
from backend.database.models.movie import Movie, MovieCreate, MovieRead, MovieUpdate


class MovieDatabaseHandler(DatabaseHandler[Movie, MovieCreate, MovieRead, MovieUpdate]):
    """CRUD operations for movie database table."""

    def __init__(self):
        super().__init__(db_model=Movie, read_model=MovieRead)
