"""Index the foreign keys of download and filefolderinfo (#732)

No index covered `download.media_id`, `filefolderinfo.media_id` or
`filefolderinfo.parent_id`. Each lookup of the downloads or the folder of
one media item read the whole table, and each delete of a media row
checked every row of `filefolderinfo`. On a large library, the scan, the
refresh and the download tasks ran for hours.

The indexes are created without a batch operation, so SQLite does not
copy the tables. ANALYZE then gives the query planner its first
statistics. Without them, SQLite used the index on `mediavideo.source`
in place of the index on `mediavideo.media_id`.

Revision ID: f295ffc28658
Revises: d4e6f1a7b3c5
Create Date: 2026-11-02 23:56:38.075702

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'f295ffc28658'
down_revision: Union[str, None] = 'd4e6f1a7b3c5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_INDEXES = (
    ("ix_download_media_id", "download", "media_id"),
    ("ix_filefolderinfo_media_id", "filefolderinfo", "media_id"),
    ("ix_filefolderinfo_parent_id", "filefolderinfo", "parent_id"),
)


def upgrade() -> None:
    for name, table, column in _INDEXES:
        op.create_index(name, table, [column], unique=False)
    op.execute("ANALYZE")


def downgrade() -> None:
    for name, table, _column in reversed(_INDEXES):
        op.drop_index(name, table_name=table)
