"""Drop media.youtube_trailer_id (Phase 9, hygiene H9)

The `mediavideo` table is the only record of known video ids from here on.
Three steps, in this order:

1. Backfill. Phase 8's migration (1c9c26339940) copied the column into
   `mediavideo` as SEARCH rows, but the Arr sync, the search and the
   YouTube ID field kept writing the column after that. Every non-empty
   id that has no row for its media yet becomes a SEARCH row with the
   same shape. The unique key `(media_id, video_id)` makes it safe to
   run again.
2. Saved filters (the Phase 5 pattern). A view filter (HOME/MOVIES/SERIES)
   on `youtube_trailer_id` with IS_EMPTY / IS_NOT_EMPTY becomes the new
   virtual field `has_videos` (the media has at least one known video):
   IS_NOT_EMPTY -> has_videos EQUALS true, IS_EMPTY -> has_videos EQUALS
   false. Any other condition cannot map and is DELETED with a warning.
   A profile (TRAILER) filter on the field is DELETED with a warning:
   `has_videos` is view-only, because a profile that filters on its own
   data is circular.
3. Drop the column (batch mode). The column had no index.

Every rewrite and delete is logged with the filter name so users can
rebuild their filters. See the v0.14.0 release notes.

Revision ID: c3d8e5f9a2b1
Revises: 9a1c4e7b2d30
Create Date: 2026-10-07 13:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from app_logger import ModuleLogger


# revision identifiers, used by Alembic.
revision: str = "c3d8e5f9a2b1"
down_revision: Union[str, None] = "9a1c4e7b2d30"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

logger = ModuleLogger("AlembicMigrations")

# youtube_trailer_id <condition> -> has_videos EQUALS <value>
_CONDITION_MAP = {
    "IS_NOT_EMPTY": "true",
    "IS_EMPTY": "false",
}


def _backfill_video_rows(conn) -> None:
    """Move every id that is still only in the column into the table."""
    result = conn.execute(
        sa.text(
            "INSERT OR IGNORE INTO mediavideo"
            " (media_id, video_id, source, season, video_type, sequence,"
            "  language, name, official, published_at, added_at, updated_at)"
            " SELECT m.id, TRIM(m.youtube_trailer_id), 'SEARCH', NULL,"
            "        'trailer', 0, NULL, '', 0, NULL,"
            "        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP"
            " FROM media m"
            " WHERE m.youtube_trailer_id IS NOT NULL"
            "   AND TRIM(m.youtube_trailer_id) != ''"
            "   AND NOT EXISTS ("
            "       SELECT 1 FROM mediavideo mv"
            "       WHERE mv.media_id = m.id"
            "         AND mv.video_id = TRIM(m.youtube_trailer_id)"
            "   )"
        )
    )
    logger.info(
        f"Trailarr moved {result.rowcount} YouTube ids from the media table"
        " into the known videos table. The media.youtube_trailer_id column"
        " is removed now."
    )


def _migrate_custom_filters(conn) -> None:
    rows = conn.execute(
        sa.text(
            """
            SELECT f.id, f.filter_by, f.filter_condition, f.filter_value,
                   cf.filter_name, cf.filter_type
            FROM "filter" f
            JOIN customfilter cf ON cf.id = f.customfilter_id
            WHERE f.filter_by = 'youtube_trailer_id'
            """
        )
    ).fetchall()

    for row in rows:
        label = f"Filter '{row.filter_name}' [{row.filter_type}]"
        cond = row.filter_condition
        old = f"youtube_trailer_id {cond} {row.filter_value or ''}".rstrip()

        if row.filter_type == "TRAILER":
            # A profile cannot filter on the known videos: the field is
            # view-only, so the condition is removed.
            conn.execute(
                sa.text('DELETE FROM "filter" WHERE id = :id'),
                {"id": row.id},
            )
            logger.warning(
                f"{label}: removed condition '{old}'. The YouTube ID field"
                " is gone, and a profile cannot filter on the known videos"
                " of a media item. Review this profile's filters."
            )
            continue

        new_value = _CONDITION_MAP.get(cond)
        if new_value is not None:
            conn.execute(
                sa.text(
                    'UPDATE "filter" SET filter_by = :fb,'
                    " filter_condition = 'EQUALS', filter_value = :fv"
                    " WHERE id = :id"
                ),
                {"fb": "has_videos", "fv": new_value, "id": row.id},
            )
            logger.info(
                f"{label}: condition '{old}' is now"
                f" 'has_videos EQUALS {new_value}'."
            )
            continue

        conn.execute(
            sa.text('DELETE FROM "filter" WHERE id = :id'),
            {"id": row.id},
        )
        logger.warning(
            f"{label}: removed condition '{old}'. It has no equivalent"
            " after v0.14.0: the YouTube ID field is gone. Use the"
            " 'has_videos' field if you need a filter on known videos."
        )

    # Custom filters left with zero conditions match everything — keep
    # them, but tell the user.
    if not rows:
        return
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
    _backfill_video_rows(conn)
    _migrate_custom_filters(conn)

    with op.batch_alter_table("media", schema=None) as batch_op:
        batch_op.drop_column("youtube_trailer_id")

    # Re-enable foreign keys after migrations
    op.execute("PRAGMA foreign_keys=ON")


def downgrade() -> None:
    raise NotImplementedError(
        "v0.14.0 removed the media.youtube_trailer_id column. Downgrade is"
        " not supported. Restore the pre-upgrade database backup instead."
    )
