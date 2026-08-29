"""Create the database and bring it up to the current schema at start."""

# backend/database/init_db.py

# !!! IMPORTANT !!!
# Import all the models that are used in the application so that \
# SQLModel can create the tables
from database.models.base import AppSQLModel
from database.models.connection import Connection
from database.models.download import Download
from database.models.downloadattempt import DownloadAttempt
from database.models.event import Event
from database.models.media import Media
from database.models.filter import Filter
from database.models.customfilter import CustomFilter
from database.models.notificationchannel import NotificationChannel
from database.models.startuppass import StartupPass
from database.models.task_config import ScheduledTaskConfig
from database.models.trailerprofile import TrailerProfile

from database.engine import engine

#  make sure all SQLModel models are imported (database.models) before\
# initializing DB. Otherwise, SQLModel might fail to initialize \
# relationships properly

__ALL__ = [
    Connection,
    Download,
    DownloadAttempt,
    Event,
    Media,
    Filter,
    CustomFilter,
    NotificationChannel,
    ScheduledTaskConfig,
    StartupPass,
    TrailerProfile,
]


def init_db():
    """Initialize the database and creates tables for SQLModels."""
    # Create the database tables
    AppSQLModel.metadata.create_all(bind=engine)
