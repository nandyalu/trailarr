import os

from alembic import command
from alembic.config import Config

# Import all models so SQLModel registers them before Alembic runs.
# db/models/__init__.py re-exports every table class; this single import is enough.
from db.models import AppSQLModel  # noqa: F401


def init_db():
    """Run Alembic migrations to bring the database schema to head."""
    alembic_cfg = Config(os.path.join(os.path.dirname(__file__), "..", "alembic.ini"))
    command.upgrade(alembic_cfg, "head")
