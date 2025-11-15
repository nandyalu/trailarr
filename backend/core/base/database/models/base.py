from datetime import datetime, timezone
from sqlalchemy import MetaData
from sqlmodel import SQLModel

CONVENTIONS = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "%(table_name)s_pkc",
}

METADATA = MetaData(naming_convention=CONVENTIONS)


class AppSQLModel(SQLModel):
    """Base class for all SQLModel models in the application.
    This ensures that all models are created with the same metadata and conventions.
    """

    metadata = METADATA

    @classmethod
    def set_timezone_to_utc(cls, value):
        if isinstance(value, datetime) and value.tzinfo is None:
            # Assume naive datetime loaded from DB is UTC
            return value.replace(tzinfo=timezone.utc)
        return value
