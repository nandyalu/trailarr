from datetime import datetime, timezone
from enum import Enum

from pydantic import field_validator
from sqlmodel import Column, Field, String

from db.models.base import AppSQLModel


def get_current_time():
    return datetime.now(timezone.utc)


class IssueType(str, Enum):
    FILE_DELETED = "file_deleted"
    CONNECTION_FAILED = "connection_failed"
    TOKEN_INVALID = "token_invalid"
    FOLDER_MISSING = "folder_missing"


class EntityType(str, Enum):
    MEDIA_TRAILER_STATUS = "media_trailer_status"
    CONNECTION = "connection"
    DOWNLOAD = "download"


class IssueBase(AppSQLModel):
    """Base model for Issue.
    Note:
        🚨DO NOT USE THIS CLASS DIRECTLY.🚨
    👉Use :class:`Issue` for working with database.👈
    👉Use :class:`IssueRead` to read data.👈
    """

    issue_type: IssueType = Field(sa_column=Column(String, nullable=False))
    entity_type: EntityType = Field(sa_column=Column(String, nullable=False))
    entity_id: int
    description: str
    details: str | None = None


class Issue(IssueBase, table=True):
    """Database model for Issue.
    Tracks actionable problems that require user intervention.
    One active issue per (issue_type, entity_type, entity_id).

    Auto-resolved (row deleted) when the underlying condition clears.
    Set only by the app — never by the user directly.
    """

    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=get_current_time)
    updated_at: datetime = Field(default_factory=get_current_time)

    @field_validator("created_at", "updated_at", mode="after")
    @classmethod
    def ensure_utc(cls, value: datetime) -> datetime:
        return cls.set_timezone_to_utc(value)


class IssueRead(IssueBase):
    """Model for reading Issue records.
    Includes entity_name joined at query time for display.
    """

    id: int
    created_at: datetime
    updated_at: datetime
    # Joined at query time for display
    entity_name: str | None = None

    @field_validator("created_at", "updated_at", mode="after")
    @classmethod
    def correct_timezone(cls, value: datetime) -> datetime:
        return cls.set_timezone_to_utc(value)
