from sqlmodel import SQLModel
from backend.database.models.connection import Connection  # noqa: F401
from backend.database.models.movie import Movie  # noqa: F401
from backend.database.models.series import Series  # noqa: F401
from backend.database.utils.engine import engine


#  make sure all SQLModel models are imported (database.models) before initializing DB
#  otherwise, SQLModel might fail to initialize relationships properly


def init_db():
    """Initialize the database and creates tables for SQLModels."""
    # Create the database tables
    SQLModel.metadata.create_all(bind=engine)
