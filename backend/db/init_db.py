# Import all models so SQLModel registers them before Alembic or create_all runs.
from db.models import (  # noqa: F401
    AppSQLModel,
    Connection,
    CustomFilter,
    Download,
    Event,
    Filter,
    Issue,
    Media,
    MediaTrailerStatus,
    PathMapping,
    ScheduledTaskConfig,
    TrailerProfile,
)
from db.engine import engine


def init_db():
    """Initialize the database and create tables for all SQLModels."""
    AppSQLModel.metadata.create_all(bind=engine)
