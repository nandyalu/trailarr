from datetime import datetime, timezone

from sqlmodel import Field

from core.base.database.models.base import AppSQLModel


def get_current_time():
    return datetime.now(timezone.utc)


class StartupPass(AppSQLModel, table=True):
    """
    Completion record for one-time startup passes (see plans/README.md →
    "Upgrade-safety rules"). A pass whose name is recorded here has run to
    completion on this database; unrecorded passes run at boot in dependency
    order before scheduled tasks. Makes version-skipping upgrades safe:
    whatever passes a user skipped simply run on first boot of the new
    version.
    """

    name: str = Field(primary_key=True)
    completed_at: datetime = Field(default_factory=get_current_time)
    app_version: str = Field(default="")
