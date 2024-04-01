from sqlmodel import SQLModel
from backend.core.base.database.models import Connection  # noqa: F401
from backend.core.radarr.models import Movie  # noqa: F401
from backend.core.sonarr.models import Series  # noqa: F401
from backend.core.base.database.utils.engine import engine


#  make sure all SQLModel models are imported (database.models) before initializing DB
#  otherwise, SQLModel might fail to initialize relationships properly


def init_db():
    """Initialize the database and creates tables for SQLModels."""
    # Create the database tables
    SQLModel.metadata.create_all(bind=engine)
