# backend/core/base/database/utils/init_db.py

# !!! IMPORTANT !!!
# Import all the models that are used in the application so that \
# SQLModel can create the tables
from core.base.database.models.base import AppSQLModel
from core.base.database.models.connection import Connection
from core.base.database.models.download import Download
from core.base.database.models.media import Media
from core.base.database.models.filter import Filter
from core.base.database.models.customfilter import CustomFilter
from core.base.database.models.trailerprofile import TrailerProfile

from core.base.database.utils.engine import engine

#  make sure all SQLModel models are imported (database.models) before\
# initializing DB. Otherwise, SQLModel might fail to initialize \
# relationships properly

__ALL__ = [Connection, Download, Media, Filter, CustomFilter, TrailerProfile]


def init_db():
    """Initialize the database and creates tables for SQLModels."""
    # Create the database tables
    AppSQLModel.metadata.create_all(bind=engine)
