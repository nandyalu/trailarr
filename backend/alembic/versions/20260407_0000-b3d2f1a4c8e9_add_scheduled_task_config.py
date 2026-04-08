"""Add ScheduledTaskConfig table with default task seed data

Revision ID: b3d2f1a4c8e9
Revises: ae0d134607f9
Create Date: 2026-04-07 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from app_logger import ModuleLogger
from config.settings import app_settings

revision: str = "b3d2f1a4c8e9"
down_revision: Union[str, None] = "ae0d134607f9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

logger = ModuleLogger("AlembicMigrations")

# Default monitor interval is 60 minutes → 3600 seconds.
# Users who have customised MONITOR_INTERVAL can update via the UI after migration.
_MONITOR_INTERVAL_SECONDS = app_settings.monitor_interval * 60.0

_DEFAULT_TASKS = [
    {
        "task_key": "api_refresh",
        "task_name": "Arr Data Refresh",
        "interval_seconds": _MONITOR_INTERVAL_SECONDS,
        "delay_seconds": 30.0,
    },
    {
        "task_key": "update_check",
        "task_name": "Docker Update Check",
        "interval_seconds": 86400.0,
        "delay_seconds": 240.0,
    },
    {
        "task_key": "scan_disk",
        "task_name": "Scan All Media Folders",
        "interval_seconds": _MONITOR_INTERVAL_SECONDS,
        "delay_seconds": 480.0,
    },
    {
        "task_key": "download_trailers",
        "task_name": "Download Missing Trailers",
        "interval_seconds": _MONITOR_INTERVAL_SECONDS,
        "delay_seconds": 900.0,
    },
    {
        "task_key": "image_refresh",
        "task_name": "Image Refresh",
        "interval_seconds": 21600.0,
        "delay_seconds": 720.0,
    },
    {
        "task_key": "cleanup",
        "task_name": "Cleanup Task",
        "interval_seconds": 86400.0,
        "delay_seconds": 14400.0,
    },
]


def upgrade() -> None:
    op.execute("PRAGMA foreign_keys=OFF")

    op.create_table(
        "scheduledtaskconfig",
        sa.Column(
            "task_key", sqlmodel.sql.sqltypes.AutoString(), nullable=False
        ),
        sa.Column(
            "task_name", sqlmodel.sql.sqltypes.AutoString(), nullable=False
        ),
        sa.Column("interval_seconds", sa.Float(), nullable=False),
        sa.Column("delay_seconds", sa.Float(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("scheduledtaskconfig_pkc")),
        sa.UniqueConstraint(
            "task_key", name=op.f("uq_scheduledtaskconfig_task_key")
        ),
    )

    task_table = sa.table(
        "scheduledtaskconfig",
        sa.column("task_key", sa.String),
        sa.column("task_name", sa.String),
        sa.column("interval_seconds", sa.Float),
        sa.column("delay_seconds", sa.Float),
    )
    op.bulk_insert(task_table, _DEFAULT_TASKS)

    op.execute("PRAGMA foreign_keys=ON")


def downgrade() -> None:
    op.execute("PRAGMA foreign_keys=OFF")
    op.drop_table("scheduledtaskconfig")
    op.execute("PRAGMA foreign_keys=ON")
