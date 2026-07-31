"""Drop legacy media status columns and profile stop_monitoring (Phase 5)

Removes `media.trailer_exists`, `media.status` and
`trailerprofile.stop_monitoring`. Download rows are the source of truth
for downloaded-ness since Phase 2/3; the monitor flag is pure user intent
since Phase 4. Before the drops, CustomFilter rows that reference the
removed fields are migrated:

- Profile filters (filter_type=TRAILER) on trailer_exists or status:
  DELETED — the download engine's satisfaction rule makes them implicit.
- View filters (HOME/MOVIES/SERIES) on trailer_exists: rewritten to the
  new virtual field has_downloads (condition and value preserved).
- View filters on status: EQUALS downloaded -> has_downloads=true,
  EQUALS missing -> has_downloads=false, EQUALS monitored -> monitor=true,
  anything else DELETED.

Every rewrite/delete is logged with the filter name so users can
reconstruct their filters. See the v0.11.0 release notes for the full
transformation table.

Revision ID: 011109b10e82
Revises: c4f2a9d81e07
Create Date: 2026-07-30 20:29:30.904945

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from app_logger import ModuleLogger


# revision identifiers, used by Alembic.
revision: str = '011109b10e82'
down_revision: Union[str, None] = 'c4f2a9d81e07'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

logger = ModuleLogger("AlembicMigrations")

# status EQUALS <value> -> (new filter_by, new filter_value); the filter
# condition stays EQUALS. Any other status filter is deleted.
_STATUS_EQUALS_MAP = {
    "downloaded": ("has_downloads", "true"),
    "missing": ("has_downloads", "false"),
    "monitored": ("monitor", "true"),
}


def _migrate_custom_filters(conn) -> None:
    rows = conn.execute(
        sa.text(
            """
            SELECT f.id, f.filter_by, f.filter_condition, f.filter_value,
                   cf.filter_name, cf.filter_type
            FROM "filter" f
            JOIN customfilter cf ON cf.id = f.customfilter_id
            WHERE f.filter_by IN ('trailer_exists', 'status')
            """
        )
    ).fetchall()

    for row in rows:
        label = f"Filter '{row.filter_name}' [{row.filter_type}]"
        cond = row.filter_condition
        value = (row.filter_value or "").strip().lower()

        if row.filter_type == "TRAILER":
            # Profile filters: satisfaction handles "already has a trailer"
            # implicitly — the condition is removed.
            conn.execute(
                sa.text('DELETE FROM "filter" WHERE id = :id'),
                {"id": row.id},
            )
            if row.filter_by == "trailer_exists" and value == "true":
                logger.warning(
                    f"{label}: removed condition 'trailer_exists = true'."
                    " This condition made the profile match only media that"
                    " already had a trailer. That behavior is not possible"
                    " anymore. Review this profile's filters."
                )
            else:
                logger.info(
                    f"{label}: removed condition"
                    f" '{row.filter_by} {cond} {row.filter_value}'."
                    " The download engine now handles this automatically."
                )
            continue

        if row.filter_by == "trailer_exists":
            # View filters keep their meaning through has_downloads
            conn.execute(
                sa.text(
                    'UPDATE "filter" SET filter_by = :fb WHERE id = :id'
                ),
                {"fb": "has_downloads", "id": row.id},
            )
            logger.info(
                f"{label}: condition 'trailer_exists {cond}"
                f" {row.filter_value}' is now 'has_downloads {cond}"
                f" {row.filter_value}'."
            )
            continue

        # View filters on status
        if cond == "EQUALS" and value in _STATUS_EQUALS_MAP:
            new_by, new_value = _STATUS_EQUALS_MAP[value]
            conn.execute(
                sa.text(
                    'UPDATE "filter" SET filter_by = :fb,'
                    " filter_value = :fv WHERE id = :id"
                ),
                {"fb": new_by, "fv": new_value, "id": row.id},
            )
            logger.info(
                f"{label}: condition 'status EQUALS {row.filter_value}' is"
                f" now '{new_by} EQUALS {new_value}'."
            )
        else:
            conn.execute(
                sa.text('DELETE FROM "filter" WHERE id = :id'),
                {"id": row.id},
            )
            logger.warning(
                f"{label}: removed condition '{row.filter_by} {cond}"
                f" {row.filter_value}'. It has no equivalent after v0.11.0."
                " Recreate it with the new fields if you need it."
            )

    # Custom filters left with zero conditions match everything — keep
    # them, but tell the user.
    empty = conn.execute(
        sa.text(
            """
            SELECT cf.filter_name, cf.filter_type
            FROM customfilter cf
            WHERE NOT EXISTS (
                SELECT 1 FROM "filter" f WHERE f.customfilter_id = cf.id
            )
            """
        )
    ).fetchall()
    for row in empty:
        logger.info(
            f"Filter '{row.filter_name}' [{row.filter_type}] has no"
            " conditions left after the migration. It now matches all media."
        )


def upgrade() -> None:
    # Disable foreign keys temporarily for migrations
    op.execute("PRAGMA foreign_keys=OFF")

    conn = op.get_bind()
    _migrate_custom_filters(conn)

    with op.batch_alter_table("media") as batch_op:
        batch_op.drop_column("trailer_exists")
        batch_op.drop_column("status")

    with op.batch_alter_table("trailerprofile") as batch_op:
        batch_op.drop_column("stop_monitoring")

    # Re-enable foreign keys after migrations
    op.execute("PRAGMA foreign_keys=ON")


def downgrade() -> None:
    raise NotImplementedError(
        "v0.11.0 removed the media.trailer_exists, media.status and"
        " trailerprofile.stop_monitoring columns. Downgrade is not"
        " supported. Restore the pre-upgrade database backup instead."
    )
