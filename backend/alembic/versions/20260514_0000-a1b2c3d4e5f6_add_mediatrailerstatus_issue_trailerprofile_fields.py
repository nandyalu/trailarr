"""Add MediaTrailerStatus and Issue tables, add for_movies/download_season_videos/max_count/video_type to TrailerProfile, drop trailer_exists and status from media

Revision ID: a1b2c3d4e5f6
Revises: f1a2b3c4d5e6
Create Date: 2026-05-14 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from app_logger import ModuleLogger


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "f1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

logger = ModuleLogger("AlembicMigrations")


def upgrade() -> None:
    # --- Create mediatrailerstatus table ---
    op.create_table(
        "mediatrailerstatus",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("media_id", sa.Integer(), nullable=False),
        sa.Column("profile_id", sa.Integer(), nullable=True),
        sa.Column("season", sa.Integer(), server_default="0", nullable=False),
        sa.Column("sequence", sa.Integer(), server_default="1", nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("source", sa.String(), nullable=False, server_default="app"),
        sa.Column("linked_download_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["media_id"], ["media.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["profile_id"], ["trailerprofile.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["linked_download_id"], ["download.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "media_id", "profile_id", "season", "sequence",
            name="uq_mediatrailerstatus_media_profile_season_sequence",
        ),
    )
    op.create_index("ix_mediatrailerstatus_media_id", "mediatrailerstatus", ["media_id"])
    op.create_index("ix_mediatrailerstatus_profile_id", "mediatrailerstatus", ["profile_id"])
    logger.info("Created 'mediatrailerstatus' table")

    # --- Create issue table ---
    op.create_table(
        "issue",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("issue_type", sa.String(), nullable=False),
        sa.Column("entity_type", sa.String(), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("details", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_issue_entity",
        "issue",
        ["issue_type", "entity_type", "entity_id"],
        unique=True,
    )
    logger.info("Created 'issue' table")

    # --- Add new columns to trailerprofile ---
    with op.batch_alter_table("trailerprofile", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "video_type",
                sa.String(),
                server_default="trailer",
                nullable=False,
            )
        )
        batch_op.add_column(
            sa.Column(
                "for_movies",
                sa.Boolean(),
                server_default="1",
                nullable=False,
            )
        )
        batch_op.add_column(
            sa.Column(
                "download_season_videos",
                sa.Boolean(),
                server_default="0",
                nullable=False,
            )
        )
        batch_op.add_column(
            sa.Column(
                "max_count",
                sa.Integer(),
                server_default="1",
                nullable=False,
            )
        )
    logger.info(
        "Added 'video_type', 'for_movies', 'download_season_videos', 'max_count'"
        " columns to trailerprofile table"
    )

    # --- Backfill for_movies for existing profiles ---
    # Rules (priority order):
    #   1. Any filter has is_movie=true  → for_movies=True
    #   2. Any filter has is_movie=false → for_movies=False
    #   3. Profile name contains movie/radarr → for_movies=True
    #   4. Profile name contains series/show/sonarr → for_movies=False
    #   5. Else → for_movies=True, enabled=False (user must review)
    conn = op.get_bind()
    rows = conn.execute(sa.text("""
        SELECT tp.id, LOWER(cf.filter_name), LOWER(f.filter_value)
        FROM trailerprofile tp
        JOIN customfilter cf ON cf.id = tp.customfilter_id
        LEFT JOIN "filter" f
            ON f.customfilter_id = cf.id AND LOWER(f.filter_by) = 'is_movie'
    """)).fetchall()

    profile_data: dict = {}
    for profile_id, name, filter_value in rows:
        if profile_id not in profile_data:
            profile_data[profile_id] = {"name": name or "", "is_movie_values": set()}
        if filter_value is not None:
            profile_data[profile_id]["is_movie_values"].add(filter_value)

    for profile_id, data in profile_data.items():
        name: str = data["name"]
        values: set = data["is_movie_values"]
        disable = False

        if "true" in values:
            for_movies = 1
        elif "false" in values:
            for_movies = 0
        elif any(kw in name for kw in ("movie", "radarr")):
            for_movies = 1
        elif any(kw in name for kw in ("series", "show", "sonarr")):
            for_movies = 0
        else:
            for_movies = 1
            disable = True

        if disable:
            conn.execute(
                sa.text(
                    "UPDATE trailerprofile SET for_movies = :fm, enabled = 0"
                    " WHERE id = :id"
                ),
                {"fm": for_movies, "id": profile_id},
            )
        else:
            conn.execute(
                sa.text("UPDATE trailerprofile SET for_movies = :fm WHERE id = :id"),
                {"fm": for_movies, "id": profile_id},
            )

    logger.info("Backfilled 'for_movies' for existing trailer profiles")

    # --- Backfill MediaTrailerStatus ---
    # NOTE: trailer_exists and status columns are dropped AFTER this backfill
    # so that Steps 2.5 and 3 can read trailer_exists to avoid creating duplicate
    # PENDING rows for media that already has a trailer on disk.
    conn = op.get_bind()
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()

    # Step 1: Profile-linked downloads (download.file_exists=True, profile_id>0).
    # One row per (media_id, profile_id); use the latest download record as the link.
    conn.execute(
        sa.text(
            """
            INSERT INTO mediatrailerstatus
                (media_id, profile_id, season, sequence, status, source,
                 linked_download_id, created_at, updated_at)
            SELECT
                d.media_id,
                d.profile_id,
                0, 1, 'downloaded', 'app',
                MAX(d.id), :now, :now
            FROM download d
            WHERE d.file_exists = 1 AND d.profile_id > 0
            GROUP BY d.media_id, d.profile_id
            """
        ),
        {"now": now},
    )
    logger.info("Backfilled profile-linked downloaded MediaTrailerStatus rows")

    # Step 2: Downloaded media with no profile-linked record (manual / unattributed).
    # Covers: download.file_exists=True with profile_id=0, or downloaded_at set
    # with no file_exists=True download at all.
    conn.execute(
        sa.text(
            """
            INSERT INTO mediatrailerstatus
                (media_id, profile_id, season, sequence, status, source,
                 linked_download_id, created_at, updated_at)
            SELECT m.id, NULL, 0, 1, 'downloaded', 'manual', NULL, :now, :now
            FROM media m
            WHERE m.downloaded_at IS NOT NULL
              AND m.id NOT IN (
                  SELECT d.media_id FROM download d
                  WHERE d.file_exists = 1 AND d.profile_id > 0
              )
            """
        ),
        {"now": now},
    )
    logger.info("Backfilled manual downloaded MediaTrailerStatus rows")

    # Step 2.5: Media with trailer_exists=True but no downloaded_at and no existing row.
    # These items have a trailer on disk that was never formally recorded via the
    # download pipeline (e.g. manually placed files, or pre-pipeline era records).
    conn.execute(
        sa.text(
            """
            INSERT INTO mediatrailerstatus
                (media_id, profile_id, season, sequence, status, source,
                 linked_download_id, created_at, updated_at)
            SELECT m.id, NULL, 0, 1, 'downloaded', 'manual', NULL, :now, :now
            FROM media m
            WHERE m.trailer_exists = 1
              AND m.downloaded_at IS NULL
              AND m.id NOT IN (
                  SELECT mts.media_id FROM mediatrailerstatus mts
              )
            """
        ),
        {"now": now},
    )
    logger.info("Backfilled manual downloaded rows for trailer_exists=1 media without downloaded_at")

    # Step 3: All remaining media with no trailer and no existing row → pending.
    # Includes both monitored and unmonitored; the download task skips unmonitored.
    # Excludes media covered by Steps 1, 2, and 2.5 via the NOT IN subquery.
    conn.execute(
        sa.text(
            """
            INSERT INTO mediatrailerstatus
                (media_id, profile_id, season, sequence, status, source,
                 linked_download_id, created_at, updated_at)
            SELECT m.id, NULL, 0, 1, 'pending', 'app', NULL, :now, :now
            FROM media m
            WHERE m.downloaded_at IS NULL
              AND (m.trailer_exists = 0 OR m.trailer_exists IS NULL)
              AND m.id NOT IN (
                  SELECT mts.media_id FROM mediatrailerstatus mts
              )
            """
        ),
        {"now": now},
    )
    logger.info("Backfilled pending MediaTrailerStatus rows for all remaining media")

    # --- Delete stale filter rows referencing dropped columns ---
    # trailer_exists and status are no longer on Media; any filter using them
    # would silently evaluate to False and break create_rows_for_new_media /
    # _sync_status_rows for ALL existing profiles (including the two default ones).
    conn.execute(
        sa.text("DELETE FROM \"filter\" WHERE filter_by IN ('trailer_exists', 'status')")
    )
    logger.info("Deleted stale 'trailer_exists' and 'status' filter rows")

    # --- Drop trailer_exists and status from media ---
    # Dropped AFTER backfill so Steps 2.5 and 3 could use trailer_exists above.
    with op.batch_alter_table("media", schema=None) as batch_op:
        batch_op.drop_column("trailer_exists")
        batch_op.drop_column("status")
    logger.info("Dropped 'trailer_exists' and 'status' columns from media table")


def downgrade() -> None:
    # Re-add status and trailer_exists columns to media
    with op.batch_alter_table("media", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "trailer_exists",
                sa.Boolean(),
                server_default="0",
                nullable=False,
            )
        )
        batch_op.add_column(
            sa.Column(
                "status",
                sa.String(),
                server_default="missing",
                nullable=False,
            )
        )

    # Drop new trailerprofile columns
    with op.batch_alter_table("trailerprofile", schema=None) as batch_op:
        batch_op.drop_column("max_count")
        batch_op.drop_column("download_season_videos")
        batch_op.drop_column("for_movies")
        batch_op.drop_column("video_type")

    # Drop new tables
    op.drop_table("issue")
    op.drop_table("mediatrailerstatus")
    logger.info("Downgrade complete: dropped issue, mediatrailerstatus tables and reverted media/trailerprofile columns")
