"""Add video types to profiles and downloads (Phase 9)

A profile gets a `video_type` ('trailer' by default) and a download
records the type it has. Every row that exists is a trailer: Trailarr
downloaded trailers only until this version.

The migration also does four small things that belong to the same
release:

- A download with no profile (profile_id = 0) takes the type that its
  name and folder say. Such a file was found on disk and no profile
  claimed it, so a new label cannot make a profile unsatisfied. A
  download that a profile owns keeps 'trailer': its profile is a trailer
  profile, and the two must agree, or the profile downloads again
  (wargame W1). When a person changes the type of a profile, its
  downloads change with it.
- `trailerprofile.max_duration` above 1200 is clamped to 1200, the new
  limit. The old check in the model let any value through (#686).
- `media.last_videos_refresh` is set to NULL, so the next refresh asks
  TMDB again: the lists in the table hold trailers only, and a profile of
  another type would find nothing for seven days (wargame W6).
- The TMDB list of each media item is then fetched again with every type.

Revision ID: 9a1c4e7b2d30
Revises: 65e07a32e5d9
Create Date: 2026-10-07 12:00:00.000000

"""
from pathlib import PurePosixPath, PureWindowsPath
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from app_logger import ModuleLogger


# revision identifiers, used by Alembic.
revision: str = '9a1c4e7b2d30'
down_revision: Union[str, None] = '65e07a32e5d9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

logger = ModuleLogger("AlembicMigrations")

MAX_DURATION_LIMIT = 1200

# The same tables as `database/models/video_type.py`, copied here so that
# the migration reads the same way in every future version of the module.
_SUFFIX_TO_TYPE = {
    "trailer": "trailer",
    "teaser": "teaser",
    "clip": "clip",
    "scene": "clip",
    "featurette": "featurette",
    "interview": "featurette",
    "behindthescenes": "behind_the_scenes",
    "bloopers": "bloopers",
    "short": "other",
    "deleted": "other",
    "extra": "other",
    "sample": "other",
    "other": "other",
}
_FOLDER_TO_TYPE = {
    "trailer": "trailer",
    "trailers": "trailer",
    "teasers": "teaser",
    "clips": "clip",
    "scenes": "clip",
    "featurettes": "featurette",
    "interviews": "featurette",
    "behind the scenes": "behind_the_scenes",
    "bloopers": "bloopers",
    "shorts": "other",
    "deleted scenes": "other",
    "extras": "other",
    "samples": "other",
    "other": "other",
    "others": "other",
}
_SUFFIXES_BY_LENGTH = sorted(_SUFFIX_TO_TYPE, key=len, reverse=True)


def _split(path: str) -> tuple[str, str]:
    """The lowercase stem and parent folder name of a path, for a path
    written on Linux or on Windows."""
    pure = PureWindowsPath(path) if "\\" in path else PurePosixPath(path)
    return pure.stem.strip().lower(), pure.parent.name.strip().lower()


def _classify(path: str) -> str:
    """The type the name of a file says, 'trailer' when nothing does."""
    stem, parent = _split(path)
    for suffix in _SUFFIXES_BY_LENGTH:
        if stem.endswith(f"-{suffix}"):
            return _SUFFIX_TO_TYPE[suffix]
    if parent in _FOLDER_TO_TYPE:
        return _FOLDER_TO_TYPE[parent]
    return "trailer"


def _label_unattributed_downloads(conn) -> None:
    rows = conn.execute(
        sa.text(
            "SELECT id, path FROM download WHERE profile_id = 0"
        )
    ).fetchall()
    changed = 0
    for row in rows:
        video_type = _classify(row.path or "")
        if video_type == "trailer":
            continue
        conn.execute(
            sa.text("UPDATE download SET video_type = :t WHERE id = :id"),
            {"t": video_type, "id": row.id},
        )
        changed += 1
    if changed:
        logger.info(
            f"Trailarr read the video type of {changed} downloads that have"
            " no profile from their file names."
        )


def _clamp_max_duration(conn) -> None:
    rows = conn.execute(
        sa.text(
            """
            SELECT p.id, p.max_duration, cf.filter_name
            FROM trailerprofile p
            LEFT JOIN customfilter cf ON cf.id = p.customfilter_id
            WHERE p.max_duration > :limit
            """
        ),
        {"limit": MAX_DURATION_LIMIT},
    ).fetchall()
    for row in rows:
        logger.warning(
            f"The profile '{row.filter_name}' had a Maximum Duration of"
            f" {row.max_duration} seconds. Trailarr set it to"
            f" {MAX_DURATION_LIMIT}, the largest value it accepts."
        )
    conn.execute(
        sa.text(
            "UPDATE trailerprofile SET max_duration = :limit"
            " WHERE max_duration > :limit"
        ),
        {"limit": MAX_DURATION_LIMIT},
    )


def upgrade() -> None:
    op.execute("PRAGMA foreign_keys=OFF")

    with op.batch_alter_table("trailerprofile", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "video_type",
                sa.String(),
                server_default="trailer",
                nullable=False,
            )
        )
    with op.batch_alter_table("download", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "video_type",
                sa.String(),
                server_default="trailer",
                nullable=False,
            )
        )
        batch_op.create_index(
            "ix_download_video_type", ["video_type"], unique=False
        )

    conn = op.get_bind()
    _label_unattributed_downloads(conn)
    _clamp_max_duration(conn)
    # Wargame W6: the TMDB lists hold trailers only. Make them stale.
    conn.execute(sa.text("UPDATE media SET last_videos_refresh = NULL"))

    op.execute("PRAGMA foreign_keys=ON")


def downgrade() -> None:
    op.execute("PRAGMA foreign_keys=OFF")

    with op.batch_alter_table("download", schema=None) as batch_op:
        batch_op.drop_index("ix_download_video_type")
        batch_op.drop_column("video_type")
    with op.batch_alter_table("trailerprofile", schema=None) as batch_op:
        batch_op.drop_column("video_type")

    op.execute("PRAGMA foreign_keys=ON")
