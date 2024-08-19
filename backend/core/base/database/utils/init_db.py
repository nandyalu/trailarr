from sqlmodel import SQLModel

# !!! IMPORTANT !!!
# Import all the models that are used in the application so that SQLModel can create the tables
from core.base.database.models.connection import Connection  # noqa: F401
from core.base.database.models.media import Media  # noqa: F401
from core.base.database.utils.engine import engine


#  make sure all SQLModel models are imported (database.models) before initializing DB
#  otherwise, SQLModel might fail to initialize relationships properly


def init_db():
    """Initialize the database and creates tables for SQLModels."""
    # Create the database tables
    SQLModel.metadata.create_all(bind=engine)
