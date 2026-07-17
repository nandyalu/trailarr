"""Connection monitor enum to monitor_new_media bool (Phase 4)

`monitor` is user intent now: the per-connection MonitorType enum becomes a
boolean `monitor_new_media` applied once at media creation. Mapping:
MONITOR_NONE -> False, everything else (MISSING/NEW/SYNC) -> True.
Existing media keep their monitor values as-is (intent snapshot).

Connections that were MONITOR_SYNC lose their follow-Arr behavior — the
replacement is a profile filter on `arr_monitored = true` (which syncs keep
maintaining). A log line below lists affected connections; the v0.10.1
release notes carry the walk-through.

Downgrade is lossy (bool -> enum): False -> MONITOR_NONE,
True -> MONITOR_MISSING. Rely on the standard pre-upgrade DB backup to
restore exact enum values.

Revision ID: c4f2a9d81e07
Revises: 830eaf99eab5
Create Date: 2026-07-17 02:10:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from app_logger import ModuleLogger


# revision identifiers, used by Alembic.
revision: str = 'c4f2a9d81e07'
down_revision: Union[str, None] = '830eaf99eab5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

logger = ModuleLogger("AlembicMigrations")


def upgrade() -> None:
    # Disable foreign keys temporarily for migrations
    op.execute("PRAGMA foreign_keys=OFF")

    conn = op.get_bind()
    rows = conn.execute(
        sa.text("SELECT id, name, monitor FROM connection")
    ).fetchall()

    op.add_column(
        "connection",
        sa.Column(
            "monitor_new_media",
            sa.Boolean(),
            server_default=sa.text("1"),
            nullable=False,
        ),
    )

    sync_connections: list[str] = []
    for row in rows:
        old_value = str(row.monitor)
        new_value = 0 if old_value == "MONITOR_NONE" else 1
        conn.execute(
            sa.text(
                "UPDATE connection SET monitor_new_media = :val"
                " WHERE id = :id"
            ),
            {"val": new_value, "id": row.id},
        )
        logger.info(
            f"Connection '{row.name}' [{row.id}]: monitor '{old_value}'"
            f" -> monitor_new_media={bool(new_value)}"
        )
        if old_value == "MONITOR_SYNC":
            sync_connections.append(f"'{row.name}'")

    if sync_connections:
        logger.warning(
            "Monitor type SYNC was removed: connection(s) "
            + ", ".join(sync_connections)
            + " no longer follow Radarr/Sonarr monitoring changes —"
            " existing media keep their current monitor values, and new"
            " media are monitored on creation. To keep sync-like behavior,"
            " add a filter 'arr_monitored equals true' to your download"
            " profiles (Trailarr keeps updating arr_monitored from your"
            " Arr apps). See the v0.10.1 release notes for a walk-through."
        )

    # SQLite: drop the old enum column via batch table rebuild (also drops
    # the enum CHECK constraint attached to it)
    with op.batch_alter_table("connection") as batch_op:
        batch_op.drop_column("monitor")

    # Enable foreign keys back
    op.execute("PRAGMA foreign_keys=ON")


def downgrade() -> None:
    # Disable foreign keys temporarily for migrations
    op.execute("PRAGMA foreign_keys=OFF")

    logger.warning(
        "Downgrading connection.monitor_new_media (bool) to the legacy"
        " MonitorType enum is LOSSY: False -> MONITOR_NONE,"
        " True -> MONITOR_MISSING. Restore the pre-upgrade DB backup to"
        " recover exact values."
    )
    op.add_column(
        "connection",
        sa.Column(
            "monitor",
            sa.Enum(
                "MONITOR_MISSING",
                "MONITOR_NEW",
                "MONITOR_NONE",
                "MONITOR_SYNC",
                name="monitortype",
            ),
            server_default=sa.text("'MONITOR_MISSING'"),
            nullable=False,
        ),
    )
    conn = op.get_bind()
    conn.execute(
        sa.text(
            "UPDATE connection SET monitor = CASE"
            " WHEN monitor_new_media = 0 THEN 'MONITOR_NONE'"
            " ELSE 'MONITOR_MISSING' END"
        )
    )
    with op.batch_alter_table("connection") as batch_op:
        batch_op.drop_column("monitor_new_media")

    # Enable foreign keys back
    op.execute("PRAGMA foreign_keys=ON")
