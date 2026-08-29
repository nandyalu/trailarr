"""A failed download attempt, and the backoff it causes."""

from datetime import datetime, timedelta, timezone

from pydantic import field_validator
from sqlalchemy import Column, String, UniqueConstraint, text
from sqlmodel import Field

from database.models.base import AppSQLModel


def get_current_time():
    return datetime.now(timezone.utc)


# Unit identifying WHAT a profile wants for a media item. A single value for
# now; becomes per-season units ("s01", "s02", ...) in Phase 10 — the
# (media, profile, unit) key shape is fixed from day one to avoid a rework.
DEFAULT_UNIT = "default"

# Failed attempts back off exponentially: 1d, 2d, 4d, then capped weekly.
BACKOFF_CAP_DAYS = 7
MAX_ERROR_LENGTH = 500


class DownloadAttemptBase(AppSQLModel):
    """
    Base model for DownloadAttempt — failure tracking for the download task,
    keyed on (media, profile, unit). A row exists only while a download for
    that key keeps failing; success deletes it.\n
    Note: \n
        🚨DO NOT USE THIS CLASS DIRECTLY.🚨 \n
    👉Use :class:`DownloadAttemptCreate` to create/update attempts.👈 \n
    👉Use :class:`DownloadAttemptRead` to read the data.👈
    """

    # NOT a foreign key on purpose: profiles can be deleted; stale attempt
    # rows are pruned lazily at task start.
    profile_id: int = Field(index=True)
    unit: str = Field(
        default=DEFAULT_UNIT,
        sa_column=Column(
            String, server_default=text("('default')"), nullable=False
        ),
    )
    attempt_count: int = Field(default=0)
    last_attempt_at: datetime = Field(default_factory=get_current_time)
    last_error: str | None = None


class DownloadAttempt(DownloadAttemptBase, table=True):
    """
    Database model for DownloadAttempt.\n
    Note: \n
        🚨DO NOT USE THIS CLASS OUTSIDE OF DATABASE MANAGER.🚨 \n
    """

    __table_args__ = (
        UniqueConstraint(
            "media_id", "profile_id", "unit", name="uq_attempt_key"
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    media_id: int = Field(
        foreign_key="media.id", index=True, ondelete="CASCADE"
    )

    @field_validator("last_attempt_at", mode="after")
    @classmethod
    def update_to_utc_to_save(cls, value: datetime) -> datetime:
        return cls.convert_to_utc(value)


class DownloadAttemptCreate(DownloadAttemptBase):
    """Model for creating/updating DownloadAttempt."""

    id: int | None = None
    media_id: int


class DownloadAttemptRead(DownloadAttemptBase):
    """Model for reading DownloadAttempt."""

    id: int
    media_id: int

    @field_validator("last_attempt_at", mode="after")
    @classmethod
    def correct_timezone_after_read(cls, value: datetime) -> datetime:
        return cls.set_timezone_to_utc(value)


def next_eligible_at(attempt: DownloadAttemptRead) -> datetime:
    """When this (media, profile, unit) may be attempted again.\n
    Exponential backoff on failures: 1d, 2d, 4d, capped at 7d."""
    delay_days = min(2 ** max(attempt.attempt_count - 1, 0), BACKOFF_CAP_DAYS)
    last = attempt.last_attempt_at
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
    return last + timedelta(days=delay_days)


def is_eligible(
    attempt: "DownloadAttemptRead | None", now: datetime | None = None
) -> bool:
    """Whether a download may be attempted for this key right now.\n
    No attempt row (never failed / cleared on success) is always eligible."""
    if attempt is None:
        return True
    if now is None:
        now = datetime.now(timezone.utc)
    return now >= next_eligible_at(attempt)
